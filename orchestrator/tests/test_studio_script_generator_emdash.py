"""
Regression: _post_process must strip every dash variant that
studio_qa_crew.EM_DASH_PATTERN catches. Otherwise scripts pass through
generation but get rejected by run_qa.check_personal_rules downstream.

Bug: 2026-05-14. _post_process covered em-dash (U+2014) and " -- " only.
LLM occasionally emits en-dash (U+2013) and word--word (no surrounding
spaces). QA rejected those as personal_rules violation. Records stuck at
qa-failed with no automated retry.
"""

import re

from orchestrator.studio_script_generator import _post_process


# Mirror the pattern QA uses so this test fails the day either side drifts.
EM_DASH_PATTERN = r"[—–]|(?:(?<=\w)--| -- )"


def _runs(text: str) -> str:
    return _post_process(text, pronunciation_dict={}, loop_interval=10_000, max_spoken_words=0)


def test_em_dash_stripped():
    out = _runs("Hello world — with em-dash here")
    assert not re.search(EM_DASH_PATTERN, out), out


def test_en_dash_stripped():
    out = _runs("Hello world – with en-dash here")
    assert not re.search(EM_DASH_PATTERN, out), out


def test_double_hyphen_with_spaces_stripped():
    out = _runs("word -- word with spaces")
    assert not re.search(EM_DASH_PATTERN, out), out


def test_double_hyphen_no_spaces_stripped():
    out = _runs("word--word no spaces")
    assert not re.search(EM_DASH_PATTERN, out), out


def test_no_dashes_unchanged():
    out = _runs("normal text with no dashes")
    assert "normal text with no dashes" in out
