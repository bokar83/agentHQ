"""Unit tests for approval_queue. DB-touching tests are added in later tasks."""
from __future__ import annotations

import os
import sys

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)

from approval_queue import normalize_feedback_tag, KNOWN_FEEDBACK_TAGS


def test_normalize_matches_exact_vocab():
    assert normalize_feedback_tag("off-voice") == "off-voice"
    assert normalize_feedback_tag("stale") == "stale"


def test_normalize_matches_spaced_input():
    assert normalize_feedback_tag("off voice") == "off-voice"
    assert normalize_feedback_tag("too salesy") == "too-salesy"


def test_normalize_case_insensitive():
    assert normalize_feedback_tag("STALE") == "stale"
    assert normalize_feedback_tag("Off-Voice") == "off-voice"


def test_normalize_substring_match():
    # "stale angle" matches "stale" because the canonical tag is contained
    assert normalize_feedback_tag("stale angle") == "stale"


def test_normalize_unmatched_returned_verbatim():
    assert normalize_feedback_tag("weird vibe") == "weird vibe"


def test_normalize_empty_returns_none():
    assert normalize_feedback_tag("") is None
    assert normalize_feedback_tag(None) is None


def test_known_vocab_is_a_tuple():
    # Guard against accidental set/list conversion which would break ordering.
    assert isinstance(KNOWN_FEEDBACK_TAGS, tuple)
    assert "off-voice" in KNOWN_FEEDBACK_TAGS


def test_count_pending_is_exposed_and_callable():
    """Codex PR #10 P2 fix: morning digest needs a true count, not len(preview)."""
    from approval_queue import count_pending
    assert callable(count_pending)
