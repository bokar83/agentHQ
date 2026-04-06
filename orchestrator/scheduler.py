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

def _run_kpi_refresh():
    """Run forge kpi refresh to update all Notion KPI callout blocks."""
    try:
        from skills.forge_cli.forge import kpi_refresh
        kpi_refresh()
        logger.info("CRON: KPI refresh complete.")
    except Exception as e:
        logger.error(f"CRON: KPI refresh failed: {e}")


def _run_daily_harvest():
    """
    Trigger the orchestrator to run the hunter task.
    """
    from orchestrator import run_orchestrator
    from notifier import send_email, log_for_remoat

    log_for_remoat("🚀 Starting Daily Ignition (Lead Harvest)...", "PROGRESS")
    logger.info("CRON: Starting Daily Lead Harvest...")
    
    task_request = "Find 20 high-intent Utah service SMB leads (Law, Accounting, Agencies, Trades) for Catalyst Works."
    
    try:
        # 1. Run the crew
        result = run_orchestrator(task_request, session_key="daily_cron")
        
        # 2. Extract report and send email
        if result.get("success"):
            report = result.get("deliverable", "No report generated.")
            subject = f"🚀 Catalyst Daily Leads — {datetime.now().strftime('%Y-%m-%d')}"
            
            # Send Email
            send_email(subject, report)
            log_for_remoat("✅ Daily Ignition complete. Report delivered.", "NOTIFICATION")
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

def start_scheduler():
    """
    Launch the scheduler in a daemon thread.
    """
    thread = threading.Thread(target=_scheduler_loop, daemon=True)
    thread.start()
    logger.info("Background scheduler initialized.")

if __name__ == "__main__":
    # Test trigger
    logging.basicConfig(level=logging.INFO)
    _run_daily_harvest()
