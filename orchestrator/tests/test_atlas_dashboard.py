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


def test_get_content_returns_items():
    mock_items = [
        {"title": "Post A", "status": "Queued", "scheduled_date": "2026-04-26", "platform": "LinkedIn"},
        {"title": "Post B", "status": "Draft",  "scheduled_date": None,         "platform": "X"},
    ]
    with patch("atlas_dashboard._fetch_content_board", return_value=mock_items):
        result = atlas_dashboard.get_content()

    assert result["count"] == 2
    assert result["items"][0]["title"] == "Post A"


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
    assert "last_action" in result
    assert "next_fire" in result
    assert "spend_pacing" in result
