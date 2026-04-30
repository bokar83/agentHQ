"""Echo M1: commit proposals as the async-partnership primitive.

The agent calls propose() at logical work boundaries. A row is enqueued
with kind='commit-proposal' in the existing tasks table. A Telegram
message is sent to Boubacar with the proposal id and a one-line summary.
The agent does NOT block: it returns the proposal id and continues.

When Boubacar acks (via /ack <N> slash command, Telegram reply, or
direct ack(proposal_id) call), the staged files are committed with the
suggested message. Reject(N) drops the proposal without committing.

Reference shape: orchestrator/approval_queue.py - same pending /
approved / rejected lifecycle, same Telegram preview pattern. Echo M3
will unify the two ack queues.
"""

from __future__ import annotations

import os
import re
import socket
import subprocess
import urllib.parse
import urllib.request
import uuid
from typing import Optional

import psycopg2
import psycopg2.extras

from . import _connect, init_schema


# Marker the substrate uses to find proposals in the tasks table.
PROPOSAL_KIND = "commit-proposal"


# ---- git helpers (run from cwd unless repo_path is set) ----

def _git(args: list[str], cwd: Optional[str] = None) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    return proc.returncode, proc.stdout, proc.stderr


def _git_status_porcelain(cwd: Optional[str] = None) -> list[tuple[str, str]]:
    rc, out, _ = _git(["status", "--porcelain=v1"], cwd=cwd)
    if rc != 0:
        return []
    rows: list[tuple[str, str]] = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        rows.append((line[:2], line[3:].strip()))
    return rows


def _git_branch(cwd: Optional[str] = None) -> str:
    rc, out, _ = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
    return out.strip() if rc == 0 else "unknown"


def _git_diff_stat(cwd: Optional[str] = None, staged: bool = True) -> str:
    args = ["diff", "--stat"]
    if staged:
        args.append("--cached")
    rc, out, _ = _git(args, cwd=cwd)
    return out.strip() if rc == 0 else ""


# ---- test runner (best-effort, never blocks the proposal) ----

def _run_tests(test_cmd: Optional[str], cwd: Optional[str] = None) -> str:
    """Returns 'green' | 'red' | 'skipped' | 'unknown'. Never raises."""
    if not test_cmd:
        return "skipped"
    try:
        proc = subprocess.run(
            test_cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, check=False, timeout=300,
        )
        return "green" if proc.returncode == 0 else "red"
    except Exception:
        return "unknown"


# ---- commit-message synthesis (deterministic, no LLM round-trip) ----

def _suggest_commit_message(files: list[str], diff_stat: str, branch: str) -> str:
    """Generate a Conventional Commits style message from the file list.

    Heuristics:
    - All paths under tests/ -> 'test(<scope>): ...'
    - All paths under docs/ -> 'docs(<scope>): ...'
    - All paths under skills/<x>/ -> 'feat(<x>): ...'
    - Mixed -> 'chore: ...'
    Subject is "<scope>: <N files> updated" plus the branch name as hint.

    The author can rewrite this in /ack via a --message override later.
    """
    if not files:
        return f"chore: misc work on {branch}"

    paths = [f.replace("\\", "/") for f in files]
    all_tests = all(p.startswith("tests/") for p in paths)
    all_docs = all(p.startswith("docs/") for p in paths)
    common_skill = None
    if all(p.startswith("skills/") for p in paths):
        seg = {p.split("/", 2)[1] for p in paths if len(p.split("/")) > 2}
        if len(seg) == 1:
            common_skill = next(iter(seg))

    if all_tests:
        prefix = "test"
        scope = _scope_from_paths(paths, prefix_strip="tests/")
    elif all_docs:
        prefix = "docs"
        scope = _scope_from_paths(paths, prefix_strip="docs/")
    elif common_skill:
        prefix = "feat"
        scope = common_skill
    else:
        prefix = "chore"
        scope = ""

    subject_files = ", ".join(sorted({_short(p) for p in paths})[:3])
    if len(paths) > 3:
        subject_files += f" (+{len(paths) - 3} more)"

    head = f"{prefix}({scope}): {subject_files}" if scope else f"{prefix}: {subject_files}"
    body = f"\nBranch: {branch}\n\n{diff_stat}\n" if diff_stat else f"\nBranch: {branch}\n"
    return head + body


def _scope_from_paths(paths: list[str], prefix_strip: str) -> str:
    segs = set()
    for p in paths:
        rest = p[len(prefix_strip):] if p.startswith(prefix_strip) else p
        first = rest.split("/", 1)[0]
        first = re.sub(r"\W", "-", first)
        if first:
            segs.add(first)
    return next(iter(segs)) if len(segs) == 1 else ""


def _short(path: str) -> str:
    return path.rsplit("/", 1)[-1]


# ---- Telegram (best-effort, never raises) ----

def _telegram_send(text: str) -> Optional[int]:
    token = os.getenv("ORCHESTRATOR_TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("OWNER_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return None
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
        with urllib.request.urlopen(req, timeout=10) as resp:
            import json as _json
            body = _json.loads(resp.read())
            return body.get("result", {}).get("message_id")
    except Exception:
        return None


# ---- public API: propose / ack / reject / list_pending ----

def propose(
    repo_path: Optional[str] = None,
    test_cmd: Optional[str] = "pytest -q",
    holder: Optional[str] = None,
    extra_message: Optional[str] = None,
) -> dict:
    """Snapshot the current working tree as a commit proposal. Non-blocking.

    Returns a dict with id, files, suggested_message, tests_status, branch.
    """
    init_schema()

    cwd = repo_path or os.getcwd()
    status_rows = _git_status_porcelain(cwd)
    files = sorted({path for _, path in status_rows})
    branch = _git_branch(cwd)
    tests = _run_tests(test_cmd, cwd)
    diff_stat = _git_diff_stat(cwd, staged=True) or _git_diff_stat(cwd, staged=False)
    suggested = _suggest_commit_message(files, diff_stat, branch)
    if extra_message:
        suggested = f"{suggested}\n\n{extra_message}"

    if holder is None:
        holder = f"{socket.gethostname()}/pid={os.getpid()}/propose"

    proposal_id = uuid.uuid4().hex
    payload = {
        "files": files,
        "suggested_message": suggested,
        "tests_status": tests,
        "branch": branch,
        "repo_path": cwd,
        "diff_summary": diff_stat,
        "extra_message": extra_message,
        "proposed_by": holder,
    }

    with _connect() as c, c.cursor() as cur:
        cur.execute(
            """
            INSERT INTO tasks (id, resource, status, kind, payload)
            VALUES (%s, %s, 'queued', %s, %s)
            """,
            (
                proposal_id,
                f"proposal:{proposal_id}",
                PROPOSAL_KIND,
                psycopg2.extras.Json(payload),
            ),
        )
        c.commit()

    summary = (
        f"*Proposal* `{proposal_id[:8]}`\n"
        f"branch: `{branch}`  |  tests: *{tests}*  |  files: {len(files)}\n"
        f"```\n{suggested.splitlines()[0]}\n```\n"
        f"reply: `/ack {proposal_id[:8]}` or `/reject {proposal_id[:8]}`"
    )
    _telegram_send(summary)

    return {
        "id": proposal_id,
        "short_id": proposal_id[:8],
        "files": files,
        "suggested_message": suggested,
        "tests_status": tests,
        "branch": branch,
        "repo_path": cwd,
    }


def _resolve_id(short_or_full: str) -> Optional[dict]:
    """Look up a proposal by its full id OR its 8-char prefix. Latest pending wins."""
    with _connect() as c, c.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if len(short_or_full) >= 32:
            cur.execute(
                "SELECT * FROM tasks WHERE id = %s AND kind = %s",
                (short_or_full, PROPOSAL_KIND),
            )
        else:
            cur.execute(
                "SELECT * FROM tasks WHERE id LIKE %s AND kind = %s "
                "ORDER BY created_at DESC LIMIT 1",
                (short_or_full + "%", PROPOSAL_KIND),
            )
        row = cur.fetchone()
        return dict(row) if row else None


def ack(proposal_id: str, message_override: Optional[str] = None) -> dict:
    """Approve a proposal: stage its files and commit. Returns commit sha or error."""
    row = _resolve_id(proposal_id)
    if row is None:
        return {"ok": False, "error": f"proposal {proposal_id!r} not found"}
    if row["status"] != "queued":
        return {"ok": False, "error": f"proposal already {row['status']}"}

    payload = row["payload"]
    cwd = payload.get("repo_path") or os.getcwd()
    files = payload.get("files", [])
    msg = message_override or payload.get("suggested_message", "chore: commit")

    if not files:
        return {"ok": False, "error": "proposal has no files"}

    rc_add, _, err_add = _git(["add", "--", *files], cwd=cwd)
    if rc_add != 0:
        return {"ok": False, "error": f"git add failed: {err_add.strip()}"}

    rc_commit, out_commit, err_commit = _git(["commit", "-m", msg], cwd=cwd)
    if rc_commit != 0:
        # Pre-commit hook may have rewritten files; user must rerun.
        return {"ok": False, "error": f"git commit failed: {err_commit.strip() or out_commit.strip()}"}

    rc_sha, sha_out, _ = _git(["rev-parse", "HEAD"], cwd=cwd)
    sha = sha_out.strip() if rc_sha == 0 else None

    with _connect() as c, c.cursor() as cur:
        cur.execute(
            """
            UPDATE tasks SET status = 'done',
                             result = %s
            WHERE id = %s
            """,
            (psycopg2.extras.Json({"acked": True, "commit_sha": sha, "message": msg}), row["id"]),
        )
        c.commit()

    _telegram_send(f"acked `{row['id'][:8]}` -> commit `{(sha or '?')[:8]}`")
    return {"ok": True, "commit_sha": sha, "message": msg, "files": files}


def reject(proposal_id: str, reason: Optional[str] = None) -> dict:
    """Reject a proposal: mark failed, don't commit, no further action."""
    row = _resolve_id(proposal_id)
    if row is None:
        return {"ok": False, "error": f"proposal {proposal_id!r} not found"}
    if row["status"] != "queued":
        return {"ok": False, "error": f"proposal already {row['status']}"}

    with _connect() as c, c.cursor() as cur:
        cur.execute(
            "UPDATE tasks SET status = 'failed', error = %s WHERE id = %s",
            (reason or "rejected by human", row["id"]),
        )
        c.commit()

    _telegram_send(f"rejected `{row['id'][:8]}`" + (f": {reason}" if reason else ""))
    return {"ok": True, "id": row["id"], "reason": reason}


def list_pending(limit: int = 10) -> list[dict]:
    """Show all queued commit proposals, newest first."""
    with _connect() as c, c.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, payload, created_at FROM tasks
            WHERE kind = %s AND status = 'queued'
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (PROPOSAL_KIND, limit),
        )
        return [dict(r) for r in cur.fetchall()]
