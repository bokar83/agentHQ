"""
handlers_approvals.py - Phase 1 approval-queue handlers for Telegram.

Three public entry points, called in order by handlers.process_telegram_update:

  handle_callback_query(update)
    -> True if this was an inline-button feedback_tag tap (eats the update).

  handle_pending_feedback_tag(text, chat_id, first_word, reply_to_msg_id)
    -> True if this message was consumed as a free-text tag for the most
       recently rejected proposal within the 5-min window. Evicts stale
       windows as a side effect. Must run BEFORE normal approval logic.

  handle_approval_reply(text, chat_id, first_word, reply_to_msg_id, now_epoch)
    -> True if this was a reply-to-proposal approve/reject/edit.

  handle_naked_approval(text, chat_id, first_word, reply_to_msg_id)
    -> True if this was a naked 'yes confirm' / 'no confirm' matched against
       the latest pending proposal, OR a disambiguating 'did you mean'
       prompt after a bare approve/reject word. Respects doc-routing
       precedence (Codex PR #10 / PR #11 findings).

State shared via state._PENDING_FEEDBACK_WINDOWS. Approval-queue access via
approval_queue module. DB connections closed in try/finally in every path
per the PR #11 P2 connection-hygiene fix.
"""
import logging
import os
import time

from state import _PENDING_FEEDBACK_WINDOWS

logger = logging.getLogger("agentsHQ.handlers_approvals")

APPROVE_ALIASES = {"yes", "yep", "yeah", "approve", "approved", "confirm", "ok"}
REJECT_ALIASES = {"no", "nope", "reject", "rejected", "not approved", "discard"}

# Emoji prefixes that belong to the doc-routing handler. Used to make sure
# the 5-min tag window does not swallow an emoji command.
_DOC_EMOJI_PREFIXES = ("✅", "✏️", "🆕", "❌", "➕")


# ══════════════════════════════════════════════════════════════
# callback_query (inline-button feedback tag tap)
# ══════════════════════════════════════════════════════════════

def handle_callback_query(update: dict) -> bool:
    """
    Phase 1: callback_query (inline-button taps for rejection-feedback).
    Returns True if the update was a callback_query (handled or not - either
    way the update should not be processed further as a regular message).
    """
    if not update.get("callback_query"):
        return False
    cb = update["callback_query"]
    cb_data = cb.get("data", "")
    cb_chat_id = str(cb.get("message", {}).get("chat", {}).get("id", ""))
    cb_id = cb.get("id")
    cb_sender_id = str(cb.get("from", {}).get("id", ""))
    allowed_raw = os.environ.get("ALLOWED_USER_IDS", "")
    allowed_ids = {uid.strip() for uid in allowed_raw.split(",") if uid.strip()}
    if allowed_ids and cb_sender_id not in allowed_ids:
        return True
    if cb_data.startswith("feedback_tag:"):
        try:
            _, qid_str, tag = cb_data.split(":", 2)
            qid = int(qid_str)
            from approval_queue import set_feedback_tag
            from notifier import answer_callback_query, send_message
            if tag == "skip":
                answer_callback_query(cb_id, "Feedback skipped.")
            else:
                set_feedback_tag(qid, tag)
                answer_callback_query(cb_id, f"Tagged: {tag}")
                send_message(cb_chat_id, f"Queue #{qid}: feedback tag '{tag}' saved.")
            _PENDING_FEEDBACK_WINDOWS.pop(qid, None)
        except Exception as e:
            logger.warning(f"callback_query feedback_tag handling error: {e}")
    return True


# ══════════════════════════════════════════════════════════════
# 5-minute free-text tag window
# ══════════════════════════════════════════════════════════════

def evict_expired_windows() -> None:
    """Drop any feedback window older than 5 minutes. Caller invokes before the tag check."""
    now = time.time()
    expired = [qid for qid, (_cid, t0) in _PENDING_FEEDBACK_WINDOWS.items() if now - t0 > 300]
    for qid in expired:
        _PENDING_FEEDBACK_WINDOWS.pop(qid, None)


def handle_pending_feedback_tag(text: str, chat_id: str, first_word: str, reply_to_msg_id) -> bool:
    """
    Consume a free-text tag for the most recent rejection if a window is open.
    Must run BEFORE normal approval logic so text like 'stale' is treated as
    a tag, not as a new command. Council-fix guards: no slash, no emoji prefix,
    not an approve/reject alias, <=40 chars, not a reply.
    """
    if not _PENDING_FEEDBACK_WINDOWS or reply_to_msg_id:
        return False
    emoji_prefix = any(text.startswith(e) for e in _DOC_EMOJI_PREFIXES)
    if not (
        len(text) <= 40
        and not text.startswith("/")
        and first_word not in APPROVE_ALIASES
        and first_word not in REJECT_ALIASES
        and not emoji_prefix
    ):
        return False
    # Pick the most recently opened window (highest ts_rejected).
    qid_target = max(_PENDING_FEEDBACK_WINDOWS, key=lambda q: _PENDING_FEEDBACK_WINDOWS[q][1])
    from approval_queue import normalize_feedback_tag, set_feedback_tag
    from notifier import send_message as _send
    tag = normalize_feedback_tag(text)
    set_feedback_tag(qid_target, tag)
    _send(chat_id, f"Queue #{qid_target}: feedback tag '{tag}' saved.")
    _PENDING_FEEDBACK_WINDOWS.pop(qid_target, None)
    return True


# ══════════════════════════════════════════════════════════════
# Reply-to-message approval path
# ══════════════════════════════════════════════════════════════

def handle_approval_reply(text: str, chat_id: str, first_word: str, reply_to_msg_id, now_epoch: float) -> bool:
    """
    Reply-to-message approve/reject/edit. Opens a 5-minute feedback window
    on reject. Returns True if the message was consumed by an approval action
    (or by an 'already decided' response).
    """
    is_edit = text.lower().startswith("edit:") or text.lower().startswith("edit ")
    if not reply_to_msg_id:
        return False
    if not (first_word in APPROVE_ALIASES or first_word in REJECT_ALIASES or is_edit):
        return False

    from approval_queue import (
        find_by_telegram_msg_id,
        approve as _aq_approve,
        reject as _aq_reject,
        edit as _aq_edit,
    )
    from notifier import send_message as _send, send_message_with_buttons

    qrow = find_by_telegram_msg_id(reply_to_msg_id)
    if qrow and qrow.status == "pending":
        if is_edit:
            new_body = text.split(":", 1)[1].strip() if ":" in text else text[5:].strip()
            new_payload = dict(qrow.payload) if qrow.payload else {}
            new_payload["body"] = new_body
            _aq_edit(qrow.id, new_payload, note=None)
            _send(chat_id, f"Queue #{qrow.id}: edited.")
            return True
        if first_word in APPROVE_ALIASES:
            _aq_approve(qrow.id, note=None)
            _send(chat_id, f"Queue #{qrow.id}: approved.")
            return True
        if first_word in REJECT_ALIASES:
            _aq_reject(qrow.id, note=None)
            _send(chat_id, f"Queue #{qrow.id}: rejected. Pick a reason below (or just type one):")
            buttons = [
                [(t, f"feedback_tag:{qrow.id}:{t}") for t in ("off-voice", "wrong-hook", "stale")],
                [(t, f"feedback_tag:{qrow.id}:{t}") for t in ("too-salesy", "other", "skip")],
            ]
            send_message_with_buttons(chat_id, f"Tag for queue #{qrow.id}?", buttons)
            _PENDING_FEEDBACK_WINDOWS[qrow.id] = (chat_id, now_epoch)
            return True
    elif qrow and qrow.status != "pending":
        _send(chat_id, f"Queue #{qrow.id}: already {qrow.status}.")
        return True
    return False


# ══════════════════════════════════════════════════════════════
# Naked approval fallback (no reply target)
# ══════════════════════════════════════════════════════════════

def _doc_routing_pending() -> bool:
    """
    Check whether a doc is pending operator attention. Close the connection
    in all paths per Codex PR #11 P2. Fail-open on any error (assume not
    pending; let queue fallback handle it).
    """
    try:
        from memory import _pg_conn
        c = _pg_conn()
        try:
            cur = c.cursor()
            try:
                cur.execute("SELECT 1 FROM notebooklm_pending_docs WHERE resolved = false LIMIT 1")
                return cur.fetchone() is not None
            finally:
                cur.close()
        finally:
            try:
                c.close()
            except Exception:
                pass
    except Exception:
        return False


def handle_naked_approval(text: str, chat_id: str, first_word: str, reply_to_msg_id) -> bool:
    """
    Bare 'yes confirm' / 'no confirm' against the latest pending proposal,
    OR a 'did you mean' disambiguation after a bare approve/reject word.

    Doc-routing precedence (Codex PR #10 / PR #11):
      Defer to the doc-routing emoji handler only when the user's first word
      is an approve-like word AND a doc is pending. Reject words always hit
      the queue fallback because doc-routing does not handle them.
    """
    if reply_to_msg_id:
        return False
    if not (first_word in APPROVE_ALIASES or first_word in REJECT_ALIASES):
        return False

    is_approve_word = first_word in APPROVE_ALIASES
    skip_fallback = is_approve_word and _doc_routing_pending()
    if skip_fallback:
        # Defer to the emoji/doc-routing path. Return False so caller can try it.
        return False

    from approval_queue import find_latest_pending, approve as _aq_approve, reject as _aq_reject
    from notifier import send_message as _send

    pending = find_latest_pending(max_age_hours=2)
    if pending is None:
        # Silent when nothing is pending; let normal chat flow continue.
        return False

    text_lower_full = text.strip().lower()
    if text_lower_full == "yes confirm":
        _aq_approve(pending.id, note=None)
        _send(chat_id, f"Queue #{pending.id}: approved.")
        return True
    if text_lower_full == "no confirm":
        _aq_reject(pending.id, note=None)
        _send(chat_id, f"Queue #{pending.id}: rejected. Use /reject {pending.id} <tag> to add a reason.")
        return True
    if first_word in APPROVE_ALIASES:
        _send(chat_id, f"Did you mean queue #{pending.id} ({pending.crew_name} {pending.proposal_type})? Reply 'yes confirm' to approve.")
        return True
    if first_word in REJECT_ALIASES:
        _send(chat_id, f"Did you mean queue #{pending.id} ({pending.crew_name} {pending.proposal_type})? Reply 'no confirm' to reject.")
        return True
    return False
