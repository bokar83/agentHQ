"""
scheduler.py — Catalyst Daily Ignition
======================================
This module runs a background thread that triggers the Hunter Agent
every morning at 6:00 AM MT.
"""

import os
import time
import threading
import logging
from datetime import datetime, time as dtime
import pytz

logger = logging.getLogger("agentsHQ.scheduler")

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
    # Test trigger
    logging.basicConfig(level=logging.INFO)
    _run_daily_harvest()
