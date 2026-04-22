"""Tests for the task router classifier."""
import os
import sys

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)

from router import _classify_raw, _looks_like_research_report, classify_task


def test_mechanic_shops_zip_routes_to_research_report():
    """The handoff's canonical example must classify to research_report."""
    assert _classify_raw("mechanic shops in South Jordan 84095") == "research_report"


def test_dentists_near_city_routes_to_research_report():
    assert _classify_raw("dentists near Denver") == "research_report"


def test_best_x_in_y_routes_to_research_report():
    assert _classify_raw("best sushi in austin") == "research_report"


def test_explicit_research_report_phrase_routes_to_research_report():
    assert _classify_raw("research report on the top 10 CRMs for SMBs") == "research_report"


def test_find_me_phrase_routes_to_research_report():
    assert _classify_raw("find me a list of local accountants in Salt Lake") == "research_report"


def test_hunter_task_still_wins_for_lead_sourcing_language():
    """Explicit lead-sourcing language must NOT be swallowed by research_report."""
    assert _classify_raw("find leads for utah dental offices") == "hunter_task"
    assert _classify_raw("prospect for mid-market SaaS companies") == "hunter_task"


def test_chat_style_message_is_not_research_report():
    assert not _looks_like_research_report("hey how are you")
    assert not _looks_like_research_report("what is the capital of france")


def test_classify_task_wraps_research_report_in_dict():
    """classify_task must return dict shape with task_type='research_report'."""
    result = classify_task("mechanic shops in 84095")
    assert isinstance(result, dict)
    assert result["task_type"] == "research_report"
    assert result["crew"] == "research_crew"
    assert result["is_unknown"] is False
