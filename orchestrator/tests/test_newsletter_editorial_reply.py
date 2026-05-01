"""Tests for the free-text reply capture for the Sunday editorial prompt."""
from __future__ import annotations

import os
import sys
from datetime import datetime
from unittest.mock import patch

import pytz

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)


def test_reply_captured_during_window():
    """Sunday 19:00 free-text reply should upsert into editorial_input."""
    from handlers_approvals import handle_newsletter_editorial_reply

    fake_now = datetime(2026, 5, 3, 19, 0, tzinfo=pytz.timezone("America/Denver"))
    with patch("handlers_approvals._now_local", return_value=fake_now), \
         patch("handlers_approvals.upsert_reply") as mock_upsert, \
         patch("handlers_approvals._operator_chat_id", return_value="12345"), \
         patch("handlers_approvals.send_message"):
        result = handle_newsletter_editorial_reply(
            text="Clients keep asking about X.",
            chat_id="12345",
            first_word="clients",
            reply_to_msg_id=None,
        )

    assert result is True
    mock_upsert.assert_called_once()
    week_arg = mock_upsert.call_args[0][0]
    assert week_arg.weekday() == 0
    assert week_arg.day == 4 and week_arg.month == 5


def test_reply_ignored_outside_window():
    """Tuesday 10:00 free-text should not be captured."""
    from handlers_approvals import handle_newsletter_editorial_reply

    fake_now = datetime(2026, 5, 5, 10, 0, tzinfo=pytz.timezone("America/Denver"))
    with patch("handlers_approvals._now_local", return_value=fake_now), \
         patch("handlers_approvals.upsert_reply") as mock_upsert, \
         patch("handlers_approvals._operator_chat_id", return_value="12345"):
        result = handle_newsletter_editorial_reply(
            text="Some random comment",
            chat_id="12345",
            first_word="some",
            reply_to_msg_id=None,
        )

    assert result is False
    mock_upsert.assert_not_called()


def test_reply_ignored_from_other_chat():
    """Reply from a chat that is not the operator chat is ignored."""
    from handlers_approvals import handle_newsletter_editorial_reply

    fake_now = datetime(2026, 5, 3, 19, 0, tzinfo=pytz.timezone("America/Denver"))
    with patch("handlers_approvals._now_local", return_value=fake_now), \
         patch("handlers_approvals.upsert_reply") as mock_upsert, \
         patch("handlers_approvals._operator_chat_id", return_value="12345"):
        result = handle_newsletter_editorial_reply(
            text="reply from other chat",
            chat_id="99999",
            first_word="reply",
            reply_to_msg_id=None,
        )

    assert result is False
    mock_upsert.assert_not_called()


def test_reply_ignored_when_replying_to_message():
    """A reply-to-message stays in approval flow territory."""
    from handlers_approvals import handle_newsletter_editorial_reply

    fake_now = datetime(2026, 5, 3, 19, 0, tzinfo=pytz.timezone("America/Denver"))
    with patch("handlers_approvals._now_local", return_value=fake_now), \
         patch("handlers_approvals.upsert_reply") as mock_upsert, \
         patch("handlers_approvals._operator_chat_id", return_value="12345"):
        result = handle_newsletter_editorial_reply(
            text="this is a reply to something",
            chat_id="12345",
            first_word="this",
            reply_to_msg_id=42,
        )

    assert result is False
    mock_upsert.assert_not_called()


def test_monday_before_06_still_captured():
    """Monday 02:00 reply still belongs to this week's Monday anchor."""
    from handlers_approvals import handle_newsletter_editorial_reply

    fake_now = datetime(2026, 5, 4, 2, 0, tzinfo=pytz.timezone("America/Denver"))
    with patch("handlers_approvals._now_local", return_value=fake_now), \
         patch("handlers_approvals.upsert_reply") as mock_upsert, \
         patch("handlers_approvals._operator_chat_id", return_value="12345"), \
         patch("handlers_approvals.send_message"):
        result = handle_newsletter_editorial_reply(
            text="late Sunday brain dump",
            chat_id="12345",
            first_word="late",
            reply_to_msg_id=None,
        )

    assert result is True
    week_arg = mock_upsert.call_args[0][0]
    assert week_arg.day == 4 and week_arg.month == 5


def test_short_command_alias_not_captured():
    """A short approval alias like 'yes' must not be eaten by editorial capture."""
    from handlers_approvals import handle_newsletter_editorial_reply

    fake_now = datetime(2026, 5, 3, 19, 0, tzinfo=pytz.timezone("America/Denver"))
    with patch("handlers_approvals._now_local", return_value=fake_now), \
         patch("handlers_approvals.upsert_reply") as mock_upsert, \
         patch("handlers_approvals._operator_chat_id", return_value="12345"):
        result = handle_newsletter_editorial_reply(
            text="yes",
            chat_id="12345",
            first_word="yes",
            reply_to_msg_id=None,
        )

    assert result is False
    mock_upsert.assert_not_called()
