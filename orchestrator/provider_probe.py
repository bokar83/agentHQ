"""
provider_probe.py - 5-minute health probe for the active LLM provider.

Registered as a heartbeat wake in app.py. On each fire:
  - If tripped: run a 1-token test call. Success = record_recovery + Telegram.
  - If healthy: run the same test call. Failure = record_failure (same circuit breaker).

Zero LLM cost intent: uses claude-haiku-4.5 with max_tokens=1.
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger("agentsHQ.provider_probe")

PROBE_MODEL = "anthropic/claude-haiku-4.5"
PROBE_MESSAGES = [{"role": "user", "content": "hi"}]


def run_probe() -> None:
    """Fire one lightweight test call and update provider_health accordingly."""
    from provider_health import get_status, record_failure, record_recovery
    from notifier import send_message

    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    current = get_status("openrouter")
    was_tripped = current["status"] == "tripped"

    try:
        from llm_helpers import call_llm
        call_llm(PROBE_MESSAGES, model=PROBE_MODEL, max_tokens=1)
        if was_tripped:
            record_recovery("openrouter")
            logger.info("PROVIDER PROBE: openrouter recovered.")
            if chat_id:
                send_message(chat_id,
                    "ATLAS: OpenRouter recovered.\n"
                    "Health probe passed. Resuming normal operations."
                )
        else:
            logger.debug("PROVIDER PROBE: openrouter healthy.")
    except Exception as exc:
        logger.warning(f"PROVIDER PROBE: openrouter probe failed: {exc}")
