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


def test_pick_x_from_weekend_jumps_to_monday():
    assert gs._pick_next_slot("X", {}, date(2026, 4, 25)) == date(2026, 4, 27)  # Sat -> Mon
    assert gs._pick_next_slot("X", {}, date(2026, 4, 26)) == date(2026, 4, 27)  # Sun -> Mon


def test_pick_x_skips_occupied_day():
    occ = {("X", "2026-04-27"): True}
    assert gs._pick_next_slot("X", occ, date(2026, 4, 27)) == date(2026, 4, 28)


def test_pick_linkedin_from_monday_goes_to_tuesday():
    assert gs._pick_next_slot("LinkedIn", {}, date(2026, 4, 27)) == date(2026, 4, 28)


def test_pick_linkedin_from_tuesday_stays_tuesday_if_open():
    assert gs._pick_next_slot("LinkedIn", {}, date(2026, 4, 28)) == date(2026, 4, 28)


def test_pick_linkedin_skips_wednesday_and_friday():
    # From Wednesday, LinkedIn's next slot is Thursday
    assert gs._pick_next_slot("LinkedIn", {}, date(2026, 4, 29)) == date(2026, 4, 30)
    # From Friday, next LinkedIn slot is the following Tuesday
    assert gs._pick_next_slot("LinkedIn", {}, date(2026, 5, 1)) == date(2026, 5, 5)


def test_pick_linkedin_tuesday_occupied_jumps_to_thursday():
    occ = {("LinkedIn", "2026-04-28"): True}
    assert gs._pick_next_slot("LinkedIn", occ, date(2026, 4, 27)) == date(2026, 4, 30)


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
    assert props["Scheduled Date"]["date"]["start"] == "2026-04-27"
    assert props["Status"]["status"]["name"] == "Queued"
    mock_scheduler.mark_scheduled.assert_called_once_with(3, "2026-04-27")


def test_tick_respects_occupancy_and_picks_next_slot(mock_scheduler, monkeypatch):
    """If Monday X slot is taken, scheduler should pick Tuesday."""
    payload = {"notion_id": "page-xyz", "title": "Test", "platform": "X"}
    monkeypatch.setattr(gs, "_fetch_unscheduled_approvals", lambda: [(5, payload)])
    # Monday 04-27 is occupied for X; scheduler should pick Tuesday 04-28
    mock_scheduler.notion_query.return_value = [
        _page("Queued", ["X"], "2026-04-27"),
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
    assert props["Scheduled Date"]["date"]["start"] == "2026-04-28"


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
    assert dates[0] == "2026-04-27"  # Monday
    assert dates[1] == "2026-04-28"  # Tuesday (next open X slot since in-memory occupancy reserved Monday)
    assert len(set(dates)) == 2
