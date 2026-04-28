"""Unit tests for studio_trend_scout.py -- Content Intelligence Scout Phase 1.

Covers:
1. Monday gate skips non-Monday
2. Monday gate fires on Monday
3. _serper_search returns results
4. _serper_search graceful degrade (no key)
5. Haiku classifier drops low-fit picks
6. Haiku classifier keeps high-fit picks
7. CW niche routes to _write_to_content_board
8. Studio niche routes to _write_to_studio_pipeline
9. scout_approve callback flips Status to Ready
10. scout_reject callback flips Status to Archived

No network calls. All external I/O is mocked.
"""
from __future__ import annotations

import json
import os
import sys
import types
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call

import pytest
import pytz

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)


@pytest.fixture(autouse=True)
def _env_setup(monkeypatch):
    monkeypatch.setenv("NOTION_STUDIO_PIPELINE_DB_ID", "test-pipeline-db-id")
    monkeypatch.setenv("FORGE_CONTENT_DB", "test-content-board-db-id")
    monkeypatch.setenv("OWNER_TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setenv("HEARTBEAT_TIMEZONE", "America/Denver")


# ═════════════════════════════════════════════════════════════════════════════
# 1 & 2: Monday gate
# ═════════════════════════════════════════════════════════════════════════════

def test_monday_gate_skips_non_monday(monkeypatch):
    """Non-Monday tick returns immediately without doing any work."""
    import importlib
    import studio_trend_scout as scout
    importlib.reload(scout)

    # Tuesday = weekday 1
    tuesday = datetime(2026, 4, 28, 7, 0, 0, tzinfo=pytz.timezone("America/Denver").localize(
        datetime(2026, 4, 28, 7, 0, 0)
    ).tzinfo)
    # Easier: patch datetime.now inside the module
    fake_dt = MagicMock()
    fake_dt.weekday.return_value = 1  # Tuesday

    notion_cls = MagicMock()
    with patch("studio_trend_scout.datetime") as mock_dt:
        mock_dt.now.return_value = fake_dt
        # If the gate is working, Notion should never be opened
        with patch("skills.forge_cli.notion_client.NotionClient", notion_cls):
            scout.studio_trend_scout_tick()

    notion_cls.assert_not_called()


def test_monday_gate_fires_on_monday(monkeypatch):
    """Monday tick opens Notion and proceeds past the gate."""
    import importlib
    import studio_trend_scout as scout
    importlib.reload(scout)

    fake_dt = MagicMock()
    fake_dt.weekday.return_value = 0  # Monday
    fake_dt.date.return_value.isoformat.return_value = "2026-04-28"

    notion = MagicMock()
    notion.query_database.return_value = []
    notion.create_page.return_value = {"id": "page-123"}
    notion_cls = MagicMock(return_value=notion)

    mock_notifier = types.ModuleType("notifier")
    mock_notifier.send_message = MagicMock()
    mock_notifier.send_message_with_buttons = MagicMock()

    mock_llm_helpers = types.ModuleType("llm_helpers")
    mock_llm_helpers.call_llm = MagicMock(return_value=MagicMock(
        choices=[MagicMock(message=MagicMock(content='{"fit": 0, "medium": "LinkedIn post", "first_line": "", "unique_add": "", "destination": "Studio Pipeline"}'))]
    ))

    with patch("studio_trend_scout.datetime") as mock_dt, \
         patch("skills.forge_cli.notion_client.NotionClient", notion_cls), \
         patch.dict("sys.modules", {"notifier": mock_notifier, "llm_helpers": mock_llm_helpers}):
        mock_dt.now.return_value = fake_dt
        scout.studio_trend_scout_tick()

    # Notion was initialised -- gate was passed
    notion_cls.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# 3 & 4: _serper_search
# ═════════════════════════════════════════════════════════════════════════════

def test_serper_search_returns_results(monkeypatch):
    """Mock httpx.post to verify _serper_search parses the response correctly."""
    import studio_trend_scout as scout
    monkeypatch.setenv("SERPER_API_KEY", "test-serper-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "news": [
            {"title": "AI Act passes", "link": "https://example.com/1", "snippet": "The EU...", "source": "Reuters", "date": "2026-04-25"},
            {"title": "SMB AI tools", "link": "https://example.com/2", "snippet": "Small biz...", "source": "Forbes", "date": "2026-04-24"},
        ]
    }

    with patch("httpx.post", return_value=mock_resp):
        results = scout._serper_search("EU AI Act 2026", max_results=5)

    assert len(results) == 2
    assert results[0]["title"] == "AI Act passes"
    assert results[0]["link"] == "https://example.com/1"
    assert results[0]["snippet"] == "The EU..."
    assert results[0]["source"] == "Reuters"
    assert results[1]["title"] == "SMB AI tools"


def test_serper_search_graceful_degrade_no_key(monkeypatch):
    """Missing SERPER_API_KEY returns [] without any network call."""
    import studio_trend_scout as scout
    monkeypatch.delenv("SERPER_API_KEY", raising=False)

    with patch("httpx.post") as mock_post:
        results = scout._serper_search("anything")

    assert results == []
    mock_post.assert_not_called()


# ═════════════════════════════════════════════════════════════════════════════
# 5 & 6: Haiku classifier
# ═════════════════════════════════════════════════════════════════════════════

def _make_cand(**kwargs):
    import studio_trend_scout as scout
    defaults = dict(
        niche="ai-tools-smb",
        channel="Catalyst Works",
        source_url="https://example.com/article",
        source_channel="TechCrunch",
        title="AI saves SMBs time",
        views=0,
        published_at="2026-04-25",
        velocity_per_hour=0.0,
        snippet="Small businesses are saving hours...",
        destination="Content Board",
    )
    defaults.update(kwargs)
    return scout.TrendCandidate(**defaults)


def test_haiku_classifier_drops_low_fit(monkeypatch):
    """fit=2 (below FIT_THRESHOLD=3) means pick is dropped by scout_niche caller."""
    import studio_trend_scout as scout

    low_fit_response = MagicMock()
    low_fit_response.choices = [MagicMock(message=MagicMock(content=json.dumps({
        "fit": 2,
        "medium": "LinkedIn post",
        "first_line": "meh opener",
        "unique_add": "nothing unique",
        "destination": "Content Board",
    })))]

    mock_llm_helpers = types.ModuleType("llm_helpers")
    mock_llm_helpers.call_llm = MagicMock(return_value=low_fit_response)

    with patch.dict("sys.modules", {"llm_helpers": mock_llm_helpers}):
        cand = _make_cand()
        result = scout._classify_pick(cand)

    assert result.fit_score == 2
    # Caller logic: dropped when fit_score < FIT_THRESHOLD (3)
    assert result.fit_score < scout.FIT_THRESHOLD


def test_haiku_classifier_keeps_high_fit(monkeypatch):
    """fit=4 passes the threshold; fields are populated from classifier JSON."""
    import studio_trend_scout as scout

    high_fit_response = MagicMock()
    high_fit_response.choices = [MagicMock(message=MagicMock(content=json.dumps({
        "fit": 4,
        "medium": "LinkedIn article",
        "first_line": "Most AI tools sold to SMBs solve the wrong problem.",
        "unique_add": "Boubacar can name the operational gap that AI is covering for.",
        "destination": "Content Board",
    })))]

    mock_llm_helpers = types.ModuleType("llm_helpers")
    mock_llm_helpers.call_llm = MagicMock(return_value=high_fit_response)

    with patch.dict("sys.modules", {"llm_helpers": mock_llm_helpers}):
        cand = _make_cand()
        result = scout._classify_pick(cand)

    assert result.fit_score == 4
    assert result.fit_score >= scout.FIT_THRESHOLD
    assert result.medium == "LinkedIn article"
    assert "SMBs solve the wrong problem" in result.first_line
    assert result.destination == "Content Board"


# ═════════════════════════════════════════════════════════════════════════════
# 7 & 8: Notion routing
# ═════════════════════════════════════════════════════════════════════════════

def test_routing_content_board(monkeypatch):
    """CW niche pick (destination=Content Board) goes to _write_to_content_board."""
    import studio_trend_scout as scout

    notion = MagicMock()
    notion.create_page.return_value = {"id": "cb-page-id"}

    cand = _make_cand(destination="Content Board", fit_score=4, medium="LinkedIn post",
                      first_line="opener", unique_add="angle")

    page_id = scout._write_to_content_board(notion, cand)

    notion.create_page.assert_called_once()
    call_kwargs = notion.create_page.call_args
    db_used = call_kwargs[1].get("database_id") or call_kwargs[0][0]
    assert db_used == "test-content-board-db-id"
    # Status must be Draft
    props = call_kwargs[1].get("properties") or call_kwargs[0][1]
    assert props["Status"]["select"]["name"] == "Draft"
    assert page_id == "cb-page-id"


def test_routing_studio_pipeline(monkeypatch):
    """Studio niche pick (destination=Studio Pipeline) goes to _write_to_studio_pipeline."""
    import studio_trend_scout as scout

    notion = MagicMock()
    notion.create_page.return_value = {"id": "sp-page-id"}

    cand = _make_cand(destination="Studio Pipeline", niche="african-folktales",
                      channel="Under the Baobab", fit_score=4)

    page_id = scout._write_to_studio_pipeline(notion, cand)

    notion.create_page.assert_called_once()
    call_kwargs = notion.create_page.call_args
    db_used = call_kwargs[1].get("database_id") or call_kwargs[0][0]
    assert db_used == "test-pipeline-db-id"
    props = call_kwargs[1].get("properties") or call_kwargs[0][1]
    assert props["Status"]["select"]["name"] == "scouted"
    assert page_id == "sp-page-id"


# ═════════════════════════════════════════════════════════════════════════════
# 9 & 10: Approve/Reject callbacks in handlers_approvals
# ═════════════════════════════════════════════════════════════════════════════

def _make_callback_update(cb_data: str, chat_id: str = "99999", sender_id: str = "42") -> dict:
    return {
        "callback_query": {
            "id": "cb-id-123",
            "data": cb_data,
            "from": {"id": sender_id},
            "message": {"chat": {"id": chat_id}},
        }
    }


def test_approve_callback_flips_status_to_ready(monkeypatch):
    """scout_approve:<page_id> should call Notion update with Status=Ready."""
    # Patch env so ALLOWED_USER_IDS is open (empty = allow all)
    monkeypatch.setenv("ALLOWED_USER_IDS", "")
    monkeypatch.setenv("NOTION_SECRET", "test-secret")

    import handlers_approvals

    mock_notion = MagicMock()
    mock_notifier = types.ModuleType("notifier")
    mock_notifier.answer_callback_query = MagicMock()
    mock_notifier.send_message = MagicMock()

    with patch.object(handlers_approvals, "_open_notion", return_value=mock_notion), \
         patch.dict("sys.modules", {"notifier": mock_notifier}):
        update = _make_callback_update("scout_approve:notion-page-abc123")
        result = handlers_approvals.handle_callback_query(update)

    assert result is True
    mock_notion.update_page.assert_called_once_with(
        "notion-page-abc123",
        properties={"Status": {"select": {"name": "Ready"}}}
    )
    mock_notifier.answer_callback_query.assert_called_once()


def test_reject_callback_flips_status_to_archived(monkeypatch):
    """scout_reject:<page_id> should call Notion update with Status=Archived."""
    monkeypatch.setenv("ALLOWED_USER_IDS", "")
    monkeypatch.setenv("NOTION_SECRET", "test-secret")

    import handlers_approvals

    mock_notion = MagicMock()
    mock_notifier = types.ModuleType("notifier")
    mock_notifier.answer_callback_query = MagicMock()
    mock_notifier.send_message = MagicMock()

    with patch.object(handlers_approvals, "_open_notion", return_value=mock_notion), \
         patch.dict("sys.modules", {"notifier": mock_notifier}):
        update = _make_callback_update("scout_reject:notion-page-abc123")
        result = handlers_approvals.handle_callback_query(update)

    assert result is True
    mock_notion.update_page.assert_called_once_with(
        "notion-page-abc123",
        properties={"Status": {"select": {"name": "Archived"}}}
    )
    mock_notifier.answer_callback_query.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# Legacy path: seeds loading and YouTube helpers (regression guard)
# ═════════════════════════════════════════════════════════════════════════════

def test_load_seeds_falls_back_to_module_default():
    import studio_trend_scout as scout
    seeds = scout._load_seeds()
    # Default seeds file has african-folktales + first-gen-money; module fallback has ai-displacement
    assert len(seeds) >= 3


def test_yt_search_returns_empty_without_api_key(monkeypatch):
    import studio_trend_scout as scout
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert scout._yt_search("anything") == []


def test_existing_source_urls_returns_set():
    import studio_trend_scout as scout
    notion = MagicMock()
    notion.query_database.return_value = [
        {"properties": {"Source URL": {"url": "https://youtube.com/watch?v=a"}}},
        {"properties": {"Source URL": {"url": "https://youtube.com/watch?v=b"}}},
        {"properties": {"Source URL": {"url": None}}},
    ]
    out = scout._existing_source_urls_today(notion, "2026-04-25")
    assert "https://youtube.com/watch?v=a" in out
    assert "https://youtube.com/watch?v=b" in out
    assert len(out) == 2
