"""
scheduler.py — Catalyst Daily Ignition
======================================
This module runs a background thread that triggers the Hunter Agent
every morning at 6:00 AM MT.
"""

import os
import sys
import json
import time
import threading
import logging
from datetime import datetime, time as dtime
import pytz

logger = logging.getLogger("agentsHQ.scheduler")

# Resolve docs/ directory -- works both locally and inside Docker (/app/docs/)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DOCS_DIR = os.path.join(_SCRIPT_DIR, "docs")
if not os.path.isdir(_DOCS_DIR):
    # Fallback: sibling of script dir (local dev layout: orchestrator/../docs)
    _DOCS_DIR = os.path.join(os.path.dirname(_SCRIPT_DIR), "docs")

# Configuration
TARGET_HOUR = 6
TARGET_MINUTE = 0
TIMEZONE = os.environ.get("GENERIC_TIMEZONE", "America/Denver")

def _send_telegram_alert(message: str):
    """Send a Telegram message to the owner as a dead-man's switch alert."""
    try:
        import httpx
        token = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("OWNER_TELEGRAM_CHAT_ID")
        if token and chat_id:
            httpx.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message},
                timeout=10,
            )
    except Exception as e:
        logger.error(f"CRON: Failed to send Telegram alert: {e}")


def _get_today_quote() -> dict:
    """Load quote bank and return today's quote by day-of-year rotation."""
    bank_path = os.path.join(_DOCS_DIR, "quote_bank.json")
    fallback = {"text": "Do the work. Especially when you don't feel like it.", "author": "Steven Pressfield"}
    try:
        with open(bank_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        quotes = data.get("quotes", [])
        if not quotes:
            return fallback
        day_of_year = datetime.now().timetuple().tm_yday
        return quotes[day_of_year % len(quotes)]
    except Exception as e:
        logger.error(f"QUOTE: Failed to load quote bank: {e}")
        return fallback


def _update_notion_quote_block(block_id: str, quote: dict) -> bool:
    """PATCH a single Notion callout block with today's quote text."""
    try:
        import httpx
        token = (os.environ.get("NOTION_API_KEY")
                 or os.environ.get("NOTION_TOKEN")
                 or os.environ.get("NOTION_SECRET"))
        if not token:
            logger.error("QUOTE: No Notion token found (tried NOTION_API_KEY, NOTION_TOKEN, NOTION_SECRET).")
            return False
        text = f"\"{quote['text']}\" -- {quote['author']} \u00b7 Quote rotates daily"
        payload = {
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
        resp = httpx.patch(
            f"https://api.notion.com/v1/blocks/{block_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )
        if resp.status_code == 200:
            return True
        logger.error(f"QUOTE: Notion block {block_id} update failed: {resp.status_code} {resp.text[:200]}")
        return False
    except Exception as e:
        logger.error(f"QUOTE: Exception updating Notion block {block_id}: {e}")
        return False


def _discover_quote_block_id(page_id: str, token: str) -> str | None:
    """Find the first gray_bg callout block on a page -- that's the quote block."""
    try:
        import httpx
        resp = httpx.get(
            f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=20",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        for block in resp.json().get("results", []):
            if block.get("type") == "callout":
                color = block.get("callout", {}).get("color", "")
                if color == "gray_background":
                    return block["id"]
        return None
    except Exception as e:
        logger.error(f"QUOTE: Block discovery failed for page {page_id}: {e}")
        return None


def _get_or_discover_block_ids(token: str) -> dict:
    """Load cached block IDs, or discover and save them."""
    cache_path = os.path.join(_DOCS_DIR, "quote_block_ids.json")

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                ids = json.load(f)
            if ids.get("agentsHQ_quote_block_id") and ids.get("forge_quote_block_id"):
                return ids
        except Exception:
            pass

    logger.info("QUOTE: Discovering quote block IDs...")
    ids = {
        "agentsHQ_quote_block_id": _discover_quote_block_id("327bcf1a-3029-80b7-9b1e-d77f94c9c61c", token),
        "forge_quote_block_id": _discover_quote_block_id("249bcf1a-3029-807f-86e8-fb97e2671154", token),
    }
    try:
        with open(cache_path, "w") as f:
            json.dump(ids, f, indent=2)
        logger.info(f"QUOTE: Block IDs saved to {cache_path}")
    except Exception as e:
        logger.warning(f"QUOTE: Could not save block ID cache: {e}")
    return ids


def _run_quote_rotation():
    """Update daily quote on agentsHQ + The Forge 2.0, then send to Telegram."""
    token = (os.environ.get("NOTION_API_KEY")
             or os.environ.get("NOTION_TOKEN")
             or os.environ.get("NOTION_SECRET"))
    if not token:
        logger.error("QUOTE: No Notion token found -- skipping quote rotation.")
        return

    quote = _get_today_quote()
    logger.info(f"QUOTE: Today's quote: \"{quote['text']}\" -- {quote['author']}")

    block_ids = _get_or_discover_block_ids(token)

    agentshq_id = block_ids.get("agentsHQ_quote_block_id")
    forge_id = block_ids.get("forge_quote_block_id")

    results = []
    if agentshq_id:
        ok = _update_notion_quote_block(agentshq_id, quote)
        results.append(f"agentsHQ: {'ok' if ok else 'FAILED'}")
    else:
        results.append("agentsHQ: block ID not found")

    if forge_id:
        ok = _update_notion_quote_block(forge_id, quote)
        results.append(f"The Forge: {'ok' if ok else 'FAILED'}")
    else:
        results.append("The Forge: block ID not found")

    status = " | ".join(results)
    logger.info(f"QUOTE: Rotation complete. {status}")

    telegram_msg = (
        f"💬 *Quote of the Day*\n\n"
        f"_{quote['text']}_\n\n"
        f"-- {quote['author']}\n\n"
        f"Have a sharp one. agentsHQ"
    )
    _send_telegram_alert(telegram_msg)


def _run_kpi_refresh():
    """Run forge kpi refresh to update all Notion KPI callout blocks."""
    try:
        from skills.forge_cli.forge import kpi_refresh
        kpi_refresh()
        logger.info("CRON: KPI refresh complete.")
    except Exception as e:
        logger.error(f"CRON: KPI refresh failed: {e}")
        _send_telegram_alert(
            f"agentsHQ ALERT: 6am KPI refresh failed. The Forge dashboard may be stale.\nError: {e}"
        )


def _run_daily_harvest():
    """
    Trigger the orchestrator to run the hunter task.
    """
    from orchestrator import run_orchestrator
    from notifier import send_hunter_report, log_for_remoat

    log_for_remoat("🚀 Starting Daily Ignition (Lead Harvest)...", "PROGRESS")
    logger.info("CRON: Starting Daily Lead Harvest...")

    task_request = "Find 20 high-intent Utah service SMB leads (Law, Accounting, Agencies, Trades) for Catalyst Works."

    try:
        # 1. Run the crew
        result = run_orchestrator(task_request, session_key="daily_cron")

        # 2. Post-harvest deep enrichment — Serper + Firecrawl, runs before report
        enrich_result = {}
        try:
            from skills.email_enrichment.enrichment_tool import enrich_missing_emails
            enrich_result = enrich_missing_emails(limit=50)
            logger.info(
                f"CRON: Enrichment — {enrich_result.get('emails_found', 0)} emails, "
                f"{enrich_result.get('linkedin_found', 0)} LinkedIn, "
                f"{enrich_result.get('no_website', 0)} no website (web prospects)."
            )
        except Exception as enrich_err:
            logger.warning(f"CRON: Email enrichment failed (non-blocking): {enrich_err}")

        # 3. Extract report and send email
        if result.get("success"):
            report = result.get("deliverable", "No report generated.")

            # Append enrichment summary to report
            if enrich_result:
                web_prospects = enrich_result.get("web_prospects", [])
                wp_list = "\n".join(
                    f"  - {p['name']} ({p['company']}, {p.get('industry', 'Unknown')})"
                    for p in web_prospects
                ) or "  None"
                enrich_summary = (
                    f"\n\n---\n## Enrichment Summary\n"
                    f"- Leads processed: {enrich_result.get('processed', 0)}\n"
                    f"- Emails found: {enrich_result.get('emails_found', 0)}\n"
                    f"- LinkedIn found: {enrich_result.get('linkedin_found', 0)}\n"
                    f"- Still missing email: {enrich_result.get('still_missing', 0)}\n"
                    f"- No website (web prospects): {enrich_result.get('no_website', 0)}\n"
                    f"\n**Web Prospects (no website found):**\n{wp_list}"
                )
                report += enrich_summary

            send_hunter_report(report)
            log_for_remoat("Daily Ignition complete. Report delivered.", "NOTIFICATION")
            logger.info("CRON: Daily Lead Harvest complete and delivered.")
        else:
            logger.error("CRON: Daily Lead Harvest failed to produce a result.")

    except Exception as e:
        logger.error(f"CRON: Critical failure in daily harvest: {e}")

def _scheduler_loop():
    """
    Check the time every minute and trigger if it matches the target.
    """
    logger.info(f"Scheduler loop started. Target: {TARGET_HOUR:02d}:{TARGET_MINUTE:02d} {TIMEZONE}")
    
    tz = pytz.timezone(TIMEZONE)
    last_run_date = None

    while True:
        now = datetime.now(tz)
        
        # Check if it's the target time and we haven't run today
        if now.hour == TARGET_HOUR and now.minute == TARGET_MINUTE:
            if last_run_date != now.date():
                _run_quote_rotation()
                _run_kpi_refresh()
                _run_daily_harvest()
                last_run_date = now.date()
        
        # Sleep for 30 seconds to avoid missing the minute or double-triggering
        time.sleep(30)

def _run_supabase_sync():
    """
    Sync any leads written to local Postgres fallback back to Supabase.
    Runs on startup and every 30 minutes.
    """
    try:
        import sys
        if "/app" not in sys.path:
            sys.path.insert(0, "/app")
        from db import sync_fallback_to_supabase
        synced = sync_fallback_to_supabase()
        if synced > 0:
            logger.info(f"Sync: moved {synced} fallback lead(s) to Supabase.")
    except Exception as e:
        logger.error(f"Supabase sync failed: {e}")


def start_scheduler():
    """
    Launch the scheduler in a daemon thread.
    Also runs Supabase sync on startup and every 30 minutes.
    """
    # Run sync immediately on startup
    _run_supabase_sync()

    def loop_with_sync():
        sync_counter = 0
        while True:
            _scheduler_loop_tick()
            sync_counter += 1
            # Every 60 ticks of 30s = 30 minutes
            if sync_counter >= 60:
                _run_supabase_sync()
                sync_counter = 0

    thread = threading.Thread(target=_scheduler_loop, daemon=True)
    thread.start()

    sync_thread = threading.Thread(target=_periodic_sync, daemon=True)
    sync_thread.start()

    logger.info("Background scheduler initialized.")


def _periodic_sync():
    """Run Supabase fallback sync every 30 minutes."""
    while True:
        time.sleep(1800)  # 30 minutes
        _run_supabase_sync()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if "--test-quotes" in sys.argv:
        _run_quote_rotation()
    else:
        _run_daily_harvest()
