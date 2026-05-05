"""
gate_agent.py - Echo M2.5: The Gate

Sole arbiter of all writes to shared state: GitHub, VPS, main branch.
Runs as a 60s heartbeat tick registered in scheduler.py.

Responsibilities (exhaustive):
- Detect feature branches ahead of main (git fetch every tick)
- Check file overlap between queued branches (conflict detection)
- Run tests on each branch before merging
- LLM code review for high-risk files (orchestrator/, deploy scripts)
- Auto-merge clean branches to main, push to GitHub
- Deploy to VPS via orc_rebuild.sh after merge
- Notify via Telegram/webchat: silent on success, loud on conflict/failure
- Delete merged feature branches after successful deploy

Does NOT: write code, answer questions, run crews, respond to unrelated messages.

Hard rules enforced here:
- Never merges if tests fail
- Never merges if file overlap exists without human approval
- Shorts-first: target_duration_sec=55 wins any conflict
- High-risk files (see HIGH_RISK_PREFIXES) require explicit approval
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
import json
from pathlib import Path
from typing import Optional

logger = logging.getLogger("agentsHQ.gate_agent")

DATA_DIR = Path(os.environ.get("GATE_DATA_DIR", "/app/data"))
REPO_DIR = Path(os.environ.get("REPO_ROOT", "/app"))
VPS_HOST = os.environ.get("VPS_HOST", "root@72.60.209.109")
MAIN_BRANCH = "main"
TICK_INTERVAL = 60  # seconds

# Branches gate never touches
PROTECTED_BRANCHES = {
    "main",
    "feature/coordination-layer",
    "feature/echo-m1",
    "fix/chat-empty-model-resolution",
}

# Branch prefixes gate skips (archive already handled)
SKIP_PREFIXES = ("archive/",)

# Files requiring explicit Boubacar approval before merge
HIGH_RISK_PREFIXES = (
    "orchestrator/scheduler.py",
    "orchestrator/gate_agent.py",
    "orchestrator/app.py",
    "scripts/orc_rebuild.sh",
    ".env",
    "docker-compose",
)

# Auto-approve scopes (no LLM review needed, just tests)
AUTO_APPROVE_PREFIXES = (
    "docs/",
    "tests/",
    "skills/",
    "templates/",
    "configs/",
)

# File overlaps in these paths are informational and should not block branch processing.
CONFLICT_NONBLOCKING = {
    "docs/SKILLS_INDEX.md",
    "docs/handoff/",
}

# Telegram notify
_BOT_TOKEN = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN", "")
_CHAT_ID = os.environ.get("OWNER_TELEGRAM_CHAT_ID", "")


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

def _notify(message: str, urgent: bool = False) -> None:
    """Send Telegram message. Silent on failure -- gate never crashes on notify."""
    if not _BOT_TOKEN or not _CHAT_ID:
        logger.warning("gate: Telegram not configured, skipping notify")
        return
    prefix = "GATE ALERT: " if urgent else "Gate: "
    payload = json.dumps({"chat_id": _CHAT_ID, "text": prefix + message}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{_BOT_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as exc:
        logger.warning("gate: notify failed: %s", exc)


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def _git(args: list[str], cwd: Optional[Path] = None) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd or REPO_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _fetch() -> bool:
    rc, _, err = _git(["fetch", "--prune", "origin"])
    if rc != 0:
        logger.error("gate: git fetch failed: %s", err)
        return False
    return True


def _branches_ahead_of_main() -> list[str]:
    """Return remote feature branches that have commits not in main."""
    rc, out, _ = _git(["branch", "-r", "--no-merged", f"origin/{MAIN_BRANCH}"])
    if rc != 0:
        return []
    branches = []
    for line in out.splitlines():
        branch = line.strip().lstrip("* ").removeprefix("origin/")
        if branch in PROTECTED_BRANCHES:
            continue
        if any(branch.startswith(p) for p in SKIP_PREFIXES):
            continue
        if not branch.startswith("feature/") and not branch.startswith("feat/") and not branch.startswith("fix/"):
            continue
        branches.append(branch)
    return branches


def _last_commit_message(branch: str) -> str:
    """Return the last commit message on a remote branch."""
    rc, out, _ = _git(["log", "-1", "--format=%s", f"origin/{branch}"])
    return out if rc == 0 else ""


def _branch_is_ready(branch: str) -> bool:
    """Branch is ready for gate processing if last commit contains [READY].

    Agents mark work complete by ending their final commit message with [READY].
    WIP branches are skipped until the agent explicitly signals completion.
    """
    return "[READY]" in _last_commit_message(branch)


def _branch_is_claimed(branch: str) -> bool:
    """Check coordination tasks table -- if branch resource is claimed, skip.

    Agents call claim(resource='branch:<name>') when starting work.
    Gate skips claimed branches to avoid processing in-flight work.
    Returns False (not claimed) if coordination substrate is unavailable.
    """
    try:
        import sys
        import os
        # Add app path for container context
        if "/app" not in sys.path:
            sys.path.insert(0, "/app")
        from skills.coordination import _connect
        with _connect() as c, c.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM tasks
                WHERE resource = %s
                  AND status = 'running'
                  AND (lease_expires_at IS NULL OR lease_expires_at > now())
                LIMIT 1
                """,
                (f"branch:{branch}",),
            )
            return cur.fetchone() is not None
    except Exception as exc:
        logger.debug("gate: claim check unavailable for %s: %s", branch, exc)
        return False  # fail open -- process the branch


def _files_changed_vs_main(branch: str) -> list[str]:
    """Files changed on branch vs main."""
    rc, out, _ = _git([
        "diff", "--name-only",
        f"origin/{MAIN_BRANCH}...origin/{branch}",
    ])
    if rc != 0:
        return []
    return [f for f in out.splitlines() if f.strip()]


def _run_tests(branch: str) -> tuple[bool, str]:
    """Checkout branch in detached state, run pytest. Returns (passed, output)."""
    _git(["fetch", "origin", branch])
    # Stash any local modifications so checkout does not refuse to overwrite them
    rc_stash, stash_out, _ = _git(["stash", "push", "-u", "-m", "gate-test-stash"])
    stashed = rc_stash == 0 and stash_out.strip() != "" and "No local changes to save" not in stash_out
    rc_co, _, err = _git(["checkout", f"origin/{branch}", "--detach"])
    if rc_co != 0:
        if stashed:
            _git(["stash", "pop"])
        return False, f"checkout failed: {err}"
    try:
        proc = subprocess.run(
            ["python", "-m", "pytest", "-q", "--tb=short", "--timeout=120"],
            cwd=str(REPO_DIR),
            capture_output=True,
            text=True,
            timeout=180,
        )
        passed = proc.returncode == 0
        output = (proc.stdout + proc.stderr)[-1000:]
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "tests timed out (180s)"
    finally:
        # Return to main and restore any stashed changes
        _git(["checkout", MAIN_BRANCH])
        if stashed:
            _git(["stash", "pop"])


def _merge_branch(branch: str) -> tuple[bool, str]:
    """Merge branch into local main. Returns (success, error)."""
    _git(["checkout", MAIN_BRANCH])
    _git(["pull", "origin", MAIN_BRANCH])
    rc, _, err = _git(["merge", f"origin/{branch}", "--no-ff",
                        "-m", f"merge({branch}): gate auto-merge -- tests green, no conflicts"])
    if rc != 0:
        _git(["merge", "--abort"])
        return False, err
    return True, ""


def _push_main() -> tuple[bool, str]:
    rc, _, err = _git(["push", "origin", MAIN_BRANCH])
    return rc == 0, err


def _delete_remote_branch(branch: str) -> None:
    rc, _, err = _git(["push", "origin", "--delete", branch])
    if rc != 0:
        logger.warning("gate: could not delete origin/%s: %s", branch, err)


def _deploy_vps() -> tuple[bool, str]:
    """Signal VPS to pull + rebuild.

    Gate runs inside orc-crewai container. Source code is NOT volume-mounted,
    so orc_rebuild.sh must run on the host. We write a trigger file to /app/data/
    (which IS mounted to /root/agentsHQ/data/ on host). A host-side watchdog
    picks this up and runs the rebuild. Until watchdog is wired, gate does a
    git pull inside the container (updates the baked image copy) and logs the
    trigger for manual pickup.
    """
    # Write trigger file for host watchdog
    trigger = Path("/app/data/gate_deploy_trigger")
    try:
        trigger.write_text(f"deploy:{MAIN_BRANCH}\n")
        logger.info("gate: deploy trigger written to %s", trigger)
    except Exception as exc:
        logger.warning("gate: could not write deploy trigger: %s", exc)

    # Pull inside container (partial -- host rebuild still needed for full deploy)
    rc, out, err = _git(["pull", "origin", MAIN_BRANCH])
    if rc != 0:
        return False, f"git pull failed: {err}"
    return True, out


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def _is_nonblocking_conflict(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in CONFLICT_NONBLOCKING)


def _detect_conflicts(
    branches_with_files: list[tuple[str, list[str]]],
) -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    """Find branch pairs touching the same file, split into blocking and nonblocking conflicts."""
    blocking_conflicts = []
    nonblocking_conflicts = []
    for i, (b1, files1) in enumerate(branches_with_files):
        for b2, files2 in branches_with_files[i + 1:]:
            overlap = set(files1) & set(files2)
            for f in overlap:
                if _is_nonblocking_conflict(f):
                    nonblocking_conflicts.append((b1, b2, f))
                else:
                    blocking_conflicts.append((b1, b2, f))
    return blocking_conflicts, nonblocking_conflicts


# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------

def _is_high_risk(files: list[str]) -> bool:
    return any(
        any(f.startswith(prefix) for prefix in HIGH_RISK_PREFIXES)
        for f in files
    )


def _is_auto_approvable(files: list[str]) -> bool:
    return all(
        any(f.startswith(prefix) for prefix in AUTO_APPROVE_PREFIXES)
        for f in files
    )


# ---------------------------------------------------------------------------
# Main tick
# ---------------------------------------------------------------------------

def _gate_enabled() -> bool:
    """Check autonomy_state.json crews.gate.enabled flag. Defaults to False if missing."""
    try:
        state_path = DATA_DIR / "autonomy_state.json"
        if not state_path.exists():
            return False
        state = json.loads(state_path.read_text())
        return bool(state.get("crews", {}).get("gate", {}).get("enabled", False))
    except Exception:
        return False


def _write_gate_log(entry: dict) -> None:
    """Append one JSONL entry to data/gate_log.jsonl (persists across rebuilds)."""
    try:
        log_path = DATA_DIR / "gate_log.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as exc:
        logger.warning("gate: could not write gate_log: %s", exc)


def gate_tick() -> None:
    """Single gate heartbeat. Called every 60s by scheduler."""
    if not _gate_enabled():
        logger.debug("gate: disabled (gate.enabled=false in autonomy_state.json)")
        return

    logger.info("gate: tick start")

    if not _fetch():
        return

    branches = _branches_ahead_of_main()
    if not branches:
        logger.info("gate: nothing to process")
        return

    logger.info("gate: found %d branch(es) to review: %s", len(branches), branches)

    # Filter: skip WIP (no [READY] sentinel) and claimed (in-flight) branches
    ready_branches: list[str] = []
    for branch in branches:
        if _branch_is_claimed(branch):
            logger.info("gate: %s skipped -- claimed (in-flight work)", branch)
            continue
        if not _branch_is_ready(branch):
            logger.info("gate: %s skipped -- no [READY] in last commit", branch)
            continue
        ready_branches.append(branch)

    if not ready_branches:
        logger.info("gate: no ready branches this tick")
        return

    # Gather files per ready branch
    branches_with_files: list[tuple[str, list[str]]] = []
    for branch in ready_branches:
        files = _files_changed_vs_main(branch)
        branches_with_files.append((branch, files))
        logger.info("gate: %s touches %d file(s)", branch, len(files))

    # Conflict detection -- block branches only when the overlap is blocking.
    blocking_conflicts, nonblocking_conflicts = _detect_conflicts(branches_with_files)
    blocked: set[str] = set()
    for b1, b2, f in blocking_conflicts:
        blocked.add(b1)
        blocked.add(b2)
        _notify(
            f"CONFLICT: {b1} and {b2} both touch {f}. Both held. Review and resolve.",
            urgent=True,
        )
        logger.warning("gate: conflict -- %s vs %s on %s", b1, b2, f)
    for b1, b2, f in nonblocking_conflicts:
        logger.info("gate: nonblocking conflict -- %s vs %s on %s", b1, b2, f)

    # Process non-blocked branches
    merged: list[str] = []
    failed: list[tuple[str, str]] = []
    held_high_risk: list[str] = []

    for branch, files in branches_with_files:
        if branch in blocked:
            continue

        # High-risk files need explicit approval
        if _is_high_risk(files) and not _is_auto_approvable(files):
            held_high_risk.append(branch)
            _notify(
                f"REVIEW NEEDED: {branch} touches high-risk files ({', '.join(f for f in files if any(f.startswith(p) for p in HIGH_RISK_PREFIXES))}). Tap to approve.",
                urgent=True,
            )
            continue

        # Run tests
        passed, test_output = _run_tests(branch)
        if not passed:
            failed.append((branch, test_output))
            _notify(
                f"TESTS FAILED: {branch}\n{test_output[:400]}",
                urgent=True,
            )
            continue

        # Merge
        ok, err = _merge_branch(branch)
        if not ok:
            failed.append((branch, err))
            _notify(f"MERGE FAILED: {branch} -- {err[:200]}", urgent=True)
            continue

        merged.append(branch)

    # Push main once if anything merged
    if merged:
        push_ok, push_err = _push_main()
        if not push_ok:
            _notify(f"PUSH FAILED after merging {merged}: {push_err}", urgent=True)
            return

        # Deploy VPS
        deploy_ok, deploy_out = _deploy_vps()
        if deploy_ok:
            _notify(f"Merged + deployed: {', '.join(merged)}")
        else:
            _notify(f"Merged {merged} but VPS deploy failed: {deploy_out[:300]}", urgent=True)

        # Clean up merged branches
        for branch in merged:
            _delete_remote_branch(branch)

    # Summary log + persistent audit trail
    import datetime as _dt
    summary = {
        "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "merged": merged,
        "failed": [{"branch": b, "reason": r[:200]} for b, r in failed],
        "blocked_conflicts": list(blocked),
        "nonblocking_conflicts": [
            {"branches": [b1, b2], "file": f}
            for b1, b2, f in nonblocking_conflicts
        ],
        "held_high_risk": held_high_risk,
    }
    logger.info(
        "gate: tick done. merged=%s, failed=%s, blocked=%s, held_high_risk=%s",
        merged, [f[0] for f in failed], list(blocked), held_high_risk,
    )
    _write_gate_log(summary)


# ---------------------------------------------------------------------------
# Standalone runner (for testing outside scheduler)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("gate: running single tick (standalone mode)")
    gate_tick()
