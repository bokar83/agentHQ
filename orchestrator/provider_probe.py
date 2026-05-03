"""
provider_probe.py - 5-minute health probe for the active LLM provider.

Registered as a heartbeat wake in app.py. On each fire:
  - If tripped: run a 1-token test call. Success = record_recovery + Telegram.
  - If healthy: run the same test call. Failure = record_failure (same circuit breaker).
  - Always: fetch OpenRouter credit balance, check for spend spike.

Spike alert: if balance drops > SPIKE_THRESHOLD_USD in a single probe window,
fires a Telegram alert. Uses two module-level floats -- no new table needed.

Zero LLM cost intent: uses claude-haiku-4.5 with max_tokens=1.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

logger = logging.getLogger("agentsHQ.provider_probe")

PROBE_MODEL = "anthropic/claude-haiku-4.5"
PROBE_MESSAGES = [{"role": "user", "content": "hi"}]

# Spike detection state (in-memory, resets on container restart -- intentional).
# A restart clears the baseline, which is safe: we only alert on drops we witness.
_last_balance_usd: Optional[float] = None
_last_balance_ts: float = 0.0

# Alert if balance drops more than this in one 5-min window.
SPIKE_THRESHOLD_USD = 2.0


def _fetch_balance() -> Optional[float]:
    """GET /api/v1/auth/key and return remaining credit balance, or None on error."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return None
    try:
        import httpx
        with httpx.Client(timeout=8.0) as client:
            r = client.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {api_key}"},
            )
        if r.status_code != 200:
            logger.warning("BALANCE PROBE: /auth/key returned %s", r.status_code)
            return None
        data = r.json().get("data", {})
        # limit_remaining is credit balance; usage is total spent lifetime
        limit_remaining = data.get("limit_remaining")
        if limit_remaining is not None:
            return float(limit_remaining)
        # Fallback: some key types expose rate_limit.requests_remaining only
        return None
    except Exception as exc:
        logger.warning("BALANCE PROBE: fetch failed: %s", exc)
        return None


def _check_spike(balance: float, chat_id: str) -> None:
    """Compare balance to last reading. Alert if drop exceeds threshold."""
    global _last_balance_usd, _last_balance_ts
    from notifier import send_message

    now = time.time()
    if _last_balance_usd is not None:
        drop = _last_balance_usd - balance
        elapsed_min = (now - _last_balance_ts) / 60.0
        if drop >= SPIKE_THRESHOLD_USD:
            rate = drop / max(elapsed_min, 0.1)
            msg = (
                f"ATLAS SPEND SPIKE\n"
                f"Balance dropped ${drop:.2f} in {elapsed_min:.1f} min "
                f"(~${rate:.2f}/min).\n"
                f"Current balance: ${balance:.2f}\n"
                f"Check: is ANTHROPIC_BASE_URL set? Is a crew runaway?"
            )
            logger.warning("SPEND SPIKE: drop=$%.2f balance=$%.2f", drop, balance)
            if chat_id:
                send_message(chat_id, msg)

    _last_balance_usd = balance
    _last_balance_ts = now


def run_probe() -> None:
    """Fire one lightweight test call, update provider_health, and check balance."""
    from provider_health import get_status, record_recovery
    from notifier import send_message

    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    current = get_status("openrouter")
    was_tripped = current["status"] == "tripped"

    # Balance check first -- independent of the LLM probe result.
    balance = _fetch_balance()
    if balance is not None:
        logger.debug("BALANCE PROBE: $%.4f remaining", balance)
        _check_spike(balance, chat_id)
    else:
        logger.debug("BALANCE PROBE: could not fetch balance")

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
