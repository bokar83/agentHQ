#!/usr/bin/env python3
"""
gate_poll.py — dumb Python cron for Atlas Gate context-burn fix (item 6)

Runs on VPS host (not in container). Polls GitHub every N seconds for
feature branches with [READY] commits. Fires Telegram when found.
Zero LLM context opened on empty-queue ticks.

LLM gate review (gate_agent.py inside container) only fires when this
script detects at least one READY branch.

Usage:
    python scripts/gate_poll.py [--interval 300] [--once] [--dry-run]

Environment (loaded from .env or system env):
    ORCHESTRATOR_TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID  (or OWNER_TELEGRAM_CHAT_ID)
    REPO_ROOT         (default: parent dir of this script)
    GITHUB_TOKEN      (optional: for authenticated GitHub API calls)

Deployment (VPS host cron, every 5 min):
    */5 * * * * cd /root/agentsHQ && python scripts/gate_poll.py --once >> /tmp/gate_poll.log 2>&1
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

SKILL_EVAL_SCRIPT = Path(__file__).resolve().parent / "skill_eval.py"
SKILL_EVAL_THRESHOLD = 0.8

REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).resolve().parents[1]))
ENV_FILE = REPO_ROOT / ".env"
MAIN_BRANCH = "main"

PROTECTED_BRANCHES = {
    "main",
    "feature/coordination-layer",
    "feature/echo-m1",
    "fix/chat-empty-model-resolution",
}
SKIP_PREFIXES = ("archive/",)
READY_BRANCHES_PREFIXES = ("feature/", "feat/", "fix/")


def _load_env() -> None:
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def _git(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout.strip()


def _fetch() -> bool:
    rc, _ = _git(["fetch", "--prune", "origin"])
    return rc == 0


def _ready_branches() -> list[str]:
    rc, out = _git(["branch", "-r", "--no-merged", f"origin/{MAIN_BRANCH}"])
    if rc != 0:
        return []
    ready = []
    for line in out.splitlines():
        branch = line.strip().lstrip("* ").removeprefix("origin/")
        if branch in PROTECTED_BRANCHES:
            continue
        if any(branch.startswith(p) for p in SKIP_PREFIXES):
            continue
        if not any(branch.startswith(p) for p in READY_BRANCHES_PREFIXES):
            continue
        rc2, msg = _git(["log", "-1", "--format=%s", f"origin/{branch}"])
        if rc2 == 0 and "[READY]" in msg:
            ready.append(branch)
    return ready


def _notify(bot_token: str, chat_id: str, text: str) -> None:
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as exc:
        print(f"[gate_poll] notify failed: {exc}", file=sys.stderr)


def _changed_skills(branch: str) -> list[Path]:
    """Return skill dirs modified in branch vs main that have a routing eval file."""
    rc, out = _git(["diff", "--name-only", f"origin/{MAIN_BRANCH}...origin/{branch}"])
    if rc != 0:
        return []
    skills_root = REPO_ROOT / "skills"
    seen: set[str] = set()
    result: list[Path] = []
    eval_filename = "routing-eval.jsonl"
    for path_str in out.splitlines():
        parts = Path(path_str).parts
        if len(parts) >= 2 and parts[0] == "skills":
            skill_name = parts[1]
            if skill_name in seen:
                continue
            seen.add(skill_name)
            skill_dir = skills_root / skill_name
            if (skill_dir / eval_filename).exists():
                result.append(skill_dir)
    return result


def _run_skill_eval(skill_dir: Path) -> tuple[bool, str]:
    """Run skill_eval.py on a skill dir. Returns (passed, summary_line)."""
    proc = subprocess.run(
        [sys.executable, str(SKILL_EVAL_SCRIPT), str(skill_dir),
         "--threshold", str(SKILL_EVAL_THRESHOLD)],
        capture_output=True,
        text=True,
        check=False,
    )
    output = proc.stdout.strip() or proc.stderr.strip()
    summary = output.splitlines()[0] if output else "no output"
    # exit 2 = no eval file — treat as warn, not block
    passed = proc.returncode in (0, 2)
    return passed, summary


def poll_once(bot_token: str, chat_id: str, dry_run: bool = False) -> list[str]:
    if not _fetch():
        print("[gate_poll] git fetch failed", file=sys.stderr)
        return []

    ready = _ready_branches()
    if not ready:
        print("[gate_poll] queue empty — no READY branches")
        return []

    for branch in ready:
        # Run skill quality check on any modified skills before LLM gate review
        skill_dirs = _changed_skills(branch)
        failures: list[str] = []
        for skill_dir in skill_dirs:
            passed, summary = _run_skill_eval(skill_dir)
            print(f"[gate_poll] skill_check {skill_dir.name}: {summary}")
            if not passed:
                failures.append(f"{skill_dir.name}: {summary}")

        if failures:
            fail_detail = "\n".join(failures)
            msg = (f"GATE: skill quality check FAILED — auto-reject\n"
                   f"Branch: {branch}\n"
                   f"Failures:\n{fail_detail}\n"
                   f"Fix routing regressions before re-pushing.")
            print(f"[gate_poll] {msg}")
            if not dry_run and bot_token and chat_id:
                _notify(bot_token, chat_id, msg)
            continue

        msg = f"GATE: READY branch detected\nBranch: {branch}\nGate review starting in container."
        print(f"[gate_poll] {msg}")
        if not dry_run and bot_token and chat_id:
            _notify(bot_token, chat_id, msg)

    return ready


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate poll — dumb cron, zero LLM on empty queue")
    parser.add_argument("--interval", type=int, default=300, help="Poll interval in seconds (default 300)")
    parser.add_argument("--once", action="store_true", help="Poll once and exit (for cron use)")
    parser.add_argument("--dry-run", action="store_true", help="Detect but don't notify")
    args = parser.parse_args()

    _load_env()
    bot_token = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("OWNER_TELEGRAM_CHAT_ID", "")

    if not bot_token or not chat_id:
        print("[gate_poll] WARN: Telegram not configured — will detect but not notify", file=sys.stderr)

    if args.once:
        ready = poll_once(bot_token, chat_id, dry_run=args.dry_run)
        return 0

    print(f"[gate_poll] starting loop, interval={args.interval}s")
    while True:
        try:
            poll_once(bot_token, chat_id, dry_run=args.dry_run)
        except Exception as exc:
            print(f"[gate_poll] tick error: {exc}", file=sys.stderr)
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
