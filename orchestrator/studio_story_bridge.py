"""
studio_story_bridge.py -- Bridge between Content Board Story entries and Studio Pipeline DB.

Runs on a heartbeat tick (every 6h). Reads Content Board records where:
  Content Type = Story
  Status = Idea

For each, creates one Pipeline DB record per Studio channel the story maps to
(1stGen, UTB, AIC) based on a lightweight LLM channel-fit classification.

Marks the Content Board record with Source Note update so it is not re-seeded.
Idempotent: checks for existing Pipeline DB record with matching source before
creating a new one.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger("agentsHQ.studio_story_bridge")

_NOTION_TOKEN = (
    os.environ.get("NOTION_SECRET")
    or os.environ.get("NOTION_API_KEY")
    or os.environ.get("NOTION_TOKEN")
    or ""
)
_CONTENT_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
_PIPELINE_DB_ID = os.environ.get("NOTION_STUDIO_PIPELINE_DB_ID", "34ebcf1a-3029-8140-a565-f7c26fe9de86")

CHANNEL_MAP = {
    "1stGen": {
        "channel": "First Gen Money",
        "niche": "first-gen-money",
        "lens": "financial literacy, wealth-building, first-gen immigrant financial reality, class mobility",
    },
    "UTB": {
        "channel": "Under the Baobab",
        "niche": "african-diaspora",
        "lens": "West African diaspora identity, belonging, cultural collision, roots and ambition",
    },
    "AIC": {
        "channel": "AI Catalyst",
        "niche": "ai-for-sme",
        "lens": "AI tools in practice, how Boubacar uses AI to run his firm, practical AI for small business",
    },
}

_HEADERS = {
    "Authorization": f"Bearer {_NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def _get_text(prop: dict) -> str:
    items = prop.get("rich_text") or prop.get("title") or []
    return "".join(t.get("plain_text", "") for t in items)


def _get_select(prop: dict) -> Optional[str]:
    sel = (prop.get("select") or {})
    return sel.get("name")


def _fetch_story_ideas() -> list[dict]:
    """Return Content Board records with Content Type=Story and Status=Idea
    that have not yet been seeded to Studio (no 'studio-seeded' marker in Source Note)."""
    try:
        resp = httpx.post(
            f"https://api.notion.com/v1/databases/{_CONTENT_DB_ID}/query",
            headers=_HEADERS,
            json={
                "filter": {
                    "and": [
                        {"property": "Status", "select": {"equals": "Idea"}},
                        {"property": "Content Type", "select": {"equals": "Story"}},
                    ]
                },
                "page_size": 50,
            },
            timeout=20,
        )
        resp.raise_for_status()
        results = []
        for p in resp.json().get("results", []):
            props = p.get("properties", {})
            source_note = _get_text(props.get("Source Note", {}))
            if "studio-seeded" in source_note:
                continue  # already seeded
            title = _get_text(props.get("Title", {}))
            draft = _get_text(props.get("Draft", {}))
            hook = _get_text(props.get("Hook", {}))
            results.append({
                "notion_id": p["id"],
                "title": title,
                "body": draft or hook,
                "source_note": source_note,
            })
        return results
    except Exception as e:
        logger.warning(f"studio_story_bridge: fetch story ideas failed: {e}")
        return []


def _classify_channels(title: str, body: str) -> list[str]:
    """Use LLM to determine which Studio channels this story fits.
    Returns list of channel codes from CHANNEL_MAP keys."""
    try:
        import litellm
        prompt = (
            f"You are classifying a personal story/observation for channel fit.\n\n"
            f"Story:\nTitle: {title}\n{body[:800]}\n\n"
            f"Available channels:\n"
            f"1stGen (First Gen Money): {CHANNEL_MAP['1stGen']['lens']}\n"
            f"UTB (Under the Baobab): {CHANNEL_MAP['UTB']['lens']}\n"
            f"AIC (AI Catalyst): {CHANNEL_MAP['AIC']['lens']}\n\n"
            f"Which channels does this story fit? A story can fit multiple channels.\n"
            f"Reply with ONLY a comma-separated list of codes, e.g.: 1stGen,UTB\n"
            f"If it fits none, reply: NONE"
        )
        resp = litellm.completion(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0,
        )
        raw = resp.choices[0].message.content.strip().upper()
        return [c.strip() for c in raw.split(",") if c.strip() in CHANNEL_MAP]
    except Exception as e:
        logger.warning(f"studio_story_bridge: channel classification failed: {e}; defaulting to all")
        return list(CHANNEL_MAP.keys())


def _pipeline_record_exists(content_board_id: str) -> bool:
    """Check if Pipeline DB already has a record sourced from this Content Board entry."""
    try:
        resp = httpx.post(
            f"https://api.notion.com/v1/databases/{_PIPELINE_DB_ID}/query",
            headers=_HEADERS,
            json={
                "filter": {
                    "property": "Source URL",
                    "url": {"equals": f"notion://content-board/{content_board_id}"},
                },
                "page_size": 1,
            },
            timeout=10,
        )
        return len(resp.json().get("results", [])) > 0
    except Exception:
        return False


def _create_pipeline_record(story: dict, channel_code: str) -> Optional[str]:
    """Create one Pipeline DB record for a given channel."""
    ch = CHANNEL_MAP[channel_code]
    title = f"[Story] {story['title'][:120]}"
    hook = story["body"][:500] if story["body"] else story["title"]
    try:
        resp = httpx.post(
            "https://api.notion.com/v1/pages",
            headers=_HEADERS,
            json={
                "parent": {"database_id": _PIPELINE_DB_ID},
                "properties": {
                    "Title": {"title": [{"text": {"content": title}}]},
                    "Status": {"select": {"name": "scouted"}},
                    "Channel": {"select": {"name": ch["channel"]}},
                    "Niche tag": {"select": {"name": ch["niche"]}},
                    "Hook": {"rich_text": [{"text": {"content": hook}}]},
                    "Source URL": {"url": f"notion://content-board/{story['notion_id']}"},
                    "QA notes": {"rich_text": [{"text": {"content": (
                        f"Source: Boubacar personal story signal from Content Board.\n"
                        f"Lens: {ch['lens']}\n"
                        f"Adapt the raw story to the {ch['channel']} channel voice and audience. "
                        f"Do not fabricate details. Use the story as a brief, not a script."
                    )}}]},
                    "Length target": {"select": {"name": "short (<60s)"}},
                },
            },
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json().get("id")
    except Exception as e:
        logger.error(f"studio_story_bridge: create pipeline record failed for {story['notion_id']} / {channel_code}: {e}")
        return None


def _mark_seeded(notion_id: str, channels: list[str], pipeline_ids: list[str]) -> None:
    """Update Content Board Source Note to mark as seeded."""
    try:
        note = (
            f"studio-seeded 2026 → channels: {', '.join(channels)}. "
            f"Pipeline records: {', '.join(pipeline_ids[:3])}. "
            f"Routed for Studio adaptation. Do not re-seed."
        )
        httpx.patch(
            f"https://api.notion.com/v1/pages/{notion_id}",
            headers=_HEADERS,
            json={"properties": {"Source Note": {"rich_text": [{"text": {"content": note[:1000]}}]}}},
            timeout=10,
        )
    except Exception as e:
        logger.warning(f"studio_story_bridge: mark-seeded failed for {notion_id}: {e}")


def studio_story_bridge_tick() -> None:
    """Heartbeat tick. Reads unseed Story entries, classifies, seeds Pipeline DB."""
    if not _PIPELINE_DB_ID or not _NOTION_TOKEN:
        logger.warning("studio_story_bridge: NOTION_STUDIO_PIPELINE_DB_ID or token not set")
        return

    stories = _fetch_story_ideas()
    if not stories:
        logger.debug("studio_story_bridge: no unseeded Story entries found")
        return

    logger.info(f"studio_story_bridge: {len(stories)} story entry(s) to process")

    for story in stories:
        if _pipeline_record_exists(story["notion_id"]):
            logger.info(f"studio_story_bridge: already seeded {story['notion_id'][:8]}, skipping")
            continue

        channels = _classify_channels(story["title"], story["body"])
        if not channels:
            logger.info(f"studio_story_bridge: no channel fit for '{story['title'][:50]}', skipping")
            continue

        pipeline_ids = []
        for ch in channels:
            pid = _create_pipeline_record(story, ch)
            if pid:
                pipeline_ids.append(pid)
                logger.info(f"studio_story_bridge: seeded '{story['title'][:40]}' → {CHANNEL_MAP[ch]['channel']} ({pid[:8]})")

        if pipeline_ids:
            _mark_seeded(story["notion_id"], channels, pipeline_ids)

    logger.info("studio_story_bridge: tick complete")
