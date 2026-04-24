"""Unit tests for the daily publish brief."""
from __future__ import annotations

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import pytz

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)

import publish_brief as pb


TZ = pytz.timezone("America/Denver")


def _dt(y, m, d, h=7, mi=30):
    return TZ.localize(datetime(y, m, d, h, mi))


def _page(status, platforms, sched, title="", draft="", hook=""):
    return {
        "id": "page-xyz",
        "properties": {
            "Title": {"title": ([{"plain_text": title}] if title else [])},
            "Status": {"select": {"name": status}},
            "Platform": {"multi_select": [{"name": p} for p in platforms]},
            "Scheduled Date": {"date": ({"start": sched} if sched else None)},
            "Draft": {"rich_text": ([{"plain_text": draft}] if draft else [])},
            "Hook": {"rich_text": ([{"plain_text": hook}] if hook else [])},
        },
    }


# ═════════════════════════════════════════════════════════════════════════════
# Share intent URLs
# ═════════════════════════════════════════════════════════════════════════════

def test_x_share_url_encodes_text():
    u = pb._x_share_url("hello & world")
    assert u.startswith("https://twitter.com/intent/tweet?text=")
    assert "hello%20%26%20world" in u


def test_linkedin_share_url_encodes_text():
    u = pb._linkedin_share_url("test msg")
    assert "linkedin.com" in u
    assert "test%20msg" in u


def test_publish_url_unknown_platform_returns_none():
    assert pb._publish_url("Instagram", "hi") is None


# ═════════════════════════════════════════════════════════════════════════════
# _fetch_todays_queued
# ═════════════════════════════════════════════════════════════════════════════

def test_fetch_only_returns_queued_for_today():
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("Queued", ["X"], "2026-04-28", title="Today X", draft="body"),
        _page("Queued", ["LinkedIn"], "2026-04-29", title="Tomorrow LI", draft="body"),
        _page("Ready", ["X"], "2026-04-28", title="Ready today", draft="body"),
        _page("Posted", ["X"], "2026-04-28", title="Already posted", draft="body"),
        _page("Queued", ["X"], None, title="No date", draft="body"),
    ]
    posts = pb._fetch_todays_queued(notion, "2026-04-28")
    assert len(posts) == 1
    assert posts[0]["title"] == "Today X"


def test_fetch_skips_platforms_without_linkedin_or_x():
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("Queued", ["Instagram"], "2026-04-28", title="IG only", draft="body"),
    ]
    posts = pb._fetch_todays_queued(notion, "2026-04-28")
    assert posts == []


# ═════════════════════════════════════════════════════════════════════════════
# Message formatting
# ═════════════════════════════════════════════════════════════════════════════

def test_empty_brief_explicit_message():
    msg = pb._format_empty_brief("2026-04-28", "Tuesday")
    assert "Tuesday 2026-04-28" in msg
    assert "No posts queued" in msg


def test_full_brief_one_message_per_post_plus_header():
    posts = [
        {"notion_id": "pid-1", "title": "First", "platform": "X", "draft": "short X post", "hook": ""},
        {"notion_id": "pid-2", "title": "Second", "platform": "LinkedIn", "draft": "long LinkedIn post", "hook": ""},
    ]
    messages = pb._format_full_brief("2026-04-28", "Tuesday", posts)
    assert len(messages) == 3  # header + 2 posts
    assert "2 post(s) to publish" in messages[0]
    # Each post message contains the draft + share URL
    assert "short X post" in messages[1]
    assert "twitter.com/intent/tweet" in messages[1]
    assert "long LinkedIn post" in messages[2]
    assert "linkedin.com" in messages[2]


def test_full_brief_falls_back_to_hook_if_no_draft():
    posts = [
        {"notion_id": "pid-h", "title": "Hook only", "platform": "X", "draft": "", "hook": "hook text"},
    ]
    messages = pb._format_full_brief("2026-04-28", "Tuesday", posts)
    assert "hook text" in messages[1]


# ═════════════════════════════════════════════════════════════════════════════
# publish_brief_tick end-to-end (mocked)
# ═════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_pub(monkeypatch):
    mocks = MagicMock()
    mocks.send_message = MagicMock()
    mocks.query_database = MagicMock()

    class _FakeNotionClient:
        def __init__(self, secret=None):
            pass
        def query_database(self, db_id, filter_obj=None):
            return mocks.query_database(db_id, filter_obj)

    notion_mod = MagicMock()
    notion_mod.NotionClient = _FakeNotionClient
    monkeypatch.setitem(sys.modules, "skills.forge_cli.notion_client", notion_mod)

    notifier = MagicMock()
    notifier.send_message = mocks.send_message
    monkeypatch.setitem(sys.modules, "notifier", notifier)

    monkeypatch.setenv("TELEGRAM_CHAT_ID", "7792432594")
    return mocks


def test_tick_skips_on_weekend(mock_pub, monkeypatch):
    monkeypatch.setattr(pb, "datetime", _FakeDT(_dt(2026, 4, 25)))  # Saturday
    pb.publish_brief_tick()
    assert not mock_pub.query_database.called
    assert not mock_pub.send_message.called


def test_tick_sends_empty_brief_when_nothing_queued(mock_pub, monkeypatch):
    monkeypatch.setattr(pb, "datetime", _FakeDT(_dt(2026, 4, 28)))  # Tuesday
    mock_pub.query_database.return_value = []
    pb.publish_brief_tick()
    assert mock_pub.send_message.called
    args = mock_pub.send_message.call_args
    assert args[0][0] == "7792432594"
    assert "No posts queued" in args[0][1]


def test_tick_sends_full_brief_with_share_urls(mock_pub, monkeypatch):
    monkeypatch.setattr(pb, "datetime", _FakeDT(_dt(2026, 4, 28)))
    mock_pub.query_database.return_value = [
        _page("Queued", ["X"], "2026-04-28", title="Today X",
              draft="One constraint nobody has named yet.", hook=""),
    ]
    pb.publish_brief_tick()
    # Two sends: header + 1 post
    assert mock_pub.send_message.call_count == 2
    # Second send has the share URL
    second_call = mock_pub.send_message.call_args_list[1]
    msg_body = second_call[0][1]
    assert "One constraint nobody has named yet." in msg_body
    assert "twitter.com/intent/tweet" in msg_body


def test_tick_skips_when_no_chat_id_env(mock_pub, monkeypatch):
    monkeypatch.setattr(pb, "datetime", _FakeDT(_dt(2026, 4, 28)))
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("OWNER_TELEGRAM_CHAT_ID", raising=False)
    mock_pub.query_database.return_value = []
    pb.publish_brief_tick()
    assert not mock_pub.send_message.called


# ═════════════════════════════════════════════════════════════════════════════
# Fake datetime helper
# ═════════════════════════════════════════════════════════════════════════════

class _FakeDT:
    def __init__(self, frozen):
        self._frozen = frozen

    def now(self, tz=None):
        if tz is not None:
            return self._frozen.astimezone(tz)
        return self._frozen

    def __getattr__(self, name):
        import datetime as _dt
        return getattr(_dt.datetime, name)
