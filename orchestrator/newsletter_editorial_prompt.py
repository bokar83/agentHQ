"""
newsletter_editorial_prompt.py - Sunday 18:00 MT heartbeat callback.

Sends one Telegram message asking Boubacar what he noticed this week worth a
newsletter. Sunday-only gate. The reply is captured by
handlers_approvals.handle_newsletter_editorial_reply between Sun 18:00 and
Mon 06:00 and stored in newsletter_editorial_input for that Monday's date.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime

import pytz

logger = logging.getLogger("agentsHQ.newsletter_editorial_prompt")

TIMEZONE = os.environ.get("GENERIC_TIMEZONE", "America/Denver")

PROMPT_TEXT = (
    "What did you notice this week worth a newsletter? "
    "One sentence reply turns into Tuesday's draft. "
    "Reply by Mon 06:00 MT or the system uses Monday's top scout pick."
)


def _now() -> datetime:
    return datetime.now(pytz.timezone(TIMEZONE))


def _chat_id() -> str | None:
    return os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")


def send_message(chat_id: str, text: str) -> None:
    """Indirection for testability."""
    from notifier import send_message as _send

    _send(chat_id, text)


def newsletter_editorial_prompt_tick() -> None:
    """Heartbeat callback. Sunday only."""
    now = _now()
    if now.weekday() != 6:
        logger.debug("newsletter_editorial_prompt: not Sunday, skipping")
        return

    chat_id = _chat_id()
    if not chat_id:
        logger.warning("newsletter_editorial_prompt: no chat id configured, skipping")
        return

    send_message(chat_id, PROMPT_TEXT)
    logger.info("newsletter_editorial_prompt: prompt sent to chat %s", chat_id)
