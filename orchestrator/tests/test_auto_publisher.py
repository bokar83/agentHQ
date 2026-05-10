"""Unit tests for auto_publisher.py.

Mocks Notion + BlotatoPublisher + Telegram + episodic_memory so no real
calls fire. Covers: empty queue, single record happy path, idempotency
flip-to-Publishing, multi-record, missing account ID, missing draft text,
Blotato POST failure, poll failure, poll timeout, stale-Publishing TTL
cleanup, future-dated record skipped, wrong-status record skipped.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)


# ═════════════════════════════════════════════════════════════════════════════
# Notion page fixture
# ═════════════════════════════════════════════════════════════════════════════

def _page(
    notion_id: str,
    status: str,
    platforms: list,
    sched: str,
    title: str = "T",
    draft: str = "body",
    last_edit_iso: str = "2026-04-25T12:00:00.000Z",
    submission_id: str = "",
):
    return {
        "id": notion_id,
        "last_edited_time": last_edit_iso,
        "properties": {
            "Title": {"title": [{"plain_text": title}]},
            "Status": {"select": {"name": status}},
            "Platform": {"multi_select": [{"name": p} for p in platforms]},
            "Scheduled Date": {"date": ({"start": sched} if sched else None)},
            "Draft": {"rich_text": ([{"plain_text": draft}] if draft else [])},
            "Hook": {"rich_text": []},
            "Submission ID": {"rich_text": ([{"plain_text": submission_id}] if submission_id else [])},
        },
    }


@pytest.fixture(autouse=True)
def _env_setup(monkeypatch):
    monkeypatch.setenv("BLOTATO_LINKEDIN_ACCOUNT_ID", "19365")
    monkeypatch.setenv("BLOTATO_X_ACCOUNT_ID", "17065")
    monkeypatch.setenv("OWNER_TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setenv("BLOTATO_API_KEY", "test-key")


# Helper: a "noon Mountain Time" datetime, so all platform slots (07:00, 11:00,
# 12:00, 14:00) are reachable. Tests that check time-of-day behavior use this
# explicitly via _fetch_due_queued(now_local=...).
import pytz as _pytz
def _noon_local(year=2026, month=4, day=25):
    return _pytz.timezone("America/Denver").localize(datetime(year, month, day, 14, 30))


# ═════════════════════════════════════════════════════════════════════════════
# _account_id_for_platform
# ═════════════════════════════════════════════════════════════════════════════

def test_account_id_resolves_linkedin_and_x():
    import auto_publisher as ap
    assert ap._account_id_for_platform("LinkedIn") == "19365"
    assert ap._account_id_for_platform("X") == "17065"


def test_account_id_returns_none_for_unconfigured_platform():
    import auto_publisher as ap
    assert ap._account_id_for_platform("MySpace") is None


def test_account_id_returns_none_for_platform_without_env(monkeypatch):
    import auto_publisher as ap
    monkeypatch.delenv("BLOTATO_TIKTOK_ACCOUNT_ID", raising=False)
    assert ap._account_id_for_platform("TikTok") is None


# ═════════════════════════════════════════════════════════════════════════════
# _fetch_due_queued
# ═════════════════════════════════════════════════════════════════════════════

def test_fetch_due_queued_includes_today_and_past_due():
    import auto_publisher as ap
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p-today", "Queued", ["X"], "2026-04-25", title="today"),
        _page("p-past", "Queued", ["LinkedIn"], "2026-04-20", title="past-due"),
        _page("p-future", "Queued", ["X"], "2026-05-01", title="future"),
    ]
    due = ap._fetch_due_queued(notion, "2026-04-25", now_local=_noon_local())
    titles = [d["title"] for d in due]
    assert "today" in titles
    assert "past-due" in titles
    assert "future" not in titles


def test_fetch_due_queued_skips_non_queued_status():
    import auto_publisher as ap
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p1", "Ready", ["X"], "2026-04-25"),
        _page("p2", "Posted", ["X"], "2026-04-25"),
        _page("p3", "Publishing", ["X"], "2026-04-25"),
        _page("p4", "PublishFailed", ["X"], "2026-04-25"),
        _page("p5", "Skipped", ["X"], "2026-04-25"),
    ]
    due = ap._fetch_due_queued(notion, "2026-04-25", now_local=_noon_local())
    assert due == []


def test_fetch_due_queued_skips_records_without_account_id(monkeypatch):
    import auto_publisher as ap
    monkeypatch.delenv("BLOTATO_TIKTOK_ACCOUNT_ID", raising=False)
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p1", "Queued", ["TikTok"], "2026-04-25"),
        _page("p2", "Queued", ["X"], "2026-04-25", title="X-only"),
    ]
    due = ap._fetch_due_queued(notion, "2026-04-25", now_local=_noon_local())
    assert len(due) == 1
    assert due[0]["title"] == "X-only"


def test_fetch_due_queued_one_publish_per_record_first_platform_wins():
    """If a record has both LinkedIn + X platforms, only one publish queued
    (first matching). Cross-platform fanout is a separate decision per record.
    """
    import auto_publisher as ap
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p1", "Queued", ["LinkedIn", "X"], "2026-04-25"),
    ]
    due = ap._fetch_due_queued(notion, "2026-04-25", now_local=_noon_local())
    assert len(due) == 1


def test_fetch_due_queued_sorted_oldest_first():
    import auto_publisher as ap
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p-newer", "Queued", ["X"], "2026-04-24", title="newer"),
        _page("p-older", "Queued", ["X"], "2026-04-20", title="older"),
    ]
    due = ap._fetch_due_queued(notion, "2026-04-25", now_local=_noon_local())
    assert [d["title"] for d in due] == ["older", "newer"]


# ═════════════════════════════════════════════════════════════════════════════
# _fetch_stale_publishing
# ═════════════════════════════════════════════════════════════════════════════

def test_fetch_stale_publishing_returns_records_older_than_ttl():
    import auto_publisher as ap
    now_utc = datetime(2026, 4, 26, 12, 0, 0, tzinfo=timezone.utc)
    old_iso = (now_utc - timedelta(hours=25)).isoformat().replace("+00:00", "Z")
    fresh_iso = (now_utc - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p-stale", "Publishing", ["X"], "2026-04-25", title="stuck", last_edit_iso=old_iso),
        _page("p-fresh", "Publishing", ["X"], "2026-04-25", title="recent", last_edit_iso=fresh_iso),
        _page("p-not-publishing", "Posted", ["X"], "2026-04-25", title="done", last_edit_iso=old_iso),
    ]
    stale = ap._fetch_stale_publishing(notion, now_utc)
    titles = [s["title"] for s in stale]
    assert "stuck" in titles
    assert "recent" not in titles
    assert "done" not in titles


# ═════════════════════════════════════════════════════════════════════════════
# Notion writes (verify exact payload shapes)
# ═════════════════════════════════════════════════════════════════════════════

def test_flip_to_publishing_writes_correct_status():
    import auto_publisher as ap
    notion = MagicMock()
    ap._flip_to_publishing(notion, "p-1")
    notion.update_page.assert_called_once_with(
        "p-1", {"Status": {"select": {"name": "Publishing"}}}
    )


def test_persist_submission_id_writes_rich_text():
    import auto_publisher as ap
    notion = MagicMock()
    ap._persist_submission_id(notion, "p-1", "sub-abc")
    notion.update_page.assert_called_once_with(
        "p-1",
        {"Submission ID": {"rich_text": [{"text": {"content": "sub-abc"}}]}},
    )


def test_flip_to_posted_writes_linkedin_url_field():
    import auto_publisher as ap
    notion = MagicMock()
    ap._flip_to_posted(notion, "p-1", "LinkedIn", "https://linkedin.com/x", "2026-04-25T22:01:44Z")
    args, _ = notion.update_page.call_args
    assert args[0] == "p-1"
    props = args[1]
    assert props["Status"] == {"select": {"name": "Posted"}}
    assert props["LinkedIn Posted URL"] == {"url": "https://linkedin.com/x"}
    assert props["Posted Date"] == {"date": {"start": "2026-04-25T22:01:44Z"}}


def test_flip_to_posted_writes_x_url_field_for_x_platform():
    import auto_publisher as ap
    notion = MagicMock()
    ap._flip_to_posted(notion, "p-1", "X", "https://x.com/a/b", "2026-04-25T22:01:49Z")
    args, _ = notion.update_page.call_args
    assert args[1]["X Posted URL"] == {"url": "https://x.com/a/b"}
    assert "LinkedIn Posted URL" not in args[1]


def test_flip_to_publish_failed_truncates_long_error():
    import auto_publisher as ap
    notion = MagicMock()
    long_err = "x" * 2000
    ap._flip_to_publish_failed(notion, "p-1", long_err)
    args, _ = notion.update_page.call_args
    src_note_text = args[1]["Source Note"]["rich_text"][0]["text"]["content"]
    assert len(src_note_text) <= 1600  # 1500 cap + "PublishFailed: " prefix
    assert src_note_text.startswith("PublishFailed: ")


# ═════════════════════════════════════════════════════════════════════════════
# auto_publisher_tick: end-to-end happy path with mocked Notion + Publisher
# ═════════════════════════════════════════════════════════════════════════════

def _patched_tick_environment(notion_pages: list, publish_sub_id: str = "sub-1",
                                poll_status: str = "published",
                                poll_url: str = "https://x.com/x/123",
                                poll_error: str = ""):
    """Build a context manager bundle: Notion + NotionClient + BlotatoPublisher
    + notifier + episodic_memory all mocked. Returns (mock_notion, mock_publisher).
    """
    mock_notion = MagicMock()
    mock_notion.query_database.return_value = notion_pages

    mock_client_cls = MagicMock()
    mock_client_cls.return_value = mock_notion

    mock_publisher = MagicMock()
    mock_publisher.publish.return_value = publish_sub_id
    mock_result = MagicMock()
    mock_result.status = poll_status
    mock_result.ok = (poll_status == "published")
    mock_result.public_url = poll_url
    mock_result.error_message = poll_error
    mock_publisher.poll_until_terminal.return_value = mock_result
    mock_publisher_cls = MagicMock(return_value=mock_publisher)

    mock_notifier = MagicMock()
    mock_em = MagicMock()
    mock_outcome = MagicMock()
    mock_outcome.id = "outcome-1"
    mock_em.start_task.return_value = mock_outcome

    return mock_notion, mock_publisher, mock_client_cls, mock_publisher_cls, mock_notifier, mock_em


def test_tick_with_no_due_records_is_noop():
    import auto_publisher as ap
    mock_notion, _, mock_client_cls, _, _, _ = _patched_tick_environment([])
    with patch("skills.forge_cli.notion_client.NotionClient", mock_client_cls):
        ap.auto_publisher_tick()
    # Notion query happened, but no publisher init, no Notion writes (other than
    # the query itself).
    assert mock_notion.query_database.called
    assert not mock_notion.update_page.called


def test_tick_happy_path_flips_to_publishing_then_posted():
    import auto_publisher as ap
    pages = [_page("p-x1", "Queued", ["X"], "2026-04-25", title="X test", draft="hello")]
    mock_notion, mock_publisher, mock_client_cls, mock_publisher_cls, mock_notifier, mock_em = _patched_tick_environment(pages)

    with patch("skills.forge_cli.notion_client.NotionClient", mock_client_cls), \
         patch("blotato_publisher.BlotatoPublisher", mock_publisher_cls), \
         patch.dict("sys.modules", {"notifier": mock_notifier, "episodic_memory": mock_em}):
        ap.auto_publisher_tick()

    # Verify publish was called with correct args
    mock_publisher.publish.assert_called_once_with(
        text="hello", account_id="17065", platform="X"
    )

    # Verify Notion writes happened in the right order: Publishing -> Submission ID -> Posted
    update_calls = mock_notion.update_page.call_args_list
    statuses_written = []
    for c in update_calls:
        props = c.args[1] if len(c.args) > 1 else c.kwargs.get("properties", {})
        if "Status" in props:
            statuses_written.append(props["Status"]["select"]["name"])
    assert "Publishing" in statuses_written
    assert "Posted" in statuses_written
    # Publishing must come before Posted
    assert statuses_written.index("Publishing") < statuses_written.index("Posted")


def test_tick_idempotency_flip_to_publishing_failure_skips_post():
    """If the pre-POST Status=Publishing flip fails, we must NOT POST.
    Record stays Queued for next-tick retry.
    """
    import auto_publisher as ap
    pages = [_page("p-x1", "Queued", ["X"], "2026-04-25")]
    mock_notion, mock_publisher, mock_client_cls, mock_publisher_cls, mock_notifier, mock_em = _patched_tick_environment(pages)
    mock_notion.update_page.side_effect = RuntimeError("Notion 502")

    with patch("skills.forge_cli.notion_client.NotionClient", mock_client_cls), \
         patch("blotato_publisher.BlotatoPublisher", mock_publisher_cls), \
         patch.dict("sys.modules", {"notifier": mock_notifier, "episodic_memory": mock_em}):
        ap.auto_publisher_tick()

    # Publisher.publish must NOT have been called
    assert not mock_publisher.publish.called


def test_tick_blotato_post_failure_flips_to_publish_failed():
    import auto_publisher as ap
    pages = [_page("p-x1", "Queued", ["X"], "2026-04-25", title="will-fail")]
    mock_notion, mock_publisher, mock_client_cls, mock_publisher_cls, mock_notifier, mock_em = _patched_tick_environment(pages)
    mock_publisher.publish.side_effect = RuntimeError("Blotato HTTP 422 quota")

    with patch("skills.forge_cli.notion_client.NotionClient", mock_client_cls), \
         patch("blotato_publisher.BlotatoPublisher", mock_publisher_cls), \
         patch.dict("sys.modules", {"notifier": mock_notifier, "episodic_memory": mock_em}):
        ap.auto_publisher_tick()

    # Both Publishing + PublishFailed Status writes should have happened
    statuses_written = []
    for c in mock_notion.update_page.call_args_list:
        props = c.args[1] if len(c.args) > 1 else c.kwargs.get("properties", {})
        if "Status" in props:
            statuses_written.append(props["Status"]["select"]["name"])
    assert "Publishing" in statuses_written
    assert "PublishFailed" in statuses_written


def test_tick_blotato_failed_status_flips_to_publish_failed():
    """Blotato POST succeeded but final status is failed (e.g. X API rejected)."""
    import auto_publisher as ap
    pages = [_page("p-x1", "Queued", ["X"], "2026-04-25")]
    mock_notion, mock_publisher, mock_client_cls, mock_publisher_cls, mock_notifier, mock_em = _patched_tick_environment(
        pages, poll_status="failed", poll_error="X rate limit hit"
    )

    with patch("skills.forge_cli.notion_client.NotionClient", mock_client_cls), \
         patch("blotato_publisher.BlotatoPublisher", mock_publisher_cls), \
         patch.dict("sys.modules", {"notifier": mock_notifier, "episodic_memory": mock_em}):
        ap.auto_publisher_tick()

    statuses_written = [
        c.args[1]["Status"]["select"]["name"]
        for c in mock_notion.update_page.call_args_list
        if "Status" in (c.args[1] if len(c.args) > 1 else {})
    ]
    assert statuses_written[-1] == "PublishFailed"


def test_tick_poll_timeout_leaves_publishing_status():
    """Timeout means we don't know yet. Leave Status=Publishing for next tick
    or for stale-Publishing TTL cleanup later.
    """
    import auto_publisher as ap
    pages = [_page("p-x1", "Queued", ["X"], "2026-04-25")]
    mock_notion, mock_publisher, mock_client_cls, mock_publisher_cls, mock_notifier, mock_em = _patched_tick_environment(
        pages, poll_status="timeout", poll_error="120s timeout"
    )

    with patch("skills.forge_cli.notion_client.NotionClient", mock_client_cls), \
         patch("blotato_publisher.BlotatoPublisher", mock_publisher_cls), \
         patch.dict("sys.modules", {"notifier": mock_notifier, "episodic_memory": mock_em}):
        ap.auto_publisher_tick()

    # Should NOT have flipped to Posted or PublishFailed
    final_statuses = [
        c.args[1]["Status"]["select"]["name"]
        for c in mock_notion.update_page.call_args_list
        if "Status" in (c.args[1] if len(c.args) > 1 else {})
    ]
    assert "Posted" not in final_statuses
    assert "PublishFailed" not in final_statuses
    assert "Publishing" in final_statuses


def test_tick_skips_record_with_empty_draft_and_hook():
    import auto_publisher as ap
    pages = [_page("p-empty", "Queued", ["X"], "2026-04-25", draft="")]
    # Override Hook to also be empty
    pages[0]["properties"]["Hook"] = {"rich_text": []}
    mock_notion, mock_publisher, mock_client_cls, mock_publisher_cls, mock_notifier, mock_em = _patched_tick_environment(pages)

    with patch("skills.forge_cli.notion_client.NotionClient", mock_client_cls), \
         patch("blotato_publisher.BlotatoPublisher", mock_publisher_cls), \
         patch.dict("sys.modules", {"notifier": mock_notifier, "episodic_memory": mock_em}):
        ap.auto_publisher_tick()

    # Publisher.publish must NOT have been called for empty-draft records
    assert not mock_publisher.publish.called
    # PublishFailed flip should have happened (no Publishing first; record skipped earlier)
    statuses_written = [
        c.args[1]["Status"]["select"]["name"]
        for c in mock_notion.update_page.call_args_list
        if "Status" in (c.args[1] if len(c.args) > 1 else {})
    ]
    assert "PublishFailed" in statuses_written


# ═════════════════════════════════════════════════════════════════════════════
# Time-of-day gate (M7b time slots)
# ═════════════════════════════════════════════════════════════════════════════

def _at(hour: int, minute: int = 0):
    """America/Denver datetime helper for tests."""
    return _pytz.timezone("America/Denver").localize(datetime(2026, 4, 25, hour, minute))


def test_today_record_skipped_before_first_slot_time():
    """6 AM MT, no LinkedIn slot 0 (07:00) yet -> today's LI not in due list."""
    import auto_publisher as ap
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p-li", "Queued", ["LinkedIn"], "2026-04-25", title="today LI"),
    ]
    due = ap._fetch_due_queued(notion, "2026-04-25", now_local=_at(6, 0))
    assert due == []


def test_today_record_fires_after_first_slot_time():
    """7:05 AM MT, LinkedIn slot 0 (07:00) reached -> today's LI in due list."""
    import auto_publisher as ap
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p-li", "Queued", ["LinkedIn"], "2026-04-25", title="today LI"),
    ]
    due = ap._fetch_due_queued(notion, "2026-04-25", now_local=_at(7, 5))
    assert len(due) == 1
    assert due[0]["title"] == "today LI"


def test_second_today_record_uses_slot_1():
    """At 7:30 AM, slot 0 already taken (Posted), so the next Queued record
    waits until slot 1 (11:00 AM)."""
    import auto_publisher as ap
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p-li-1", "Posted", ["LinkedIn"], "2026-04-25", title="already-out"),
        _page("p-li-2", "Queued", ["LinkedIn"], "2026-04-25", title="next-up"),
    ]
    # 7:30 AM: slot 0 taken; slot 1 (11:00) not reached
    due_730 = ap._fetch_due_queued(notion, "2026-04-25", now_local=_at(7, 30))
    assert due_730 == []
    # 11:05 AM: slot 1 reached
    due_1105 = ap._fetch_due_queued(notion, "2026-04-25", now_local=_at(11, 5))
    assert len(due_1105) == 1
    assert due_1105[0]["title"] == "next-up"


def test_x_third_slot_at_2pm():
    """X has slots at 05:15, 08:30, 11:45, 15:00. Third X record waits until 11:45 MT."""
    import auto_publisher as ap
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p-x-1", "Posted", ["X"], "2026-04-25", title="x1"),
        _page("p-x-2", "Posted", ["X"], "2026-04-25", title="x2"),
        _page("p-x-3", "Queued", ["X"], "2026-04-25", title="x3"),
    ]
    # At 11:00 AM: slot 2 (11:45) is not reached yet
    due_11 = ap._fetch_due_queued(notion, "2026-04-25", now_local=_at(11, 0))
    assert due_11 == []
    # At 12:05 PM: slot 2 (11:45) is reached
    due_12 = ap._fetch_due_queued(notion, "2026-04-25", now_local=_at(12, 5))
    assert len(due_12) == 1
    assert due_12[0]["title"] == "x3"


def test_past_due_ignores_time_of_day_gate():
    """Past-due records fire regardless of time-of-day. They have is_past_due=True."""
    import auto_publisher as ap
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p-stale", "Queued", ["LinkedIn"], "2026-04-22", title="3-days-late"),
    ]
    # 5 AM (before any slot) - past-due still fires
    due = ap._fetch_due_queued(notion, "2026-04-25", now_local=_at(5, 0))
    assert len(due) == 1
    assert due[0]["title"] == "3-days-late"
    assert due[0]["is_past_due"] is True


def test_today_record_marked_not_past_due():
    import auto_publisher as ap
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p-today", "Queued", ["X"], "2026-04-25", title="today"),
    ]
    due = ap._fetch_due_queued(notion, "2026-04-25", now_local=_at(8, 0))
    assert due[0]["is_past_due"] is False


def test_publishing_status_counts_toward_today_slot():
    """A record currently mid-flight (Status=Publishing) for today already
    occupies its slot. The next Queued record waits for the next slot.
    """
    import auto_publisher as ap
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p-pub", "Publishing", ["LinkedIn"], "2026-04-25", title="in-flight"),
        _page("p-q", "Queued", ["LinkedIn"], "2026-04-25", title="next-up"),
    ]
    due_8 = ap._fetch_due_queued(notion, "2026-04-25", now_local=_at(8, 0))
    assert due_8 == []  # slot 0 taken by Publishing; slot 1 (11:00) not reached


# ═════════════════════════════════════════════════════════════════════════════
# Weekday policy (M7b: skip Sun, publish Mon-Sat)
# ═════════════════════════════════════════════════════════════════════════════

def test_sunday_today_records_deferred_past_due_still_fires():
    """On a Sunday the wake fires but today's records are deferred. Past-due
    records still publish (audit trail must catch up).
    """
    import auto_publisher as ap
    sunday = _pytz.timezone("America/Denver").localize(datetime(2026, 4, 26, 8, 0))  # Sunday
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p-today", "Queued", ["X"], "2026-04-26", title="sunday-record"),
        _page("p-stale", "Queued", ["X"], "2026-04-22", title="past-due"),
    ]
    mock_client_cls = MagicMock(return_value=notion)
    mock_publisher = MagicMock()
    mock_publisher.publish.return_value = "sub-1"
    mr = MagicMock(); mr.status = "published"; mr.ok = True; mr.public_url = "https://x"; mr.error_message = None
    mock_publisher.poll_until_terminal.return_value = mr
    mock_publisher_cls = MagicMock(return_value=mock_publisher)
    mock_notifier = MagicMock(); mock_em = MagicMock(); mock_em.start_task.return_value = MagicMock(id="o1")

    with patch("skills.forge_cli.notion_client.NotionClient", mock_client_cls), \
         patch("blotato_publisher.BlotatoPublisher", mock_publisher_cls), \
         patch.dict("sys.modules", {"notifier": mock_notifier, "episodic_memory": mock_em}), \
         patch("auto_publisher.datetime") as mock_dt:
        # Make datetime.now(tz) return our Sunday for the tick body
        mock_dt.now.side_effect = lambda tz=None: sunday if tz else datetime.now()
        mock_dt.fromisoformat = datetime.fromisoformat
        ap.auto_publisher_tick()

    # Past-due fired; sunday-record did NOT
    publish_calls = mock_publisher.publish.call_args_list
    assert len(publish_calls) == 1
    # Verify it was the past-due record (notion_id=p-stale), not the Sunday record (p-today)
    notion_ids_touched = [c.args[0] for c in notion.update_page.call_args_list]
    assert "p-stale" in notion_ids_touched
    assert "p-today" not in notion_ids_touched


# ═════════════════════════════════════════════════════════════════════════════
# Past-due stagger (max_per_tick cap)
# ═════════════════════════════════════════════════════════════════════════════

def test_past_due_capped_per_tick(monkeypatch):
    """If 6 past-dues exist and max_per_tick=4, only 4 fire this tick.
    All 6 records are dated in the past (no today-record) so the cap applies cleanly.
    """
    import auto_publisher as ap
    notion = MagicMock()
    # All 6 past-due (Apr 19, 20, 21, 22, 23, 24 - all before today Apr 25)
    pages = [
        _page(f"p-{i}", "Queued", ["X"], f"2026-04-{19+i}", title=f"stale-{i}", draft=f"body-{i}")
        for i in range(6)
    ]
    notion.query_database.return_value = pages
    mock_client_cls = MagicMock(return_value=notion)
    mock_publisher = MagicMock()
    mock_publisher.publish.return_value = "sub-1"
    mr = MagicMock(); mr.status = "published"; mr.ok = True; mr.public_url = "https://x"; mr.error_message = None
    mock_publisher.poll_until_terminal.return_value = mr
    mock_publisher_cls = MagicMock(return_value=mock_publisher)
    mock_notifier = MagicMock(); mock_em = MagicMock(); mock_em.start_task.return_value = MagicMock(id="o1")

    mock_sched = {
        "past_due": {
            "max_per_tick": 4,
            "max_posts_per_tick": 4
        },
        "weekday_policy": {
            "skip_days": [6]
        }
    }

    with patch("skills.forge_cli.notion_client.NotionClient", mock_client_cls), \
         patch("blotato_publisher.BlotatoPublisher", mock_publisher_cls), \
         patch("auto_publisher._load_schedule", return_value=mock_sched), \
         patch.dict("sys.modules", {"notifier": mock_notifier, "episodic_memory": mock_em}):
        ap.auto_publisher_tick()

    # Should be capped at mock schedule's max_posts_per_tick (4)
    assert mock_publisher.publish.call_count == 4


def test_tick_single_fire_stagger_limit():
    """If multiple records are due (e.g. 2 today-records or 1 today + 1 past-due),
    by default max_posts_per_tick is 1, so only 1 fires in this tick.
    """
    import auto_publisher as ap
    notion = MagicMock()
    # 2 due records
    pages = [
        _page("p-0", "Queued", ["X"], "2026-04-25", title="today-1", draft="body-1"),
        _page("p-1", "Queued", ["LinkedIn"], "2026-04-25", title="today-2", draft="body-2")
    ]
    notion.query_database.return_value = pages
    mock_client_cls = MagicMock(return_value=notion)
    mock_publisher = MagicMock()
    mock_publisher.publish.return_value = "sub-1"
    mr = MagicMock(); mr.status = "published"; mr.ok = True; mr.public_url = "https://x"; mr.error_message = None
    mock_publisher.poll_until_terminal.return_value = mr
    mock_publisher_cls = MagicMock(return_value=mock_publisher)
    mock_notifier = MagicMock(); mock_em = MagicMock(); mock_em.start_task.return_value = MagicMock(id="o1")

    # Use default schedule loaded from disk which has max_posts_per_tick = 1
    with patch("skills.forge_cli.notion_client.NotionClient", mock_client_cls), \
         patch("blotato_publisher.BlotatoPublisher", mock_publisher_cls), \
         patch.dict("sys.modules", {"notifier": mock_notifier, "episodic_memory": mock_em}):
        ap.auto_publisher_tick()

    # Only 1 record should fire in this tick
    assert mock_publisher.publish.call_count == 1


def test_tick_stale_publishing_promoted_to_publish_failed():
    """A record stuck in Status=Publishing for >TTL should be promoted to
    PublishFailed at the start of the tick (before main publish loop).
    """
    import auto_publisher as ap
    now_utc = datetime.now(timezone.utc)
    old_iso = (now_utc - timedelta(hours=30)).isoformat().replace("+00:00", "Z")
    pages = [_page("p-stale", "Publishing", ["X"], "2026-04-20", title="stuck",
                   last_edit_iso=old_iso, submission_id="sub-old")]
    mock_notion, mock_publisher, mock_client_cls, mock_publisher_cls, mock_notifier, mock_em = _patched_tick_environment(pages)

    with patch("skills.forge_cli.notion_client.NotionClient", mock_client_cls), \
         patch("blotato_publisher.BlotatoPublisher", mock_publisher_cls), \
         patch.dict("sys.modules", {"notifier": mock_notifier, "episodic_memory": mock_em}):
        ap.auto_publisher_tick()

    # The stale row should have been flipped to PublishFailed
    statuses_written = [
        c.args[1]["Status"]["select"]["name"]
        for c in mock_notion.update_page.call_args_list
        if "Status" in (c.args[1] if len(c.args) > 1 else {})
    ]
    assert "PublishFailed" in statuses_written
    # Publisher.publish should NOT have been called (the record is in Publishing,
    # not Queued, so the main loop skips it)
    assert not mock_publisher.publish.called


# =============================================================================
# _should_hold_for_timely_check (C13 TTL gate)
# =============================================================================

def test_timely_record_within_ttl_publishes():
    """A Timely record approved 3 days ago (under 14-day TTL) should not be held."""
    from auto_publisher import _should_hold_for_timely_check
    from datetime import datetime, timedelta, timezone

    approved_at = datetime.now(timezone.utc) - timedelta(days=3)
    result = _should_hold_for_timely_check(
        content_type="Timely",
        approved_at=approved_at,
        ttl_days=14,
    )
    assert result is False


def test_timely_record_past_ttl_holds():
    """A Timely record approved 20 days ago (past 14-day TTL) should be held."""
    from auto_publisher import _should_hold_for_timely_check
    from datetime import datetime, timedelta, timezone

    approved_at = datetime.now(timezone.utc) - timedelta(days=20)
    result = _should_hold_for_timely_check(
        content_type="Timely",
        approved_at=approved_at,
        ttl_days=14,
    )
    assert result is True


def test_evergreen_record_never_holds():
    """An Evergreen record never triggers a TTL hold regardless of age."""
    from auto_publisher import _should_hold_for_timely_check
    from datetime import datetime, timedelta, timezone

    approved_at = datetime.now(timezone.utc) - timedelta(days=365)
    result = _should_hold_for_timely_check(
        content_type="Evergreen",
        approved_at=approved_at,
        ttl_days=14,
    )
    assert result is False


def test_missing_content_type_defaults_to_timely_behavior():
    """Records without Content Type field are treated as Timely (safe default)."""
    from auto_publisher import _should_hold_for_timely_check
    from datetime import datetime, timedelta, timezone

    approved_at = datetime.now(timezone.utc) - timedelta(days=20)
    result = _should_hold_for_timely_check(
        content_type=None,
        approved_at=approved_at,
        ttl_days=14,
    )
    assert result is True
