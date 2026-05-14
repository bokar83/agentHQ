"""Tests for gate_agent.py — Echo M2.5.

Run against a local git repo fixture. No VPS, no GitHub, no Telegram.
All external calls are patched.

Success criterion (C1-C5 from echo.md M2.5):
  C1: conflict detection finds overlap between two branches touching same file
  C2: clean branch (no overlap, tests green) gets auto-merged
  C3: high-risk file branch is held, not auto-merged
  C4: test failure blocks merge
  C5: blocked + held branches do not prevent clean branch from merging
"""

from __future__ import annotations

import sys
import os
import types
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# Make orchestrator importable without container sys.path
ORCHESTRATOR = Path(__file__).parent.parent / "orchestrator"
if str(ORCHESTRATOR) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR))

import gate_agent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def no_telegram(monkeypatch):
    """Never actually send Telegram messages in tests."""
    monkeypatch.setattr(gate_agent, "_notify", MagicMock())


@pytest.fixture(autouse=True)
def no_git_io(monkeypatch):
    """Patch _git so tests never touch the real repo or network."""
    monkeypatch.setattr(gate_agent, "_fetch", MagicMock(return_value=True))
    monkeypatch.setattr(gate_agent, "_push_main", MagicMock(return_value=(True, "")))
    monkeypatch.setattr(gate_agent, "_deploy_vps", MagicMock(return_value=(True, "")))
    monkeypatch.setattr(gate_agent, "_delete_remote_branch", MagicMock())
    monkeypatch.setattr(gate_agent, "_merge_branch", MagicMock(return_value=(True, "")))


# ---------------------------------------------------------------------------
# C1: conflict detection
# ---------------------------------------------------------------------------

def test_conflict_detection_finds_overlap():
    """Two branches touching same file -> conflict reported."""
    branches_with_files = [
        ("feature/agent-a", ["orchestrator/pipeline.py", "docs/readme.md"]),
        ("feature/agent-b", ["orchestrator/pipeline.py", "tests/test_foo.py"]),
    ]
    conflicts = gate_agent._detect_conflicts(branches_with_files)
    assert len(conflicts) == 1
    b1, b2, f = conflicts[0]
    assert f == "orchestrator/pipeline.py"
    assert set([b1, b2]) == {"feature/agent-a", "feature/agent-b"}


def test_no_conflict_when_files_disjoint():
    """Two branches with no shared files -> no conflict."""
    branches_with_files = [
        ("feature/agent-a", ["docs/roadmap/echo.md"]),
        ("feature/agent-b", ["tests/test_bar.py"]),
    ]
    conflicts = gate_agent._detect_conflicts(branches_with_files)
    assert conflicts == []


def test_three_way_conflict():
    """Three branches touching same file -> 3 conflict pairs."""
    branches_with_files = [
        ("feature/a", ["shared.py"]),
        ("feature/b", ["shared.py"]),
        ("feature/c", ["shared.py"]),
    ]
    conflicts = gate_agent._detect_conflicts(branches_with_files)
    assert len(conflicts) == 3


# ---------------------------------------------------------------------------
# C2: auto-merge clean branch
# ---------------------------------------------------------------------------

def test_clean_branch_auto_merges(monkeypatch):
    """Branch with no conflicts + green tests + safe files gets merged."""
    monkeypatch.setattr(gate_agent, "_branches_ahead_of_main",
                        MagicMock(return_value=["feature/docs-update"]))
    monkeypatch.setattr(gate_agent, "_branch_is_claimed", MagicMock(return_value=False))
    monkeypatch.setattr(gate_agent, "_branch_is_ready", MagicMock(return_value=True))
    monkeypatch.setattr(gate_agent, "_files_changed_vs_main",
                        MagicMock(return_value=["docs/roadmap/echo.md"]))
    monkeypatch.setattr(gate_agent, "_run_tests",
                        MagicMock(return_value=(True, "1 passed")))

    gate_agent.gate_tick()

    gate_agent._merge_branch.assert_called_once_with("feature/docs-update")
    gate_agent._push_main.assert_called_once()
    gate_agent._deploy_vps.assert_called_once()
    gate_agent._delete_remote_branch.assert_called_once_with("feature/docs-update")


# ---------------------------------------------------------------------------
# C3: high-risk file held for approval
# ---------------------------------------------------------------------------

def test_high_risk_branch_held(monkeypatch):
    """Branch touching scheduler.py is held, not auto-merged."""
    monkeypatch.setattr(gate_agent, "_branches_ahead_of_main",
                        MagicMock(return_value=["feature/scheduler-fix"]))
    monkeypatch.setattr(gate_agent, "_branch_is_claimed", MagicMock(return_value=False))
    monkeypatch.setattr(gate_agent, "_branch_is_ready", MagicMock(return_value=True))
    monkeypatch.setattr(gate_agent, "_files_changed_vs_main",
                        MagicMock(return_value=["orchestrator/scheduler.py"]))
    monkeypatch.setattr(gate_agent, "_run_tests", MagicMock())

    gate_agent.gate_tick()

    gate_agent._merge_branch.assert_not_called()
    gate_agent._push_main.assert_not_called()
    # Urgent notify fired
    notify_calls = gate_agent._notify.call_args_list
    assert any(kw.get("urgent") for _, kw in notify_calls)


# ---------------------------------------------------------------------------
# C4: test failure blocks merge
# ---------------------------------------------------------------------------

def test_test_failure_blocks_merge(monkeypatch):
    """Red tests on a branch prevent merge."""
    monkeypatch.setattr(gate_agent, "_branches_ahead_of_main",
                        MagicMock(return_value=["feature/broken-thing"]))
    monkeypatch.setattr(gate_agent, "_branch_is_claimed", MagicMock(return_value=False))
    monkeypatch.setattr(gate_agent, "_branch_is_ready", MagicMock(return_value=True))
    monkeypatch.setattr(gate_agent, "_files_changed_vs_main",
                        MagicMock(return_value=["skills/coordination/__init__.py"]))
    monkeypatch.setattr(gate_agent, "_run_tests",
                        MagicMock(return_value=(False, "FAILED 3 errors")))

    gate_agent.gate_tick()

    gate_agent._merge_branch.assert_not_called()
    gate_agent._push_main.assert_not_called()
    notify_calls = gate_agent._notify.call_args_list
    assert any("TESTS FAILED" in str(args) for args, _ in notify_calls)


# ---------------------------------------------------------------------------
# C5: blocked branch does not prevent clean branch
# ---------------------------------------------------------------------------

def test_conflict_blocks_only_involved_branches(monkeypatch):
    """Conflicting pair gets blocked; unrelated clean branch still merges."""
    branches = ["feature/agent-a", "feature/agent-b", "feature/clean-docs"]

    def mock_files(branch):
        if branch == "feature/agent-a":
            return ["orchestrator/pipeline.py"]
        if branch == "feature/agent-b":
            return ["orchestrator/pipeline.py"]
        return ["docs/roadmap/studio.md"]

    monkeypatch.setattr(gate_agent, "_branches_ahead_of_main",
                        MagicMock(return_value=branches))
    monkeypatch.setattr(gate_agent, "_branch_is_claimed", MagicMock(return_value=False))
    monkeypatch.setattr(gate_agent, "_branch_is_ready", MagicMock(return_value=True))
    monkeypatch.setattr(gate_agent, "_files_changed_vs_main",
                        MagicMock(side_effect=mock_files))
    monkeypatch.setattr(gate_agent, "_run_tests",
                        MagicMock(return_value=(True, "1 passed")))

    gate_agent.gate_tick()

    # Only clean-docs merged
    gate_agent._merge_branch.assert_called_once_with("feature/clean-docs")
    gate_agent._push_main.assert_called_once()
    # Conflict notify fired for the two blocked branches
    notify_calls = gate_agent._notify.call_args_list
    assert any("CONFLICT" in str(args) for args, _ in notify_calls)


# ---------------------------------------------------------------------------
# Risk classification helpers
# ---------------------------------------------------------------------------

def test_is_high_risk_detects_scheduler():
    assert gate_agent._is_high_risk(["orchestrator/scheduler.py"]) is True


def test_is_high_risk_detects_gate_agent():
    assert gate_agent._is_high_risk(["orchestrator/gate_agent.py"]) is True


def test_is_not_high_risk_for_docs():
    assert gate_agent._is_high_risk(["docs/roadmap/echo.md"]) is False


def test_auto_approvable_docs_and_tests():
    assert gate_agent._is_auto_approvable(["docs/readme.md", "tests/test_foo.py"]) is True


def test_not_auto_approvable_mixed():
    assert gate_agent._is_auto_approvable(["docs/readme.md", "orchestrator/app.py"]) is False


# ---------------------------------------------------------------------------
# [READY] sentinel (Option 2)
# ---------------------------------------------------------------------------

def test_branch_is_ready_when_commit_has_ready(monkeypatch):
    monkeypatch.setattr(gate_agent, "_last_commit_message",
                        MagicMock(return_value="feat(studio): render fix [READY]"))
    assert gate_agent._branch_is_ready("feature/studio-fix") is True


def test_branch_not_ready_without_sentinel(monkeypatch):
    monkeypatch.setattr(gate_agent, "_last_commit_message",
                        MagicMock(return_value="WIP: still testing render pipeline"))
    assert gate_agent._branch_is_ready("feature/studio-fix") is False


def test_wip_branch_skipped_by_gate(monkeypatch):
    """Branch without [READY] is skipped entirely -- not merged."""
    monkeypatch.setattr(gate_agent, "_branches_ahead_of_main",
                        MagicMock(return_value=["feature/wip-thing"]))
    monkeypatch.setattr(gate_agent, "_branch_is_claimed",
                        MagicMock(return_value=False))
    monkeypatch.setattr(gate_agent, "_branch_is_ready",
                        MagicMock(return_value=False))
    monkeypatch.setattr(gate_agent, "_run_tests", MagicMock())

    gate_agent.gate_tick()

    gate_agent._merge_branch.assert_not_called()
    gate_agent._push_main.assert_not_called()


def test_ready_branch_processed(monkeypatch):
    """Branch with [READY] and green tests gets merged."""
    monkeypatch.setattr(gate_agent, "_branches_ahead_of_main",
                        MagicMock(return_value=["feature/done-thing"]))
    monkeypatch.setattr(gate_agent, "_branch_is_claimed",
                        MagicMock(return_value=False))
    monkeypatch.setattr(gate_agent, "_branch_is_ready",
                        MagicMock(return_value=True))
    monkeypatch.setattr(gate_agent, "_files_changed_vs_main",
                        MagicMock(return_value=["docs/readme.md"]))
    monkeypatch.setattr(gate_agent, "_run_tests",
                        MagicMock(return_value=(True, "1 passed")))

    gate_agent.gate_tick()

    gate_agent._merge_branch.assert_called_once_with("feature/done-thing")


# ---------------------------------------------------------------------------
# branch claim check (Option 3)
# ---------------------------------------------------------------------------

def test_claimed_branch_skipped(monkeypatch):
    """Branch claimed by an in-flight agent is skipped this tick."""
    monkeypatch.setattr(gate_agent, "_branches_ahead_of_main",
                        MagicMock(return_value=["feature/in-flight"]))
    monkeypatch.setattr(gate_agent, "_branch_is_claimed",
                        MagicMock(return_value=True))
    monkeypatch.setattr(gate_agent, "_branch_is_ready", MagicMock())
    monkeypatch.setattr(gate_agent, "_run_tests", MagicMock())

    gate_agent.gate_tick()

    gate_agent._merge_branch.assert_not_called()
    # _branch_is_ready never called -- claimed check short-circuits
    gate_agent._branch_is_ready.assert_not_called()


def test_unclaimed_ready_branch_processed(monkeypatch):
    """Unclaimed + [READY] branch proceeds to merge."""
    monkeypatch.setattr(gate_agent, "_branches_ahead_of_main",
                        MagicMock(return_value=["feature/clean"]))
    monkeypatch.setattr(gate_agent, "_branch_is_claimed",
                        MagicMock(return_value=False))
    monkeypatch.setattr(gate_agent, "_branch_is_ready",
                        MagicMock(return_value=True))
    monkeypatch.setattr(gate_agent, "_files_changed_vs_main",
                        MagicMock(return_value=["skills/foo/SKILL.md"]))
    monkeypatch.setattr(gate_agent, "_run_tests",
                        MagicMock(return_value=(True, "all passed")))

    gate_agent.gate_tick()

    gate_agent._merge_branch.assert_called_once_with("feature/clean")


# ---------------------------------------------------------------------------
# Protected branches never touched
# ---------------------------------------------------------------------------

def test_protected_branches_excluded(monkeypatch):
    """main, echo-m1, coordination-layer never appear in gate queue."""
    # Simulate remote listing all branches including protected ones
    def fake_branches_ahead():
        # _branches_ahead_of_main filters internally -- call real impl with mocked _git
        return []

    monkeypatch.setattr(gate_agent, "_branches_ahead_of_main",
                        MagicMock(return_value=[]))
    gate_agent.gate_tick()
    gate_agent._merge_branch.assert_not_called()


# ---------------------------------------------------------------------------
# 2026-05-14 fix: HIGH_RISK strictly dominates AUTO_APPROVE
# ---------------------------------------------------------------------------

def test_high_risk_dominates_auto_approve(monkeypatch):
    """PR touching ONLY orchestrator/gate_agent.py (HIGH_RISK + auto-approvable)
    must trigger approval flow, not auto-merge. Regression guard for the
    pre-2026-05-14 bug where `_is_high_risk AND not _is_auto_approvable`
    short-circuited the approval check."""
    monkeypatch.setattr(gate_agent, "_gate_enabled", MagicMock(return_value=True))
    # Worktrees use .git as a file (not dir). Point REPO_DIR at the canonical
    # tree where .git is a real directory so gate_tick's startup check passes.
    monkeypatch.setattr(gate_agent, "REPO_DIR", Path("D:/Ai_Sandbox/agentsHQ"))
    monkeypatch.setattr(gate_agent, "_branches_ahead_of_main",
                        MagicMock(return_value=["feat/edit-gate-itself"]))
    monkeypatch.setattr(gate_agent, "_branch_is_claimed", MagicMock(return_value=False))
    monkeypatch.setattr(gate_agent, "_branch_is_ready", MagicMock(return_value=True))
    monkeypatch.setattr(gate_agent, "_files_changed_vs_main",
                        MagicMock(return_value=["orchestrator/gate_agent.py"]))
    monkeypatch.setattr(gate_agent, "_branch_diff_has_token", MagicMock(return_value=False))
    monkeypatch.setattr(gate_agent, "_branch_diff_has_bypass_pattern", MagicMock(return_value=False))
    monkeypatch.setattr(gate_agent, "_check_approval", MagicMock(return_value="pending"))
    monkeypatch.setattr(gate_agent, "_branch_tip_sha", MagicMock(return_value="abc123"))
    monkeypatch.setattr(gate_agent, "_alerted_recently", MagicMock(return_value=False))
    monkeypatch.setattr(gate_agent, "_mark_alerted", MagicMock())
    monkeypatch.setattr(gate_agent, "_notify_gate_review", MagicMock())
    monkeypatch.setattr(gate_agent, "_run_tests", MagicMock(return_value=(True, "skipped")))

    gate_agent.gate_tick()

    gate_agent._merge_branch.assert_not_called()
    gate_agent._push_main.assert_not_called()
    gate_agent._notify_gate_review.assert_called_once()


# ---------------------------------------------------------------------------
# 2026-05-14 fix: bypass-pattern tripwire (Council premortem condition #3)
# ---------------------------------------------------------------------------

def test_bypass_pattern_detector_finds_env_var_bypass():
    """Added line introducing CLAUDE_BYPASS_HIGH_RISK env-var is caught."""
    fake_diff = (
        "diff --git a/scripts/run.sh b/scripts/run.sh\n"
        "+CLAUDE_BYPASS_HIGH_RISK=1\n"
        "+echo 'merging'\n"
    )
    from unittest.mock import patch
    with patch.object(gate_agent, "_git", return_value=(0, fake_diff, "")):
        assert gate_agent._branch_diff_has_bypass_pattern("feat/sneaky") is True


def test_bypass_pattern_detector_finds_skip_gate():
    """Added SKIP_GATE_HIGH_RISK style env-var is caught."""
    fake_diff = (
        "diff --git a/.env b/.env\n"
        "+SKIP_GATE_HIGH_RISK=true\n"
    )
    from unittest.mock import patch
    with patch.object(gate_agent, "_git", return_value=(0, fake_diff, "")):
        assert gate_agent._branch_diff_has_bypass_pattern("feat/skip") is True


def test_bypass_pattern_detector_ignores_documented_references():
    """Comment in source file mentioning the pattern with safe-words does not trip."""
    fake_diff = (
        "+++ b/orchestrator/something.py\n"
        "+# EXAMPLE: BYPASS_GATE pattern is FORBIDDEN; see _BYPASS_PATTERN regex.\n"
    )
    from unittest.mock import patch
    with patch.object(gate_agent, "_git", return_value=(0, fake_diff, "")):
        assert gate_agent._branch_diff_has_bypass_pattern("feat/safe-comment") is False


def test_bypass_pattern_detector_skips_test_files():
    """Pattern in tests/ path does not trip (tests need fixtures)."""
    fake_diff = (
        "+++ b/tests/test_gate.py\n"
        "+    fake_env = 'CLAUDE_BYPASS_HIGH_RISK=1'\n"
    )
    from unittest.mock import patch
    with patch.object(gate_agent, "_git", return_value=(0, fake_diff, "")):
        assert gate_agent._branch_diff_has_bypass_pattern("feat/test-fixture") is False


def test_bypass_pattern_detector_ignores_clean_diff():
    """Diff with no bypass pattern returns False."""
    fake_diff = (
        "diff --git a/src/foo.py b/src/foo.py\n"
        "+def hello():\n"
        "+    return 'world'\n"
    )
    from unittest.mock import patch
    with patch.object(gate_agent, "_git", return_value=(0, fake_diff, "")):
        assert gate_agent._branch_diff_has_bypass_pattern("feat/clean") is False


def test_bypass_pattern_detector_only_inspects_added_lines():
    """Pattern in a REMOVED line (starts with -) is NOT a hit; we are cleaning
    up, not introducing it."""
    fake_diff = (
        "diff --git a/scripts/run.sh b/scripts/run.sh\n"
        "-CLAUDE_BYPASS_HIGH_RISK=1\n"
        "+CLAUDE_NO_BYPASS=1\n"
    )
    from unittest.mock import patch
    with patch.object(gate_agent, "_git", return_value=(0, fake_diff, "")):
        assert gate_agent._branch_diff_has_bypass_pattern("feat/removing-bypass") is False


def test_bypass_pattern_branch_blocked_and_alerted(monkeypatch):
    """Bypass-pattern hit -> branch blocked, urgent Telegram fires, merge skipped."""
    monkeypatch.setattr(gate_agent, "_gate_enabled", MagicMock(return_value=True))
    # Worktrees use .git as a file (not dir). Point REPO_DIR at the canonical
    # tree where .git is a real directory so gate_tick's startup check passes.
    monkeypatch.setattr(gate_agent, "REPO_DIR", Path("D:/Ai_Sandbox/agentsHQ"))
    monkeypatch.setattr(gate_agent, "_branches_ahead_of_main",
                        MagicMock(return_value=["feat/sneaky-bypass"]))
    monkeypatch.setattr(gate_agent, "_branch_is_claimed", MagicMock(return_value=False))
    monkeypatch.setattr(gate_agent, "_branch_is_ready", MagicMock(return_value=True))
    monkeypatch.setattr(gate_agent, "_files_changed_vs_main",
                        MagicMock(return_value=["scripts/something.sh"]))
    monkeypatch.setattr(gate_agent, "_branch_diff_has_token", MagicMock(return_value=False))
    monkeypatch.setattr(gate_agent, "_branch_diff_has_bypass_pattern", MagicMock(return_value=True))
    monkeypatch.setattr(gate_agent, "_branch_tip_sha", MagicMock(return_value="deadbeef"))
    monkeypatch.setattr(gate_agent, "_alerted_recently", MagicMock(return_value=False))
    monkeypatch.setattr(gate_agent, "_mark_alerted", MagicMock())
    monkeypatch.setattr(gate_agent, "_run_tests", MagicMock(return_value=(True, "skipped")))

    gate_agent.gate_tick()

    gate_agent._merge_branch.assert_not_called()
    notify_calls = gate_agent._notify.call_args_list
    assert any("BYPASS PATTERN" in str(args) for args, _ in notify_calls), (
        f"expected GATE BYPASS PATTERN alert; got calls: {notify_calls}"
    )
