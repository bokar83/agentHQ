"""
griot_signal_brief.py -- LéGroit weekly theme detection + Signal Brief.

Fires every Monday at 09:00 MT. Reads the last 7 days of:
  - Telegram messages stored in chat_artifacts (user-side messages only)
  - Content Board Story entries created in the last 7 days
  - task_outcomes crew logs (what Boubacar asked about repeatedly)

Passes to Claude Haiku for theme extraction. Returns top 3 recurring themes
with one draft post per theme. Sends to Boubacar via Telegram.

This is the intelligence upgrade: LéGroit notices what Boubacar keeps returning
to, even when Boubacar doesn't frame it as a content idea.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import pytz

logger = logging.getLogger("agentsHQ.griot_signal_brief")

TIMEZONE = os.environ.get("HEARTBEAT_TIMEZONE", "America/Denver")
_NOTION_TOKEN = (
    os.environ.get("NOTION_SECRET")
    or os.environ.get("NOTION_API_KEY")
    or os.environ.get("NOTION_TOKEN")
    or ""
)
_CONTENT_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")


def _fetch_recent_story_entries(days: int = 7) -> list[str]:
    """Fetch Story-tagged Content Board entries from the last N days."""
    try:
        import httpx
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        resp = httpx.post(
            f"https://api.notion.com/v1/databases/{_CONTENT_DB_ID}/query",
            headers={
                "Authorization": f"Bearer {_NOTION_TOKEN}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            json={
                "filter": {"property": "Content Type", "select": {"equals": "Story"}},
                "sorts": [{"timestamp": "created_time", "direction": "descending"}],
                "page_size": 20,
            },
            timeout=20,
        )
        snippets = []
        for p in resp.json().get("results", []):
            created = p.get("created_time", "")
            if created < cutoff:
                continue
            props = p.get("properties", {})
            title_arr = props.get("Title", {}).get("title", [])
            title = title_arr[0]["plain_text"] if title_arr else ""
            draft_arr = props.get("Draft", {}).get("rich_text", [])
            draft = "".join(t["plain_text"] for t in draft_arr)[:300]
            if title or draft:
                snippets.append(f"STORY: {title} — {draft}")
        return snippets
    except Exception as e:
        logger.warning(f"griot_signal_brief: story fetch failed: {e}")
        return []


def _fetch_recent_chat_messages(days: int = 7) -> list[str]:
    """Fetch recent user-side chat_artifacts messages from Postgres."""
    try:
        import psycopg2
        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            return []
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cur.execute(
            """
            SELECT content FROM chat_artifacts
            WHERE role = 'user'
              AND created_at >= %s
              AND content IS NOT NULL
              AND length(content) > 30
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (cutoff,),
        )
        rows = cur.fetchall()
        conn.close()
        return [r[0][:200] for r in rows if r[0]]
    except Exception as e:
        logger.warning(f"griot_signal_brief: chat fetch failed: {e}")
        return []


def _extract_themes_and_drafts(snippets: list[str]) -> Optional[str]:
    """Pass snippets to Claude Haiku. Returns formatted Signal Brief or None."""
    if not snippets:
        return None
    try:
        import litellm
        combined = "\n\n".join(snippets[:30])
        prompt = (
            "You are LéGroit, Boubacar Barry's content intelligence layer.\n\n"
            "Below are snippets from Boubacar's conversations and story inputs over the past 7 days.\n"
            "Your job: find the top 3 themes he kept returning to — things he repeated, "
            "struggled with, or clearly cares about deeply.\n\n"
            "For each theme:\n"
            "1. Name it in 5 words or fewer\n"
            "2. One sentence: why this is showing up repeatedly for him right now\n"
            "3. One draft post (X-format, under 280 chars, his voice: direct, no hedging, "
            "ends on a statement not a question, zero em-dashes)\n\n"
            "HARD RULE: Do not fabricate stories. If you cannot find 3 real themes, return fewer.\n\n"
            f"SNIPPETS:\n{combined}\n\n"
            "FORMAT YOUR RESPONSE EXACTLY LIKE THIS:\n"
            "THEME 1: [name]\n"
            "WHY NOW: [one sentence]\n"
            "DRAFT: [post under 280 chars]\n\n"
            "THEME 2: ...\n"
            "THEME 3: ..."
        )
        resp = litellm.completion(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"griot_signal_brief: LLM theme extraction failed: {e}")
        return None


def _send_brief(brief_text: str) -> None:
    try:
        from notifier import send_message  # type: ignore[import]
        chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
        if not chat_id:
            return
        msg = (
            "Weekly Signal Brief from LéGroit:\n\n"
            "These are the themes you kept returning to this week. "
            "Each has a draft post ready when you want it.\n\n"
            f"{brief_text}\n\n"
            "Reply with a theme number to develop any of these further."
        )
        send_message(str(chat_id), msg)
        logger.info("griot_signal_brief: signal brief sent")
    except Exception as e:
        logger.warning(f"griot_signal_brief: Telegram send failed: {e}")


def griot_signal_brief_tick() -> None:
    """Fires every Monday at 09:00 MT. Builds and sends the weekly Signal Brief."""
    if os.environ.get("SIGNAL_BRIEF_ENABLED", "1") == "0":
        return

    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    if now.weekday() != 0:  # 0 = Monday
        logger.debug(f"griot_signal_brief: skipping on {now.strftime('%A')}")
        return

    logger.info("griot_signal_brief: building weekly signal brief")

    story_snippets = _fetch_recent_story_entries(days=7)
    chat_snippets = _fetch_recent_chat_messages(days=7)
    all_snippets = story_snippets + chat_snippets

    if not all_snippets:
        logger.info("griot_signal_brief: no snippets found this week, skipping")
        return

    brief = _extract_themes_and_drafts(all_snippets)
    if not brief:
        logger.warning("griot_signal_brief: theme extraction returned nothing")
        return

    _send_brief(brief)
