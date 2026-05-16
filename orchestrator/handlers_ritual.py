"""
handlers_ritual.py - Telegram callback + message dispatch for the ritual engine.

Two entry points called from orchestrator/handlers.py:
  - handle_ritual_callback(update) -> bool
        Routes inline-keyboard taps starting with "ritual_*".
  - handle_ritual_rationale(text, chat_id, sender_id) -> bool
        Routes free-text rationale replies when a ritual session is awaiting one.

The dispatcher does NOT poll Telegram on its own; the orchestrator already
runs telegram_polling_loop in handlers.py. We simply hook into the existing
update-processing chain via callback prefix match.

Callback data conventions:
  ritual_start:<ritual_key>          (intro -> Start now)
  ritual_hold:<ritual_key>           (intro -> Hold)
  ritual_pick:<session_id>:<value>   (per-step button pick)
  ritual_confirm:<session_id>        (summary -> Confirm & Commit)
  ritual_edit:<session_id>           (summary -> Edit, cancel + restart)
  ritual_cancel:<session_id>         (any step -> Cancel ritual)

All callbacks ALWAYS call answer_callback_query so the Telegram spinner clears.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import ritual_engine as _ritual

logger = logging.getLogger("agentsHQ.handlers_ritual")

_PICK_PREFIXES = (
    "ritual_start:",
    "ritual_hold:",
    "ritual_pick:",
    "ritual_confirm:",
    "ritual_edit:",
    "ritual_cancel:",
)


# ──────────────────────────────────────────────────────────
# Callback router
# ──────────────────────────────────────────────────────────

def _send_step(session: dict) -> None:
    from notifier import send_message_with_buttons
    msg = _ritual.render_step_prompt(session)
    send_message_with_buttons(session["user_chat_id"], msg["text"], msg["buttons"])


def _send_rationale_prompt(session: dict) -> None:
    from notifier import send_message_with_buttons
    msg = _ritual.render_rationale_prompt(session)
    send_message_with_buttons(session["user_chat_id"], msg["text"], msg["buttons"])


def _send_summary(session: dict) -> None:
    from notifier import send_message_with_buttons
    msg = _ritual.render_summary(session)
    send_message_with_buttons(session["user_chat_id"], msg["text"], msg["buttons"])


def handle_ritual_callback(update: dict) -> bool:
    """Return True if this was a ritual_* callback (handled or not)."""
    cb = update.get("callback_query")
    if not cb:
        return False
    data = cb.get("data", "") or ""
    if not data.startswith(_PICK_PREFIXES):
        return False

    cb_id = cb.get("id")
    chat_id = str(cb.get("message", {}).get("chat", {}).get("id", ""))
    sender_id = str(cb.get("from", {}).get("id", ""))

    allowed_raw = os.environ.get("ALLOWED_USER_IDS", "")
    allowed_ids = {uid.strip() for uid in allowed_raw.split(",") if uid.strip()}
    if allowed_ids and sender_id not in allowed_ids:
        from notifier import answer_callback_query
        answer_callback_query(cb_id, "Not authorised.")
        return True

    from notifier import answer_callback_query, send_message
    try:
        if data.startswith("ritual_start:"):
            ritual_key = data.split(":", 1)[1]
            sess = _ritual.start_session(ritual_key, chat_id)
            answer_callback_query(cb_id, "Starting ritual...")
            _send_step(sess)
            return True

        if data.startswith("ritual_hold:"):
            ritual_key = data.split(":", 1)[1]
            answer_callback_query(cb_id, "Held. I will not re-fire this week.")
            send_message(chat_id, f"Ritual `{ritual_key}` held for this cadence.")
            return True

        if data.startswith("ritual_pick:"):
            _, session_id, value = data.split(":", 2)
            sess = _ritual.record_pick(session_id, value)
            answer_callback_query(cb_id, "Pick recorded.")
            _send_rationale_prompt(sess)
            return True

        if data.startswith("ritual_confirm:"):
            session_id = data.split(":", 1)[1]
            sess = _ritual.get_session(session_id)
            if not sess or sess["awaiting"] != "confirm":
                answer_callback_query(cb_id, "Not at confirm step.")
                return True
            answer_callback_query(cb_id, "Committing...")
            try:
                result = _ritual.finalize_session(session_id)
                msg = (
                    "Ritual committed.\n"
                    f"Branch: {result.get('branch', '?')}\n"
                    f"SHA: {result.get('sha', '?')[:12]}\n"
                    f"Subject: {result.get('commit_subject', '?')}\n\n"
                    "Gate will auto-merge within 5 min."
                )
            except Exception as e:
                logger.error(f"finalize_session failed: {e}", exc_info=True)
                msg = f"Commit failed: {e}. Session left active; reply 'cancel' to drop it."
            send_message(chat_id, msg)
            return True

        if data.startswith("ritual_edit:"):
            session_id = data.split(":", 1)[1]
            sess = _ritual.get_session(session_id)
            if sess:
                ritual_key = sess["ritual_key"]
                _ritual.cancel_session(session_id)
                new_sess = _ritual.start_session(ritual_key, chat_id)
                answer_callback_query(cb_id, "Restarted from step 1.")
                _send_step(new_sess)
            else:
                answer_callback_query(cb_id, "Session not found.")
            return True

        if data.startswith("ritual_cancel:"):
            session_id = data.split(":", 1)[1]
            _ritual.cancel_session(session_id)
            answer_callback_query(cb_id, "Cancelled.")
            send_message(chat_id, "Ritual cancelled. Next cron will re-prompt.")
            return True

    except _ritual.RitualError as e:
        answer_callback_query(cb_id, f"Step error: {e}")
        return True
    except Exception as e:
        logger.error(f"ritual callback {data} failed: {e}", exc_info=True)
        answer_callback_query(cb_id, "Internal error; check logs.")
        return True

    return False


# ──────────────────────────────────────────────────────────
# Free-text rationale router (runs from process_telegram_update)
# ──────────────────────────────────────────────────────────

def handle_ritual_rationale(text: str, chat_id: str, sender_id: str) -> bool:
    """Return True if there is an active rationale-awaiting session for chat_id."""
    if not text or not chat_id:
        return False
    # Look across all rituals to find the one awaiting a rationale on this chat.
    # Cheap because the index is (ritual_key, user_chat_id, status).
    from db import get_local_connection
    try:
        conn = get_local_connection()
    except Exception as e:
        logger.warning(f"handle_ritual_rationale: db connect failed: {e}")
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, ritual_key, awaiting
                 FROM ritual_sessions
                WHERE user_chat_id=%s AND status='active' AND awaiting='rationale'
                LIMIT 1""",
            (chat_id,),
        )
        row = cur.fetchone()
        cur.close()
    finally:
        conn.close()
    if not row:
        return False

    allowed_raw = os.environ.get("ALLOWED_USER_IDS", "")
    allowed_ids = {uid.strip() for uid in allowed_raw.split(",") if uid.strip()}
    if allowed_ids and sender_id not in allowed_ids:
        return False  # silent - let normal auth path handle it

    from notifier import send_message
    rationale = "(no rationale)" if text.strip().lower() == "skip" else text
    try:
        sess = _ritual.record_rationale(str(row["id"]), rationale)
    except _ritual.RitualError as e:
        send_message(chat_id, f"Rationale rejected: {e}")
        return True
    if sess["awaiting"] == "confirm":
        _send_summary(sess)
    else:
        _send_step(sess)
    return True


# ──────────────────────────────────────────────────────────
# Startup hook
# ──────────────────────────────────────────────────────────

def ensure_startup() -> None:
    """Called from app.py startup_event. Idempotent table bootstrap."""
    _ritual.ensure_table()
