# orchestrator/tests/test_atlas_dashboard.py
import json
import os
import sys

import pytest

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)

from unittest.mock import MagicMock, patch
import atlas_dashboard


def test_get_state_returns_expected_shape():
    state = {
        "killed": False,
        "killed_reason": None,
        "crews": {"griot": {"enabled": True, "dry_run": False}},
        "cap_usd": 1.0,
    }
    with patch("autonomy_guard.get_guard") as mock_guard:
        mock_guard.return_value.state_summary.return_value = state
        result = atlas_dashboard.get_state()

    assert result["killed"] is False
    assert "crews" in result
    assert "griot" in result["crews"]
    assert result["cap_usd"] == 1.0


def test_get_queue_returns_pending_rows():
    from datetime import datetime
    mock_row = MagicMock()
    mock_row.id = 42
    mock_row.ts_created = datetime(2026, 4, 25, 10, 0, 0)
    mock_row.crew_name = "griot"
    mock_row.proposal_type = "linkedin_post"
    mock_row.payload = {"title": "Test post"}
    mock_row.status = "pending"

    with patch("approval_queue.list_pending", return_value=[mock_row]):
        result = atlas_dashboard.get_queue()

    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["id"] == 42
    assert item["crew_name"] == "griot"
    assert item["proposal_type"] == "linkedin_post"
    assert "ts_created" in item
    assert item["notion_url"] == ""  # no notion_id in payload, no url


def test_get_queue_builds_notion_url_from_notion_id():
    from datetime import datetime
    mock_row = MagicMock()
    mock_row.id = 7
    mock_row.ts_created = datetime(2026, 4, 30, 10, 0, 0)
    mock_row.crew_name = "griot"
    mock_row.proposal_type = "post_candidate"
    mock_row.payload = {"title": "x", "notion_id": "341bcf1a-3029-8175-9710-e42c46133e08"}
    mock_row.status = "pending"
    with patch("approval_queue.list_pending", return_value=[mock_row]):
        item = atlas_dashboard.get_queue()["items"][0]
    assert item["notion_url"] == "https://www.notion.so/341bcf1a302981759710e42c46133e08"


def test_get_queue_prefers_explicit_notion_url():
    from datetime import datetime
    mock_row = MagicMock()
    mock_row.id = 8
    mock_row.ts_created = datetime(2026, 4, 30, 10, 0, 0)
    mock_row.crew_name = "griot"
    mock_row.proposal_type = "post_candidate"
    explicit = "https://app.notion.com/p/something-abc123"
    mock_row.payload = {"title": "x", "notion_url": explicit, "notion_id": "ignore"}
    mock_row.status = "pending"
    with patch("approval_queue.list_pending", return_value=[mock_row]):
        item = atlas_dashboard.get_queue()["items"][0]
    assert item["notion_url"] == explicit


def test_get_content_returns_items():
    mock_board = {
        "recent": [{"title": "Post A", "status": "Posted", "scheduled_date": "2026-04-25", "platform": "LinkedIn"}],
        "upcoming": [{"title": "Post B", "status": "Queued", "scheduled_date": "2026-04-27", "platform": "X"}],
        "past_due": [],
    }
    with patch("atlas_dashboard._fetch_content_board", return_value=mock_board):
        result = atlas_dashboard.get_content()

    assert result["count"] == 2
    assert result["recent"][0]["title"] == "Post A"


def test_get_spend_returns_shape():
    mock_snap = MagicMock()
    mock_snap.spent_today_usd = 0.12
    mock_snap.cap_usd = 1.0
    mock_snap.remaining_usd = 0.88
    mock_snap.per_crew = {"griot": 0.10, "chairman": 0.02}

    with patch("autonomy_guard.get_guard") as mock_guard, \
         patch("atlas_dashboard._spend_7d_by_day", return_value=[{"date": "2026-04-25", "usd": 0.12}]):
        mock_guard.return_value.snapshot.return_value = mock_snap
        result = atlas_dashboard.get_spend()

    assert result["today"]["spent_usd"] == 0.12
    assert result["today"]["cap_usd"] == 1.0
    assert result["today"]["remaining_usd"] == 0.88
    assert len(result["by_day"]) == 1


def test_get_spend_includes_token_totals_and_ledger_ts():
    """Token totals and ledger_last_ts must surface from _spend_aggregates."""
    mock_snap = MagicMock()
    mock_snap.spent_today_usd = 0.0
    mock_snap.cap_usd = 1.0
    mock_snap.remaining_usd = 1.0
    mock_snap.per_crew = {}

    agg = {
        "today_usd": 0.0, "last_day_usd": 0.0, "last_day_date": None,
        "show_last_day": False, "week_usd": 0.5, "month_usd": 1.25,
        "today_tokens": 0, "week_tokens": 12_345, "month_tokens": 98_765,
        "ledger_last_ts": "2026-04-23T23:58:27+00:00",
    }
    with patch("autonomy_guard.get_guard") as mock_guard, \
         patch("atlas_dashboard._spend_aggregates", return_value=agg), \
         patch("atlas_dashboard._spend_7d_by_day", return_value=[]):
        mock_guard.return_value.snapshot.return_value = mock_snap
        result = atlas_dashboard.get_spend()

    assert result["today_tokens"] == 0
    assert result["week_tokens"] == 12_345
    assert result["month_tokens"] == 98_765
    assert result["ledger_last_ts"] == "2026-04-23T23:58:27+00:00"


def test_last_autonomous_action_ignores_heartbeat_self_test():
    """heartbeat-self-test fires every minute -- must be filtered out so the
    Hero strip surfaces real autonomous work (auto_publisher, griot, etc.)."""
    from datetime import datetime, timezone
    import importlib
    import memory

    # Ensure attribute exists for patch's get_original() lookup. Test ordering
    # in the full suite can leave `memory` partially imported on Windows where
    # psycopg2 isn't available; reimporting guarantees _pg_conn is on the module.
    if not hasattr(memory, "_pg_conn"):
        importlib.reload(memory)

    real_action_ts = datetime(2026, 4, 30, 13, 2, 15, tzinfo=timezone.utc)
    fake_row = (real_action_ts, "auto_publisher", None, "success")

    fake_cur = MagicMock()
    fake_cur.fetchone.return_value = fake_row
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cur

    with patch.object(memory, "_pg_conn", return_value=fake_conn):
        result = atlas_dashboard._last_autonomous_action()

    sql_arg = fake_cur.execute.call_args.args[0]
    assert "heartbeat-self-test" in sql_arg
    assert "<>" in sql_arg or "!=" in sql_arg or "NOT IN" in sql_arg.upper()

    assert result["task_type"] == "auto_publisher"
    assert result["description"] == "success"
    assert result["ts"] == real_action_ts.isoformat()


def test_get_heartbeats_returns_wakes():
    mock_wake = MagicMock()
    mock_wake.name = "griot_daily"
    mock_wake.crew_name = "griot"
    mock_wake.at_hour = 7
    mock_wake.at_minute = 30
    mock_wake.every_seconds = None
    mock_wake.last_fired_epoch = None
    mock_wake.last_fired_date = None

    with patch("heartbeat.list_wakes", return_value=[mock_wake]):
        result = atlas_dashboard.get_heartbeats()

    assert len(result["wakes"]) == 1
    w = result["wakes"][0]
    assert w["name"] == "griot_daily"
    assert w["at_hour"] == 7


def test_get_errors_returns_shape():
    with patch("atlas_dashboard._router_log_fallbacks", return_value=[
        {"ts": "2026-04-25T09:00:00", "task_type": "griot_run", "raw_input": "test"}
    ]):
        with patch("atlas_dashboard._error_log_tail", return_value=[]):
            result = atlas_dashboard.get_errors()

    assert "fallbacks" in result
    assert "log_lines" in result
    assert len(result["fallbacks"]) == 1


def test_get_hero_returns_four_tiles():
    mock_snap = MagicMock()
    mock_snap.spent_today_usd = 0.05
    mock_snap.cap_usd = 1.0
    mock_snap.remaining_usd = 0.95

    with patch("autonomy_guard.get_guard") as mg, \
         patch("atlas_dashboard._next_scheduled_fire", return_value={"name": "griot_daily", "at": "07:30", "in_minutes": 60}), \
         patch("atlas_dashboard._last_autonomous_action", return_value={"ts": "2026-04-25T07:30:00", "description": "Griot posted"}), \
         patch("atlas_dashboard._router_log_fallbacks", return_value=[]):
        mg.return_value.snapshot.return_value = mock_snap
        mg.return_value.is_killed.return_value = False
        result = atlas_dashboard.get_hero()

    assert result["system_status"] in ("green", "amber", "red")
    assert result["system_status"] == "green"
    assert "killed" in result
    assert result["killed"] is False
    assert "last_action" in result
    assert "next_fire" in result
    assert "spend_pacing" in result


def test_get_ideas_returns_ranked():
    mock_items = [
        {"title": "High Impact Low Effort", "impact": "High", "effort": "Low", "category": "Feature", "status": "New", "score": 6},
        {"title": "Medium Impact Medium Effort", "impact": "Medium", "effort": "Medium", "category": "Tool", "status": "New", "score": 4},
    ]
    with patch("atlas_dashboard._fetch_ideas", return_value=mock_items):
        result = atlas_dashboard.get_ideas()

    assert result["count"] == 2
    assert result["items"][0]["score"] == 6
    assert result["items"][0]["title"] == "High Impact Low Effort"
