import os
import logging
import time
from datetime import date, timedelta

import requests

logger = logging.getLogger(__name__)

GRIOT_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
STUDIO_DB_ID = os.environ.get("NOTION_STUDIO_PIPELINE_DB_ID", "34ebcf1a-3029-8140-a565-f7c26fe9de86")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
_BOT_TOKEN = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN", os.environ.get("TELEGRAM_BOT_TOKEN", ""))


def _filter_candidates(candidates: list[dict]) -> list[dict]:
    filtered = [c for c in candidates if not c.get("hyperframe_twin_id")]
    return sorted(filtered, key=lambda c: c.get("total_score", 0), reverse=True)[:3]


def _parse_reply(reply_text: str, count: int) -> list[int]:
    reply_text = reply_text.strip().lower()
    if reply_text == "skip":
        return []
    if reply_text == "all":
        return list(range(count))
    indices = []
    for part in reply_text.replace(" ", "").split(","):
        try:
            idx = int(part) - 1
            if 0 <= idx < count:
                indices.append(idx)
        except ValueError:
            pass
    return indices


def _extract_text(prop) -> str:
    if not prop or not prop.get("rich_text"):
        return ""
    return "".join(t["plain_text"] for t in prop["rich_text"])


def _extract_platforms(prop) -> list[str]:
    if not prop or not prop.get("multi_select"):
        return []
    return [s["name"].lower() for s in prop["multi_select"]]


class HyperframeBoostAgent:
    def __init__(self):
        from notion_client import Client as NotionClient
        self._notion = NotionClient(auth=os.environ["NOTION_SECRET"])

    def _notion_query(self) -> list[dict]:
        response = self._notion.databases.query(
            database_id=GRIOT_DB_ID,
            filter={
                "and": [
                    {"property": "Status", "select": {"is_not_empty": True}},
                    {"property": "Status", "select": {"does_not_equal": "Posted"}},
                    {"property": "hyperframe_twin_id", "relation": {"is_empty": True}},
                ]
            },
            sorts=[{"property": "total_score", "direction": "descending"}],
            page_size=20,
        )
        return response.get("results", [])

    def _query_candidates(self) -> list[dict]:
        raw = self._notion_query()
        parsed = []
        for page in raw:
            props = page["properties"]
            platforms = _extract_platforms(props.get("Platform"))
            if not any(p in platforms for p in ["linkedin", "x"]):
                continue
            full_text = _extract_text(props.get("Draft")) or _extract_text(props.get("Hook"))
            if not full_text:
                continue
            parsed.append({
                "notion_id": page["id"],
                "total_score": (props.get("total_score") or {}).get("number", 0) or 0,
                "text_preview": full_text[:150],
                "full_text": full_text,
                "scheduled_date": ((props.get("Scheduled Date") or {}).get("date") or {}).get("start", ""),
                "platform": platforms,
                "hyperframe_twin_id": bool((props.get("hyperframe_twin_id") or {}).get("relation")),
            })
        return _filter_candidates(parsed)

    def _send_telegram_menu(self, candidates: list[dict]) -> None:
        from orchestrator.notifier import send_message
        lines = ["HyperFrame candidates ready:\n"]
        for i, c in enumerate(candidates, 1):
            lines.append(f"{i}. [score: {c['total_score']:.0f}] {c['text_preview'][:100]}...")
        lines.append("\nReply: 1, 2, 3, 1,3, all, or skip")
        send_message(TELEGRAM_CHAT_ID, "\n".join(lines))

    def _poll_telegram_reply(self, count: int, timeout_hours: int = 24) -> list[int]:
        """Poll Telegram getUpdates for reply. Returns approved indices or [] on timeout/skip."""
        if not _BOT_TOKEN:
            logger.warning("No bot token — cannot poll Telegram. Auto-skipping.")
            return []
        api_base = f"https://api.telegram.org/bot{_BOT_TOKEN}"
        deadline = time.time() + timeout_hours * 3600
        offset = 0
        while time.time() < deadline:
            try:
                resp = requests.get(
                    f"{api_base}/getUpdates",
                    params={"offset": offset, "timeout": 30, "allowed_updates": ["message"]},
                    timeout=35,
                )
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    if chat_id != str(TELEGRAM_CHAT_ID):
                        continue
                    text = msg.get("text", "").strip()
                    if text:
                        return _parse_reply(text, count)
            except Exception as e:
                logger.warning("Telegram poll error: %s", e)
                time.sleep(5)
        logger.warning("Telegram reply timeout after %sh. Auto-skipping.", timeout_hours)
        return []

    def run(self):
        raise NotImplementedError("Implemented in Task 4")
