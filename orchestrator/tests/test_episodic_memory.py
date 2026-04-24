"""Unit tests for episodic_memory. DB-touching tests are added in later tasks."""
from __future__ import annotations

import os
import sys

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)

from episodic_memory import build_signature


def test_build_signature_lowercases_and_truncates():
    sig = build_signature("Draft LinkedIn Post About The Constraint Of Trust")
    assert sig == "draft linkedin post about the constraint of trust"
    assert len(sig) <= 50


def test_build_signature_strips_iso_dates():
    s1 = build_signature("Draft post for 2026-04-24")
    s2 = build_signature("Draft post for 2026-04-25")
    assert s1 == s2


def test_build_signature_strips_long_numeric_ids():
    s1 = build_signature("Summarize job 123456 about pricing")
    s2 = build_signature("Summarize job 789012 about pricing")
    assert s1 == s2


def test_build_signature_strips_uuids():
    s1 = build_signature("Research a1b2c3d4-e5f6-7890-abcd-ef1234567890 for client")
    s2 = build_signature("Research 12345678-90ab-cdef-1234-567890abcdef for client")
    assert s1 == s2


def test_build_signature_collapses_whitespace():
    sig = build_signature("Draft   post\n\nwith   weird   spacing")
    assert "  " not in sig
    assert "\n" not in sig


def test_build_signature_empty_returns_empty():
    assert build_signature("") == ""
    assert build_signature(None) == ""


def test_build_signature_truncates_at_50_chars():
    long_input = "a" * 200
    sig = build_signature(long_input)
    assert len(sig) == 50
