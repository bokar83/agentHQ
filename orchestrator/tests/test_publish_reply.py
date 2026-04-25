"""
Atlas M1: tests for handle_publish_reply.

The handler is invoked from handlers.process_telegram_update with
(text, chat_id, first_word, reply_to_msg_id). It returns True when it
consumed the update (so the caller stops processing), False when the
update was not for it.
"""
from __future__ import annotations

import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)


# ---------- helpers ----------

def _seed_window(msg_id: int, page_id: str = "page-abc",
                 title: str = "One constraint nobody has named yet",
                 platform: str = "X", chat_id: str = "7792432594") -> None:
    """Insert a fresh publish-brief window entry."""
    from state import _PUBLISH_BRIEF_WINDOWS
    _PUBLISH_BRIEF_WINDOWS[msg_id] = {
        "notion_page_id": page_id,
        "title": title,
        "platform": platform,
        "chat_id": chat_id,
        "ts_sent": time.time(),
    }


@pytest.fixture(autouse=True)
def clear_windows():
    """Each test starts with an empty dict and we leave it clean."""
    from state import _PUBLISH_BRIEF_WINDOWS
    _PUBLISH_BRIEF_WINDOWS.clear()
    yield
    _PUBLISH_BRIEF_WINDOWS.clear()


# ---------- tests ----------

def test_happy_path_posted():
    """Reply 'posted' to a brief msg in the dict: Notion flips to Posted,
    one task_outcomes row is written, dict is evicted, confirmation is sent.
    """
    from state import _PUBLISH_BRIEF_WINDOWS

    _seed_window(msg_id=1001, page_id="page-abc",
                 title="One constraint nobody has named yet")

    notion_mock = MagicMock()
    notion_mock.get_page.return_value = {
        "properties": {"Status": {"select": {"name": "Queued"}}}
    }
    outcome = MagicMock()
    outcome.id = 42

    with patch("handlers_approvals._open_notion", return_value=notion_mock), \
         patch("handlers_approvals.start_task", return_value=outcome) as start_mock, \
         patch("handlers_approvals.complete_task") as complete_mock, \
         patch("handlers_approvals.send_message") as send_mock:

        from handlers_approvals import handle_publish_reply
        result = handle_publish_reply("posted", chat_id="7792432594",
                                      first_word="posted", reply_to_msg_id=1001)

    assert result is True
    notion_mock.update_page.assert_called_once_with(
        "page-abc",
        properties={"Status": {"select": {"name": "Posted"}}},
    )
    start_mock.assert_called_once()
    complete_mock.assert_called_once()
    assert 1001 not in _PUBLISH_BRIEF_WINDOWS
    sent = send_mock.call_args.args[1]
    assert "Marked Posted" in sent
    assert "One constraint nobody" in sent


def test_happy_path_skip():
    """Reply 'skip': Notion flips to Skipped, otherwise same."""
    from state import _PUBLISH_BRIEF_WINDOWS

    _seed_window(msg_id=1002, page_id="page-xyz", title="Tuesday post")

    notion_mock = MagicMock()
    notion_mock.get_page.return_value = {
        "properties": {"Status": {"select": {"name": "Queued"}}}
    }
    outcome = MagicMock()
    outcome.id = 43

    with patch("handlers_approvals._open_notion", return_value=notion_mock), \
         patch("handlers_approvals.start_task", return_value=outcome), \
         patch("handlers_approvals.complete_task"), \
         patch("handlers_approvals.send_message") as send_mock:

        from handlers_approvals import handle_publish_reply
        result = handle_publish_reply("skip", chat_id="7792432594",
                                      first_word="skip", reply_to_msg_id=1002)

    assert result is True
    notion_mock.update_page.assert_called_once_with(
        "page-xyz",
        properties={"Status": {"select": {"name": "Skipped"}}},
    )
    assert 1002 not in _PUBLISH_BRIEF_WINDOWS
    assert "Marked Skipped" in send_mock.call_args.args[1]


def test_idempotent_double_reply():
    """Two 'posted' replies to the same msg: first processes, second sees
    no dict entry and returns False (no Notion call, no task_outcomes write).
    """
    from state import _PUBLISH_BRIEF_WINDOWS

    _seed_window(msg_id=1003)

    notion_mock = MagicMock()
    notion_mock.get_page.return_value = {
        "properties": {"Status": {"select": {"name": "Queued"}}}
    }
    outcome = MagicMock()
    outcome.id = 44

    with patch("handlers_approvals._open_notion", return_value=notion_mock), \
         patch("handlers_approvals.start_task", return_value=outcome), \
         patch("handlers_approvals.complete_task") as complete_mock, \
         patch("handlers_approvals.send_message"):

        from handlers_approvals import handle_publish_reply
        first = handle_publish_reply("posted", "7792432594", "posted", 1003)
        second = handle_publish_reply("posted", "7792432594", "posted", 1003)

    assert first is True
    assert second is False
    assert notion_mock.update_page.call_count == 1
    assert complete_mock.call_count == 1
    assert 1003 not in _PUBLISH_BRIEF_WINDOWS


def test_out_of_band_notion_flip():
    """Notion already shows Posted when the reply arrives. Handler does NOT
    call update_page again. Writes one task_outcomes row capturing the no-op.
    Replies 'Already marked Posted in Notion.' Evicts the dict entry.
    """
    from state import _PUBLISH_BRIEF_WINDOWS

    _seed_window(msg_id=1004)

    notion_mock = MagicMock()
    notion_mock.get_page.return_value = {
        "properties": {"Status": {"select": {"name": "Posted"}}}
    }
    outcome = MagicMock()
    outcome.id = 45

    with patch("handlers_approvals._open_notion", return_value=notion_mock), \
         patch("handlers_approvals.start_task", return_value=outcome), \
         patch("handlers_approvals.complete_task") as complete_mock, \
         patch("handlers_approvals.send_message") as send_mock:

        from handlers_approvals import handle_publish_reply
        result = handle_publish_reply("posted", "7792432594", "posted", 1004)

    assert result is True
    notion_mock.update_page.assert_not_called()
    assert complete_mock.call_count == 1
    assert 1004 not in _PUBLISH_BRIEF_WINDOWS
    assert "Already marked Posted" in send_mock.call_args.args[1]


def test_stray_yes_reply_to_publish_brief_not_consumed():
    """User replies 'yes' to a brief msg in the dict. handle_publish_reply
    must return False because 'yes' is neither in POSTED_ALIASES nor
    SKIP_ALIASES. The dict entry stays so the brief reply window remains.

    This is the bug Sankofa caught: an in-memory dict avoids approval_queue
    overlap, so 'yes' falls through cleanly without misroute.
    """
    from state import _PUBLISH_BRIEF_WINDOWS

    _seed_window(msg_id=1005)

    with patch("handlers_approvals._open_notion") as notion_open:
        from handlers_approvals import handle_publish_reply
        result = handle_publish_reply("yes", "7792432594", "yes", 1005)

    assert result is False
    notion_open.assert_not_called()
    assert 1005 in _PUBLISH_BRIEF_WINDOWS  # entry preserved


def test_multi_post_day_independent():
    """Two posts in today's brief: dict has two entries. Reply 'posted' to
    msg 1, then 'skip' to msg 2. Each Notion page flipped independently.
    """
    from state import _PUBLISH_BRIEF_WINDOWS

    _seed_window(msg_id=2001, page_id="page-1", title="Post one")
    _seed_window(msg_id=2002, page_id="page-2", title="Post two")

    notion_mock = MagicMock()
    notion_mock.get_page.return_value = {
        "properties": {"Status": {"select": {"name": "Queued"}}}
    }
    outcome = MagicMock()
    outcome.id = 50

    with patch("handlers_approvals._open_notion", return_value=notion_mock), \
         patch("handlers_approvals.start_task", return_value=outcome), \
         patch("handlers_approvals.complete_task"), \
         patch("handlers_approvals.send_message"):

        from handlers_approvals import handle_publish_reply
        r1 = handle_publish_reply("posted", "7792432594", "posted", 2001)
        r2 = handle_publish_reply("skip", "7792432594", "skip", 2002)

    assert r1 is True
    assert r2 is True

    calls = notion_mock.update_page.call_args_list
    assert len(calls) == 2
    assert calls[0].args[0] == "page-1"
    assert calls[0].kwargs["properties"]["Status"]["select"]["name"] == "Posted"
    assert calls[1].args[0] == "page-2"
    assert calls[1].kwargs["properties"]["Status"]["select"]["name"] == "Skipped"

    assert 2001 not in _PUBLISH_BRIEF_WINDOWS
    assert 2002 not in _PUBLISH_BRIEF_WINDOWS
