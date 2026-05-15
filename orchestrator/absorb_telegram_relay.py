"""
absorb_telegram_relay.py -- multi-bot Telegram poller for absorb candidates.

The main orchestrator bot (ORCHESTRATOR_TELEGRAM_BOT_TOKEN) already runs the
full dispatcher chain in handlers.py and picks up URL forwards via the Phase
2 handle_absorb_url_forward step. This module covers the *other* Boubacar-
owned bots whose tokens are in .env but which are not the main orchestrator
loop: CC_TELEGRAM_BOT_TOKEN, REMOAT_TELEGRAM_BOT_TOKEN, and any future bot
listed in ABSORB_RELAY_TOKENS (comma-separated list of env-var names).

Each relay loop:
  - Calls deleteWebhook once (so polling works)
  - getUpdates long-poll (timeout=20)
  - For each message: if text is a bare http(s):// URL, enqueue via
    absorb_inbound.enqueue() and reply "Queued for absorb_crew #N."
  - All other messages: ignored. This is a URL-only relay, not a full bot.

Offset is process-local (resets to 0 on container restart -- Telegram will
serve the last ~24h on first poll, find_duplicate de-dupes those).
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Optional

import httpx

logger = logging.getLogger("agentsHQ.absorb_telegram_relay")

URL_RE = re.compile(r"https?://\S+")

DEFAULT_BOT_ENVS = ("CC_TELEGRAM_BOT_TOKEN", "REMOAT_TELEGRAM_BOT_TOKEN")
EXCLUDE_ENVS = ("ORCHESTRATOR_TELEGRAM_BOT_TOKEN",)


def _resolve_bot_env_names() -> list[str]:
    """Returns the env-var names to poll. ABSORB_RELAY_TOKENS overrides
    the default list (CC + REMOAT). ORCHESTRATOR is always excluded — it
    is owned by handlers.py.
    """
    override = os.environ.get("ABSORB_RELAY_TOKENS", "").strip()
    if override:
        names = [n.strip() for n in override.split(",") if n.strip()]
    else:
        names = list(DEFAULT_BOT_ENVS)
    return [n for n in names if n not in EXCLUDE_ENVS]


async def _send_message(token: str, chat_id: str, text: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text},
            )
    except Exception as e:
        logger.warning(f"relay sendMessage failed (chat={chat_id}): {e}")


async def _process_message(bot_label: str, token: str, message: dict) -> None:
    text = (message.get("text") or "").strip()
    if not text:
        return
    chat_id = str(message.get("chat", {}).get("id", ""))
    sender_id = str(message.get("from", {}).get("id", ""))
    if not chat_id:
        return

    m = URL_RE.match(text)
    if not m:
        return
    url = m.group(0).rstrip(").,;:'\"")

    try:
        from absorb_inbound import enqueue, find_duplicate
    except Exception as e:
        logger.error(f"relay: absorb_inbound import failed: {e}")
        return

    try:
        prior = find_duplicate(url)
        if prior is not None:
            await _send_message(token, chat_id, f"Already absorbed (prior absorb_queue #{prior}). Skipping.")
            return
        row_id = enqueue(url, "telegram", submitted_by=f"{bot_label}:{sender_id}")
    except Exception as e:
        logger.error(f"relay enqueue failed (bot={bot_label}, url={url}): {e}")
        await _send_message(token, chat_id, f"Enqueue failed: {e}")
        return

    await _send_message(
        token, chat_id,
        f"Queued for absorb_crew #{row_id}. Verdict in this chat when ready.",
    )


async def _relay_loop_for_bot(env_name: str) -> None:
    token = os.environ.get(env_name, "").strip()
    if not token:
        logger.warning(f"relay: env {env_name} unset; skipping this bot")
        return
    bot_label = env_name.removesuffix("_TELEGRAM_BOT_TOKEN").lower() or env_name

    # Clear webhook so getUpdates works (best-effort, no retry storm)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.get(f"https://api.telegram.org/bot{token}/deleteWebhook")
    except Exception as e:
        logger.warning(f"relay {bot_label}: deleteWebhook failed: {e}")

    base_url = f"https://api.telegram.org/bot{token}/getUpdates"
    offset = 0
    logger.info(f"relay {bot_label}: starting URL-only poll loop")

    while True:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    base_url,
                    params={
                        "offset": offset,
                        "timeout": 20,
                        "allowed_updates": '["message","edited_message"]',
                    },
                )
                if resp.status_code == 401:
                    logger.error(f"relay {bot_label}: invalid token; stopping")
                    return
                if resp.status_code != 200:
                    await asyncio.sleep(5)
                    continue
                for update in (resp.json().get("result") or []):
                    offset = update["update_id"] + 1
                    msg = update.get("message") or update.get("edited_message")
                    if msg:
                        await _process_message(bot_label, token, msg)
        except Exception as e:
            logger.error(f"relay {bot_label}: loop error: {e}", exc_info=True)
            await asyncio.sleep(10)


async def start_absorb_relays() -> list:
    """Spawn one polling task per non-orchestrator bot. Caller awaits or
    keeps the returned tasks alive.
    """
    tasks = []
    for env_name in _resolve_bot_env_names():
        task = asyncio.create_task(
            _relay_loop_for_bot(env_name),
            name=f"absorb_relay_{env_name}",
        )
        tasks.append(task)
    return tasks
