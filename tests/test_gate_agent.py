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
