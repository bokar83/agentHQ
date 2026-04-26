"""
auto_publisher.py - Atlas M7b. Autonomous publish tick.

Heartbeat callback that closes Atlas L3 (Publish loop). Every 5 minutes:

  1. Query Notion Content Board for records where:
       Status = Queued AND Scheduled Date <= today AND Platform in (LinkedIn, X)
  2. For each record, in order:
       a. Flip Status to Publishing in Notion BEFORE the API call.
          This is the idempotency safeguard: if we crash between POST and
          the postSubmissionId write, the next tick sees Status=Publishing
          (not Queued) and skips, preventing a double-post.
       b. Call BlotatoPublisher.publish() to fire the post.
       c. Persist postSubmissionId to Notion's Submission ID field.
       d. Poll until terminal (published or failed or timeout).
       e. On published: flip Status=Posted, write LinkedIn/X Posted URL,
          set Posted Date, write task_outcomes row (Atlas L4 reconcile path).
       f. On failed: flip Status=PublishFailed, write errorMessage to Source
          Note, alert Telegram. Status=PublishFailed blocks the slot from M2
          backfill (audit trail; needs human attention).
       g. On timeout: leave Status=Publishing (next tick will poll the same
          submission), but cap the in-flight time at 24h via TTL check.

Coordination with publish_brief (M1):
  - publish_brief queries Status=Queued AND Scheduled Date=today
  - auto_publisher queries Status=Queued AND Scheduled Date<=today
  - Both will see today's records. publish_brief sends a Telegram brief;
    auto_publisher fires the actual post. This is intentional dual-channel:
    Boubacar sees the brief AND the post lands automatically. After
    auto_publisher flips Status=Publishing, publish_brief no longer sees
    the record (Status changed). No race, no double-publish.

Coordination with griot_scheduler M2 backfill:
  - M2 backfill scans Status=Skipped slots in the yesterday-or-today window
  - PublishFailed records intentionally do NOT get backfilled (they block
    the slot until human attention). Updated in griot_scheduler.py separately.

Built on the Blotato API contract verified end-to-end during M7a smoke test
(2026-04-25 22:01 UTC, LinkedIn 5 sec submit-to-live, X 9 sec).
"""
from __future__ import annotations

import logging
import os
import time
from datetime import date, datetime, timedelta
from typing import Optional

import pytz

logger = logging.getLogger("agentsHQ.auto_publisher")

TIMEZONE = os.environ.get("HEARTBEAT_TIMEZONE", "America/Denver")
CONTENT_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")

# Publishing TTL: if a record sits in Status=Publishing longer than this
# without resolving, the next tick promotes it to PublishFailed. Protects
# against orphaned in-flight rows from a process crash during polling.
PUBLISHING_TTL_HOURS = 24


# ═════════════════════════════════════════════════════════════════════════════
# Notion helpers (mirror publish_brief.py + griot_scheduler.py shape)
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


def _last_edited_time(page) -> Optional[str]:
    return page.get("last_edited_time")


# ═════════════════════════════════════════════════════════════════════════════
# Account ID lookup
# ═════════════════════════════════════════════════════════════════════════════

def _account_id_for_platform(platform: str) -> Optional[str]:
    """Resolve the Blotato accountId env var for a Notion-side platform name."""
    if platform == "LinkedIn":
        return os.environ.get("BLOTATO_LINKEDIN_ACCOUNT_ID")
    if platform == "X":
        return os.environ.get("BLOTATO_X_ACCOUNT_ID")
    if platform == "Facebook":
        return os.environ.get("BLOTATO_FACEBOOK_ACCOUNT_ID")
    if platform == "Instagram":
        return os.environ.get("BLOTATO_INSTAGRAM_ACCOUNT_ID")
    if platform == "TikTok":
        return os.environ.get("BLOTATO_TIKTOK_ACCOUNT_ID")
    if platform == "Threads":
        return os.environ.get("BLOTATO_THREADS_ACCOUNT_ID")
    if platform == "YouTube":
        return os.environ.get("BLOTATO_YOUTUBE_ACCOUNT_ID")
    if platform == "Pinterest":
        return os.environ.get("BLOTATO_PINTEREST_ACCOUNT_ID")
    if platform == "Bluesky":
        return os.environ.get("BLOTATO_BLUESKY_ACCOUNT_ID")
    return None


# ═════════════════════════════════════════════════════════════════════════════
# Fetch eligible records
# ═════════════════════════════════════════════════════════════════════════════

def _fetch_due_queued(notion, today_iso: str) -> list:
    """Return Content Board records where:
      Status = Queued
      Scheduled Date <= today
      Platform contains LinkedIn OR X (or any other supported platform)

    Past-due records (Scheduled Date in the past) are included; they
    represent posts that publish_brief notified Boubacar about but
    he did not tap to publish. M7b auto-publishes them.
    """
    posts = notion.query_database(CONTENT_DB_ID, filter_obj=None)
    due = []
    for p in posts:
        props = p.get("properties", {})
        if _select(props.get("Status", {})) != "Queued":
            continue
        sd = _date_start(props.get("Scheduled Date", {}))
        if not sd:
            continue
        # sd is "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM:SS+OFFSET"; compare date prefix
        if sd[:10] > today_iso:
            continue  # future, not due yet
        platforms = _multi(props.get("Platform", {}))
        for pf in platforms:
            if _account_id_for_platform(pf) is None:
                continue  # no account ID configured for this platform
            due.append({
                "notion_id": p["id"],
                "title": _title(props.get("Title", {})),
                "draft": _text(props.get("Draft", {})),
                "hook": _text(props.get("Hook", {})),
                "platform": pf,
                "scheduled_date": sd[:10],
            })
            break  # one publish per record (first matching platform)
    # Stable order: oldest scheduled first, then platform alpha.
    due.sort(key=lambda r: (r["scheduled_date"], r["platform"], r["notion_id"]))
    return due


def _fetch_stale_publishing(notion, now_utc: datetime) -> list:
    """Return Content Board records stuck in Status=Publishing for >TTL.

    Used at the start of each tick to promote orphaned in-flight rows to
    PublishFailed so they no longer block their slot indefinitely. Runs
    BEFORE _fetch_due_queued to clean up the queue first.
    """
    cutoff = now_utc - timedelta(hours=PUBLISHING_TTL_HOURS)
    posts = notion.query_database(CONTENT_DB_ID, filter_obj=None)
    stale = []
    for p in posts:
        props = p.get("properties", {})
        if _select(props.get("Status", {})) != "Publishing":
            continue
        last_edit = _last_edited_time(p)
        if not last_edit:
            continue
        try:
            last_edit_dt = datetime.fromisoformat(last_edit.replace("Z", "+00:00"))
        except Exception:
            continue
        if last_edit_dt < cutoff:
            stale.append({
                "notion_id": p["id"],
                "title": _title(props.get("Title", {})),
                "submission_id": _text(props.get("Submission ID", {})),
                "last_edited": last_edit,
            })
    return stale


# ═════════════════════════════════════════════════════════════════════════════
# Notion writes (each one self-contained so a failure mid-flow flips a
# specific Status without leaking partial state)
# ═════════════════════════════════════════════════════════════════════════════

def _flip_to_publishing(notion, notion_id: str) -> None:
    """Status=Queued -> Publishing. Idempotency safeguard: must succeed
    BEFORE the Blotato POST call.
    """
    notion.update_page(notion_id, {"Status": {"select": {"name": "Publishing"}}})


def _persist_submission_id(notion, notion_id: str, submission_id: str) -> None:
    """Write postSubmissionId to Notion's Submission ID field.

    Called immediately after a successful Blotato POST. If this write fails
    we log and continue to poll; the next tick will see Status=Publishing
    with no Submission ID and promote to PublishFailed via the TTL path
    (24h orphan cleanup). Better than re-POSTing.
    """
    notion.update_page(notion_id, {
        "Submission ID": {"rich_text": [{"text": {"content": submission_id}}]}
    })


def _flip_to_posted(
    notion, notion_id: str, platform: str, public_url: str, posted_at_iso: str
) -> None:
    """Terminal success: Status=Posted, write platform-specific Posted URL,
    set Posted Date.
    """
    url_field = "LinkedIn Posted URL" if platform == "LinkedIn" else "X Posted URL"
    properties = {
        "Status": {"select": {"name": "Posted"}},
        url_field: {"url": public_url},
        "Posted Date": {"date": {"start": posted_at_iso}},
    }
    notion.update_page(notion_id, properties)


def _flip_to_publish_failed(notion, notion_id: str, error_message: str) -> None:
    """Terminal failure: Status=PublishFailed, append errorMessage to
    Source Note. Slot stays blocked (M2 backfill ignores PublishFailed).
    """
    truncated = (error_message or "")[:1500]
    properties = {
        "Status": {"select": {"name": "PublishFailed"}},
        "Source Note": {"rich_text": [{"text": {"content": f"PublishFailed: {truncated}"}}]},
    }
    notion.update_page(notion_id, properties)


# ═════════════════════════════════════════════════════════════════════════════
# Telegram alert helpers
# ═════════════════════════════════════════════════════════════════════════════

def _telegram_chat_id() -> Optional[str]:
    return os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")


def _alert_posted(title: str, platform: str, public_url: str) -> None:
    chat_id = _telegram_chat_id()
    if not chat_id:
        return
    try:
        from notifier import send_message
        send_message(
            str(chat_id),
            f"Posted (auto): {platform}\n{title[:80]}\n{public_url}",
        )
    except Exception as e:
        logger.warning(f"auto_publisher: posted Telegram notify failed: {e}")


def _alert_failed(title: str, platform: str, error_message: str) -> None:
    chat_id = _telegram_chat_id()
    if not chat_id:
        return
    try:
        from notifier import send_message
        send_message(
            str(chat_id),
            f"Publish FAILED: {platform}\n{title[:80]}\nError: {error_message[:300]}\n"
            f"Status set to PublishFailed; slot blocked until human acts.",
        )
    except Exception as e:
        logger.warning(f"auto_publisher: failed-alert Telegram notify failed: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# Outcome row (Atlas L4 reconcile path)
# ═════════════════════════════════════════════════════════════════════════════

def _write_outcome(crew_name: str, summary: str, success: bool) -> None:
    """Mirror the L4 path used by handlers_approvals.handle_publish_reply.
    Failure-soft: if episodic_memory unreachable, log and continue.
    """
    try:
        from episodic_memory import start_task, complete_task
        outcome = start_task(crew_name=crew_name, plan_summary=summary)
        complete_task(
            outcome.id,
            result_summary=("success" if success else "failed"),
            total_cost_usd=0.0,
        )
    except Exception as e:
        logger.warning(f"auto_publisher: episodic_memory write failed: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# Main wake callback
# ═════════════════════════════════════════════════════════════════════════════

def auto_publisher_tick() -> None:
    """Heartbeat callback. Fires every 5 minutes. 7-day cadence (the
    publishing schedule itself controls when to fire; this tick just executes
    whatever is due). Per-crew gate auto_publisher.enabled controls whether
    this is allowed to act.

    Called by heartbeat._fire after the kill-switch + per-crew checks pass.
    """
    tz = pytz.timezone(TIMEZONE)
    now_local = datetime.now(tz)
    now_utc = datetime.now(pytz.UTC)
    today_iso = now_local.date().isoformat()

    # Open a Notion client.
    try:
        from skills.forge_cli.notion_client import NotionClient
        notion_secret = (
            os.environ.get("NOTION_SECRET")
            or os.environ.get("NOTION_API_KEY")
            or os.environ.get("NOTION_TOKEN")
        )
        notion = NotionClient(secret=notion_secret)
    except Exception as e:
        logger.error(f"auto_publisher: cannot open Notion client: {e}")
        return

    # ─────────────────────────────────────────────────────────────────────
    # Stale-Publishing cleanup (TTL path). Promote orphaned in-flight rows
    # to PublishFailed so their slots stop blocking the queue.
    # ─────────────────────────────────────────────────────────────────────
    try:
        stale = _fetch_stale_publishing(notion, now_utc)
    except Exception as e:
        logger.warning(f"auto_publisher: stale-Publishing scan failed: {e}")
        stale = []

    for row in stale:
        try:
            _flip_to_publish_failed(
                notion,
                row["notion_id"],
                f"Orphaned in Publishing for >{PUBLISHING_TTL_HOURS}h "
                f"(submission_id={row['submission_id'] or 'unknown'}). "
                f"Last edited {row['last_edited']}. Promoted by TTL cleanup.",
            )
            _alert_failed(row["title"], "(unknown)", f"Orphaned in Publishing >{PUBLISHING_TTL_HOURS}h")
            _write_outcome("auto_publisher", f"TTL-orphan {row['title'][:60]}", success=False)
            logger.warning(
                f"auto_publisher: promoted stale Publishing row {row['notion_id']} "
                f"({row['title'][:60]}) to PublishFailed"
            )
        except Exception as e:
            logger.error(f"auto_publisher: stale cleanup failed for {row['notion_id']}: {e}")

    # ─────────────────────────────────────────────────────────────────────
    # Main publish loop.
    # ─────────────────────────────────────────────────────────────────────
    try:
        due = _fetch_due_queued(notion, today_iso)
    except Exception as e:
        logger.error(f"auto_publisher: due-fetch failed: {e}")
        return

    if not due:
        logger.debug("auto_publisher: no due records")
        return

    logger.info(f"auto_publisher: {len(due)} due record(s) to publish")

    # Open the publisher once, reuse the httpx client across records.
    try:
        from blotato_publisher import BlotatoPublisher
        publisher = BlotatoPublisher()
    except Exception as e:
        logger.error(f"auto_publisher: BlotatoPublisher init failed: {e}")
        return

    posted_count = 0
    failed_count = 0
    timeout_count = 0

    try:
        for rec in due:
            notion_id = rec["notion_id"]
            title = rec["title"]
            platform = rec["platform"]
            text = rec["draft"] or rec["hook"]

            if not text or not text.strip():
                logger.warning(
                    f"auto_publisher: record {notion_id} ({title[:50]}) has no Draft "
                    f"or Hook text; flipping to PublishFailed"
                )
                try:
                    _flip_to_publish_failed(notion, notion_id, "No Draft or Hook text in Notion record")
                    _alert_failed(title, platform, "No Draft or Hook text")
                    _write_outcome("auto_publisher", f"empty-text {title[:60]}", success=False)
                    failed_count += 1
                except Exception as e:
                    logger.error(f"auto_publisher: empty-text flip failed for {notion_id}: {e}")
                continue

            account_id = _account_id_for_platform(platform)
            if not account_id:
                logger.warning(
                    f"auto_publisher: no Blotato account ID configured for "
                    f"platform {platform!r}, skipping {notion_id}"
                )
                continue

            # Step 1 (idempotency safeguard): flip Status to Publishing
            # BEFORE the Blotato POST. If this fails, we do NOT POST; the
            # record stays Queued and the next tick retries.
            try:
                _flip_to_publishing(notion, notion_id)
            except Exception as e:
                logger.error(
                    f"auto_publisher: pre-POST Status=Publishing flip failed "
                    f"for {notion_id}: {e}"
                )
                continue

            # Step 2: Blotato POST.
            submission_id = None
            try:
                submission_id = publisher.publish(
                    text=text,
                    account_id=account_id,
                    platform=platform,
                )
            except Exception as e:
                logger.error(
                    f"auto_publisher: Blotato POST failed for {notion_id} ({platform}): {e}"
                )
                try:
                    _flip_to_publish_failed(notion, notion_id, f"Blotato POST error: {e}")
                    _alert_failed(title, platform, str(e))
                    _write_outcome("auto_publisher", f"post-fail {title[:60]}", success=False)
                except Exception as e2:
                    logger.error(f"auto_publisher: PublishFailed flip after POST error failed: {e2}")
                failed_count += 1
                continue

            # Step 3: persist postSubmissionId immediately (idempotency).
            try:
                _persist_submission_id(notion, notion_id, submission_id)
            except Exception as e:
                # Logged but non-fatal: poll still proceeds. TTL cleanup will
                # promote to PublishFailed later if poll itself crashes.
                logger.warning(
                    f"auto_publisher: Submission ID persist failed for {notion_id}: {e}"
                )

            # Step 4: poll until terminal.
            result = publisher.poll_until_terminal(submission_id)

            # Step 5: terminal-state Notion write.
            if result.ok:
                posted_at_iso = datetime.now(pytz.UTC).isoformat()
                try:
                    _flip_to_posted(
                        notion, notion_id, platform, result.public_url or "", posted_at_iso
                    )
                    _alert_posted(title, platform, result.public_url or "")
                    _write_outcome("auto_publisher", f"posted {platform} {title[:50]}", success=True)
                    posted_count += 1
                except Exception as e:
                    logger.error(
                        f"auto_publisher: Posted-flip failed for {notion_id}: {e}. "
                        f"Post is LIVE on {platform} at {result.public_url} but Notion "
                        f"row stuck in Publishing. TTL cleanup will eventually flip."
                    )
            elif result.status == "failed":
                err = result.error_message or "unknown failure"
                try:
                    _flip_to_publish_failed(notion, notion_id, f"Blotato status=failed: {err}")
                    _alert_failed(title, platform, err)
                    _write_outcome("auto_publisher", f"failed {title[:60]}", success=False)
                    failed_count += 1
                except Exception as e:
                    logger.error(f"auto_publisher: PublishFailed flip after Blotato fail: {e}")
            else:
                # Timeout. Leave Status=Publishing with submission_id persisted.
                # Next tick's stale-Publishing cleanup will catch it after TTL.
                logger.warning(
                    f"auto_publisher: poll timeout for {notion_id} "
                    f"(submission_id={submission_id}); leaving Status=Publishing "
                    f"for next tick or TTL"
                )
                timeout_count += 1
    finally:
        publisher.close()

    logger.info(
        f"auto_publisher: tick done posted={posted_count} failed={failed_count} "
        f"timeout={timeout_count} stale_promoted={len(stale)}"
    )
