"""Tests for orchestrator/gate_resolvers.py - the union-resolver path is the
critical innovation; cover it thoroughly. Archive + branch-wins are thin
subprocess wrappers verified via integration on the VPS."""
from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator.gate_resolvers import (
    APPEND_ONLY_LOG_PATTERNS,
    is_append_only_log,
    resolve_append_only_log,
    union_entries,
)


def test_is_append_only_log_matches_roadmap():
    assert is_append_only_log("docs/roadmap/lighthouse.md")
    assert is_append_only_log("docs/roadmap/atlas.md")


def test_is_append_only_log_matches_inbound_signal():
    assert is_append_only_log("data/inbound-signal-log.md")


def test_is_append_only_log_excludes_source_files():
    assert not is_append_only_log("orchestrator/gate_agent.py")
    assert not is_append_only_log("scripts/orc_rebuild.sh")
    assert not is_append_only_log("data/lighthouse-warm-list.md")


def test_union_entries_two_distinct_headers_both_kept():
    ours = "### 2026-05-14 morning entry\n\nMorning body.\n\n"
    theirs = "### 2026-05-14 evening entry\n\nEvening body.\n\n"
    result = union_entries(ours, theirs)
    assert "### 2026-05-14 morning entry" in result
    assert "### 2026-05-14 evening entry" in result
    # ours-first ordering: morning appears before evening
    assert result.index("morning entry") < result.index("evening entry")


def test_union_entries_dedup_on_identical_header():
    ours = "### 2026-05-14 entry\n\nOurs body.\n\n"
    theirs = "### 2026-05-14 entry\n\nTheirs body.\n\n"
    result = union_entries(ours, theirs)
    # Only one copy of the header (ours wins on tie)
    assert result.count("### 2026-05-14 entry") == 1
    assert "Ours body." in result
    assert "Theirs body." not in result


def test_union_entries_empty_ours():
    result = union_entries("", "### only theirs\n\nbody\n")
    assert "### only theirs" in result


def test_union_entries_empty_theirs():
    result = union_entries("### only ours\n\nbody\n", "")
    assert "### only ours" in result


def test_union_entries_preamble_only_from_ours():
    """Preamble (text before first ### marker) only kept from ours.
    Theirs preamble would duplicate or drift; archive preserves it for unwind."""
    ours = "preamble ours\n\n### entry a\nbody a\n"
    theirs = "preamble theirs\n\n### entry b\nbody b\n"
    result = union_entries(ours, theirs)
    assert "preamble ours" in result
    assert "preamble theirs" not in result
    assert "### entry a" in result
    assert "### entry b" in result


def test_resolve_append_only_log_file_round_trip(tmp_path: Path):
    """End-to-end: write a file with conflict markers, resolve, verify both
    entries land in output and markers are gone."""
    content = (
        "# Lighthouse Roadmap\n\n"
        "## Session Log\n\n"
        "<<<<<<< HEAD\n"
        "### 2026-05-14 morning - Day 2 AM tab-shutdown\n\n"
        "Morning body.\n\n"
        "=======\n"
        "### 2026-05-14 evening - Nate delivered\n\n"
        "Evening body.\n\n"
        ">>>>>>> origin/feat/nate-tanner-audit-2026-05-14\n"
        "### 2026-05-13 (Day 1)\n\nDay 1 body.\n"
    )
    f = tmp_path / "lighthouse.md"
    f.write_text(content, encoding="utf-8")
    count = resolve_append_only_log(f)
    out = f.read_text(encoding="utf-8")
    assert count == 1, f"expected 1 conflict block, got {count}"
    assert "<<<<<<<" not in out
    assert "=======" not in out
    assert ">>>>>>>" not in out
    assert "Day 2 AM tab-shutdown" in out
    assert "Nate delivered" in out
    assert "### 2026-05-13 (Day 1)" in out


def test_resolve_append_only_log_no_conflict_no_op(tmp_path: Path):
    """File without conflict markers passes through unchanged."""
    content = "# Roadmap\n\n## Session Log\n\n### 2026-05-14\nbody\n"
    f = tmp_path / "clean.md"
    f.write_text(content, encoding="utf-8")
    count = resolve_append_only_log(f)
    assert count == 0
    assert f.read_text(encoding="utf-8") == content


def test_resolve_append_only_log_multiple_conflict_blocks(tmp_path: Path):
    """File with 2 conflict blocks resolves both."""
    content = (
        "## A\n\n"
        "<<<<<<< HEAD\n"
        "### entry 1\n\nbody 1\n"
        "=======\n"
        "### entry 2\n\nbody 2\n"
        ">>>>>>> branch\n"
        "## B\n\n"
        "<<<<<<< HEAD\n"
        "### entry 3\n\nbody 3\n"
        "=======\n"
        "### entry 4\n\nbody 4\n"
        ">>>>>>> branch\n"
    )
    f = tmp_path / "two-conflicts.md"
    f.write_text(content, encoding="utf-8")
    count = resolve_append_only_log(f)
    out = f.read_text(encoding="utf-8")
    assert count == 2
    for tag in ("entry 1", "entry 2", "entry 3", "entry 4"):
        assert tag in out
    assert "<<<<<<<" not in out


def test_append_only_log_patterns_has_no_em_dashes():
    """Memory rule: no em-dashes anywhere in repo content."""
    for p in APPEND_ONLY_LOG_PATTERNS:
        assert "—" not in p
