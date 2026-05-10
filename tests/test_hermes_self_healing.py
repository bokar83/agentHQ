# tests/test_hermes_self_healing.py
"""
Tests for Milestone M24: Hermes Self-Healing Execution.
Verifies queue triggering, sandbox branching, immunological write checks,
and successful commit packaging with [READY] and [GATE-NOTE] blocks.
"""
from __future__ import annotations

import json
from unittest import mock
import pytest

from orchestrator import approval_queue
from orchestrator import hermes_worker
import skills.coordination as coordination


def test_immunological_path_safety():
    """Verify that path safety checks correctly classify allowed vs forbidden paths."""
    # Allowed paths
    assert hermes_worker.is_path_safe("skills/new_skill/skill.py") is True
    assert hermes_worker.is_path_safe("workspace/clients/brief.md") is True
    assert hermes_worker.is_path_safe("agent_outputs/report.json") is True
    assert hermes_worker.is_path_safe("docs/audits/2026-05-10-audit.md") is True
    assert hermes_worker.is_path_safe("data/changelog.md") is True
    assert hermes_worker.is_path_safe("docs/roadmap/atlas.md") is True

    # Forbidden paths (Hard block)
    assert hermes_worker.is_path_safe("CLAUDE.md") is False
    assert hermes_worker.is_path_safe("AGENTS.md") is False
    assert hermes_worker.is_path_safe("docs/AGENT_SOP.md") is False
    assert hermes_worker.is_path_safe("docs/GOVERNANCE.md") is False
    assert hermes_worker.is_path_safe("docs/governance.manifest.json") is False
    assert hermes_worker.is_path_safe(".claude/settings.json") is False
    assert hermes_worker.is_path_safe(".vscode/settings.json") is False
    assert hermes_worker.is_path_safe("config/settings.json") is False
    assert hermes_worker.is_path_safe(".pre-commit-config.yaml") is False
    assert hermes_worker.is_path_safe("scripts/some_script.py") is False
    assert hermes_worker.is_path_safe("secrets/secret_key.txt") is False
    assert hermes_worker.is_path_safe(".env") is False
    assert hermes_worker.is_path_safe("orchestrator/app.py") is False
    assert hermes_worker.is_path_safe("skills/coordination.py") is False


@mock.patch("orchestrator.approval_queue._conn")
@mock.patch("skills.coordination.enqueue")
def test_approval_triggers_hermes_enqueue(mock_enqueue, mock_conn):
    """Verify that approving a concierge-fix enqueues a minion:hermes-fix task."""
    mock_cur = mock_conn.return_value.cursor.return_value
    
    # Mock a concierge-fix row in the queue
    mock_cur.fetchone.return_value = (
        123,                           # id
        "2026-05-10 12:00:00",          # ts_created
        None,                          # ts_decided
        "concierge",                   # crew_name
        "concierge-fix",               # proposal_type
        json.dumps({                   # payload
            "signature": "ValueError: Index out of range",
            "summary": "Fix index error",
            "samples": ["ValueError at line 45 in skills/test.py"],
            "triage_note": "Adjust list slicing"
        }),
        45678,                         # telegram_msg_id
        "pending",                     # status
        None,                          # decision_note
        None,                          # boubacar_feedback_tag
        None,                          # edited_payload
        789,                           # task_outcome_id
    )

    # Approve the proposal
    approval_queue.approve(queue_id=123, note="Go ahead with the fix")

    # Verify coordinator enqueued the task with the correct payload
    mock_enqueue.assert_called_once_with(
        kind="minion:hermes-fix",
        payload={
            "queue_id": 123,
            "signature": "ValueError: Index out of range",
            "summary": "Fix index error",
            "samples": ["ValueError at line 45 in skills/test.py"],
            "triage_note": "Adjust list slicing",
            "edited_payload": None,
        }
    )


@mock.patch("subprocess.run")
def test_checkout_sandbox_branch(mock_run):
    """Verify that Hermes isolates execution in a temporary git branch."""
    branch_name = hermes_worker.checkout_sandbox_branch(queue_id=123)
    
    assert branch_name.startswith("fix/hermes-123")
    assert mock_run.call_count == 2
    mock_run.assert_any_call(["git", "fetch", "origin"], check=True)
    mock_run.assert_any_call(["git", "checkout", "-b", branch_name, "origin/main"], check=True)


@mock.patch("subprocess.run")
def test_commit_and_push_packaging(mock_run):
    """Verify commit and git packaging includes correct [READY] and [GATE-NOTE] formats."""
    hermes_worker.commit_and_push_fix(
        branch_name="fix/hermes-123",
        queue_id=123,
        summary="Fix index error"
    )

    # Verify git actions are called in order.
    # Sankofa audit finding: "git add ." risks committing .env or secrets.
    # Implementation stages explicit safe paths only.
    assert mock_run.call_count == 3
    first_call_args = mock_run.call_args_list[0][0][0]
    assert first_call_args[0] == "git"
    assert first_call_args[1] == "add"
    # Must stage at least one explicit path -- never a bare "."
    assert "." not in first_call_args[2:]
    assert len(first_call_args) > 2
    
    # Extract commit message from call args
    commit_call = mock_run.call_args_list[1]
    args = commit_call[0][0]
    commit_msg = args[3]
    
    assert "[READY]" in commit_msg
    assert "[GATE-NOTE:" in commit_msg
    assert "branch=fix/hermes-123" in commit_msg
    assert "merge-target=main" in commit_msg
    
    mock_run.assert_any_call(["git", "push", "origin", "fix/hermes-123"], check=True)
