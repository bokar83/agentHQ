"""Echo M1 Stop-hook nag.

Runs at the end of every Claude Code turn. If the turn left uncommitted
work AND no /propose was filed in the last 60s on this branch, fire a
single Telegram nag. Never blocks the user. Never raises. Always exits 0.

Heuristics (in order):
1. If not in a git repo, silent exit.
2. If working tree clean, silent exit.
3. If diff is trivial (< 6 lines), silent exit.
4. If a commit-proposal row was inserted on this branch in the last 60s
   and is still status='queued', silent exit (agent did propose).
5. Else send one Telegram nag.

Performance: targets under 800ms wall-clock. Cheap git calls, one
Postgres query, urllib Telegram. No model calls.
"""

from __future__ import annotations

import os
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# Trivial-change threshold: nag does NOT fire below this many changed lines.
TRIVIAL_LINE_THRESHOLD = 6

# How recent a /propose row counts as "the agent already proposed this turn."
RECENT_PROPOSE_SECONDS = 60


def _git(args, cwd):
    try:
        proc = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True,
            check=False, timeout=5,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except Exception:
        return 1, "", ""


def _is_git_repo(cwd: str) -> bool:
    rc, _, _ = _git(["rev-parse", "--git-dir"], cwd)
    return rc == 0


def _branch(cwd: str) -> str:
    rc, out, _ = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    return out.strip() if rc == 0 else "unknown"


def _changed_lines(cwd: str) -> int:
    """Count total lines changed in working tree (staged + unstaged)."""
    total = 0
    for args in (["diff", "--numstat"], ["diff", "--numstat", "--cached"]):
        rc, out, _ = _git(args, cwd)
        if rc != 0:
            continue
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            try:
                added = int(parts[0]) if parts[0] != "-" else 0
                removed = int(parts[1]) if parts[1] != "-" else 0
                total += added + removed
            except ValueError:
                continue
    return total


def _file_count(cwd: str) -> int:
    rc, out, _ = _git(["status", "--porcelain=v1"], cwd)
    if rc != 0:
        return 0
    return sum(1 for line in out.splitlines() if line.strip())


def _recent_proposal_exists(branch: str) -> bool:
    """Was a commit-proposal filed for this branch in the last RECENT_PROPOSE_SECONDS seconds?"""
    try:
        import psycopg2
    except ImportError:
        return False  # If psycopg2 missing, default to firing the nag (fail-open)
    try:
        host = os.environ.get("POSTGRES_HOST") or "127.0.0.1"
        user = os.environ.get("POSTGRES_USER") or "postgres"
        pw = os.environ.get("POSTGRES_PASSWORD") or ""
        db = os.environ.get("POSTGRES_DB") or "postgres"
        conn = psycopg2.connect(
            host=host, user=user, password=pw, dbname=db, connect_timeout=2,
        )
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1 FROM tasks
                WHERE kind = 'commit-proposal'
                  AND status IN ('queued', 'done')
                  AND payload->>'branch' = %s
                  AND created_at > now() - make_interval(secs => %s)
                LIMIT 1
                """,
                (branch, RECENT_PROPOSE_SECONDS),
            )
            return cur.fetchone() is not None
        finally:
            conn.close()
    except Exception:
        return False  # If query fails, default to firing nag


def _telegram_send(text: str) -> None:
    token = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    try:
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": text[:4000],
            "parse_mode": "Markdown",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data, method="POST",
        )
        urllib.request.urlopen(req, timeout=5).read()
    except Exception:
        pass


def _load_dotenv(repo_root: str) -> None:
    """Best-effort .env load so this works from a fresh shell with no env."""
    env_path = Path(repo_root) / ".env"
    if not env_path.exists():
        # Fall back to main checkout's .env (worktrees share it)
        env_path = Path("D:/Ai_Sandbox/agentsHQ/.env")
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v
    except Exception:
        pass


def main() -> int:
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    if not _is_git_repo(cwd):
        return 0

    files = _file_count(cwd)
    if files == 0:
        return 0  # Clean tree, nothing to nag about.

    lines = _changed_lines(cwd)
    if lines < TRIVIAL_LINE_THRESHOLD:
        return 0  # Trivial change, exempt per CLAUDE.md.

    branch = _branch(cwd)

    _load_dotenv(cwd)

    if _recent_proposal_exists(branch):
        return 0  # Agent already proposed this turn.

    msg = (
        f"Echo nag: turn ended with uncommitted work on `{branch}`.\n"
        f"Files: {files}, lines changed: {lines}.\n"
        f"No `/propose` filed in the last {RECENT_PROPOSE_SECONDS}s.\n"
        f"Run `/propose` or `/list-proposals` to check."
    )
    _telegram_send(msg)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # Hooks must never block agent.
