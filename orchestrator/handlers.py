"""
handlers.py - Telegram update orchestrator + polling loop.

Thin dispatcher. All the real work lives in:
  - handlers_approvals.py  (callback_query, reply approvals, feedback windows)
  - handlers_commands.py   (15 slash commands)
  - handlers_doc.py        (doc-routing emoji handlers)
  - handlers_chat.py       (run_chat + praise/critique)
  - worker.py              (_run_background_job)

Dispatch order in process_telegram_update is load-bearing. Reordering any of
steps 1-9 risks regressing the PR #10/#11/#13 feedback-window precedence rules.

The polling loop uses 3-attempt deleteWebhook retry, 401 -> stop,
allowed_updates includes callback_query.
"""
import asyncio
import logging
import os
import time
import uuid

import httpx

from handlers_approvals import (
    handle_callback_query,
    evict_expired_windows,
    handle_pending_feedback_tag,
    handle_newsletter_editorial_reply,
    handle_approval_reply,
    handle_publish_reply,
    handle_naked_approval,
    APPROVE_ALIASES,
    REJECT_ALIASES,
)
from handlers_chat import run_chat, run_chat_with_buttons, handle_feedback
from handlers_commands import dispatch_command
from handlers_doc import handle_doc_emoji
from state import _active_project

logger = logging.getLogger("agentsHQ.handlers")


# ══════════════════════════════════════════════════════════════
# Classifiers (delegating to router per routing-architecture.md)
# ══════════════════════════════════════════════════════════════

def _shortcut_classify(msg: str):
    """
    Run keyword shortcuts BEFORE the obvious-chat pre-filter.
    Returns a task_type string if matched, else None.
    This prevents short messages from being swallowed by _classify_obvious_chat().

    Delegates to router._keyword_shortcut per docs/routing-architecture.md.
    Must not be expanded inline here - the router owns keyword semantics.
    """
    from router import _keyword_shortcut
    return _keyword_shortcut(msg)


def _classify_obvious_chat(msg: str) -> bool:
    """
    Returns True only for unmistakable single-word greetings with no task content.
    Everything else goes through classify_task (LLM fallback included).

    Per docs/routing-architecture.md rule 4: do NOT expand this with length
    checks, prefix lists, or keyword exclusions. Those heuristics blocked the
    LLM fallback for short natural-language task requests.
    """
    m = msg.strip().lower().rstrip("!.,?")
    return m in {"hi", "hey", "hello", "thanks", "thank you", "morning", "good morning", "good evening"}


# ══════════════════════════════════════════════════════════════
# process_telegram_update
# ══════════════════════════════════════════════════════════════

async def process_telegram_update(update: dict) -> None:
    """
    Unified processor for Telegram updates (webhook or polling).

    Dispatch order matters. Reordering risks regressing feedback-window precedence rules:
      1. callback_query (Phase 1 inline-button feedback tag)
      2. sender auth
      3. evict expired feedback windows, then 5-min free-text tag window
      4. reply-to-message approval (approve/reject/edit)
      5. naked approval fallback (yes confirm / no confirm, with doc-routing precedence)
      6. doc-routing emoji handlers (✅/✏️/🆕/❌/➕ + text aliases)
      7. slash commands (15 of them)
      8. praise/critique (gated by MEMORY_LEARNING_ENABLED)
      9. classify + dispatch (chat -> run_chat, task -> _run_background_job)
    """
    # 1. Phase 1 callback_query taps (inline buttons for feedback_tag)
    if handle_callback_query(update):
        return

    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    text = message.get("text", "").strip()
    chat_id = str(message.get("chat", {}).get("id", ""))
    sender_id = str(message.get("from", {}).get("id", ""))
    reply_to = message.get("reply_to_message", {}) or {}
    reply_to_msg_id = reply_to.get("message_id")

    if not text or not chat_id:
        return

    # 2. Sender authentication (fail-closed when ALLOWED_USER_IDS is set)
    allowed_raw = os.environ.get("ALLOWED_USER_IDS", "")
    allowed_ids = {uid.strip() for uid in allowed_raw.split(",") if uid.strip()}
    if allowed_ids and sender_id not in allowed_ids:
        from notifier import send_message as _send
        _send(chat_id, "Sorry, you are not authorised to use this bot.")
        logger.warning(f"Unauthorised Telegram access attempt from sender_id={sender_id}")
        return

    text_lower_full = text.strip().lower()
    first_word = text_lower_full.split()[0] if text_lower_full else ""
    now_epoch = time.time()

    # 3a. Evict expired feedback windows BEFORE the tag check (5-min TTL)
    evict_expired_windows()

    # 3b. 5-minute free-text tag window. Must run BEFORE approval logic so
    #     a short "stale" is treated as a tag, not a new command.
    if handle_pending_feedback_tag(text, chat_id, first_word, reply_to_msg_id):
        return

    # 3c. Sunday editorial input capture window.
    if handle_newsletter_editorial_reply(text, chat_id, first_word, reply_to_msg_id):
        return

    # 4. Reply-to-message approve/reject/edit
    if handle_approval_reply(text, chat_id, first_word, reply_to_msg_id, now_epoch):
        return

    # 4.5 Atlas M1: reply 'posted'/'skip' to a publish-brief message
    if handle_publish_reply(text, chat_id, first_word, reply_to_msg_id):
        return

    # 5. Naked fallback: yes confirm / no confirm (with doc-routing precedence)
    if handle_naked_approval(text, chat_id, first_word, reply_to_msg_id):
        return

    # 6. Doc-routing emoji / text aliases. handle_doc_emoji accepts the emoji
    #    directly; we resolve the emoji or alias here to match monolith behavior.
    _EMOJI_COMMANDS = ("✅", "✏️", "🆕", "❌", "➕")
    _TEXT_ALIASES = {
        "yes": "✅", "confirm": "✅", "approved": "✅", "approve": "✅",
        "flag": "❌", "discard": "❌", "reject": "❌",
    }
    matched_emoji = next((e for e in _EMOJI_COMMANDS if text.startswith(e)), None)
    if not matched_emoji:
        matched_emoji = _TEXT_ALIASES.get(first_word)
        if not matched_emoji and first_word == "edit":
            matched_emoji = "✏️"
    if matched_emoji:
        if handle_doc_emoji(matched_emoji, text, chat_id, reply_to_msg_id):
            return

    # 7. Slash commands (15: original 6 + /switch + Phase 0/1/2 9)
    if dispatch_command(text, chat_id):
        return

    # 8. Praise / critique (noop when MEMORY_LEARNING_ENABLED != "true")
    if handle_feedback(text, chat_id):
        return

    # 9. Classify and dispatch.
    job_id = str(uuid.uuid4())
    from notifier import send_briefing

    active_project = _active_project.get(chat_id)
    session_key = f"{chat_id}:{active_project}" if active_project else chat_id

    # Shortcut first, catches task phrases before the obvious-chat gate eats them
    shortcut = _shortcut_classify(text)
    if shortcut and shortcut != "memory_capture":
        task_type = shortcut
        classification = {"task_type": shortcut, "confidence": 0.95, "is_unknown": False, "has_email_followup": False}
    elif shortcut == "memory_capture":
        # memory_capture is handled in chat via the save_memory tool
        task_type = "chat"
        classification = {"task_type": "chat", "confidence": 0.95, "is_unknown": False, "has_email_followup": False}
    elif _classify_obvious_chat(text):
        task_type = "chat"
        classification = {"task_type": "chat", "confidence": 0.95, "is_unknown": False, "has_email_followup": False}
    else:
        from router import classify_task
        classification = classify_task(text)
        task_type = classification.get("task_type", "unknown")

    send_briefing(chat_id, task_type, text)

    loop = asyncio.get_running_loop()
    if task_type == "chat":
        # Inject Qdrant context recall for conversational continuity
        enriched_text = text
        try:
            from memory import query_memory
            memories = query_memory(text, top_k=3)
            if memories:
                context_lines = ["[Relevant past context:"]
                for m in memories:
                    ts = m.get("date", "?")
                    summary = m.get("summary", "")[:120]
                    context_lines.append(f"  {ts}: {summary}")
                context_lines.append("]")
                enriched_text = "\n".join(context_lines) + "\n\n" + text
        except Exception:
            pass  # non-fatal, proceed with plain text

        await loop.run_in_executor(
            None,
            lambda: run_chat_with_buttons(
                message=enriched_text,
                session_key=session_key,
                chat_id=chat_id,
                channel="telegram",
            ),
        )
    else:
        from worker import _run_background_job
        loop.run_in_executor(
            None,
            lambda: _run_background_job(
                task=text,
                from_number=chat_id,
                session_key=session_key,
                job_id=job_id,
                classification=classification,
            ),
        )


# ══════════════════════════════════════════════════════════════
# Telegram polling loop (hardened: 3-attempt deleteWebhook, 401 -> stop)
# ══════════════════════════════════════════════════════════════

async def telegram_polling_loop() -> None:
    """
    Poll for Telegram updates instead of waiting on webhooks.
    Poll for Telegram updates instead of waiting on webhooks.
    """
    token = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_POLLING: No token found. Polling disabled.")
        return

    logger.info("TELEGRAM_POLLING: Starting loop...")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    offset = 0

    # Ensure webhook is cleared so polling works (3 attempts, 2s apart)
    webhook_cleared = False
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"https://api.telegram.org/bot{token}/deleteWebhook")
                if resp.status_code == 200 and resp.json().get("result"):
                    webhook_cleared = True
                    break
        except Exception as e:
            logger.warning(f"TELEGRAM_POLLING: deleteWebhook attempt {attempt+1} failed: {e}")
        await asyncio.sleep(2)

    if not webhook_cleared:
        logger.error("TELEGRAM_POLLING: Could not clear webhook after 3 attempts. Polling may conflict with webhook delivery.")

    while True:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    url,
                    params={
                        "offset": offset,
                        "timeout": 20,
                        "allowed_updates": '["message","edited_message","callback_query"]',
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        asyncio.create_task(process_telegram_update(update))
                elif resp.status_code == 401:
                    logger.error("TELEGRAM_POLLING: Invalid Token. Stopping.")
                    break
                else:
                    await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"TELEGRAM_POLLING: Error: {e}", exc_info=True)
            await asyncio.sleep(10)
