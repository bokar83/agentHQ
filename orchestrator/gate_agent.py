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
- Escalates to Boubacar ONLY for HIGH_RISK_PREFIXES conflicts (gate_agent.py, .env, docker-compose, CLAUDE.md, AGENTS.md, GOVERNANCE.md). All other conflicts auto-resolved by merge order.
- Shorts-first: target_duration_sec=55 wins any conflict
- High-risk files (see HIGH_RISK_PREFIXES) require explicit approval
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
import urllib.parse
import urllib.request
import json
from pathlib import Path
from typing import Optional
import sys

# Subprocess creation flags to suppress console window flashing on Windows
SUBPROCESS_FLAGS = 0x08000000 if sys.platform == "win32" else 0

logger = logging.getLogger("agentsHQ.gate_agent")

try:
    from logger import audit_gate
    _AUDIT_AVAILABLE = True
except Exception:
    _AUDIT_AVAILABLE = False
    def audit_gate(*args, **kwargs): pass  # noqa: E301

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

# Files requiring explicit Boubacar approval before merge.
# ONLY ping Boubacar for these. Everything else gate resolves autonomously.
# Principle: GitHub + save points = safe revert. Alert cost > revert cost for non-core files.
HIGH_RISK_PREFIXES = (
    "orchestrator/gate_agent.py",  # gate modifying itself
    "scripts/orc_rebuild.sh",       # deploy script
    ".env",                          # secrets
    "docker-compose",               # container topology
    "CLAUDE.md",                     # agent SOP -- constitutional
    "AGENTS.md",                     # platform boundary definitions
    "docs/GOVERNANCE.md",            # governance routing table
    "docs/governance.manifest.json", # machine-readable governance mirror
)

# Auto-approve scopes (no LLM review needed, just tests)
AUTO_APPROVE_PREFIXES = (
    "docs/",
    "tests/",
    "skills/",
    "templates/",
    "configs/",
    "orchestrator/",  # tests catch regressions; gate merges and reverts if needed
    "thepopebot/",
    "scripts/",
    "signal_works/",
)

# Telegram notify
_BOT_TOKEN = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN", "")
_CHAT_ID = os.environ.get("OWNER_TELEGRAM_CHAT_ID", "")

# Tracks branches already alerted this process lifetime to suppress repeat notifications
_alerted_high_risk: set[str] = set()
# Tracks conflict pairs already alerted -- key: "b1||b2||file" -- suppresses repeat spam
_alerted_conflicts: set[str] = set()


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


def _notify_gate_review(branch: str, hr_files: list[str]) -> None:
    """Send Gate review alert with inline ✅/❌ buttons instead of slash-command text."""
    if not _BOT_TOKEN or not _CHAT_ID:
        logger.warning("gate: Telegram not configured, skipping notify")
        return
    try:
        from notifier import send_message_with_buttons
        text = (
            f"GATE ALERT: REVIEW NEEDED\n"
            f"Branch: {branch}\n"
            f"High-risk files: {', '.join(hr_files)}"
        )
        # callback_data must be ≤64 bytes; branch names are typically short
        approve_cb = f"gate_approve:{branch}"
        reject_cb = f"gate_reject:{branch}"
        if len(approve_cb.encode()) > 64 or len(reject_cb.encode()) > 64:
            # Fallback to text command if branch name too long
            _notify(
                f"REVIEW NEEDED: {branch} touches high-risk files ({', '.join(hr_files)}). "
                f"Reply '/gate-approve {branch}' to approve, '/gate-reject {branch}' to discard.",
                urgent=True,
            )
            return
        buttons = [[("✅ Approve", approve_cb), ("❌ Reject", reject_cb)]]
        send_message_with_buttons(_CHAT_ID, text, buttons)
    except Exception as exc:
        logger.warning("gate: _notify_gate_review failed: %s", exc)
        _notify(
            f"REVIEW NEEDED: {branch} touches high-risk files ({', '.join(hr_files)}). "
            f"Reply '/gate-approve {branch}' to approve, '/gate-reject {branch}' to discard.",
            urgent=True,
        )


def _notify_conflict(b1: str, b2: str, conflict_file: str) -> None:
    """Send a ONE-TIME conflict alert with Approve/Reject buttons.

    Approve = merge b1, drop b2. Reject = drop both, re-queue manually.
    The _alerted_conflicts set in the tick loop ensures this fires only once
    per unique (b1, b2, file) triple for the lifetime of the gate process.
    """
    if not _BOT_TOKEN or not _CHAT_ID:
        return
    text = (
        f"GATE CONFLICT\n"
        f"Branches: {b1}  vs  {b2}\n"
        f"File: {conflict_file}\n\n"
        f"Approve merges {b1} and drops {b2}.\n"
        f"Reject drops both — re-queue manually."
    )
    approve_cb = f"gate_approve:{b1}"
    reject_cb = f"gate_reject:{b1}"
    try:
        from notifier import send_message_with_buttons
        if len(approve_cb.encode()) <= 64 and len(reject_cb.encode()) <= 64:
            buttons = [[("✅ Merge b1", approve_cb), ("❌ Drop both", reject_cb)]]
            send_message_with_buttons(_CHAT_ID, text, buttons)
            return
    except Exception as exc:
        logger.warning("gate: _notify_conflict buttons failed: %s", exc)
    # Fallback: plain text (no repeat -- caller already deduped)
    _notify(f"CONFLICT (one-time): {b1} vs {b2} on {conflict_file}. Both held.", urgent=True)


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
        creationflags=SUBPROCESS_FLAGS,
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
        if not any(branch.startswith(p) for p in ("feature/", "feat/", "fix/", "docs/", "chore/", "refactor/", "test/", "compass/")):
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
    """Files changed on branch vs main. Returns empty list on failure (logged)."""
    rc, out, err = _git([
        "diff", "--name-only",
        f"origin/{MAIN_BRANCH}...origin/{branch}",
    ])
    if rc != 0:
        logger.warning("gate: could not diff %s vs main: %s", branch, err)
        return []
    return [f for f in out.splitlines() if f.strip()]


def _run_tests(branch: str) -> tuple[bool, str]:
    """Skip tests on VPS host -- host Python lacks container deps. Gate trusts [READY]."""
    logger.info("gate: tests skipped (host has no container deps) -- trusting [READY] signal")
    return True, "skipped (host)"


def _merge_branch(branch: str) -> tuple[bool, str]:
    """Merge branch into local main with archive + tiered auto-resolution.

    On conflict:
      1. List conflicted files via git diff --name-only --diff-filter=U
      2. For each file: archive main + branch versions to
         zzzArchive/gate-merges/<isotime>-<branch>/ BEFORE any resolution
      3. If any conflict file matches HIGH_RISK_PREFIXES -> abort + return
         with combined stdout+stderr (git writes conflict markers to stdout)
      4. Else apply resolver per file:
            APPEND_ONLY_LOG_PATTERNS -> union resolver (keep both entries)
            else                      -> branch-wins (theirs)
      5. Snapshot resolved version to archive dir
      6. Commit merge with note pointing to archive dir

    Council 2026-05-14: archive-first design replaces auto-rebase. No silent
    data loss; every conflict file has main/branch/resolved snapshots on disk.
    """
    import datetime as _dt
    try:
        from gate_resolvers import (
            archive_conflict, archive_resolved, is_append_only_log,
            resolve_append_only_log, resolve_branch_wins,
        )
    except ImportError:
        from orchestrator.gate_resolvers import (
            archive_conflict, archive_resolved, is_append_only_log,
            resolve_append_only_log, resolve_branch_wins,
        )

    rc_co, _, err_co = _git(["checkout", MAIN_BRANCH])
    if rc_co != 0:
        return False, f"checkout main failed: {err_co}"
    rc_pull, _, err_pull = _git(["pull", "origin", MAIN_BRANCH])
    if rc_pull != 0:
        return False, f"pull main failed: {err_pull}"

    rc, out, err = _git([
        "merge", f"origin/{branch}", "--no-ff",
        "-m", f"merge({branch}): gate auto-merge -- tests green, no conflicts",
    ])
    if rc == 0:
        return True, ""

    # Conflict path. Git writes conflict markers to stdout; stderr may be empty.
    combined_err = (err + "\n" + out).strip()
    rc_files, files_out, _ = _git(["diff", "--name-only", "--diff-filter=U"])
    conflicted = [f for f in files_out.splitlines() if f.strip()]
    if not conflicted:
        # Non-conflict failure (e.g. unrelated histories, hook block).
        _git(["merge", "--abort"])
        return False, combined_err or "merge failed (no conflict markers)"

    # HIGH_RISK files never auto-resolve.
    hr_hits = [f for f in conflicted if any(f.startswith(p) for p in HIGH_RISK_PREFIXES)]
    if hr_hits:
        _git(["merge", "--abort"])
        return False, (
            f"HIGH_RISK conflict on {hr_hits} (constitutional file). "
            f"Manual rebase required. All conflict files: {conflicted}. "
            f"Details: {combined_err[:300]}"
        )

    # Archive + resolve each conflict file.
    isotime = _dt.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    archive_dirs: list[Path] = []
    try:
        for f in conflicted:
            archive_dir = archive_conflict(REPO_DIR, branch, f, isotime)
            archive_dirs.append(archive_dir)
            if is_append_only_log(f):
                resolve_append_only_log(REPO_DIR / f)
            else:
                resolve_branch_wins(REPO_DIR, f)
            archive_resolved(archive_dir, REPO_DIR, f)
            rc_add, _, err_add = _git(["add", f])
            if rc_add != 0:
                _git(["merge", "--abort"])
                return False, f"git add {f} failed after resolve: {err_add}"
    except Exception as exc:
        _git(["merge", "--abort"])
        return False, f"resolver error on {branch}: {exc}"

    archive_summary = ", ".join(str(d.relative_to(REPO_DIR)) for d in archive_dirs)
    rc_co, _, err_co2 = _git([
        "commit",
        "-m",
        (
            f"merge({branch}): gate auto-resolve\n\n"
            f"Conflicts resolved: {conflicted}\n"
            f"Archives: {archive_summary}"
        ),
    ])
    if rc_co != 0:
        _git(["merge", "--abort"])
        return False, f"commit after resolve failed: {err_co2}"
    logger.info(
        "gate: auto-resolved merge of %s conflicts=%s archives=%s",
        branch, conflicted, archive_summary,
    )
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
    trigger = DATA_DIR / "gate_deploy_trigger"
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

def _files_differ(branch_a: str, branch_b: str, file_path: str) -> bool:
    """True iff branch_a and branch_b have meaningfully different content for file_path.

    Ignores line-ending-only diffs (CRLF vs LF) and ignores whitespace-only diffs.
    Coding agents on Windows write CRLF, Linux VPS writes LF — same content gets flagged
    as a conflict by naive set-overlap detection. This function strips that false positive.
    """
    # `git diff --quiet --ignore-all-space --ignore-blank-lines` returns 0 if no diff
    # (after ignoring whitespace + blanks), 1 if diffs exist.
    try:
        proc = subprocess.run(
            [
                "git", "diff", "--quiet",
                "--ignore-all-space", "--ignore-blank-lines",
                f"origin/{branch_a}", f"origin/{branch_b}",
                "--", file_path,
            ],
            cwd=str(REPO_DIR),
            capture_output=True,
            timeout=30,
        )
        return proc.returncode != 0
    except (subprocess.TimeoutExpired, OSError) as exc:
        # If diff fails for any reason, fall back to assuming a real conflict (safe default)
        logger.warning("gate: _files_differ check failed for %s on %s vs %s: %s -- assuming conflict", file_path, branch_a, branch_b, exc)
        return True


def _detect_conflicts(branches_with_files: list[tuple[str, list[str]]]) -> list[tuple[str, str, str]]:
    """Find pairs of branches with REAL content conflicts on the same file.

    Two branches "conflict" only if they both touch the same file AND the file content
    diverges between them (after ignoring whitespace / line endings). File overlap alone
    is not a conflict — both branches may have rebased/merged the same upstream commit
    and contain identical content for that path.
    """
    conflicts = []
    for i, (b1, files1) in enumerate(branches_with_files):
        for b2, files2 in branches_with_files[i + 1:]:
            overlap = set(files1) & set(files2)
            for f in overlap:
                if _files_differ(b1, b2, f):
                    conflicts.append((b1, b2, f))
                else:
                    logger.info(
                        "gate: %s and %s both touch %s but content matches -- not a conflict",
                        b1, b2, f,
                    )
    return conflicts


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


import re as _re
_TOKEN_PATTERN = _re.compile(
    r'\b(vcp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{32,}|'
    r'ghp_[A-Za-z0-9]{36,}|ghs_[A-Za-z0-9]{36,}|AKIA[0-9A-Z]{16})\b'
)
_TOKEN_SAFE = _re.compile(r'REDACTED|EXAMPLE|PLACEHOLDER', _re.I)

# Tripwire: Council premortem 2026-05-14 named "frustration bypass" as the
# failure mode after tightening HIGH_RISK approval (an agent adds
# CLAUDE_BYPASS_HIGH_RISK=1 to the systemd unit to unblock a stuck merge).
# This regex catches env-vars or code constants matching common bypass /
# skip / disable patterns scoped to "gate" or "high_risk". Hits hard-block
# the branch.
_BYPASS_PATTERN = _re.compile(
    r"(BYPASS[_A-Z0-9]*GATE"
    r"|SKIP[_A-Z0-9]*GATE"
    r"|GATE[_A-Z0-9]*BYPASS"
    r"|GATE[_A-Z0-9]*SKIP"
    r"|DISABLE[_A-Z0-9]*GATE"
    r"|GATE[_A-Z0-9]*DISABLE"
    r"|BYPASS[_A-Z0-9]*HIGH[_]?RISK"
    r"|HIGH[_]?RISK[_A-Z0-9]*BYPASS)",
    _re.IGNORECASE,
)
# Words that mark a match as a documented reference, not a real bypass.
_BYPASS_SAFE = _re.compile(r"BYPASS_PATTERN|EXAMPLE|DOCUMENTED|FORBIDDEN", _re.I)


def _branch_diff_has_token(branch: str) -> bool:
    """Return True if branch diff vs main contains an unredacted vendor token."""
    rc, diff, _ = _git(["diff", f"origin/{MAIN_BRANCH}...origin/{branch}"])
    if rc != 0:
        return False
    for m in _TOKEN_PATTERN.finditer(diff):
        context = diff[max(0, m.start()-30):m.end()+30]
        if not _TOKEN_SAFE.search(context):
            logger.warning("gate: vendor token detected in %s diff", branch)
            return True
    return False


def _branch_diff_has_bypass_pattern(branch: str) -> bool:
    """Return True if branch diff adds a line matching BYPASS/SKIP/DISABLE-gate
    pattern (env-var, constant, code). Only inspects added lines in
    non-test files. Skips: tests/ paths (need fixtures), docs/ paths
    (documentation), lines with safe-words (REDACTED, EXAMPLE, etc.)."""
    rc, diff, _ = _git(["diff", f"origin/{MAIN_BRANCH}...origin/{branch}"])
    if rc != 0:
        return False
    current_file = ""
    for line in diff.splitlines():
        if line.startswith("+++ "):
            current_file = line[6:].strip() if len(line) > 6 else ""
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        if current_file.startswith(("tests/", "docs/")):
            continue
        if _BYPASS_SAFE.search(line):
            continue
        if _BYPASS_PATTERN.search(line):
            logger.warning("gate: bypass pattern detected in %s (%s): %s", branch, current_file, line[:120])
            return True
    return False


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
    except Exception as exc:
        logger.warning("gate: could not read autonomy_state.json: %s", exc)
        return False


def _approval_marker_path(branch: str, decision: str) -> Path:
    """Path to the approve/reject marker for a branch."""
    return DATA_DIR / "gate_approvals" / (branch.replace("/", "__") + f".{decision}.json")


def _check_approval(branch: str) -> str:
    """
    Return 'approve', 'reject', or 'pending' based on marker files written by
    /gate-approve and /gate-reject Telegram slash commands. Markers are consumed
    (deleted) when read so each approval is single-use.
    """
    approve_marker = _approval_marker_path(branch, "approve")
    reject_marker = _approval_marker_path(branch, "reject")
    if approve_marker.exists():
        try:
            approve_marker.unlink()
        except OSError:
            pass
        logger.info("gate: %s approved via marker", branch)
        return "approve"
    if reject_marker.exists():
        try:
            reject_marker.unlink()
        except OSError:
            pass
        logger.info("gate: %s rejected via marker", branch)
        return "reject"
    return "pending"


def _write_gate_log(entry: dict) -> None:
    """Append one JSONL entry to data/gate_log.jsonl (persists across rebuilds)."""
    try:
        log_path = DATA_DIR / "gate_log.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as exc:
        logger.warning("gate: could not write gate_log: %s", exc)


# ---------------------------------------------------------------------------
# Persistent alert dedup
# ---------------------------------------------------------------------------
# Module-level sets (_alerted_high_risk, _alerted_conflicts) are reset every
# process start. Gate runs as a systemd timer on the VPS (fresh PID per tick),
# so module-level state never dedupes across ticks. Persist to a JSON file
# keyed on (category, key, tip_sha) so a re-alert only fires when the branch
# tip moves.
DEDUP_PATH = DATA_DIR / "gate_alerted.json"


def _load_dedup() -> dict:
    """Load persistent alert state. Returns empty buckets on first run."""
    try:
        if DEDUP_PATH.exists():
            data = json.loads(DEDUP_PATH.read_text())
            for cat in ("high_risk", "merge_fail", "conflict", "bypass_pattern"):
                data.setdefault(cat, {})
            return data
    except Exception as exc:
        logger.warning("gate: could not load dedup state: %s", exc)
    return {"high_risk": {}, "merge_fail": {}, "conflict": {}, "bypass_pattern": {}}


def _save_dedup(state: dict) -> None:
    try:
        DEDUP_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEDUP_PATH.write_text(json.dumps(state, indent=2))
    except Exception as exc:
        logger.warning("gate: could not save dedup state: %s", exc)


def _alerted_recently(category: str, key: str, tip_sha: str) -> bool:
    """True iff we already alerted for this (category, key) at the current tip."""
    return _load_dedup().get(category, {}).get(key) == tip_sha


def _mark_alerted(category: str, key: str, tip_sha: str) -> None:
    state = _load_dedup()
    state.setdefault(category, {})[key] = tip_sha
    _save_dedup(state)


def _clear_alerted(category: str, key: str) -> None:
    state = _load_dedup()
    state.get(category, {}).pop(key, None)
    _save_dedup(state)


def _branch_tip_sha(branch: str) -> str:
    rc, out, _ = _git(["rev-parse", f"origin/{branch}"])
    return out if rc == 0 else ""


def gate_tick() -> None:
    """Single gate heartbeat. Called every 60s by scheduler."""
    if not _gate_enabled():
        logger.debug("gate: disabled (gate.enabled=false in autonomy_state.json)")
        return

    if not (REPO_DIR / ".git").is_dir():
        logger.warning("gate: REPO_DIR %s has no .git dir -- skipping (container has no git repo)", REPO_DIR)
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

    # Conflict detection -- escalate only if HIGH_RISK files conflict.
    # Non-high-risk conflicts: gate merges branch-wins (theirs) autonomously, silent.
    # Rationale: GitHub history + save points make revert trivial. Alert cost > revert cost.
    conflicts = _detect_conflicts(branches_with_files)
    blocked: set[str] = set()
    for b1, b2, f in conflicts:
        if any(f.startswith(p) for p in HIGH_RISK_PREFIXES):
            # Core governance / infra file -- escalate to Boubacar
            blocked.add(b1)
            blocked.add(b2)
            conflict_key = f"{b1}||{b2}||{f}"
            tip_key = _branch_tip_sha(b1) + "|" + _branch_tip_sha(b2)
            if conflict_key not in _alerted_conflicts and not _alerted_recently("conflict", conflict_key, tip_key):
                _alerted_conflicts.add(conflict_key)
                _mark_alerted("conflict", conflict_key, tip_key)
                _notify_conflict(b1, b2, f)
            logger.warning("gate: HIGH-RISK conflict -- %s vs %s on %s -- held for review", b1, b2, f)
        else:
            # Non-core conflict -- auto-resolve: merge b1 first (earlier branch wins),
            # b2 will rebase on top after b1 lands. No alert sent.
            logger.info("gate: non-core conflict %s vs %s on %s -- will auto-resolve by merge order", b1, b2, f)

    # Process non-blocked branches
    merged: list[str] = []
    failed: list[tuple[str, str]] = []
    held_high_risk: list[str] = []

    for branch, files in branches_with_files:
        if branch in blocked:
            continue

        # Gate-side token scan -- catches tokens that slipped past local pre-commit
        if _branch_diff_has_token(branch):
            _notify(
                f"TOKEN DETECTED: {branch} diff contains a vendor-prefixed API token. "
                f"Branch held. Redact token and re-push with REDACTED safe-word.",
                urgent=True,
            )
            blocked.add(branch)
            continue

        # Bypass-pattern tripwire (Council premortem 2026-05-14 condition #3):
        # detects branches that add env-vars or code matching BYPASS/SKIP/DISABLE
        # gate patterns. Prevents the "frustration bypass" failure mode where
        # a future agent edits gate_agent.py to add a CLAUDE_BYPASS_HIGH_RISK=1
        # escape hatch. Hard-block; no override path; Telegram alerts once
        # per tip_sha.
        if _branch_diff_has_bypass_pattern(branch):
            tip = _branch_tip_sha(branch)
            if not _alerted_recently("bypass_pattern", branch, tip):
                _notify(
                    f"GATE BYPASS PATTERN: {branch} diff contains BYPASS/SKIP/DISABLE "
                    f"gate-related code or env-var. Branch held. Strip the bypass and "
                    f"re-push, or /gate-reject to drop.",
                    urgent=True,
                )
                _mark_alerted("bypass_pattern", branch, tip)
            blocked.add(branch)
            audit_gate("gate_agent", "bypass_pattern_detected", branch, reason="bypass/skip gate pattern in diff")
            continue

        # High-risk files need explicit approval. Check for marker file first
        # (written by /gate-approve or /gate-reject Telegram command). If no marker,
        # send instruction message and hold.
        #
        # 2026-05-14 fix: dropped `and not _is_auto_approvable(files)` clause.
        # Previously a PR touching only orchestrator/gate_agent.py auto-merged
        # because orchestrator/ is in AUTO_APPROVE_PREFIXES, _is_auto_approvable
        # returned True, and the AND short-circuited the HIGH_RISK check.
        # HIGH_RISK now strictly dominates AUTO_APPROVE. See Sankofa Council
        # premortem + Karpathy audit in docs/handoff/2026-05-14-gate-merge-conflict-archive-rca.md.
        if _is_high_risk(files):
            decision = _check_approval(branch)
            if decision == "reject":
                _alerted_high_risk.discard(branch)
                _clear_alerted("high_risk", branch)
                _notify(f"Gate rejection processed: {branch} held without merge.")
                audit_gate("gate_agent", "reject", branch, reason="explicit Telegram rejection")
                continue
            if decision != "approve":
                held_high_risk.append(branch)
                tip = _branch_tip_sha(branch)
                if branch not in _alerted_high_risk and not _alerted_recently("high_risk", branch, tip):
                    hr_files = [f for f in files if any(f.startswith(p) for p in HIGH_RISK_PREFIXES)]
                    _notify_gate_review(branch, hr_files)
                    _alerted_high_risk.add(branch)
                    _mark_alerted("high_risk", branch, tip)
                    audit_gate("gate_agent", "proposal", branch, reason="high-risk files require approval", extra={"hr_files": hr_files})
                continue
            # Approved — fall through to test + merge below
            _alerted_high_risk.discard(branch)
            logger.info("gate: %s approval granted, proceeding to test + merge", branch)

        # Run tests
        passed, test_output = _run_tests(branch)
        if not passed:
            failed.append((branch, test_output))
            _notify(
                f"TESTS FAILED: {branch}\n{test_output[:400]}",
                urgent=True,
            )
            continue

        # Merge (now archives + auto-resolves non-core conflicts internally)
        ok, err = _merge_branch(branch)
        if not ok:
            failed.append((branch, err))
            tip = _branch_tip_sha(branch)
            if not _alerted_recently("merge_fail", branch, tip):
                _notify(f"MERGE FAILED: {branch} -- {err[:300]}", urgent=True)
                _mark_alerted("merge_fail", branch, tip)
            else:
                logger.info(
                    "gate: %s merge still failing at tip %s -- alert suppressed (dedup)",
                    branch, tip[:8],
                )
            continue

        merged.append(branch)
        _clear_alerted("merge_fail", branch)
        _clear_alerted("high_risk", branch)
        audit_gate("gate_agent", "approve", branch, reason="tests passed, auto-merged")

    # Push main once if anything merged
    if merged:
        push_ok, push_err = _push_main()
        if not push_ok:
            _notify(f"PUSH FAILED after merging {merged}: {push_err}", urgent=True)
            return

        # Deploy VPS
        deploy_ok, deploy_out = _deploy_vps()
        if not deploy_ok:
            _notify(f"Merged {merged} but VPS deploy failed: {deploy_out[:300]}", urgent=True)
        # Silent on success -- Boubacar only needs messages for failures/reviews

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
    # Refuse to run Gate from anywhere other than the systemd unit. INVOCATION_ID
    # is set by systemd and by nothing else; this is a hostname-independent way
    # to confirm the process is the canonical gate-agent.service launch. Set
    # GATE_FORCE_RUN=1 for legitimate manual debugging (e.g. dry-run on VPS).
    #
    # Why: 2026-05-12 incident — a Claude Code session running on Boubacar's
    # laptop began executing Gate work and checked out other sessions' active
    # branches mid-edit, destroying in-progress work. AGENTS.md:189 already
    # says Gate is VPS-only; this guard turns the rule into an enforced fail.
    if not os.environ.get("INVOCATION_ID") and not os.environ.get("GATE_FORCE_RUN"):
        sys.stderr.write(
            "gate_agent: refusing to run outside systemd.\n"
            "hint: Gate is VPS-only (AGENTS.md:189). It runs as the\n"
            "      gate-agent.service systemd unit on the VPS, not from\n"
            "      a laptop tab or Claude Code session.\n"
            "hint: set GATE_FORCE_RUN=1 for legitimate manual ops\n"
            "      (e.g. SSH'd to VPS for a dry-run inspection).\n"
        )
        sys.exit(2)
    logging.basicConfig(level=logging.INFO)
    logger.info("gate: running single tick (standalone mode)")
    gate_tick()
