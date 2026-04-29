"""
publish_brief.py - Phase 3.75+: daily morning publish brief.

Every weekday at 07:30 MT, read the Notion Content Board for records where:
  Status = Queued
  Scheduled Date = today

Send a Telegram brief to the owner with:
  - Title + Draft text ready to copy
  - LinkedIn share intent URL (one tap opens LinkedIn composer with text)
  - X share intent URL (one tap opens Twitter composer with text)

No auto-publishing. Boubacar taps the share URL, reviews final text in
the native composer, hits Post. 10 seconds per post. Label is explicitly
"publish reminder" so expectations stay clear.

Empty queue: send a short "nothing to publish today" heads-up. Not silence,
so we know the brief itself is healthy.

Zero LLM. Pure Notion read + format + send.
"""
from __future__ import annotations

import logging
import os
import urllib.parse
from datetime import date, datetime
from typing import Optional

import pathlib
import tempfile

import pytz

logger = logging.getLogger("agentsHQ.publish_brief")

# ─── per-day dedup sentinel (survives container restarts via /tmp) ────────────
_SENTINEL_DIR = pathlib.Path(tempfile.gettempdir())


def _brief_already_sent(today_iso: str) -> bool:
    return (_SENTINEL_DIR / f"publish_brief_sent_{today_iso}.flag").exists()


def _mark_brief_sent(today_iso: str) -> None:
    try:
        (_SENTINEL_DIR / f"publish_brief_sent_{today_iso}.flag").touch()
    except OSError:
        pass

TIMEZONE = os.environ.get("HEARTBEAT_TIMEZONE", "America/Denver")
CONTENT_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")


# ═════════════════════════════════════════════════════════════════════════════
# Notion helpers
# ═════════════════════════════════════════════════════════════════════════════

def _title(prop):
    arr = prop.get("title") if prop else None
    return arr[0].get("plain_text", "") if arr else ""


def _text(prop):
    arr = prop.get("rich_text") if prop else None
    return "".join(t.get("plain_text", "") for t in arr) if arr else ""


def _select(prop):
    if not prop:
        return None
    sel = prop.get("select") or prop.get("status")
    return sel.get("name") if sel else None


def _multi(prop):
    arr = prop.get("multi_select") if prop else None
    return [x.get("name") for x in arr] if arr else []


def _date_start(prop):
    d = prop.get("date") if prop else None
    return d.get("start") if d else None


# ═════════════════════════════════════════════════════════════════════════════
# Share intent URLs
# ═════════════════════════════════════════════════════════════════════════════

def _linkedin_share_url(text: str) -> str:
    """LinkedIn does not have a text-only share intent (only URL-sharing).
    Use the feed-share URL with the text in the `summary` param; LinkedIn's
    composer prefills for authenticated users.
    """
    base = "https://www.linkedin.com/feed/?shareActive=true"
    # LinkedIn truncates heavily on share intents; provide text as query param
    encoded = urllib.parse.quote(text, safe="")
    return f"{base}&text={encoded}"


def _x_share_url(text: str) -> str:
    """X (Twitter) composer share intent. One tap opens the composer with
    the text pre-filled. Works on web + native apps on iOS/Android.
    """
    encoded = urllib.parse.quote(text, safe="")
    return f"https://twitter.com/intent/tweet?text={encoded}"


def _publish_url(platform: str, text: str) -> Optional[str]:
    if platform == "LinkedIn":
        return _linkedin_share_url(text)
    if platform == "X":
        return _x_share_url(text)
    return None


# ═════════════════════════════════════════════════════════════════════════════
# Fetch today's Queued posts
# ═════════════════════════════════════════════════════════════════════════════

def _fetch_todays_queued(notion, today_iso: str) -> list:
    """Return Content Board records where Status=Queued AND Scheduled Date=today.
    Ignores archived / ready / posted / other statuses.
    """
    posts = notion.query_database(CONTENT_DB_ID, filter_obj=None)
    today_queued = []
    for p in posts:
        props = p.get("properties", {})
        if _select(props.get("Status", {})) != "Queued":
            continue
        sd = _date_start(props.get("Scheduled Date", {}))
        if not sd or sd[:10] != today_iso:
            continue
        platforms = _multi(props.get("Platform", {}))
        if not any(pf in ("LinkedIn", "X") for pf in platforms):
            continue
        today_queued.append({
            "notion_id": p["id"],
            "title": _title(props.get("Title", {})),
            "draft": _text(props.get("Draft", {})),
            "hook": _text(props.get("Hook", {})),
            "platform": platforms[0] if platforms else None,
        })
    return today_queued


# ═════════════════════════════════════════════════════════════════════════════
# Message formatting
# ═════════════════════════════════════════════════════════════════════════════

def _format_empty_brief(today_iso: str, day_name: str) -> str:
    return (
        f"Publish brief for {day_name} {today_iso}\n\n"
        f"No posts queued for today. Content Board is quiet.\n"
        f"(This is a normal morning if Griot has not proposed anything yet or all picks were rejected.)"
    )


def _format_full_brief(today_iso: str, day_name: str, posts: list) -> list:
    """Build one Telegram message per post plus a header. Returns a list of
    strings to send (one per message). Telegram has a 4096-char limit so
    LinkedIn posts (1000-1400 chars) need their own message.
    """
    messages = []
    header = f"Publish brief for {day_name} {today_iso}\n{len(posts)} post(s) to publish today.\n"
    messages.append(header)

    for i, post in enumerate(posts, 1):
        body = post["draft"] or post["hook"] or "(no draft body)"
        platform = post["platform"]
        publish_url = _publish_url(platform, body)

        lines = [
            f"{i}. {platform}: {post['title'][:80]}",
            "",
            body,
            "",
        ]
        if publish_url:
            lines.append(f"Tap to publish: {publish_url}")
        else:
            lines.append(f"(no share URL for platform {platform})")
        lines.append("Reply `posted` or `skip` to mark this post.")
        lines.append("")
        lines.append(f"Notion: https://www.notion.so/{post['notion_id'].replace('-', '')}")
        messages.append("\n".join(lines))
    return messages


# ═════════════════════════════════════════════════════════════════════════════
# Wake callback
# ═════════════════════════════════════════════════════════════════════════════

def publish_brief_tick() -> None:
    """Heartbeat callback. Fires daily at 07:30 MT. No-op on weekends to
    match the publishing cadence (no posts go out Sat/Sun).
    """
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    today = now.date()
    today_iso = today.isoformat()
    day_name = today.strftime("%A")

    if today.weekday() >= 5:
        logger.info(f"publish_brief_tick: skip (weekend, day={day_name})")
        return

    logger.info(f"publish_brief_tick: start for {day_name} {today_iso}")

    try:
        from skills.forge_cli.notion_client import NotionClient
        notion_secret = os.environ.get("NOTION_SECRET") or os.environ.get("NOTION_API_KEY")
        notion = NotionClient(secret=notion_secret)
    except Exception as e:
        logger.error(f"publish_brief_tick: cannot open Notion client: {e}")
        return

    try:
        posts = _fetch_todays_queued(notion, today_iso)
    except Exception as e:
        logger.error(f"publish_brief_tick: Content Board fetch failed: {e}")
        return

    chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
    if not chat_id:
        logger.warning("publish_brief_tick: no OWNER_TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID; skip")
        return

    try:
        from notifier import send_message, send_message_returning_id
    except Exception as e:
        logger.error(f"publish_brief_tick: notifier import failed: {e}")
        return

    if not posts:
        if _brief_already_sent(today_iso):
            logger.info("publish_brief_tick: empty brief already sent today, skip")
            return
        send_message(str(chat_id), _format_empty_brief(today_iso, day_name))
        _mark_brief_sent(today_iso)
        logger.info(f"publish_brief_tick: sent empty brief")
        return

    if _brief_already_sent(today_iso):
        logger.info("publish_brief_tick: full brief already sent today, skip")
        return

    # Atlas M1: evict stale dict entries (24h+) before populating new ones.
    import time as _time
    from state import _PUBLISH_BRIEF_WINDOWS
    cutoff = _time.time() - 86400
    stale = [k for k, v in _PUBLISH_BRIEF_WINDOWS.items() if v.get("ts_sent", 0) < cutoff]
    for k in stale:
        _PUBLISH_BRIEF_WINDOWS.pop(k, None)
    if stale:
        logger.info(f"publish_brief_tick: evicted {len(stale)} stale brief windows")

    messages = _format_full_brief(today_iso, day_name, posts)

    # Send header (no dict entry; nothing to mark on the header).
    try:
        send_message(str(chat_id), messages[0])
    except Exception as e:
        logger.warning(f"publish_brief_tick: header send failed: {e}")

    # Send per-post messages and capture msg_ids into the dict.
    populated = 0
    for post, msg in zip(posts, messages[1:]):
        try:
            msg_id = send_message_returning_id(str(chat_id), msg)
        except Exception as e:
            logger.warning(f"publish_brief_tick: per-post send failed: {e}")
            msg_id = None
        if msg_id is not None:
            _PUBLISH_BRIEF_WINDOWS[msg_id] = {
                "notion_page_id": post["notion_id"],
                "title": post["title"],
                "platform": post["platform"],
                "chat_id": str(chat_id),
                "ts_sent": _time.time(),
            }
            populated += 1

    _mark_brief_sent(today_iso)
    logger.info(
        f"publish_brief_tick: sent {len(messages)} messages "
        f"({len(posts)} posts, {populated} reply windows opened)"
    )
