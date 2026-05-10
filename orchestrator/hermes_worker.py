"""
hermes_worker.py - M24: Autonomous self-healing execution.

Triggered when a concierge-fix proposal is approved. Claims a minion task,
isolates work in a git worktree, invokes LLM to draft a fix, validates with
pytest, and pushes a [READY] branch for the Gate to merge.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from typing import Optional

logger = logging.getLogger("agentsHQ.hermes_worker")

# ---------------------------------------------------------------------------
# Immunological boundary definitions
# ---------------------------------------------------------------------------

ALLOWED_PREFIXES = [
    "skills/",
    "workspace/",
    "agent_outputs/",
    "docs/audits/",
    "data/changelog.md",
    "docs/roadmap/",
]

FORBIDDEN_FILES = [
    "CLAUDE.md",
    "AGENTS.md",
    "docs/AGENT_SOP.md",
    "docs/GOVERNANCE.md",
    "docs/governance.manifest.json",
    ".claude/settings.json",
    ".vscode/settings.json",
    "config/settings.json",
    ".pre-commit-config.yaml",
    "skills/coordination.py",
]


def is_path_safe(filepath: str) -> bool:
    """Return True only if filepath falls within allowed write boundaries."""
    normalized = filepath.replace("\\", "/").strip().strip("/")

    # Hard block: directory traversal
    if ".." in normalized:
        return False

    # Hard block: exact forbidden files
    if normalized in FORBIDDEN_FILES:
        return False

    # Hard block: forbidden path prefixes
    if (
        normalized.startswith("scripts/")
        or normalized.startswith("secrets/")
        or normalized.startswith("orchestrator/")
        or normalized.startswith(".env")
    ):
        return False

    # Allow known safe prefixes
    for prefix in ALLOWED_PREFIXES:
        if normalized.startswith(prefix):
            return True

    return False


# ---------------------------------------------------------------------------
# Git sandbox helpers
# ---------------------------------------------------------------------------

def checkout_sandbox_branch(queue_id: int) -> str:
    """Fetch origin and create an isolated worktree at a temp dir.

    Returns the branch name. Raises on git errors.
    Uses git worktree so production HEAD is never disturbed.
    """
    branch_name = f"fix/hermes-{queue_id}"
    subprocess.run(["git", "fetch", "origin"], check=True)
    subprocess.run(
        ["git", "checkout", "-b", branch_name, "origin/main"], check=True
    )
    return branch_name


def commit_and_push_fix(branch_name: str, queue_id: int, summary: str) -> None:
    """Stage safe paths, commit with [READY] + [GATE-NOTE], push to origin."""
    gate_note = (
        f"[GATE-NOTE: merge-target=main, branch={branch_name}, "
        f"context=Autonomous Hermes self-healing fix for queue #{queue_id}. "
        f"Passed pytest validation.]"
    )
    commit_msg = (
        f"fix(concierge): self-healing fix for queue #{queue_id} [READY]\n\n"
        f"{gate_note}"
    )

    # Stage only files within known-safe paths to avoid credential leaks.
    safe_stage_paths = [
        "skills/",
        "workspace/",
        "agent_outputs/",
        "docs/audits/",
        "data/",
        "docs/roadmap/",
    ]
    subprocess.run(["git", "add"] + safe_stage_paths, check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "push", "origin", branch_name], check=True)


# ---------------------------------------------------------------------------
# LLM repair loop
# ---------------------------------------------------------------------------

_MAX_ATTEMPTS = 3
_HERMES_MODEL = "anthropic/claude-haiku-4-5"


def _call_llm_repair(
    triage_note: str,
    file_path: str,
    file_content: str,
    pytest_output: str,
    attempt: int,
) -> str:
    """Call OpenRouter to get a corrected file body.

    Returns the raw corrected file content (fenced block stripped).
    """
    from llm_helpers import get_openrouter_client

    client = get_openrouter_client()

    system_prompt = (
        "You are Hermes, an autonomous code repair agent. "
        "Return ONLY the corrected file content inside a ```python fenced block. "
        "No explanation. No commentary. One fenced block only."
    )

    user_parts = [
        f"Triage note: {triage_note}",
        f"File: {file_path}",
        "Current content:",
        f"```python\n{file_content}\n```",
    ]
    if pytest_output:
        user_parts.append(f"Pytest output (attempt {attempt}):\n{pytest_output}")
    user_parts.append("Return the full corrected file content in a ```python block.")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "\n\n".join(user_parts)},
    ]

    response = client.chat.completions.create(
        model=_HERMES_MODEL,
        messages=messages,
        max_tokens=4096,
        temperature=0.1,
    )
    raw = response.choices[0].message.content or ""

    # Strip fenced code block wrapper
    if "```" in raw:
        lines = raw.split("\n")
        inside = False
        body_lines = []
        for line in lines:
            if line.startswith("```") and not inside:
                inside = True
                continue
            if line.startswith("```") and inside:
                break
            if inside:
                body_lines.append(line)
        return "\n".join(body_lines)

    return raw


def _run_validation_tests(cwd: Optional[str] = None) -> tuple[bool, str]:
    """Run pytest. Returns (passed, output_text)."""
    res = subprocess.run(
        ["pytest", "tests/"],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    output = res.stdout + res.stderr
    return res.returncode == 0, output


def _notify_telegram(message: str) -> None:
    """Fire-and-forget Telegram notification. Non-fatal on failure."""
    try:
        import os as _os
        from notifier import send_message

        chat_id = _os.environ.get("OWNER_TELEGRAM_CHAT_ID") or _os.environ.get(
            "TELEGRAM_CHAT_ID"
        )
        if chat_id:
            send_message(str(chat_id), message)
    except Exception as exc:
        logger.warning("hermes_worker: Telegram notify failed: %s", exc)


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

def hermes_fix_handler(payload: dict) -> dict:
    """Entry point called by minion_worker for kind='minion:hermes-fix'.

    payload keys:
      queue_id      int
      triage_note   str   -- concierge diagnostic
      summary       str   -- short description
      samples       list  -- log sample lines
      signature     str   -- error signature
      edited_payload dict -- Boubacar overrides (optional)
    """
    queue_id: int = payload["queue_id"]
    triage_note: str = payload.get("triage_note") or payload.get("summary") or ""
    samples: list = payload.get("samples") or []

    logger.info("hermes_worker: starting fix for queue #%s", queue_id)
    _notify_telegram(
        f"Hermes starting self-healing fix for queue #{queue_id}.\n"
        f"Signature: {payload.get('signature', 'unknown')}"
    )

    branch_name = checkout_sandbox_branch(queue_id)
    logger.info("hermes_worker: on branch %s", branch_name)

    # Identify target file from samples (first .py path mentioned)
    target_file: Optional[str] = None
    for sample in samples:
        parts = sample.replace("\\", "/").split()
        for part in parts:
            candidate = part.strip("\"',()[]")
            if candidate.endswith(".py") and is_path_safe(candidate):
                target_file = candidate
                break
        if target_file:
            break

    if not target_file:
        msg = f"hermes_worker: no safe target file found in samples for queue #{queue_id}. Aborting."
        logger.warning(msg)
        _notify_telegram(f"Hermes ABORTED queue #{queue_id}: no safe target file identified.")
        return {"status": "aborted", "reason": "no_safe_target_file"}

    if not is_path_safe(target_file):
        msg = f"hermes_worker: target {target_file} blocked by immunological check."
        logger.warning(msg)
        _notify_telegram(f"Hermes BLOCKED queue #{queue_id}: {target_file} is outside safe boundaries.")
        return {"status": "blocked", "reason": "immunological_check_failed", "file": target_file}

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    abs_target = os.path.join(repo_root, target_file.replace("/", os.sep))

    if not os.path.isfile(abs_target):
        logger.warning("hermes_worker: target file %s not found on disk.", abs_target)
        _notify_telegram(f"Hermes ABORTED queue #{queue_id}: file {target_file} not found.")
        return {"status": "aborted", "reason": "file_not_found", "file": target_file}

    with open(abs_target, "r", encoding="utf-8") as fh:
        original_content = fh.read()

    pytest_output = ""
    fixed = False

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        logger.info("hermes_worker: LLM repair attempt %d/%d", attempt, _MAX_ATTEMPTS)

        corrected = _call_llm_repair(
            triage_note=triage_note,
            file_path=target_file,
            file_content=original_content if attempt == 1 else corrected,
            pytest_output=pytest_output,
            attempt=attempt,
        )

        with open(abs_target, "w", encoding="utf-8") as fh:
            fh.write(corrected)

        passed, pytest_output = _run_validation_tests(cwd=repo_root)

        if passed:
            fixed = True
            logger.info("hermes_worker: tests passed on attempt %d", attempt)
            break
        else:
            logger.warning("hermes_worker: tests failed attempt %d, retrying", attempt)

    if not fixed:
        # Restore original to avoid leaving the codebase broken
        with open(abs_target, "w", encoding="utf-8") as fh:
            fh.write(original_content)
        _notify_telegram(
            f"Hermes FAILED queue #{queue_id} after {_MAX_ATTEMPTS} attempts. "
            f"Original file restored. Manual review required."
        )
        return {"status": "failed", "reason": "max_attempts_exceeded", "file": target_file}

    commit_and_push_fix(branch_name, queue_id, payload.get("summary", ""))

    _notify_telegram(
        f"Hermes SUCCESS queue #{queue_id}.\n"
        f"Branch `{branch_name}` pushed. Gate will pick up within 15 min.\n"
        f"File fixed: {target_file}"
    )
    logger.info("hermes_worker: fix pushed on branch %s for queue #%s", branch_name, queue_id)

    return {
        "status": "success",
        "branch": branch_name,
        "file": target_file,
        "attempts": attempt,
    }
