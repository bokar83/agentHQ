"""
studio_blotato_publisher.py - Studio M4.

Heartbeat tick that publishes Studio Pipeline DB records to their
scheduled platform via the Blotato API. Runs daily at 09:00 MT.

Logic:
  1. Query Notion Studio Pipeline DB for records where:
       Status = scheduled  AND  Scheduled Date = today
  2. For each record, in order:
       a. Resolve channel + platform → Blotato account ID from env.
       b. Flip Status = publishing BEFORE the API call (idempotency guard:
          a crash between POST and postSubmissionId write leaves the record
          in 'publishing', not 'scheduled', so the next tick skips it and
          avoids a double-post).
       c. Call BlotatoPublisher.publish() with Draft text + Asset URL.
       d. Persist postSubmissionId to Pipeline DB Submission ID field.
       e. Poll until terminal.
       f. On published: flip Status = posted, write Posted URL + Posted Date.
       g. On failed: flip Status = publish-failed, alert Telegram.
       h. On timeout: leave Status = publishing (next tick re-polls via TTL).
  3. Send Telegram summary.

Dry-run mode: --dry-run or STUDIO_PUBLISHER_DRY_RUN=1 logs actions without
calling Blotato or flipping Notion statuses.

Blotato account IDs per channel × platform (set in .env):
  BLOTATO_YT_BAOBAB_ACCOUNT_ID=35697   (YouTube, Under the Baobab)    ✅ set
  BLOTATO_YT_CATALYST_ACCOUNT_ID=35696 (YouTube, AI Catalyst)         ✅ set
  BLOTATO_YT_1STGEN_ACCOUNT_ID=35698   (YouTube, First Gen Money)     ✅ set
  BLOTATO_X_BAOBAB_ACCOUNT_ID=...      (X, Under the Baobab)          ✅ set
  BLOTATO_X_CATALYST_ACCOUNT_ID=...    (X, AI Catalyst)               ✅ set
  BLOTATO_X_1STGEN_ACCOUNT_ID=...      (X, First Gen Money)           ✅ set
  BLOTATO_IG_BAOBAB_ACCOUNT_ID=...     (Instagram, Under the Baobab)  ⏳ pending account creation
  BLOTATO_IG_CATALYST_ACCOUNT_ID=...   (Instagram, AI Catalyst)       ⏳ pending
  BLOTATO_IG_1STGEN_ACCOUNT_ID=...     (Instagram, First Gen Money)   ⏳ pending
  BLOTATO_TT_BAOBAB_ACCOUNT_ID=...     (TikTok, Under the Baobab)     ⏳ pending
  BLOTATO_TT_CATALYST_ACCOUNT_ID=...   (TikTok, AI Catalyst)          ⏳ pending
  BLOTATO_TT_1STGEN_ACCOUNT_ID=...     (TikTok, First Gen Money)      ⏳ pending

Pipeline DB ID: 34ebcf1a-3029-8140-a565-f7c26fe9de86
"""
from __future__ import annotations

import argparse
import logging
import os
import time
from datetime import date, datetime, timezone
from typing import Optional

logger = logging.getLogger("agentsHQ.studio_blotato_publisher")

PIPELINE_DB_ID = os.environ.get(
    "NOTION_STUDIO_PIPELINE_DB_ID",
    "34ebcf1a-3029-8140-a565-f7c26fe9de86",
)
TIMEZONE = os.environ.get("HEARTBEAT_TIMEZONE", "America/Denver")

# A record stuck in Status=publishing for this long gets promoted to
# publish-failed on the next tick (in-flight orphan guard).
PUBLISHING_TTL_HOURS = 24

# Studio Pipeline DB property names (from M1 schema, 20 properties).
PROP_STATUS = "Status"
PROP_CHANNEL = "Channel"
PROP_PLATFORM = "Platform"
PROP_DRAFT = "Draft"
PROP_ASSET_URL = "Asset URL"
PROP_SCHEDULED_DATE = "Scheduled Date"
PROP_POSTED_DATE = "Posted Date"
PROP_POSTED_URL = "Posted URL"
PROP_SUBMISSION_ID = "Submission ID"
PROP_QA_NOTES = "QA notes"

# Channel name → env-var channel code.
_CHANNEL_CODE: dict[str, str] = {
    "Under the Baobab": "BAOBAB",
    "AI Catalyst": "CATALYST",
    "First Generation Money": "1STGEN",
}

# Notion platform name → env-var platform suffix (matches .env naming).
# YouTube: BLOTATO_YT_{CH}_ACCOUNT_ID (legacy YT prefix, handled separately)
# Others: BLOTATO_{CH}_{PLATFORM}_ACCOUNT_ID
_PLATFORM_CODE: dict[str, str] = {
    "YouTube": "YT",
    "X": "X",
    "Instagram": "INSTAGRAM",
    "TikTok": "TIKTOK",
}


def _account_id_for(channel: str, platform: str) -> Optional[str]:
    """Return Blotato account ID for channel x platform, or None if unset.

    Matches .env naming: BLOTATO_{CHANNEL}_{PLATFORM_FULL}_ACCOUNT_ID
    e.g. BLOTATO_BAOBAB_INSTAGRAM_ACCOUNT_ID, BLOTATO_YT_BAOBAB_ACCOUNT_ID
    YouTube uses YT prefix per existing .env convention.
    """
    ch = _CHANNEL_CODE.get(channel)
    pl = _PLATFORM_CODE.get(platform)
    if not ch or not pl:
        return None
    if platform == "YouTube":
        return os.environ.get(f"BLOTATO_YT_{ch}_ACCOUNT_ID")
    return os.environ.get(f"BLOTATO_{ch}_{pl}_ACCOUNT_ID")


def _env_key_for(channel: str, platform: str) -> str:
    """Return the env var name for this channel x platform pair."""
    ch = _CHANNEL_CODE.get(channel, "?")
    pl = _PLATFORM_CODE.get(platform, "?")
    return f"BLOTATO_{pl}_{ch}_ACCOUNT_ID"


def _today_str() -> str:
    try:
        import pytz
        tz = pytz.timezone(TIMEZONE)
        return datetime.now(tz).strftime("%Y-%m-%d")
    except Exception:
        return date.today().isoformat()


def _notion_client():
    from notion_client import Client
    api_key = os.environ.get("NOTION_API_KEY")
    if not api_key:
        raise ValueError("NOTION_API_KEY not set")
    return Client(auth=api_key)


def _prop_text(record: dict, name: str) -> str:
    """Extract plain text value from a Notion property."""
    prop = record.get("properties", {}).get(name, {})
    ptype = prop.get("type", "")
    if ptype == "rich_text":
        return "".join(p.get("plain_text", "") for p in prop.get("rich_text", []))
    if ptype == "title":
        return "".join(p.get("plain_text", "") for p in prop.get("title", []))
    if ptype in ("select", "status"):
        sel = prop.get(ptype) or {}
        return sel.get("name", "")
    if ptype == "url":
        return prop.get("url") or ""
    if ptype == "date":
        return (prop.get("date") or {}).get("start") or ""
    return ""


def _query_db(notion, db_id: str, filter_obj: dict) -> list[dict]:
    """Paginated query of a Notion database."""
    results: list[dict] = []
    cursor = None
    while True:
        kwargs: dict = {"database_id": db_id, "filter": filter_obj}
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = notion.databases.query(**kwargs)
        results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return results


def _flip_status(notion, page_id: str, status: str) -> None:
    notion.pages.update(
        page_id=page_id,
        properties={PROP_STATUS: {"status": {"name": status}}},
    )


def _write_props(notion, page_id: str, props: dict) -> None:
    notion.pages.update(page_id=page_id, properties=props)


def _send_telegram(msg: str) -> None:
    try:
        from notifier import send_message
        send_message(msg)
    except Exception as e:
        logger.warning(f"Telegram send failed: {e}")


def _clear_orphaned_publishing(notion, dry_run: bool) -> int:
    """Promote stuck publishing records to publish-failed after TTL."""
    records = _query_db(notion, PIPELINE_DB_ID, {
        "property": PROP_STATUS,
        "status": {"equals": "publishing"},
    })
    promoted = 0
    now_utc = datetime.now(timezone.utc)
    for rec in records:
        page_id = rec["id"]
        last_edited = rec.get("last_edited_time", "")
        if not last_edited:
            continue
        try:
            edited_dt = datetime.fromisoformat(last_edited.replace("Z", "+00:00"))
        except Exception:
            continue
        age_h = (now_utc - edited_dt).total_seconds() / 3600
        if age_h < PUBLISHING_TTL_HOURS:
            continue
        channel = _prop_text(rec, PROP_CHANNEL)
        platform = _prop_text(rec, PROP_PLATFORM)
        logger.warning(
            f"STUDIO PUBLISHER: orphan {page_id} ({channel}/{platform}, "
            f"age={age_h:.1f}h) → publish-failed"
        )
        if not dry_run:
            _flip_status(notion, page_id, "publish-failed")
            _send_telegram(
                f"⚠️ Studio Publisher: {channel}/{platform} stuck in publishing "
                f"for {age_h:.1f}h → publish-failed. Check Blotato dashboard."
            )
        promoted += 1
    return promoted


def studio_blotato_publisher_tick(dry_run: bool = False) -> dict:
    """Publish all records scheduled for today.

    Returns summary dict: {date, scheduled, published, failed, skipped, orphans_promoted}.
    Called by heartbeat at 09:00 MT or directly via __main__.
    """
    from blotato_publisher import BlotatoPublisher, NOTION_TO_BLOTATO_PLATFORM

    notion = _notion_client()
    today = _today_str()
    logger.info(f"STUDIO PUBLISHER: tick start date={today} dry_run={dry_run}")

    orphans = _clear_orphaned_publishing(notion, dry_run)

    records = _query_db(notion, PIPELINE_DB_ID, {
        "and": [
            {"property": PROP_STATUS, "status": {"equals": "scheduled"}},
            {"property": PROP_SCHEDULED_DATE, "date": {"equals": today}},
        ]
    })
    logger.info(f"STUDIO PUBLISHER: {len(records)} record(s) scheduled for {today}")

    if not records:
        return {"date": today, "scheduled": 0, "published": 0, "failed": 0,
                "skipped": 0, "orphans_promoted": orphans}

    publisher = BlotatoPublisher() if not dry_run else None
    published = failed = skipped = 0
    summaries: list[str] = []

    for rec in records:
        page_id = rec["id"]
        channel = _prop_text(rec, PROP_CHANNEL)
        platform = _prop_text(rec, PROP_PLATFORM)
        draft = _prop_text(rec, PROP_DRAFT)
        asset_url = _prop_text(rec, PROP_ASSET_URL)

        account_id = _account_id_for(channel, platform)
        if not account_id:
            env_key = _env_key_for(channel, platform)
            logger.warning(
                f"STUDIO PUBLISHER: skip {page_id} ({channel}/{platform}) — "
                f"{env_key} not set"
            )
            summaries.append(f"⏭️ {channel}/{platform}: no account ID ({env_key} not set)")
            skipped += 1
            continue

        if not draft and not asset_url:
            logger.warning(f"STUDIO PUBLISHER: skip {page_id} — no Draft and no Asset URL")
            summaries.append(f"⏭️ {channel}/{platform}: missing Draft + Asset URL")
            skipped += 1
            continue

        text = draft or f"New content from {channel}."
        media_urls = [asset_url] if asset_url else []

        if dry_run:
            logger.info(
                f"STUDIO PUBLISHER [DRY RUN]: {page_id} ({channel}/{platform}) "
                f"account={account_id} text_len={len(text)} media={media_urls}"
            )
            summaries.append(f"🔍 [DRY RUN] {channel}/{platform}: would publish (account={account_id})")
            continue

        # Step b: idempotency flip before API call.
        try:
            _flip_status(notion, page_id, "publishing")
        except Exception as e:
            logger.error(f"STUDIO PUBLISHER: cannot flip {page_id} to publishing: {e}")
            skipped += 1
            continue

        # Step c: publish.
        blotato_platform = NOTION_TO_BLOTATO_PLATFORM.get(platform, platform.lower())
        try:
            submission_id = publisher.publish(
                text=text,
                account_id=account_id,
                platform=blotato_platform,
                media_urls=media_urls,
            )
        except Exception as e:
            logger.error(f"STUDIO PUBLISHER: publish error {page_id} ({channel}/{platform}): {e}")
            _flip_status(notion, page_id, "publish-failed")
            _write_props(notion, page_id, {
                PROP_QA_NOTES: {"rich_text": [{"text": {"content": f"Publish error: {e}"}}]},
            })
            _send_telegram(f"❌ Studio Publisher: {channel}/{platform} — {e}")
            summaries.append(f"❌ {channel}/{platform}: publish error — {e}")
            failed += 1
            continue

        # Step d: persist submission ID.
        try:
            _write_props(notion, page_id, {
                PROP_SUBMISSION_ID: {"rich_text": [{"text": {"content": submission_id}}]},
            })
        except Exception as e:
            logger.warning(f"STUDIO PUBLISHER: could not write submission_id {page_id}: {e}")

        # Step e: poll.
        try:
            result = publisher.poll_until_terminal(submission_id)
        except Exception as e:
            logger.error(f"STUDIO PUBLISHER: poll error {submission_id}: {e}")
            _send_telegram(
                f"⚠️ Studio Publisher: {channel}/{platform} poll error — {e}. "
                f"Record left in publishing."
            )
            continue

        if result.ok:
            posted_date = datetime.now(timezone.utc).date().isoformat()
            props_update: dict = {
                PROP_STATUS: {"status": {"name": "posted"}},
                PROP_POSTED_DATE: {"date": {"start": posted_date}},
            }
            if result.public_url:
                props_update[PROP_POSTED_URL] = {"url": result.public_url}
            _write_props(notion, page_id, props_update)
            published += 1
            summaries.append(
                f"✅ {channel}/{platform}: posted in {result.elapsed_sec:.1f}s "
                f"— {result.public_url or 'no URL'}"
            )
            logger.info(
                f"STUDIO PUBLISHER: {page_id} ({channel}/{platform}) "
                f"posted in {result.elapsed_sec:.1f}s"
            )
        elif result.status == "failed":
            _flip_status(notion, page_id, "publish-failed")
            _write_props(notion, page_id, {
                PROP_QA_NOTES: {"rich_text": [{"text": {"content": f"Blotato failed: {result.error_message}"}}]},
            })
            _send_telegram(
                f"❌ Studio Publisher: {channel}/{platform} failed — {result.error_message}"
            )
            summaries.append(f"❌ {channel}/{platform}: Blotato failed — {result.error_message}")
            failed += 1
        else:
            # Timeout: leave in publishing for next tick TTL check.
            logger.warning(
                f"STUDIO PUBLISHER: {page_id} ({channel}/{platform}) "
                f"poll timeout — left in publishing"
            )
            summaries.append(f"⏱️ {channel}/{platform}: poll timeout — left in publishing")

    summary = {
        "date": today,
        "scheduled": len(records),
        "published": published,
        "failed": failed,
        "skipped": skipped,
        "orphans_promoted": orphans,
    }

    if not dry_run and summaries:
        lines = [f"📢 Studio Publisher — {today}"] + summaries
        lines.append(
            f"\nTotal: {published} posted / {failed} failed / "
            f"{skipped} skipped / {orphans} orphans cleared"
        )
        _send_telegram("\n".join(lines))

    logger.info(f"STUDIO PUBLISHER: tick done — {summary}")
    return summary


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    parser = argparse.ArgumentParser(
        description="Studio Blotato Publisher — M4 daily publish tick"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would publish without calling Blotato or flipping Notion",
    )
    args = parser.parse_args()
    dry_run = args.dry_run or bool(os.environ.get("STUDIO_PUBLISHER_DRY_RUN", ""))
    if dry_run:
        print("[DRY RUN] No posts sent. No Notion statuses flipped.")
    result = studio_blotato_publisher_tick(dry_run=dry_run)
    print(result)
