"""Unit tests for M5 Chairman Crew (L5 Learning Loop).

Covers: fetch_outcomes DB query shape, analyse_patterns math, propose_mutations
Sonnet call + JSON parsing, enqueue_proposals dedup logic, apply_mutation
agent_config write, and the weekly tick gate (Monday-only).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import pytz

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)

import chairman_crew

TZ = pytz.timezone("America/Denver")


def _dt(y, m, d, h=6, mi=0):
    return TZ.localize(datetime(y, m, d, h, mi))


# =============================================================================
# Fixtures
# =============================================================================

def _outcome(
    outcome="approved",
    rejection_reason="",
    score=40.0,
    platform="LinkedIn",
    arc_phase="Hidden costs",
    topic=None,
):
    return {
        "title": "Test post",
        "score": score,
        "platform": platform,
        "arc_phase": arc_phase,
        "topic": topic or ["AI"],
        "outcome": outcome,
        "rejection_reason": rejection_reason,
        "ts_decided": "2026-05-05T10:00:00+00:00",
    }


def _make_outcomes(n_approved=10, n_rejected=4, rejection_reason="off-voice"):
    outcomes = [_outcome(outcome="approved") for _ in range(n_approved)]
    outcomes += [_outcome(outcome="rejected", rejection_reason=rejection_reason) for _ in range(n_rejected)]
    return outcomes


# =============================================================================
# fetch_outcomes
# =============================================================================

def test_fetch_outcomes_parses_db_row():
    mock_row = (
        "Test title",     # title
        "42.5",           # score
        "LinkedIn",       # platform
        "Hidden costs",   # arc_phase
        '["AI","Systems"]',  # topic_json
        "rejected",       # status
        "off-voice",      # boubacar_feedback_tag
        datetime(2026, 5, 5, 10, 0, tzinfo=timezone.utc),  # ts_decided
    )
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchall.return_value = [mock_row]

    with patch("memory._pg_conn", return_value=mock_conn):
        result = chairman_crew.fetch_outcomes(days=14)

    assert len(result) == 1
    r = result[0]
    assert r["title"] == "Test title"
    assert r["score"] == pytest.approx(42.5)
    assert r["platform"] == "LinkedIn"
    assert r["outcome"] == "rejected"
    assert r["rejection_reason"] == "off-voice"
    assert r["topic"] == ["AI", "Systems"]
    assert r["ts_decided"] == "2026-05-05T10:00:00+00:00"


# =============================================================================
# analyse_patterns
# =============================================================================

def test_analyse_patterns_approval_rate():
    outcomes = _make_outcomes(n_approved=8, n_rejected=2)
    analysis = chairman_crew.analyse_patterns(outcomes)
    assert analysis["total"] == 10
    assert analysis["approved"] == 8
    assert analysis["rejected"] == 2
    assert analysis["approval_rate"] == pytest.approx(0.8)


def test_analyse_patterns_rejection_counts():
    outcomes = _make_outcomes(n_approved=5, n_rejected=3, rejection_reason="off-voice")
    outcomes += [_outcome(outcome="rejected", rejection_reason="stale")]
    analysis = chairman_crew.analyse_patterns(outcomes)
    assert analysis["rejection_counts"]["off-voice"] == 3
    assert analysis["rejection_counts"]["stale"] == 1


def test_analyse_patterns_avg_scores():
    outcomes = [
        _outcome(outcome="approved", score=45.0),
        _outcome(outcome="approved", score=35.0),
        _outcome(outcome="rejected", score=20.0),
        _outcome(outcome="rejected", score=10.0),
    ]
    analysis = chairman_crew.analyse_patterns(outcomes)
    assert analysis["avg_score_approved"] == pytest.approx(40.0)
    assert analysis["avg_score_rejected"] == pytest.approx(15.0)


def test_analyse_patterns_empty():
    analysis = chairman_crew.analyse_patterns([])
    assert analysis["total"] == 0
    assert analysis["approval_rate"] == 0.0
    assert analysis["avg_score_approved"] is None


def test_analyse_patterns_platform_rates():
    outcomes = [
        _outcome(outcome="approved", platform="LinkedIn"),
        _outcome(outcome="rejected", platform="LinkedIn"),
        _outcome(outcome="approved", platform="X"),
    ]
    analysis = chairman_crew.analyse_patterns(outcomes)
    assert analysis["platform_rates"]["LinkedIn"]["approved"] == 1
    assert analysis["platform_rates"]["LinkedIn"]["rejected"] == 1
    assert analysis["platform_rates"]["X"]["approved"] == 1


# =============================================================================
# propose_mutations
# =============================================================================

def _make_analysis(**kwargs):
    base = {
        "total": 14,
        "approved": 8,
        "rejected": 6,
        "approval_rate": 0.57,
        "rejection_counts": {"off-voice": 4, "stale": 2},
        "avg_score_approved": 42.0,
        "avg_score_rejected": 25.0,
        "platform_rates": {"LinkedIn": {"approved": 8, "rejected": 6}},
        "drift_threshold": 0.15,
    }
    base.update(kwargs)
    return base


def _mock_weights():
    return {
        "total_score_weight": 1.0,
        "next_arc_bonus": 5.0,
        "topic_overlap_penalty": 10.0,
        "recent_arc_phase_penalty": 20.0,
        "RECENCY_WINDOW_DAYS": 7.0,
        "ARC_PHASE_WINDOW_DAYS": 3.0,
    }


def test_propose_mutations_returns_validated_list():
    analysis = _make_analysis()
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = json.dumps([
        {
            "field": "topic_overlap_penalty",
            "current": 10.0,
            "proposed": 8.0,
            "rationale": "High off-voice rejection rate suggests topic overlap penalty is too low",
        }
    ])

    with patch("llm_helpers.call_llm", return_value=mock_resp):
        with patch("chairman_crew._current_weights", return_value=_mock_weights()):
            result = chairman_crew.propose_mutations(analysis)

    assert len(result) == 1
    assert result[0]["field"] == "topic_overlap_penalty"
    assert result[0]["current"] == 10.0
    assert result[0]["proposed"] == 8.0
    assert result[0]["target"] == "weight"


def test_propose_mutations_rejects_unknown_field():
    analysis = _make_analysis()
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = json.dumps([
        {"field": "unknown_field", "current": 1.0, "proposed": 2.0, "rationale": "test"}
    ])

    with patch("llm_helpers.call_llm", return_value=mock_resp):
        with patch("chairman_crew._current_weights", return_value=_mock_weights()):
            result = chairman_crew.propose_mutations(analysis)

    assert result == []


def test_propose_mutations_handles_invalid_json():
    analysis = _make_analysis()
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = "not valid json at all"

    with patch("llm_helpers.call_llm", return_value=mock_resp):
        with patch("chairman_crew._current_weights", return_value=_mock_weights()):
            result = chairman_crew.propose_mutations(analysis)

    assert result == []


def test_propose_mutations_strips_em_dashes():
    analysis = _make_analysis()
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = json.dumps([
        {
            "field": "next_arc_bonus",
            "current": 5.0,
            "proposed": 7.0,
            "rationale": "Arc coverage is low -- needs boost",
        }
    ])

    with patch("llm_helpers.call_llm", return_value=mock_resp):
        with patch("chairman_crew._current_weights", return_value=_mock_weights()):
            result = chairman_crew.propose_mutations(analysis)

    assert len(result) == 1
    assert "—" not in result[0]["rationale"]
    assert "–" not in result[0]["rationale"]


# =============================================================================
# enqueue_proposals - dedup
# =============================================================================

def test_enqueue_proposals_skips_already_queued():
    mutations = [
        {"field": "topic_overlap_penalty", "current": 10.0, "proposed": 8.0, "rationale": "test", "target": "weight"}
    ]
    with patch("chairman_crew._field_already_queued", return_value=True):
        with patch("approval_queue.enqueue") as mock_enqueue:
            result = chairman_crew.enqueue_proposals(mutations)

    assert result == []
    mock_enqueue.assert_not_called()


def test_enqueue_proposals_enqueues_when_not_queued():
    mutations = [
        {"field": "topic_overlap_penalty", "current": 10.0, "proposed": 8.0, "rationale": "test", "target": "weight"}
    ]
    mock_row = MagicMock()
    mock_row.id = 42

    with patch("chairman_crew._field_already_queued", return_value=False):
        with patch("approval_queue.enqueue", return_value=mock_row) as mock_enqueue:
            result = chairman_crew.enqueue_proposals(mutations)

    assert result == [42]
    mock_enqueue.assert_called_once()
    call_kwargs = mock_enqueue.call_args
    assert call_kwargs.kwargs["crew_name"] == "chairman"
    assert call_kwargs.kwargs["proposal_type"] == "weight-mutation"
    assert call_kwargs.kwargs["payload"]["field"] == "topic_overlap_penalty"


def test_enqueue_proposals_deduplicates_per_field():
    mutations = [
        {"field": "topic_overlap_penalty", "current": 10.0, "proposed": 8.0, "rationale": "a", "target": "weight"},
        {"field": "next_arc_bonus", "current": 5.0, "proposed": 7.0, "rationale": "b", "target": "weight"},
    ]
    mock_row = MagicMock()
    mock_row.id = 99

    def already_queued(field):
        return field == "topic_overlap_penalty"

    with patch("chairman_crew._field_already_queued", side_effect=already_queued):
        with patch("approval_queue.enqueue", return_value=mock_row) as mock_enqueue:
            result = chairman_crew.enqueue_proposals(mutations)

    assert result == [99]
    assert mock_enqueue.call_count == 1


# =============================================================================
# apply_mutation
# =============================================================================

def test_apply_mutation_writes_agent_config():
    payload = {"field": "topic_overlap_penalty", "proposed": 8.0}
    with patch("agent_config.set_config", return_value=True) as mock_set:
        result = chairman_crew.apply_mutation(42, payload)

    assert result is True
    mock_set.assert_called_once_with(
        "GRIOT_TOPIC_OVERLAP_PENALTY",
        "8.0",
        note="Set by chairman queue #42",
    )


def test_apply_mutation_rejects_unknown_field():
    payload = {"field": "UNKNOWN_FIELD", "proposed": 99.0}
    result = chairman_crew.apply_mutation(1, payload)
    assert result is False


def test_apply_mutation_missing_field():
    payload = {"proposed": 8.0}
    result = chairman_crew.apply_mutation(1, payload)
    assert result is False


def test_apply_mutation_missing_proposed():
    payload = {"field": "next_arc_bonus"}
    result = chairman_crew.apply_mutation(1, payload)
    assert result is False


# =============================================================================
# chairman_weekly_tick - Monday gate
# =============================================================================

def test_chairman_weekly_tick_skips_non_monday():
    tuesday = _dt(2026, 5, 5)  # Tuesday
    assert tuesday.weekday() == 1
    with patch("chairman_crew.datetime") as mock_dt:
        mock_dt.now.return_value = tuesday
        with patch("chairman_crew.fetch_outcomes") as mock_fetch:
            chairman_crew.chairman_weekly_tick()
            mock_fetch.assert_not_called()


def test_chairman_weekly_tick_skips_on_insufficient_data():
    monday = _dt(2026, 5, 4)  # Monday
    assert monday.weekday() == 0
    with patch("chairman_crew.datetime") as mock_dt:
        mock_dt.now.return_value = monday
        with patch("chairman_crew.fetch_outcomes", return_value=[_outcome()] * 3):
            with patch("chairman_crew.analyse_patterns") as mock_analyse:
                chairman_crew.chairman_weekly_tick()
                mock_analyse.assert_not_called()


def test_chairman_weekly_tick_runs_full_pipeline_on_monday():
    monday = _dt(2026, 5, 4)
    assert monday.weekday() == 0

    mock_row = MagicMock()
    mock_row.id = 55

    with patch("chairman_crew.datetime") as mock_dt:
        mock_dt.now.return_value = monday
        with patch("chairman_crew.fetch_outcomes", return_value=_make_outcomes(8, 6)):
            with patch("chairman_crew.analyse_patterns", wraps=chairman_crew.analyse_patterns):
                with patch("chairman_crew.propose_mutations", return_value=[
                    {"field": "topic_overlap_penalty", "current": 10.0, "proposed": 8.0, "rationale": "test", "target": "weight"}
                ]):
                    with patch("chairman_crew.enqueue_proposals", return_value=[55]) as mock_enqueue:
                        chairman_crew.chairman_weekly_tick()
                        mock_enqueue.assert_called_once()


def test_chairman_weekly_tick_no_proposals_no_enqueue():
    monday = _dt(2026, 5, 4)

    with patch("chairman_crew.datetime") as mock_dt:
        mock_dt.now.return_value = monday
        with patch("chairman_crew.fetch_outcomes", return_value=_make_outcomes(10, 2)):
            with patch("chairman_crew.propose_mutations", return_value=[]):
                with patch("chairman_crew.enqueue_proposals") as mock_enqueue:
                    chairman_crew.chairman_weekly_tick()
                    mock_enqueue.assert_not_called()
