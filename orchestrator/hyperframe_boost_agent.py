import os
import logging
import time
from datetime import date, timedelta

import requests
from orchestrator.hyperframe_brief_generator import HyperframeBriefGenerator

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
        from skills.forge_cli.notion_client import NotionClient
        self._notion = NotionClient(secret=os.environ["NOTION_SECRET"])

    def _notion_query(self) -> list[dict]:
        return self._notion.query_database(
            GRIOT_DB_ID,
            filter_obj={
                "and": [
                    {"property": "Status", "select": {"is_not_empty": True}},
                    {"property": "Status", "select": {"does_not_equal": "Posted"}},
                    {"property": "hyperframe_twin_id", "relation": {"is_empty": True}},
                ]
            },
            sorts=[{"property": "Total Score", "direction": "descending"}],
        )

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
                "total_score": (props.get("Total Score") or {}).get("number", 0) or 0,
                "text_preview": full_text[:150],
                "full_text": full_text,
                "scheduled_date": ((props.get("Scheduled Date") or {}).get("date") or {}).get("start", ""),
                "platform": platforms,
                "hyperframe_twin_id": bool((props.get("hyperframe_twin_id") or {}).get("relation")),
            })
        return _filter_candidates(parsed)

    def _send_telegram_menu(self, candidates: list[dict]) -> None:
        from orchestrator.notifier import send_message_with_buttons
        lines = ["🎬 HyperFrame Boost — pick posts to convert:\n"]
        for i, c in enumerate(candidates, 1):
            score_100 = round(c['total_score'] * 2)
            lines.append(f"{i}. [{score_100}/100] {c['text_preview'][:60]}...")
        msg = "\n".join(lines)
        if len(msg) > 3800:
            msg = msg[:3800] + "..."
        # Inline keyboard: numbered buttons + ALL + SKIP
        num_buttons = [(str(i), str(i)) for i in range(1, len(candidates) + 1)]
        action_buttons = [("ALL", "all"), ("SKIP", "skip")]
        buttons = [num_buttons, action_buttons]
        send_message_with_buttons(TELEGRAM_CHAT_ID, msg, buttons)

    def _get_latest_update_id(self) -> int:
        """Fetch current highest update_id so polling ignores pre-existing messages."""
        if not _BOT_TOKEN:
            return 0
        try:
            resp = requests.get(
                f"https://api.telegram.org/bot{_BOT_TOKEN}/getUpdates",
                params={"limit": 1, "offset": -1},
                timeout=10,
            )
            results = resp.json().get("result", [])
            return results[-1]["update_id"] + 1 if results else 0
        except Exception:
            return 0

    def _poll_telegram_reply(self, count: int, timeout_hours: int = 24) -> list[int]:
        """Poll for button callback_query OR text reply. Returns approved indices or [] on timeout/skip."""
        if not _BOT_TOKEN:
            logger.warning("No bot token — cannot poll Telegram. Auto-skipping.")
            return []
        api_base = f"https://api.telegram.org/bot{_BOT_TOKEN}"
        deadline = time.time() + timeout_hours * 3600
        offset = self._get_latest_update_id()
        while time.time() < deadline:
            try:
                resp = requests.get(
                    f"{api_base}/getUpdates",
                    params={"offset": offset, "timeout": 30, "allowed_updates": ["message", "callback_query"]},
                    timeout=35,
                )
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    # Handle button tap (callback_query)
                    if "callback_query" in update:
                        cb = update["callback_query"]
                        cb_chat = str(cb.get("message", {}).get("chat", {}).get("id", ""))
                        if cb_chat != str(TELEGRAM_CHAT_ID):
                            continue
                        # Acknowledge the callback
                        try:
                            requests.post(
                                f"{api_base}/answerCallbackQuery",
                                json={"callback_query_id": cb["id"], "text": "Got it ✓"},
                                timeout=5,
                            )
                        except Exception:
                            pass
                        return _parse_reply(cb["data"], count)
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

    def _render_and_queue(self, candidate: dict) -> None:
        import tempfile
        gen = HyperframeBriefGenerator()
        twin_id = None

        for aspect_ratio, platforms in [("9:16", ["x", "youtube-shorts"]), ("1:1", ["LinkedIn"])]:
            try:
                out_path = tempfile.mktemp(suffix=f"_{aspect_ratio.replace(':','x')}.mp4")
                gen.render_to_mp4(candidate["full_text"], aspect_ratio=aspect_ratio, output_path=out_path)
                upload = _drive_upload(out_path, f"hf_boost_{candidate['notion_id']}_{aspect_ratio.replace(':','x')}.mp4")
                record_id = _create_studio_record(
                    self._notion, candidate, upload["webViewLink"], aspect_ratio, platforms
                )
                twin_id = record_id
            except Exception as e:
                send_message(TELEGRAM_CHAT_ID, f"HF Boost render failed ({aspect_ratio}) for '{candidate['text_preview'][:60]}': {str(e)[:150]}")
                logger.error("Render failed %s %s: %s", candidate["notion_id"], aspect_ratio, e)

        if twin_id:
            try:
                _mark_twin(self._notion, candidate["notion_id"], twin_id)
            except Exception as e:
                logger.error("Failed to mark twin on %s: %s", candidate["notion_id"], e)

    def run(self):
        candidates = self._query_candidates()
        if not candidates:
            send_message(TELEGRAM_CHAT_ID, "HyperFrame Boost: No new candidates. Skipping cycle.")
            return

        self._send_telegram_menu(candidates)
        approved_indices = self._poll_telegram_reply(len(candidates))

        if not approved_indices:
            send_message(TELEGRAM_CHAT_ID, "HyperFrame Boost: Skipped this cycle.")
            return

        for idx in approved_indices:
            self._render_and_queue(candidates[idx])

        send_message(
            TELEGRAM_CHAT_ID,
            f"HyperFrame Boost: Done. {len(approved_indices)} post(s) boosted and queued.",
        )


# ---------------------------------------------------------------------------
# Module-level helpers (used by _render_and_queue and patchable in tests)
# ---------------------------------------------------------------------------

def send_message(chat_id: str, text: str) -> None:
    """Thin wrapper so tests can patch orchestrator.hyperframe_boost_agent.send_message."""
    from orchestrator.notifier import send_message as _send
    _send(chat_id, text)


def _drive_upload(local_path: str, filename: str) -> dict:
    """Upload MP4 to Drive. Returns dict with webViewLink and id."""
    try:
        from pathlib import Path
        from kie_media import _upload_to_drive
        folder_id = os.environ.get("HF_BOOST_DRIVE_FOLDER_ID", "")
        return _upload_to_drive(Path(local_path), folder_id, filename, "video/mp4")
    except ImportError:
        logger.warning("kie_media not available — Drive upload skipped (dev mode)")
        return {"webViewLink": f"file://{local_path}", "id": "local"}


def _create_studio_record(notion_client, candidate: dict, drive_url: str,
                           aspect_ratio: str, platforms: list) -> str:
    """Create companion Studio Pipeline DB record. Returns new page ID."""
    scheduled = candidate.get("scheduled_date", "")
    if scheduled:
        d = date.fromisoformat(scheduled[:10])
        video_date = (d + timedelta(days=1)).isoformat()
    else:
        video_date = (date.today() + timedelta(days=1)).isoformat()

    response = notion_client.create_page(
        STUDIO_DB_ID,
        {
            "Title": {"title": [{"text": {"content": f"HF Boost — {candidate['text_preview'][:60]}"}}]},
            "Status": {"select": {"name": "scheduled"}},
            "Scheduled Date": {"date": {"start": video_date}},
            "Platform": {"multi_select": [{"name": p} for p in platforms]},
            "Asset URL": {"url": drive_url},
            "linked_text_post_id": {"rich_text": [{"text": {"content": candidate["notion_id"]}}]},
            "hf_channel": {"select": {"name": "personal"}},
            "hf_format": {"select": {"name": "hyperframe-boost"}},
            "aspect_ratio": {"select": {"name": aspect_ratio}},
        }
    )
    return response["id"]


def _mark_twin(notion_client, griot_page_id: str, twin_page_id: str) -> None:
    """Write hyperframe_twin_id back to source Griot record as dedup guard."""
    notion_client.update_page(
        griot_page_id,
        {"hyperframe_twin_id": {"relation": [{"id": twin_page_id}]}}
    )
