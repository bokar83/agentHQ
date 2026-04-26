"""Unit tests for Phase 3.75 Griot scheduler."""
from __future__ import annotations

import os
import sys
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)

import griot_scheduler as gs


# ═════════════════════════════════════════════════════════════════════════════
# _pick_next_slot
# ═════════════════════════════════════════════════════════════════════════════

def test_pick_x_from_weekday_returns_same_day():
    assert gs._pick_next_slot("X", {}, date(2026, 4, 27)) == date(2026, 4, 27)  # Mon


def test_pick_x_from_sunday_jumps_to_monday():
    # M7b cadence change 2026-04-25: X publishes Mon-Sat, skip Sun only.
    assert gs._pick_next_slot("X", {}, date(2026, 4, 25)) == date(2026, 4, 25)  # Sat is now valid
    assert gs._pick_next_slot("X", {}, date(2026, 4, 26)) == date(2026, 4, 27)  # Sun still skipped


def test_pick_x_skips_occupied_day():
    occ = {("X", "2026-04-27"): True}
    assert gs._pick_next_slot("X", occ, date(2026, 4, 27)) == date(2026, 4, 28)


def test_pick_linkedin_from_monday_stays_monday():
    # M7b: LinkedIn now publishes Mon-Sat (was Tue/Thu only).
    assert gs._pick_next_slot("LinkedIn", {}, date(2026, 4, 27)) == date(2026, 4, 27)


def test_pick_linkedin_from_tuesday_stays_tuesday_if_open():
    assert gs._pick_next_slot("LinkedIn", {}, date(2026, 4, 28)) == date(2026, 4, 28)


def test_pick_linkedin_takes_any_weekday():
    # All weekdays + Sat are valid LinkedIn slots after M7b.
    assert gs._pick_next_slot("LinkedIn", {}, date(2026, 4, 29)) == date(2026, 4, 29)  # Wed
    assert gs._pick_next_slot("LinkedIn", {}, date(2026, 5, 1)) == date(2026, 5, 1)    # Fri
    assert gs._pick_next_slot("LinkedIn", {}, date(2026, 4, 25)) == date(2026, 4, 25)  # Sat


def test_pick_linkedin_skips_sunday():
    assert gs._pick_next_slot("LinkedIn", {}, date(2026, 4, 26)) == date(2026, 4, 27)  # Sun -> Mon


def test_pick_linkedin_monday_occupied_jumps_to_tuesday():
    # Was: LinkedIn Tue occupied -> Thu. New: Mon occupied -> Tue (next Mon-Sat day).
    occ = {("LinkedIn", "2026-04-27"): True}
    assert gs._pick_next_slot("LinkedIn", occ, date(2026, 4, 27)) == date(2026, 4, 28)


def test_pick_unknown_platform_returns_none():
    assert gs._pick_next_slot("Instagram", {}, date(2026, 4, 27)) is None


def test_pick_returns_none_when_horizon_exhausted():
    # Fill every slot for LinkedIn for 50 days -> None within MAX_SCHEDULE_HORIZON_DAYS
    occ = {}
    for i in range(50):
        d = date(2026, 4, 27) + __import__("datetime").timedelta(days=i)
        occ[("LinkedIn", d.isoformat())] = True
    assert gs._pick_next_slot("LinkedIn", occ, date(2026, 4, 27)) is None


# ═════════════════════════════════════════════════════════════════════════════
# _fetch_occupancy
# ═════════════════════════════════════════════════════════════════════════════

def _page(status, platforms, sched):
    """Build a Notion page dict with just the fields the scheduler reads."""
    return {
        "id": "fake-id",
        "properties": {
            "Status": {"select": {"name": status}},
            "Platform": {"multi_select": [{"name": p} for p in platforms]},
            "Scheduled Date": {"date": ({"start": sched} if sched else None)},
        },
    }


def test_fetch_occupancy_only_captures_scheduled_posts():
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("Queued", ["LinkedIn"], "2026-04-28"),
        _page("Ready", ["X"], "2026-04-27"),
        _page("Posted", ["LinkedIn"], "2026-04-21"),
        _page("Ready", ["LinkedIn"], None),       # unscheduled -> NOT in occupancy
        _page("Archived", ["LinkedIn"], "2026-04-20"),  # archived -> skipped
        _page("Idea", ["X"], None),
    ]
    occ = gs._fetch_occupancy(notion)
    assert occ == {
        ("LinkedIn", "2026-04-28"): True,
        ("X", "2026-04-27"): True,
        ("LinkedIn", "2026-04-21"): True,
    }


def test_fetch_occupancy_handles_multi_platform_post():
    """A post with both LinkedIn + X marks both slots occupied."""
    notion = MagicMock()
    notion.query_database.return_value = [
        _page("Queued", ["LinkedIn", "X"], "2026-04-28"),
    ]
    occ = gs._fetch_occupancy(notion)
    assert occ == {
        ("LinkedIn", "2026-04-28"): True,
        ("X", "2026-04-28"): True,
    }


# ═════════════════════════════════════════════════════════════════════════════
# griot_scheduler_tick end-to-end (mocked)
# ═════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_scheduler(monkeypatch):
    mocks = MagicMock()
    mocks.update_page = MagicMock()
    mocks.send_message = MagicMock()
    mocks.mark_scheduled = MagicMock()

    class _FakeNotionClient:
        def __init__(self, secret=None):
            pass
        def query_database(self, db_id, filter_obj=None):
            return mocks.notion_query(db_id, filter_obj)
        def update_page(self, page_id, properties):
            return mocks.update_page(page_id, properties)

    notion_mod = MagicMock()
    notion_mod.NotionClient = _FakeNotionClient
    monkeypatch.setitem(sys.modules, "skills.forge_cli.notion_client", notion_mod)

    notifier = MagicMock()
    notifier.send_message = mocks.send_message
    monkeypatch.setitem(sys.modules, "notifier", notifier)

    monkeypatch.setattr(gs, "_mark_scheduled", mocks.mark_scheduled)

    return mocks


def test_tick_skips_when_no_approvals(mock_scheduler, monkeypatch):
    monkeypatch.setattr(gs, "_fetch_unscheduled_approvals", lambda: [])
    gs.griot_scheduler_tick()
    assert not mock_scheduler.update_page.called
    assert not mock_scheduler.send_message.called


def test_tick_schedules_approved_x_post(mock_scheduler, monkeypatch):
    payload = {
        "notion_id": "page-abc",
        "title": "One constraint nobody has named yet",
        "platform": "X",
    }
    monkeypatch.setattr(gs, "_fetch_unscheduled_approvals", lambda: [(3, payload)])
    mock_scheduler.notion_query.return_value = []  # empty board, no occupancy

    # Freeze datetime.now so start_from is deterministic: today = 2026-04-24 Fri,
    # start_from = tomorrow Sat -> _pick_next_slot jumps to Monday 2026-04-27.
    import pytz
    from datetime import datetime as _real_dt

    class _FakeDT:
        @staticmethod
        def now(tz=None):
            fixed = pytz.timezone("America/Denver").localize(_real_dt(2026, 4, 24, 12, 0))
            return fixed.astimezone(tz) if tz else fixed

    monkeypatch.setattr(gs, "datetime", _FakeDT)
    gs.griot_scheduler_tick()

    mock_scheduler.update_page.assert_called_once()
    pid, props = mock_scheduler.update_page.call_args[0]
    assert pid == "page-abc"
    # M7b: X publishes Mon-Sat. Today=Fri 04-24, start=Sat 04-25 (now valid).
    assert props["Scheduled Date"]["date"]["start"] == "2026-04-25"
    assert props["Status"]["select"]["name"] == "Queued"
    mock_scheduler.mark_scheduled.assert_called_once_with(3, "2026-04-25")


def test_tick_respects_occupancy_and_picks_next_slot(mock_scheduler, monkeypatch):
    """If Saturday X slot is taken, scheduler should pick Monday (skipping Sun)."""
    payload = {"notion_id": "page-xyz", "title": "Test", "platform": "X"}
    monkeypatch.setattr(gs, "_fetch_unscheduled_approvals", lambda: [(5, payload)])
    # M7b: X = Mon-Sat. Today=Fri 04-24, start=Sat 04-25. Sat occupied -> Sun
    # skipped -> Mon 04-27.
    mock_scheduler.notion_query.return_value = [
        _page("Queued", ["X"], "2026-04-25"),
    ]

    import pytz
    from datetime import datetime as _real_dt

    class _FakeDT:
        @staticmethod
        def now(tz=None):
            fixed = pytz.timezone("America/Denver").localize(_real_dt(2026, 4, 24, 12, 0))
            return fixed.astimezone(tz) if tz else fixed

    monkeypatch.setattr(gs, "datetime", _FakeDT)
    gs.griot_scheduler_tick()

    _pid, props = mock_scheduler.update_page.call_args[0]
    assert props["Scheduled Date"]["date"]["start"] == "2026-04-27"


def test_tick_skips_unknown_platform(mock_scheduler, monkeypatch):
    payload = {"notion_id": "page-ig", "title": "Instagram post", "platform": "Instagram"}
    monkeypatch.setattr(gs, "_fetch_unscheduled_approvals", lambda: [(9, payload)])
    mock_scheduler.notion_query.return_value = []
    gs.griot_scheduler_tick()
    assert not mock_scheduler.update_page.called
    assert not mock_scheduler.mark_scheduled.called


def test_tick_schedules_multiple_approvals_without_collision(mock_scheduler, monkeypatch):
    """Two approved X posts on the same tick must land on different days."""
    payloads = [
        (10, {"notion_id": "p-1", "title": "First X", "platform": "X"}),
        (11, {"notion_id": "p-2", "title": "Second X", "platform": "X"}),
    ]
    monkeypatch.setattr(gs, "_fetch_unscheduled_approvals", lambda: payloads)
    mock_scheduler.notion_query.return_value = []

    import pytz
    from datetime import datetime as _real_dt

    class _FakeDT:
        @staticmethod
        def now(tz=None):
            fixed = pytz.timezone("America/Denver").localize(_real_dt(2026, 4, 24, 12, 0))
            return fixed.astimezone(tz) if tz else fixed

    monkeypatch.setattr(gs, "datetime", _FakeDT)
    gs.griot_scheduler_tick()

    # Both update_page calls made; dates must differ
    assert mock_scheduler.update_page.call_count == 2
    dates = [call[0][1]["Scheduled Date"]["date"]["start"] for call in mock_scheduler.update_page.call_args_list]
    # M7b: X = Mon-Sat. Today=Fri 04-24, start=Sat 04-25 (now valid). First lands
    # on Sat; Sun skipped; second on Mon 04-27.
    assert dates[0] == "2026-04-25"  # Saturday
    assert dates[1] == "2026-04-27"  # Monday (Sun skipped)
    assert len(set(dates)) == 2


# ═════════════════════════════════════════════════════════════════════════════
# Atlas M2: backfill of recently-Skipped slots
# ═════════════════════════════════════════════════════════════════════════════

def _skipped_page(notion_id, platform, sched, title="Skipped post"):
    return {
        "id": notion_id,
        "properties": {
            "Title": {"title": [{"plain_text": title}]},
            "Status": {"select": {"name": "Skipped"}},
            "Platform": {"multi_select": [{"name": platform}]},
            "Scheduled Date": {"date": {"start": sched}},
        },
    }


def _queued_page(notion_id, platform, sched, title="Queued post"):
    return {
        "id": notion_id,
        "properties": {
            "Title": {"title": [{"plain_text": title}]},
            "Status": {"select": {"name": "Queued"}},
            "Platform": {"multi_select": [{"name": platform}]},
            "Scheduled Date": {"date": {"start": sched}},
        },
    }


def _freeze_today_to_tuesday_2026_04_28():
    """Returns a _FakeDT class freezing now() to 2026-04-28 12:00 MT (Tuesday).
    Yesterday is 2026-04-27 (Monday). The backfill window is yesterday or today.
    """
    import pytz
    from datetime import datetime as _real_dt
    tz = pytz.timezone("America/Denver")

    class _FakeDT:
        @staticmethod
        def now(tz_arg=None):
            fixed = tz.localize(_real_dt(2026, 4, 28, 12, 0))
            return fixed.astimezone(tz_arg) if tz_arg else fixed

    return _FakeDT


def test_backfill_yesterday_skipped_today_empty(mock_scheduler, monkeypatch):
    """Yesterday LinkedIn Skipped, today empty for LinkedIn, one approved
    LinkedIn candidate in queue. Backfill phase fills yesterday's LinkedIn
    slot with the candidate. Forward-scheduling phase has no work left.
    """
    payload = {"notion_id": "page-cand", "title": "Candidate post", "platform": "LinkedIn"}
    monkeypatch.setattr(gs, "_fetch_unscheduled_approvals", lambda: [(50, payload)])
    # Yesterday (Mon 04-27) LinkedIn Skipped; nothing else on the board.
    mock_scheduler.notion_query.return_value = [
        _skipped_page("page-skipped", "LinkedIn", "2026-04-27", title="Skipped one"),
    ]
    monkeypatch.setattr(gs, "datetime", _freeze_today_to_tuesday_2026_04_28())

    gs.griot_scheduler_tick()

    # Candidate gets scheduled on yesterday's date (2026-04-27, the now-empty slot).
    assert mock_scheduler.update_page.call_count == 1
    pid, props = mock_scheduler.update_page.call_args[0]
    assert pid == "page-cand"
    assert props["Scheduled Date"]["date"]["start"] == "2026-04-27"
    assert props["Status"]["select"]["name"] == "Queued"
    mock_scheduler.mark_scheduled.assert_called_once_with(50, "2026-04-27")
    # Telegram notify fired (backfill announcement)
    assert mock_scheduler.send_message.called


def test_no_backfill_if_slot_already_filled(mock_scheduler, monkeypatch):
    """Yesterday LinkedIn Skipped, but yesterday LinkedIn ALSO has a Queued
    row (e.g., a Skipped row from an earlier day plus a backfilled or
    pre-existing Queued row). Backfill phase must NOT overwrite. Approval
    falls through to forward-scheduling.
    """
    payload = {"notion_id": "page-cand", "title": "Candidate", "platform": "LinkedIn"}
    monkeypatch.setattr(gs, "_fetch_unscheduled_approvals", lambda: [(60, payload)])
    mock_scheduler.notion_query.return_value = [
        _skipped_page("page-skipped", "LinkedIn", "2026-04-27", title="Skipped"),
        _queued_page("page-existing", "LinkedIn", "2026-04-27", title="Already there"),
    ]
    monkeypatch.setattr(gs, "datetime", _freeze_today_to_tuesday_2026_04_28())

    gs.griot_scheduler_tick()

    # Backfill should NOT use 04-27 (occupied). Forward-scheduling kicks in
    # and assigns the next open LinkedIn slot. M7b: LinkedIn = Mon-Sat, so
    # today=Tue 04-28, start=Wed 04-29. Wed is valid -> result = 04-29.
    assert mock_scheduler.update_page.call_count == 1
    _pid, props = mock_scheduler.update_page.call_args[0]
    sched = props["Scheduled Date"]["date"]["start"]
    # Must NOT be the occupied 04-27 (yesterday). Must be a future LinkedIn day.
    assert sched != "2026-04-27"
    assert sched == "2026-04-29"  # M7b: Wed is valid LinkedIn day


def test_no_backfill_outside_window(mock_scheduler, monkeypatch):
    """Skipped row from 3 days ago. Backfill phase ignores it (window is
    yesterday or today only). Approval forwards to the next open slot.
    """
    payload = {"notion_id": "page-cand", "title": "Cand", "platform": "X"}
    monkeypatch.setattr(gs, "_fetch_unscheduled_approvals", lambda: [(70, payload)])
    mock_scheduler.notion_query.return_value = [
        # Skipped 3 days ago (2026-04-25 Saturday) - outside window.
        _skipped_page("page-old-skip", "X", "2026-04-25", title="Old skip"),
    ]
    monkeypatch.setattr(gs, "datetime", _freeze_today_to_tuesday_2026_04_28())

    gs.griot_scheduler_tick()

    # Old Skipped slot ignored. Forward-scheduling places it on next X slot
    # (tomorrow Wed 04-29 since today Tue is past tomorrow's start_from logic).
    assert mock_scheduler.update_page.call_count == 1
    _pid, props = mock_scheduler.update_page.call_args[0]
    sched = props["Scheduled Date"]["date"]["start"]
    assert sched != "2026-04-25"  # never backfill an out-of-window date
    assert sched == "2026-04-29"  # forward-scheduled to next X weekday


def test_backfill_chooses_matching_platform(mock_scheduler, monkeypatch):
    """Yesterday LinkedIn Skipped, but only an X candidate is in the queue.
    Backfill skips this slot (no platform match). The X candidate is then
    forward-scheduled normally. Telegram backfill notify NOT fired.
    """
    payload = {"notion_id": "page-x-cand", "title": "X cand", "platform": "X"}
    monkeypatch.setattr(gs, "_fetch_unscheduled_approvals", lambda: [(80, payload)])
    mock_scheduler.notion_query.return_value = [
        _skipped_page("page-li-skip", "LinkedIn", "2026-04-27", title="LI skip"),
    ]
    monkeypatch.setattr(gs, "datetime", _freeze_today_to_tuesday_2026_04_28())

    gs.griot_scheduler_tick()

    # X candidate forward-scheduled to next X weekday (Wed 04-29).
    assert mock_scheduler.update_page.call_count == 1
    _pid, props = mock_scheduler.update_page.call_args[0]
    assert props["Scheduled Date"]["date"]["start"] == "2026-04-29"

    # The Telegram notify that DID fire is the standard "Scheduled" message,
    # not a "Backfilled" announcement. Check the body to make sure no backfill
    # notification was sent.
    backfill_calls = [
        c for c in mock_scheduler.send_message.call_args_list
        if "Backfilled" in (c.args[1] if len(c.args) >= 2 else "")
    ]
    assert backfill_calls == []


def test_backfill_then_forward_scheduling_independent(mock_scheduler, monkeypatch):
    """Yesterday X Skipped + 3 approved X candidates. Backfill consumes ONE
    candidate for yesterday's slot. The other TWO go through forward-scheduling
    onto future X weekdays. Total update_page calls = 3, all distinct dates.
    """
    payloads = [
        (90, {"notion_id": "p-a", "title": "Cand A", "platform": "X"}),
        (91, {"notion_id": "p-b", "title": "Cand B", "platform": "X"}),
        (92, {"notion_id": "p-c", "title": "Cand C", "platform": "X"}),
    ]
    monkeypatch.setattr(gs, "_fetch_unscheduled_approvals", lambda: list(payloads))
    mock_scheduler.notion_query.return_value = [
        _skipped_page("page-x-skip", "X", "2026-04-27", title="Yesterday X skip"),
    ]
    monkeypatch.setattr(gs, "datetime", _freeze_today_to_tuesday_2026_04_28())

    gs.griot_scheduler_tick()

    # 3 update_page calls total: 1 backfill + 2 forward.
    assert mock_scheduler.update_page.call_count == 3
    dates = [c.args[1]["Scheduled Date"]["date"]["start"] for c in mock_scheduler.update_page.call_args_list]
    assert "2026-04-27" in dates  # backfilled into yesterday's slot
    assert len(set(dates)) == 3   # all distinct
    # mark_scheduled called for all 3
    assert mock_scheduler.mark_scheduled.call_count == 3
