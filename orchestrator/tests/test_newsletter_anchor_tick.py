"""Tests for Monday newsletter anchor drafting tick."""
from __future__ import annotations

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytz

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)


def _anchor_page(page_id: str = "anchor-page-123") -> dict:
    return {
        "id": page_id,
        "properties": {
            "Title": {"title": [{"plain_text": "Why operators need tighter feedback loops"}]},
            "Source Note": {
                "rich_text": [
                    {"plain_text": "Clients keep asking where execution is really slowing down."}
                ]
            },
            "Draft": {"rich_text": []},
        },
    }


def test_tick_skips_non_monday():
    import newsletter_anchor_tick as mod

    fake_now = datetime(2026, 5, 5, 12, 0, tzinfo=pytz.timezone("America/Denver"))
    with patch.object(mod, "_now", return_value=fake_now), \
         patch.object(mod, "_open_notion") as mock_open_notion, \
         patch.object(mod, "send_message") as mock_send_message:
        mod.newsletter_anchor_tick()

    mock_open_notion.assert_not_called()
    mock_send_message.assert_not_called()


def test_tick_alerts_when_no_anchor():
    import newsletter_anchor_tick as mod

    fake_now = datetime(2026, 5, 4, 12, 0, tzinfo=pytz.timezone("America/Denver"))
    notion = MagicMock()
    notion.query_database.return_value = []

    with patch.object(mod, "_now", return_value=fake_now), \
         patch.object(mod, "_chat_id", return_value="12345"), \
         patch.object(mod, "_open_notion", return_value=notion), \
         patch.object(mod, "send_message") as mock_send_message, \
         patch.object(mod, "send_message_with_buttons") as mock_send_buttons, \
         patch.object(mod, "build_newsletter_crew") as mock_build_crew:
        mod.newsletter_anchor_tick()

    mock_build_crew.assert_not_called()
    mock_send_buttons.assert_not_called()
    mock_send_message.assert_called_once()
    assert "no anchor" in mock_send_message.call_args.args[1].lower()


def test_tick_runs_crew_when_anchor_present_and_persists_draft():
    import newsletter_anchor_tick as mod

    fake_now = datetime(2026, 5, 4, 12, 0, tzinfo=pytz.timezone("America/Denver"))
    notion = MagicMock()
    notion.query_database.return_value = [_anchor_page()]
    crew = MagicMock()
    crew.kickoff.return_value = "Subject: Tighter feedback loops\n\nBody paragraph one.\n\nBody paragraph two."
    outcome = MagicMock(id=41)

    with patch.object(mod, "_now", return_value=fake_now), \
         patch.object(mod, "_chat_id", return_value="12345"), \
         patch.object(mod, "_open_notion", return_value=notion), \
         patch.object(mod, "build_newsletter_crew", return_value=crew) as mock_build_crew, \
         patch.object(mod, "send_message") as mock_send_message, \
         patch.object(mod, "send_message_with_buttons") as mock_send_buttons, \
         patch.object(mod, "start_task", return_value=outcome) as mock_start_task, \
         patch.object(mod, "complete_task") as mock_complete_task:
        mod.newsletter_anchor_tick()

    query_filter = notion.query_database.call_args.kwargs["filter_obj"]
    assert query_filter == {
        "and": [
            {"property": "Anchor Date", "date": {"equals": "2026-05-04"}},
            {"property": "Type", "select": {"equals": "Newsletter"}},
        ]
    }
    mock_build_crew.assert_called_once()
    request = mock_build_crew.call_args.args[0]
    metadata = mock_build_crew.call_args.kwargs["metadata"]
    assert "Why operators need tighter feedback loops" in request
    assert "Clients keep asking where execution is really slowing down." in request
    assert metadata["anchor_page_id"] == "anchor-page-123"
    assert metadata["anchor_date"] == "2026-05-04"
    notion.update_page.assert_called_once()
    update_props = notion.update_page.call_args.kwargs["properties"]
    assert "Draft" in update_props
    draft_chunks = update_props["Draft"]["rich_text"]
    assert "".join(chunk["text"]["content"] for chunk in draft_chunks).startswith("Subject: Tighter")
    mock_send_message.assert_not_called()
    mock_send_buttons.assert_called_once()
    message_text = mock_send_buttons.call_args.args[1]
    buttons = mock_send_buttons.call_args.args[2]
    assert "Why operators need tighter feedback loops" in message_text
    assert buttons == [[
        ("Approve", "newsletter_approve:anchor-page-123"),
        ("Revise", "newsletter_revise:anchor-page-123"),
    ]]
    mock_start_task.assert_called_once()
    mock_complete_task.assert_called_once()


def test_once_cli_prepends_test_subject_and_callback_flag():
    import newsletter_anchor_tick as mod

    fake_now = datetime(2026, 5, 6, 12, 0, tzinfo=pytz.timezone("America/Denver"))
    notion = MagicMock()
    notion.query_database.return_value = [_anchor_page(page_id="anchor-page-test")]
    crew = MagicMock()
    crew.kickoff.return_value = "Subject: Tighter feedback loops\n\nBody paragraph."
    outcome = MagicMock(id=42)

    with patch.object(mod, "_now", return_value=fake_now), \
         patch.object(mod, "_chat_id", return_value="12345"), \
         patch.object(mod, "_open_notion", return_value=notion), \
         patch.object(mod, "build_newsletter_crew", return_value=crew), \
         patch.object(mod, "send_message_with_buttons") as mock_send_buttons, \
         patch.object(mod, "start_task", return_value=outcome), \
         patch.object(mod, "complete_task"):
        mod.main(["--once"])

    message_text = mock_send_buttons.call_args.args[1]
    buttons = mock_send_buttons.call_args.args[2]
    assert "[TEST]" in message_text
    assert buttons == [[
        ("Approve", "newsletter_approve:anchor-page-test:test"),
        ("Revise", "newsletter_revise:anchor-page-test:test"),
    ]]
