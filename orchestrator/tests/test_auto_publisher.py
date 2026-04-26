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
    due = ap._fetch_due_queued(notion, "2026-04-25")
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
    due = ap._fetch_due_queued(notion, "2026-04-25")
    assert due == []


def test_fetch_due_queued_skips_records_without_account_id(monkeypatch):
    import auto_publisher as ap
    monkeypatch.delenv("BLOTATO_TIKTOK_ACCOUNT_ID", raising=False)
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p1", "Queued", ["TikTok"], "2026-04-25"),
        _page("p2", "Queued", ["X"], "2026-04-25", title="X-only"),
    ]
    due = ap._fetch_due_queued(notion, "2026-04-25")
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
    due = ap._fetch_due_queued(notion, "2026-04-25")
    assert len(due) == 1


def test_fetch_due_queued_sorted_oldest_first():
    import auto_publisher as ap
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("p-newer", "Queued", ["X"], "2026-04-24", title="newer"),
        _page("p-older", "Queued", ["X"], "2026-04-20", title="older"),
    ]
    due = ap._fetch_due_queued(notion, "2026-04-25")
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
