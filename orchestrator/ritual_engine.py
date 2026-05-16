"""
ritual_engine.py - Saturday-ritual state machine driven by JSON configs.

A ritual is a fixed sequence of (button-pick + 1-line-rationale) steps that
ends in a single atomic git commit to docs/roadmap/<file>.md and
data/lighthouse-decisions.md with [READY] in the subject so Gate auto-merges.

State lives in postgres table `ritual_sessions`. Each (ritual_key, user_chat_id)
can have at most ONE active session at a time (uniqueness enforced via index).

Public API:
  - load_ritual_config(ritual_key) -> dict
  - ensure_table()                  -> idempotent schema bootstrap
  - start_session(ritual_key, user_chat_id) -> dict (session row)
  - get_active_session(ritual_key, user_chat_id) -> dict | None
  - record_pick(session_id, step_id, option_value, label) -> dict
  - record_rationale(session_id, text) -> dict
  - cancel_session(session_id) -> None
  - finalize_session(session_id) -> dict (paths committed + sha)
  - render_summary(session) -> str (Telegram markdown-safe)

The engine never sends Telegram messages directly. The handler layer
(handlers_ritual.py) reads engine output and posts to Telegram.

Sequence of one ritual session, per the spec:
   1. cron fires -> handler posts intro w/ [Start][Hold] buttons
   2. user taps Start -> handler calls start_session
   3. engine returns first step prompt + options
   4. user picks a button -> handler calls record_pick
   5. engine advances to "awaiting_rationale" for that step
   6. user types a free-text line -> handler calls record_rationale
   7. engine advances current_step + returns next prompt
   8. on last step done -> handler renders summary + [Confirm][Edit] buttons
   9. user Confirm -> handler calls finalize_session
  10. finalize_session writes decisions file + commits with [READY] subject
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("agentsHQ.ritual_engine")

# Repo root resolved at runtime: orchestrator/ -> ..
_HERE = Path(__file__).resolve().parent
_REPO_ROOT_ENV = os.environ.get("AGENTS_REPO_ROOT")
REPO_ROOT = Path(_REPO_ROOT_ENV).resolve() if _REPO_ROOT_ENV else _HERE.parent
RITUALS_DIR = _HERE / "rituals"


# ──────────────────────────────────────────────────────────
# Config loading
# ──────────────────────────────────────────────────────────

def load_ritual_config(ritual_key: str) -> dict:
    """Load and validate a ritual JSON config.

    Raises FileNotFoundError if the file is missing, ValueError on schema
    violations so the cron entry surfaces config breakage immediately.
    """
    path = RITUALS_DIR / f"{ritual_key}.json"
    if not path.exists():
        raise FileNotFoundError(f"ritual config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    _validate_config(cfg)
    return cfg


def _validate_config(cfg: dict) -> None:
    required = ("ritual_key", "title", "intro", "output_file",
                "commit_subject_template", "steps")
    for k in required:
        if k not in cfg:
            raise ValueError(f"ritual config missing required key: {k}")
    if not isinstance(cfg["steps"], list) or not cfg["steps"]:
        raise ValueError("ritual config 'steps' must be a non-empty list")
    seen_ids = set()
    for i, step in enumerate(cfg["steps"]):
        if "id" not in step or "prompt" not in step or "options" not in step:
            raise ValueError(f"step {i} missing id/prompt/options")
        if step["id"] in seen_ids:
            raise ValueError(f"duplicate step id: {step['id']}")
        seen_ids.add(step["id"])
        if not isinstance(step["options"], list) or not step["options"]:
            raise ValueError(f"step {step['id']} options empty")
        for opt in step["options"]:
            if not (isinstance(opt, (list, tuple)) and len(opt) == 2):
                raise ValueError(
                    f"step {step['id']} option must be [label, value]: {opt}"
                )
    if "[READY]" not in cfg["commit_subject_template"]:
        raise ValueError("commit_subject_template must contain [READY]")


# ──────────────────────────────────────────────────────────
# Postgres schema + helpers
# ──────────────────────────────────────────────────────────

CREATE_RITUAL_SESSIONS = """
CREATE TABLE IF NOT EXISTS ritual_sessions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ritual_key    TEXT NOT NULL,
    user_chat_id  TEXT NOT NULL,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at  TIMESTAMPTZ,
    current_step  INTEGER NOT NULL DEFAULT 0,
    awaiting      TEXT NOT NULL DEFAULT 'pick',
    payload       JSONB NOT NULL DEFAULT '{}'::jsonb,
    status        TEXT NOT NULL DEFAULT 'active'
);

CREATE UNIQUE INDEX IF NOT EXISTS ritual_sessions_one_active
    ON ritual_sessions (ritual_key, user_chat_id)
    WHERE status = 'active';

CREATE INDEX IF NOT EXISTS ritual_sessions_lookup
    ON ritual_sessions (ritual_key, user_chat_id, status);
"""


def _conn():
    """Lazy psycopg2 connection - imports here so tests can monkeypatch."""
    from db import get_local_connection
    return get_local_connection()


def ensure_table() -> None:
    """Idempotent table creation. Safe to call on every app start."""
    try:
        conn = _conn()
        try:
            cur = conn.cursor()
            cur.execute(CREATE_RITUAL_SESSIONS)
            conn.commit()
            cur.close()
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"ensure_table(ritual_sessions) failed (non-fatal): {e}")


# ──────────────────────────────────────────────────────────
# Session lifecycle
# ──────────────────────────────────────────────────────────

def start_session(ritual_key: str, user_chat_id: str) -> dict:
    """Create a new active session (or return existing active one if user retries)."""
    cfg = load_ritual_config(ritual_key)
    existing = get_active_session(ritual_key, user_chat_id)
    if existing:
        return existing
    payload = {
        "config_snapshot": {
            "title": cfg["title"],
            "n_steps": len(cfg["steps"]),
            "version": cfg.get("version", "v1"),
        },
        "answers": {},  # step_id -> {pick_value, pick_label, rationale}
    }
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO ritual_sessions
                 (ritual_key, user_chat_id, current_step, awaiting, payload, status)
               VALUES (%s, %s, 0, 'pick', %s::jsonb, 'active')
               RETURNING id, ritual_key, user_chat_id, current_step,
                         awaiting, payload, status, started_at""",
            (ritual_key, user_chat_id, json.dumps(payload)),
        )
        row = dict(cur.fetchone())
        conn.commit()
        cur.close()
        return row
    finally:
        conn.close()


def get_active_session(ritual_key: str, user_chat_id: str) -> Optional[dict]:
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, ritual_key, user_chat_id, current_step, awaiting,
                      payload, status, started_at
                 FROM ritual_sessions
                WHERE ritual_key = %s AND user_chat_id = %s AND status = 'active'
                LIMIT 1""",
            (ritual_key, user_chat_id),
        )
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None
    finally:
        conn.close()


def get_session(session_id: str) -> Optional[dict]:
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, ritual_key, user_chat_id, current_step, awaiting,
                      payload, status, started_at, completed_at
                 FROM ritual_sessions WHERE id = %s""",
            (str(session_id),),
        )
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None
    finally:
        conn.close()


def cancel_session(session_id: str) -> None:
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE ritual_sessions SET status='cancelled', completed_at=now() WHERE id=%s",
            (str(session_id),),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────
# Step machinery
# ──────────────────────────────────────────────────────────

class RitualError(ValueError):
    """Raised when the caller violates the state machine (wrong step, bad pick)."""


def current_step_dict(session: dict, cfg: Optional[dict] = None) -> Optional[dict]:
    """Return the step dict for session['current_step'], or None if past end."""
    cfg = cfg or load_ritual_config(session["ritual_key"])
    idx = session["current_step"]
    if idx >= len(cfg["steps"]):
        return None
    return cfg["steps"][idx]


def record_pick(session_id: str, option_value: str) -> dict:
    """Persist a button pick for the current step. Advances awaiting -> 'rationale'."""
    sess = get_session(session_id)
    if not sess or sess["status"] != "active":
        raise RitualError(f"session {session_id} not active")
    if sess["awaiting"] != "pick":
        raise RitualError(f"session awaiting={sess['awaiting']}, not pick")
    cfg = load_ritual_config(sess["ritual_key"])
    step = current_step_dict(sess, cfg)
    if step is None:
        raise RitualError("session already past last step")
    valid = {opt[1]: opt[0] for opt in step["options"]}
    if option_value not in valid:
        raise RitualError(f"invalid option_value '{option_value}' for step {step['id']}")
    payload = sess["payload"] or {}
    payload.setdefault("answers", {})
    payload["answers"][step["id"]] = {
        "pick_value": option_value,
        "pick_label": valid[option_value],
        "rationale": None,
    }
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """UPDATE ritual_sessions
                  SET awaiting='rationale', payload=%s::jsonb
                WHERE id=%s
              RETURNING id, ritual_key, user_chat_id, current_step,
                        awaiting, payload, status, started_at""",
            (json.dumps(payload), str(session_id)),
        )
        row = dict(cur.fetchone())
        conn.commit()
        cur.close()
        return row
    finally:
        conn.close()


def record_rationale(session_id: str, text: str) -> dict:
    """Persist a 1-line rationale. Advances current_step + sets awaiting='pick'.

    If this was the last step, awaiting moves to 'confirm' and current_step
    stays at len(steps) - 1 (no out-of-range index).
    """
    sess = get_session(session_id)
    if not sess or sess["status"] != "active":
        raise RitualError(f"session {session_id} not active")
    if sess["awaiting"] != "rationale":
        raise RitualError(f"session awaiting={sess['awaiting']}, not rationale")
    text = (text or "").strip()
    if not text:
        raise RitualError("rationale text empty")
    # cap length to one chat line so summary stays readable
    if len(text) > 500:
        text = text[:500] + "..."
    cfg = load_ritual_config(sess["ritual_key"])
    step = current_step_dict(sess, cfg)
    payload = sess["payload"] or {}
    answers = payload.setdefault("answers", {})
    ans = answers.get(step["id"])
    if not ans:
        raise RitualError(f"no pick recorded for step {step['id']}")
    ans["rationale"] = text

    next_idx = sess["current_step"] + 1
    if next_idx >= len(cfg["steps"]):
        new_awaiting = "confirm"
        new_step = sess["current_step"]  # park at last
    else:
        new_awaiting = "pick"
        new_step = next_idx

    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """UPDATE ritual_sessions
                  SET current_step=%s, awaiting=%s, payload=%s::jsonb
                WHERE id=%s
              RETURNING id, ritual_key, user_chat_id, current_step,
                        awaiting, payload, status, started_at""",
            (new_step, new_awaiting, json.dumps(payload), str(session_id)),
        )
        row = dict(cur.fetchone())
        conn.commit()
        cur.close()
        return row
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────
# Rendering
# ──────────────────────────────────────────────────────────

def render_step_prompt(session: dict, cfg: Optional[dict] = None) -> dict:
    """Return {text, buttons} for the current step. Caller posts to Telegram."""
    cfg = cfg or load_ritual_config(session["ritual_key"])
    step = current_step_dict(session, cfg)
    if step is None:
        return {"text": "(ritual complete)", "buttons": []}
    buttons = [
        [(label, f"ritual_pick:{session['id']}:{value}")
         for (label, value) in step["options"]]
    ]
    cancel_row = [("Cancel ritual", f"ritual_cancel:{session['id']}")]
    buttons.append(cancel_row)
    return {"text": step["prompt"], "buttons": buttons}


def render_rationale_prompt(session: dict, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or load_ritual_config(session["ritual_key"])
    step = current_step_dict(session, cfg)
    pick_label = ((session.get("payload") or {}).get("answers", {})
                  .get(step["id"], {}).get("pick_label", "?"))
    return {
        "text": (
            f"Picked: {pick_label}\n\n"
            f"Now send 1 line rationale (or 'skip' to leave blank)."
        ),
        "buttons": [[("Cancel ritual", f"ritual_cancel:{session['id']}")]],
    }


def render_summary(session: dict, cfg: Optional[dict] = None) -> dict:
    """Final summary card for [Confirm][Edit] step."""
    cfg = cfg or load_ritual_config(session["ritual_key"])
    payload = session.get("payload") or {}
    answers = payload.get("answers", {})
    lines = [f"*{cfg['title']} - summary*"]
    for i, step in enumerate(cfg["steps"], start=1):
        ans = answers.get(step["id"], {})
        label = ans.get("pick_label", "(no pick)")
        rat = ans.get("rationale") or "(no rationale)"
        # Strip newlines so the summary stays compact in Telegram
        rat_oneline = " ".join(rat.split())
        lines.append(f"{i}. {step['id']}: {label} - {rat_oneline}")
    lines.append("")
    lines.append("Tap Confirm & Commit to push, or Edit to restart.")
    buttons = [
        [("Confirm & Commit", f"ritual_confirm:{session['id']}")],
        [("Edit (restart)", f"ritual_edit:{session['id']}")],
        [("Cancel", f"ritual_cancel:{session['id']}")],
    ]
    return {"text": "\n".join(lines), "buttons": buttons}


# ──────────────────────────────────────────────────────────
# Finalisation - write file + git commit
# ──────────────────────────────────────────────────────────

def _build_decisions_markdown(session: dict, cfg: dict) -> str:
    """Build the markdown block appended to data/lighthouse-decisions.md."""
    payload = session.get("payload") or {}
    answers = payload.get("answers", {})
    date_str = _dt.datetime.utcnow().strftime("%Y-%m-%d")
    lines = [
        "",
        f"## {cfg['title']} - {date_str}",
        "",
        f"_Session id: `{session['id']}`. Captured via orchestrator-bot ritual dispatcher._",
        "",
    ]
    for i, step in enumerate(cfg["steps"], start=1):
        ans = answers.get(step["id"], {})
        label = ans.get("pick_label", "(no pick)")
        rat = ans.get("rationale") or "(no rationale)"
        lines.append(f"**{i}. {step['id']}** - {label}")
        lines.append(f"  - rationale: {rat}")
        lines.append("")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _run_git(args: list[str], cwd: Path) -> str:
    """Run a git subprocess, return stdout, raise on non-zero exit."""
    full = ["git"] + args
    res = subprocess.run(
        full, cwd=str(cwd), capture_output=True, text=True, timeout=60,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed (rc={res.returncode}): {res.stderr.strip()}"
        )
    return res.stdout.strip()


def finalize_session(session_id: str,
                     repo_root: Optional[Path] = None,
                     dry_run: bool = False) -> dict:
    """Atomic write + git commit. Returns {paths, sha, branch, commit_subject}.

    On VPS / production: dry_run=False, runs real git.
    Tests: dry_run=True, skips git but returns the rendered file content.
    """
    sess = get_session(session_id)
    if not sess:
        raise RitualError(f"session {session_id} not found")
    if sess["status"] != "active":
        raise RitualError(f"session {session_id} status={sess['status']}, expected active")
    if sess["awaiting"] != "confirm":
        raise RitualError(f"session {session_id} awaiting={sess['awaiting']}, expected confirm")

    cfg = load_ritual_config(sess["ritual_key"])
    root = (repo_root or REPO_ROOT).resolve()
    decisions_path = root / cfg["output_file"]
    decisions_path.parent.mkdir(parents=True, exist_ok=True)

    block = _build_decisions_markdown(sess, cfg)
    if decisions_path.exists():
        existing = decisions_path.read_text(encoding="utf-8")
    else:
        existing = "# Lighthouse decisions ledger\n\n_Auto-appended by orchestrator-bot ritual dispatcher._\n"
    new_content = existing.rstrip() + "\n" + block
    decisions_path.write_text(new_content, encoding="utf-8")

    date_str = _dt.datetime.utcnow().strftime("%Y-%m-%d")
    # Week number is best-effort; ritual configs that don't use {week} just ignore.
    iso_week = _dt.datetime.utcnow().isocalendar().week
    subject = cfg["commit_subject_template"].format(date=date_str, week=iso_week)
    body = cfg["commit_body_template"].format(
        ritual_key=sess["ritual_key"],
        date=date_str,
        user_chat_id=sess["user_chat_id"],
    )
    commit_msg = f"{subject}\n\n{body}"

    if not subject.rstrip().endswith("[READY]"):
        raise RitualError("commit subject missing [READY]; refusing to commit")

    result = {
        "paths": [str(decisions_path)],
        "commit_subject": subject,
        "commit_body": body,
        "dry_run": dry_run,
    }
    if dry_run:
        # Mark complete so unit tests can assert the lifecycle terminus.
        _mark_completed(session_id)
        return result

    # Real git path. Atomic chain.
    rel = decisions_path.relative_to(root).as_posix()
    _run_git(["add", rel], cwd=root)
    # Skip session-log pre-commit hook for this file (not a roadmap edit).
    env_skip = os.environ.copy()
    env_skip.setdefault("SKIP_SESSION_LOG", "1")
    full = ["git", "commit", "-m", commit_msg]
    res = subprocess.run(
        full, cwd=str(root), capture_output=True, text=True, env=env_skip, timeout=60,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"git commit failed (rc={res.returncode}): {res.stderr.strip()}"
        )
    sha = _run_git(["rev-parse", "HEAD"], cwd=root)
    branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    # Push so Gate sees [READY] within 5min.
    try:
        _run_git(["push", "origin", branch], cwd=root)
    except Exception as e:
        logger.warning(f"git push origin {branch} failed (will retry on next session): {e}")

    _mark_completed(session_id)
    result["sha"] = sha
    result["branch"] = branch
    return result


def _mark_completed(session_id: str) -> None:
    try:
        conn = _conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE ritual_sessions SET status='completed', completed_at=now() WHERE id=%s",
                (str(session_id),),
            )
            conn.commit()
            cur.close()
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"mark completed failed for {session_id}: {e}")


# ──────────────────────────────────────────────────────────
# Cron entrypoint - the cron job calls THIS, not curl directly
# ──────────────────────────────────────────────────────────

def cron_dispatch(ritual_key: str, user_chat_id: Optional[str] = None) -> dict:
    """Cron entry: post intro w/ [Start][Hold] to user_chat_id.

    Pure-python; uses notifier so the existing httpx client is reused.
    """
    user_chat_id = user_chat_id or os.environ.get("OWNER_TELEGRAM_CHAT_ID", "")
    if not user_chat_id:
        raise RuntimeError("OWNER_TELEGRAM_CHAT_ID not set; cannot cron-dispatch")
    cfg = load_ritual_config(ritual_key)
    text = (
        f"*{cfg['title']}*\n"
        f"Cadence: {cfg.get('cadence', '?')}\n\n"
        f"{cfg['intro']}\n\n"
        f"Ready to start now?"
    )
    buttons = [
        [("Start now", f"ritual_start:{ritual_key}")],
        [("Hold (defer)", f"ritual_hold:{ritual_key}")],
    ]
    from notifier import send_message_with_buttons
    msg_id = send_message_with_buttons(user_chat_id, text, buttons)
    return {"chat_id": user_chat_id, "message_id": msg_id, "ritual_key": ritual_key}
