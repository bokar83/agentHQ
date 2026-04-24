"""Unit tests for Phase 3 L0.5 Griot pilot.

Covers: weekday gate, empty backlog, Notion row parsing (schema fixture),
split_pool partitioning, _min_unused_arc_priority with duplicates, scoring
math with all weights, tiebreak behavior, _candidate_already_proposed dedup
path, and the end-to-end callback with mocked dependencies.
"""
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

import griot


TZ = pytz.timezone("America/Denver")


def _dt(y, m, d, h=7, mi=0):
    return TZ.localize(datetime(y, m, d, h, mi))


# ═════════════════════════════════════════════════════════════════════════════
# Schema fixtures. These mirror the REAL shape returned by NotionClient on the
# live Content Board (verified against the running container 2026-04-24).
# If the Notion schema drifts, these fixtures break BEFORE production does.
# ═════════════════════════════════════════════════════════════════════════════

def _notion_page(
    page_id: str,
    title: str,
    status: str = "Ready",
    platform=("LinkedIn",),
    topic=(),
    arc_priority=None,
    arc_phase=None,
    total_score: float = 40.0,
    hook: str = "",
    scheduled_date: str = None,
) -> dict:
    """Return a Notion page dict in the exact shape NotionClient.query_database gives."""
    return {
        "id": page_id,
        "properties": {
            "Title": {"title": [{"plain_text": title}]},
            "Status": {"select": {"name": status}},
            "Platform": {"multi_select": [{"name": p} for p in platform]},
            "Topic": {"multi_select": [{"name": t} for t in topic]},
            "Arc Priority": {"number": arc_priority},
            "Arc Phase": {"select": ({"name": arc_phase} if arc_phase else None)},
            "Total Score": {"number": total_score},
            "Hook": {"rich_text": ([{"plain_text": hook}] if hook else [])},
            "Scheduled Date": {"date": ({"start": scheduled_date} if scheduled_date else None)},
        },
    }


# ═════════════════════════════════════════════════════════════════════════════
# _is_weekend
# ═════════════════════════════════════════════════════════════════════════════

def test_is_weekend_saturday_true():
    assert griot._is_weekend(_dt(2026, 4, 25)) is True  # Saturday


def test_is_weekend_sunday_true():
    assert griot._is_weekend(_dt(2026, 4, 26)) is True  # Sunday


def test_is_weekend_friday_false():
    assert griot._is_weekend(_dt(2026, 4, 24)) is False  # Friday


def test_is_weekend_monday_false():
    assert griot._is_weekend(_dt(2026, 4, 27)) is False  # Monday


# ═════════════════════════════════════════════════════════════════════════════
# _row_from_notion (schema parsing)
# ═════════════════════════════════════════════════════════════════════════════

def test_row_from_notion_extracts_all_fields():
    page = _notion_page(
        "pid-1", "Why systems beat intentions",
        status="Ready", platform=("LinkedIn", "X"),
        topic=("AI", "Systems"), arc_priority=5, arc_phase="Hidden costs",
        total_score=49, hook="Short hook preview",
    )
    row = griot._row_from_notion(page)
    assert row["notion_id"] == "pid-1"
    assert row["title"] == "Why systems beat intentions"
    assert row["status"] == "Ready"
    assert set(row["platform"]) == {"LinkedIn", "X"}
    assert set(row["topic"]) == {"AI", "Systems"}
    assert row["arc_priority"] == 5
    assert row["arc_phase"] == "Hidden costs"
    assert row["total_score"] == 49
    assert row["hook"] == "Short hook preview"
    assert row["scheduled_date"] is None


def test_row_from_notion_handles_null_fields():
    """Keeper records (pre-arc) have null Arc Priority / Topic / Hook."""
    page = _notion_page(
        "keeper-1", "Old post from before the arc",
        status="Ready", platform=("LinkedIn",),
        arc_priority=None, arc_phase=None, total_score=None,
    )
    row = griot._row_from_notion(page)
    assert row["arc_priority"] is None
    assert row["arc_phase"] is None
    assert row["total_score"] is None
    assert row["topic"] == []
    assert row["hook"] == ""


# ═════════════════════════════════════════════════════════════════════════════
# _split_pool
# ═════════════════════════════════════════════════════════════════════════════

def test_split_pool_separates_ready_unsched_from_recent_posts():
    today = "2026-04-24"
    rows = [
        # Ready without sched: candidate
        griot._row_from_notion(_notion_page(
            "r1", "Ready no sched", status="Ready", platform=("LinkedIn",),
            scheduled_date=None, arc_priority=1,
        )),
        # Ready with sched: NOT a candidate, IS a recent_post
        griot._row_from_notion(_notion_page(
            "r2", "Ready sched", status="Ready", platform=("LinkedIn",),
            scheduled_date="2026-04-23", arc_priority=2,
        )),
        # Queued future: recent_post
        griot._row_from_notion(_notion_page(
            "q1", "Queued", status="Queued", platform=("X",),
            scheduled_date="2026-04-25", arc_priority=3,
        )),
        # Old Posted: out of window
        griot._row_from_notion(_notion_page(
            "p1", "Old post", status="Posted", platform=("LinkedIn",),
            scheduled_date="2026-01-01", arc_priority=4,
        )),
        # Archived: neither
        griot._row_from_notion(_notion_page(
            "a1", "Archived", status="Archived", platform=("LinkedIn",),
        )),
    ]
    candidates, recent_posts = griot._split_pool(rows, today)
    assert [c["notion_id"] for c in candidates] == ["r1"]
    assert sorted(r["notion_id"] for r in recent_posts) == ["q1", "r2"]


def test_split_pool_requires_platform():
    today = "2026-04-24"
    # Platform empty -> not a candidate
    rows = [
        griot._row_from_notion(_notion_page(
            "r1", "No platform", status="Ready", platform=(),
            scheduled_date=None,
        )),
        # Platform Instagram only -> not a candidate (only LinkedIn/X)
        griot._row_from_notion(_notion_page(
            "r2", "Instagram only", status="Ready", platform=("Instagram",),
            scheduled_date=None,
        )),
    ]
    candidates, recent = griot._split_pool(rows, today)
    assert candidates == []
    assert recent == []


def test_split_pool_requires_title_or_hook():
    today = "2026-04-24"
    rows = [
        griot._row_from_notion(_notion_page(
            "r1", "", status="Ready", platform=("LinkedIn",),
            scheduled_date=None, hook="",
        )),
    ]
    candidates, _ = griot._split_pool(rows, today)
    assert candidates == []


# ═════════════════════════════════════════════════════════════════════════════
# _min_unused_arc_priority
# ═════════════════════════════════════════════════════════════════════════════

def test_min_unused_arc_priority_returns_smallest_not_in_recent():
    candidates = [
        {"arc_priority": 3}, {"arc_priority": 5}, {"arc_priority": 7},
    ]
    recent = [
        {"arc_priority": 3}, {"arc_priority": 7},
    ]
    assert griot._min_unused_arc_priority(candidates, recent) == 5


def test_min_unused_arc_priority_duplicates_across_platforms_ok():
    """LinkedIn + X share the same Arc Priority. Use of set() handles this."""
    candidates = [
        {"arc_priority": 5}, {"arc_priority": 5},  # LinkedIn + X pair
        {"arc_priority": 7},
    ]
    recent = [{"arc_priority": 5}]
    assert griot._min_unused_arc_priority(candidates, recent) == 7


def test_min_unused_arc_priority_returns_none_when_all_used():
    candidates = [{"arc_priority": 3}]
    recent = [{"arc_priority": 3}]
    assert griot._min_unused_arc_priority(candidates, recent) is None


def test_min_unused_arc_priority_ignores_null_priority():
    candidates = [
        {"arc_priority": None}, {"arc_priority": 2},
    ]
    recent = []
    assert griot._min_unused_arc_priority(candidates, recent) == 2


# ═════════════════════════════════════════════════════════════════════════════
# _score_candidate
# ═════════════════════════════════════════════════════════════════════════════

def test_score_base_equals_total_score():
    cand = {"total_score": 44, "arc_priority": 2, "topic": [], "arc_phase": None}
    score, breakdown = griot._score_candidate(cand, [], next_arc_priority=None)
    assert score == 44.0
    assert "base=44" in breakdown


def test_score_next_in_arc_bonus_applied():
    cand = {"total_score": 40, "arc_priority": 2, "topic": [], "arc_phase": None}
    score, breakdown = griot._score_candidate(cand, [], next_arc_priority=2)
    assert score == 45.0
    assert "next-in-arc" in breakdown


def test_score_topic_overlap_penalty_applied():
    cand = {"total_score": 40, "arc_priority": None, "topic": ["AI", "Systems"], "arc_phase": None}
    recent = [{"topic": ["AI"], "arc_phase": None, "scheduled_date": None}]
    score, breakdown = griot._score_candidate(cand, recent, next_arc_priority=None)
    assert score == 30.0
    assert "topic overlap" in breakdown


def test_score_topic_overlap_handled_as_multi_select_intersection():
    """Topic is a list. Regression guard: don't use string equality."""
    cand = {"total_score": 40, "arc_priority": None, "topic": ["Systems", "AI"], "arc_phase": None}
    recent = [{"topic": ["AI", "Leadership"], "arc_phase": None, "scheduled_date": None}]
    score, breakdown = griot._score_candidate(cand, recent, next_arc_priority=None)
    assert "topic overlap" in breakdown  # intersection {AI}, overlap detected


def test_score_no_topic_overlap_when_sets_disjoint():
    cand = {"total_score": 40, "arc_priority": None, "topic": ["AI"], "arc_phase": None}
    recent = [{"topic": ["Governance"], "arc_phase": None, "scheduled_date": None}]
    score, breakdown = griot._score_candidate(cand, recent, next_arc_priority=None)
    assert score == 40.0
    assert "topic overlap" not in breakdown


def test_score_recent_arc_phase_penalty_applied():
    from datetime import date as _date, timedelta
    today = _date.today()
    yesterday = (today - timedelta(days=1)).isoformat()
    cand = {"total_score": 40, "arc_priority": None, "topic": [], "arc_phase": "Hidden costs"}
    recent = [{"topic": [], "arc_phase": "Hidden costs", "scheduled_date": yesterday}]
    score, breakdown = griot._score_candidate(cand, recent, next_arc_priority=None)
    assert score == 20.0
    assert "recent arc phase" in breakdown


def test_score_older_arc_phase_no_penalty():
    from datetime import date as _date, timedelta
    today = _date.today()
    far_back = (today - timedelta(days=30)).isoformat()
    cand = {"total_score": 40, "arc_priority": None, "topic": [], "arc_phase": "Hidden costs"}
    recent = [{"topic": [], "arc_phase": "Hidden costs", "scheduled_date": far_back}]
    score, breakdown = griot._score_candidate(cand, recent, next_arc_priority=None)
    assert "recent arc phase" not in breakdown


# ═════════════════════════════════════════════════════════════════════════════
# _pick_top_candidate
# ═════════════════════════════════════════════════════════════════════════════

def test_pick_top_candidate_returns_highest_score():
    cands = [
        {"notion_id": "a", "total_score": 42, "arc_priority": 1, "topic": [], "arc_phase": None},
        {"notion_id": "b", "total_score": 49, "arc_priority": 5, "topic": [], "arc_phase": None},
        {"notion_id": "c", "total_score": 30, "arc_priority": 2, "topic": [], "arc_phase": None},
    ]
    top = griot._pick_top_candidate(cands, [])
    assert top["notion_id"] == "b"
    assert top["score"] == 49.0


def test_pick_top_candidate_tiebreak_smallest_arc_priority():
    cands = [
        {"notion_id": "a", "total_score": 40, "arc_priority": 5, "topic": [], "arc_phase": None},
        {"notion_id": "b", "total_score": 40, "arc_priority": 1, "topic": [], "arc_phase": None},
    ]
    top = griot._pick_top_candidate(cands, [])
    assert top["notion_id"] == "b"  # tie on score, but arc=1 < arc=5


def test_pick_top_candidate_returns_none_when_empty():
    assert griot._pick_top_candidate([], []) is None


# ═════════════════════════════════════════════════════════════════════════════
# griot_morning_tick end-to-end (all deps mocked)
# ═════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_deps(monkeypatch):
    """Patch everything the tick touches: Notion client, episodic_memory,
    approval_queue, notifier, and the two guard queries."""
    mocks = MagicMock()
    mocks.start_task = MagicMock(return_value=MagicMock(id=123))
    mocks.complete_task = MagicMock()
    mocks.enqueue = MagicMock(return_value=MagicMock(id=99))
    mocks.send_message = MagicMock()
    mocks.notion_instance = MagicMock()

    class _FakeNotionClient:
        def __init__(self, secret=None):
            pass
        def query_database(self, db_id, filter_obj=None):
            return mocks.notion_instance.query_database(db_id, filter_obj)

    # Patch all the lazy imports inside griot.
    import sys
    em = MagicMock()
    em.start_task = mocks.start_task
    em.complete_task = mocks.complete_task
    monkeypatch.setitem(sys.modules, "episodic_memory", em)

    aq = MagicMock()
    aq.enqueue = mocks.enqueue
    monkeypatch.setitem(sys.modules, "approval_queue", aq)

    notifier = MagicMock()
    notifier.send_message = mocks.send_message
    monkeypatch.setitem(sys.modules, "notifier", notifier)

    # The NotionClient import path is skills.forge_cli.notion_client.NotionClient
    forge_cli_pkg = MagicMock()
    notion_mod = MagicMock()
    notion_mod.NotionClient = _FakeNotionClient
    monkeypatch.setitem(sys.modules, "skills.forge_cli.notion_client", notion_mod)

    # Guard queries: default to "no recent fire, no prior proposal"
    monkeypatch.setattr(griot, "_recently_fired_successfully", lambda: False)
    monkeypatch.setattr(griot, "_candidate_already_proposed", lambda nid: False)
    return mocks


def test_tick_skips_on_weekend(mock_deps, monkeypatch):
    """Saturday must not start a task_outcome."""
    monkeypatch.setattr(griot, "datetime", _FakeDatetime(_dt(2026, 4, 25, 7, 0)))
    griot.griot_morning_tick()
    assert not mock_deps.start_task.called
    assert not mock_deps.enqueue.called


def test_tick_skips_on_recent_fire(mock_deps, monkeypatch):
    monkeypatch.setattr(griot, "datetime", _FakeDatetime(_dt(2026, 4, 24, 7, 0)))  # Friday
    monkeypatch.setattr(griot, "_recently_fired_successfully", lambda: True)
    griot.griot_morning_tick()
    assert not mock_deps.start_task.called
    assert not mock_deps.enqueue.called


def test_tick_notifies_on_empty_backlog(mock_deps, monkeypatch):
    monkeypatch.setattr(griot, "datetime", _FakeDatetime(_dt(2026, 4, 24, 7, 0)))
    mock_deps.notion_instance.query_database.return_value = []
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "777")
    griot.griot_morning_tick()
    assert mock_deps.start_task.called  # outcome row IS opened (we committed to real work)
    assert not mock_deps.enqueue.called
    assert mock_deps.send_message.called
    args = mock_deps.send_message.call_args
    assert "backlog empty" in args[0][1].lower()
    # complete_task still called
    assert mock_deps.complete_task.called


def test_tick_happy_path_enqueues_top_candidate(mock_deps, monkeypatch):
    monkeypatch.setattr(griot, "datetime", _FakeDatetime(_dt(2026, 4, 24, 7, 0)))  # Friday
    # Three candidates; expect the highest score (arc 3, score 49) to win.
    pages = [
        _notion_page("pid-a", "Post A", status="Ready", platform=("LinkedIn",),
                     topic=("AI",), arc_priority=1, arc_phase="Establish the frame", total_score=42,
                     hook="hook a"),
        _notion_page("pid-b", "Post B", status="Ready", platform=("LinkedIn",),
                     topic=("Systems",), arc_priority=3, arc_phase="Hidden costs", total_score=49,
                     hook="hook b"),
        _notion_page("pid-c", "Post C", status="Ready", platform=("X",),
                     topic=("Leadership",), arc_priority=2, arc_phase=None, total_score=30,
                     hook="hook c"),
    ]
    mock_deps.notion_instance.query_database.return_value = pages
    griot.griot_morning_tick()
    assert mock_deps.enqueue.called
    call_kwargs = mock_deps.enqueue.call_args.kwargs
    assert call_kwargs["crew_name"] == "griot"
    assert call_kwargs["proposal_type"] == "post_candidate"
    payload = call_kwargs["payload"]
    assert payload["notion_id"] == "pid-b"
    assert payload["title"] == "Post B"
    assert payload["platform"] == "LinkedIn"
    assert payload["arc_phase"] == "Hidden costs"
    assert payload["total_score"] == 49
    assert payload["score"] == 49.0
    assert "hook b" in payload["hook_preview"]
    # outcome row opened and closed
    assert mock_deps.start_task.called
    assert mock_deps.complete_task.called
    # complete_task result_summary mentions the enqueue
    complete_kwargs = mock_deps.complete_task.call_args.kwargs
    assert "proposed" in complete_kwargs["result_summary"]


def test_tick_dedup_filters_already_proposed(mock_deps, monkeypatch):
    monkeypatch.setattr(griot, "datetime", _FakeDatetime(_dt(2026, 4, 24, 7, 0)))
    pages = [
        _notion_page("pid-a", "Post A", status="Ready", platform=("LinkedIn",),
                     arc_priority=1, total_score=42, hook="hook a"),
        _notion_page("pid-b", "Post B", status="Ready", platform=("LinkedIn",),
                     arc_priority=3, total_score=49, hook="hook b"),
    ]
    mock_deps.notion_instance.query_database.return_value = pages
    # pid-b (the higher score) is deduplicated; pid-a should win instead.
    monkeypatch.setattr(griot, "_candidate_already_proposed", lambda nid: nid == "pid-b")
    griot.griot_morning_tick()
    assert mock_deps.enqueue.called
    payload = mock_deps.enqueue.call_args.kwargs["payload"]
    assert payload["notion_id"] == "pid-a"


def test_tick_handles_notion_unreachable(mock_deps, monkeypatch):
    monkeypatch.setattr(griot, "datetime", _FakeDatetime(_dt(2026, 4, 24, 7, 0)))
    mock_deps.notion_instance.query_database.side_effect = RuntimeError("notion 500")
    griot.griot_morning_tick()
    assert mock_deps.start_task.called
    assert not mock_deps.enqueue.called
    assert mock_deps.complete_task.called
    complete_kwargs = mock_deps.complete_task.call_args.kwargs
    assert "notion_unreachable" in complete_kwargs["result_summary"]


# ═════════════════════════════════════════════════════════════════════════════
# Helper: fake datetime so we can freeze time for the weekday gate.
# ═════════════════════════════════════════════════════════════════════════════

class _FakeDatetime:
    """datetime drop-in that returns a frozen .now() but otherwise delegates."""
    def __init__(self, frozen):
        self._frozen = frozen

    def now(self, tz=None):
        if tz is not None:
            return self._frozen.astimezone(tz)
        return self._frozen

    def __getattr__(self, name):
        import datetime as _dt
        return getattr(_dt.datetime, name)
