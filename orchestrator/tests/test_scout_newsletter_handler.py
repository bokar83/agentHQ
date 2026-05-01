from __future__ import annotations

import os
import sys
import types
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytz

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)


def _make_callback_update(cb_data: str, chat_id: str = "99999", sender_id: str = "42") -> dict:
    return {
        "callback_query": {
            "id": "cb-id-123",
            "data": cb_data,
            "from": {"id": sender_id},
            "message": {"chat": {"id": chat_id}},
        }
    }


def test_send_pick_with_buttons_adds_newsletter_only_for_content_board(monkeypatch):
    import studio_trend_scout as scout

    monkeypatch.setenv("OWNER_TELEGRAM_CHAT_ID", "12345")
    mock_notifier = types.ModuleType("notifier")
    mock_notifier.send_message_with_buttons = MagicMock()

    cw_pick = scout.TrendCandidate(
        niche="ops",
        channel="YouTube",
        source_url="https://example.com/cw",
        source_channel="example.com",
        title="CW title",
        views=1000,
        published_at="2026-04-30T12:00:00Z",
        velocity_per_hour=10.0,
        fit_score=5,
        medium="LinkedIn post",
        first_line="Opening line",
        unique_add="Angle",
        destination="Content Board",
    )
    studio_pick = scout.TrendCandidate(
        niche="studio",
        channel="YouTube",
        source_url="https://example.com/studio",
        source_channel="example.com",
        title="Studio title",
        views=1000,
        published_at="2026-04-30T12:00:00Z",
        velocity_per_hour=10.0,
        fit_score=5,
        medium="LinkedIn post",
        first_line="Opening line",
        unique_add="Angle",
        destination="Studio Pipeline",
    )

    with patch.dict("sys.modules", {"notifier": mock_notifier}):
        scout._send_pick_with_buttons(cw_pick, "cw-page-id")
        scout._send_pick_with_buttons(studio_pick, "studio-page-id")

    cw_buttons = mock_notifier.send_message_with_buttons.call_args_list[0].args[2]
    studio_buttons = mock_notifier.send_message_with_buttons.call_args_list[1].args[2]

    assert ("Newsletter", "scout_newsletter:cw-page-id") in cw_buttons[0]
    assert ("Newsletter", "scout_newsletter:studio-page-id") not in studio_buttons[0]


def test_scout_newsletter_rejects_cross_talk_type():
    import handlers_approvals

    mock_notion = MagicMock()
    mock_notion.get_page.return_value = {
        "id": "notion-page-abc123",
        "properties": {"Type": {"select": {"name": "X Post"}}},
    }
    mock_notifier = types.ModuleType("notifier")
    mock_notifier.answer_callback_query = MagicMock()
    mock_notifier.send_message = MagicMock()

    with patch.object(handlers_approvals, "_open_notion", return_value=mock_notion), \
         patch.dict("sys.modules", {"notifier": mock_notifier}):
        result = handlers_approvals.handle_callback_query(
            _make_callback_update("scout_newsletter:notion-page-abc123")
        )

    assert result is True
    mock_notion.get_page.assert_called_once_with("notion-page-abc123")
    mock_notion.update_page.assert_not_called()
    mock_notion.query_database.assert_not_called()
    mock_notifier.send_message.assert_called_once()
    assert "already typed as X Post" in mock_notifier.send_message.call_args.args[1]


def test_scout_newsletter_sets_new_anchor_and_clears_previous_anchors_today():
    import handlers_approvals

    fake_now = datetime(2026, 4, 30, 9, 0, tzinfo=pytz.timezone("America/Denver"))
    mock_notion = MagicMock()
    mock_notion.get_page.return_value = {
        "id": "notion-page-abc123",
        "properties": {"Type": {"select": None}},
    }
    mock_notion.query_database.return_value = [
        {"id": "notion-page-abc123"},
        {"id": "old-anchor-1"},
        {"id": "old-anchor-2"},
    ]
    mock_notifier = types.ModuleType("notifier")
    mock_notifier.answer_callback_query = MagicMock()
    mock_notifier.send_message = MagicMock()

    with patch.object(handlers_approvals, "_open_notion", return_value=mock_notion), \
         patch.object(handlers_approvals, "_now_local", return_value=fake_now), \
         patch.dict("sys.modules", {"notifier": mock_notifier}):
        result = handlers_approvals.handle_callback_query(
            _make_callback_update("scout_newsletter:notion-page-abc123")
        )

    assert result is True
    mock_notion.get_page.assert_called_once_with("notion-page-abc123")
    assert mock_notion.update_page.call_count == 3
    first_call = mock_notion.update_page.call_args_list[0]
    assert first_call.args[0] == "notion-page-abc123"
    assert first_call.kwargs["properties"] == {
        "Type": {"select": {"name": "Newsletter"}},
        "Platform": {"multi_select": [{"name": "Beehiiv"}]},
        "Anchor Date": {"date": {"start": "2026-04-30"}},
    }
    clear_props = {
        "Type": {"select": None},
        "Platform": {"multi_select": []},
        "Anchor Date": {"date": None},
    }
    assert mock_notion.update_page.call_args_list[1].args[0] == "old-anchor-1"
    assert mock_notion.update_page.call_args_list[1].kwargs["properties"] == clear_props
    assert mock_notion.update_page.call_args_list[2].args[0] == "old-anchor-2"
    assert mock_notion.update_page.call_args_list[2].kwargs["properties"] == clear_props
    query_filter = mock_notion.query_database.call_args.kwargs["filter_obj"]
    assert query_filter == {
        "and": [
            {"property": "Anchor Date", "date": {"equals": "2026-04-30"}},
            {"property": "Type", "select": {"equals": "Newsletter"}},
        ]
    }
    sent_text = mock_notifier.send_message.call_args.args[1]
    assert "Newsletter anchor set" in sent_text
    assert "old-anchor-1" in sent_text
    assert "old-anchor-2" in sent_text


def test_scout_newsletter_allows_existing_newsletter_without_cross_talk():
    import handlers_approvals

    fake_now = datetime(2026, 4, 30, 9, 0, tzinfo=pytz.timezone("America/Denver"))
    mock_notion = MagicMock()
    mock_notion.get_page.return_value = {
        "id": "notion-page-abc123",
        "properties": {"Type": {"select": {"name": "Newsletter"}}},
    }
    mock_notion.query_database.return_value = []
    mock_notifier = types.ModuleType("notifier")
    mock_notifier.answer_callback_query = MagicMock()
    mock_notifier.send_message = MagicMock()

    with patch.object(handlers_approvals, "_open_notion", return_value=mock_notion), \
         patch.object(handlers_approvals, "_now_local", return_value=fake_now), \
         patch.dict("sys.modules", {"notifier": mock_notifier}):
        result = handlers_approvals.handle_callback_query(
            _make_callback_update("scout_newsletter:notion-page-abc123")
        )

    assert result is True
    mock_notion.update_page.assert_called_once_with(
        "notion-page-abc123",
        properties={
            "Type": {"select": {"name": "Newsletter"}},
            "Platform": {"multi_select": [{"name": "Beehiiv"}]},
            "Anchor Date": {"date": {"start": "2026-04-30"}},
        },
    )
