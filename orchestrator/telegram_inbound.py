import logging
import os
import threading
import time

import requests

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 5  # seconds
_BOT_TOKEN = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN", "")
_OWNER_CHAT_ID = int(os.environ.get("OWNER_TELEGRAM_CHAT_ID", "0"))


def _poll_loop():
    offset = 0
    logger.info("TGINBOUND: poll loop started (chat_id=%s)", _OWNER_CHAT_ID)
    while True:
        try:
            resp = requests.get(
                f"https://api.telegram.org/bot{_BOT_TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 0, "limit": 100},
                timeout=10,
            )
            data = resp.json()
            if not data.get("ok"):
                logger.warning("TGINBOUND: getUpdates not ok: %s", data)
                time.sleep(_POLL_INTERVAL)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message") or update.get("edited_message")
                if not msg:
                    continue
                chat_id = msg.get("chat", {}).get("id")
                if chat_id != _OWNER_CHAT_ID:
                    continue
                text = msg.get("text", "")
                logger.info("[TGINBOUND] text=%s", text)
                try:
                    from notifier import send_message
                    send_message(str(_OWNER_CHAT_ID), f"ACK: {text}")
                except Exception as e:
                    logger.error("TGINBOUND: echo failed: %s", e)

        except Exception as e:
            logger.error("TGINBOUND: poll error: %s", e)

        time.sleep(_POLL_INTERVAL)


def start():
    if not _BOT_TOKEN:
        logger.warning("TGINBOUND: ORCHESTRATOR_TELEGRAM_BOT_TOKEN not set, skipping")
        return
    if not _OWNER_CHAT_ID:
        logger.warning("TGINBOUND: OWNER_TELEGRAM_CHAT_ID not set, skipping")
        return
    t = threading.Thread(target=_poll_loop, daemon=True)
    t.start()
    logger.info("TGINBOUND: inbound poll thread registered")
