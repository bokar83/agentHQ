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
from datetime import datetime
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
        text = f"\"{ quote['text']}\" -- {quote['author']}"
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
        "agentsHQ_quote_block_id": _discover_quote_block_id(os.environ.get("NOTION_AGENTSHQ_PAGE_ID", "327bcf1a-3029-80b7-9b1e-d77f94c9c61c"), token),
        "forge_quote_block_id": _discover_quote_block_id(os.environ.get("NOTION_FORGE_PAGE_ID", "249bcf1a-3029-807f-86e8-fb97e2671154"), token),
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
        f"\U0001f4ac *Quote of the Day*\n\n"
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

    log_for_remoat("\U0001f680 Starting Daily Ignition (Lead Harvest)...", "PROGRESS")
    logger.info("CRON: Starting Daily Lead Harvest...")

    task_request = "Find 20 high-intent Utah service SMB leads (Law, Accounting, Agencies, Trades) for Catalyst Works."

    try:
        # 1. Run the crew
        result = run_orchestrator(task_request, session_key="daily_cron")

        # 2. Post-harvest deep enrichment -- Serper + Firecrawl, runs before report
        enrich_result = {}
        try:
            from skills.email_enrichment.enrichment_tool import enrich_missing_emails
            enrich_result = enrich_missing_emails(limit=50)
            logger.info(
                f"CRON: Enrichment -- {enrich_result.get('emails_found', 0)} emails, "
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

            send_hunter_report(report, enrich_result=enrich_result)
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
    last_digest_date = None

    while True:
        now = datetime.now(tz)

        # Check if it's the target time and we haven't run today
        if now.hour == TARGET_HOUR and now.minute == TARGET_MINUTE:
            if last_run_date != now.date():
                _run_quote_rotation()
                _run_kpi_refresh()
                _run_notion_sync()
                _run_daily_harvest()
                last_run_date = now.date()

        # NotebookLM digest at 08:30 AM MT
        if now.hour == 8 and now.minute == 30:
            if last_digest_date != now.date():
                _run_notebooklm_digest()
                last_digest_date = now.date()

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


def _run_notion_sync():
    """
    Sync all Supabase leads into the Notion CRM Leads database.
    Triggered by Supabase LISTEN/NOTIFY on lead changes, with 10am/1pm MT fallback.
    """
    try:
        import sys
        if "/app" not in sys.path:
            sys.path.insert(0, "/app")
        from db import sync_supabase_to_notion
        synced = sync_supabase_to_notion()
        logger.info(f"NOTION SYNC: {synced} lead(s) synced to Notion CRM.")
    except Exception as e:
        logger.error(f"NOTION SYNC: Failed: {e}")


def start_scheduler():
    """
    Launch the scheduler in a daemon thread.
    Also runs Supabase sync on startup and every 30 minutes.
    """
    # Run sync immediately on startup
    _run_supabase_sync()

    thread = threading.Thread(target=_scheduler_loop, daemon=True)
    thread.start()

    sync_thread = threading.Thread(target=_periodic_sync, daemon=True)
    sync_thread.start()

    listen_thread = threading.Thread(target=_listen_for_supabase_changes, daemon=True)
    listen_thread.start()

    if os.environ.get("DRIVE_WATCH_ENABLED", "false").lower() == "true":
        drive_watch_thread = threading.Thread(target=_drive_watch_loop, daemon=True)
        drive_watch_thread.start()
        logger.info("Drive watch thread started.")

    logger.info("Background scheduler initialized.")


def _periodic_sync():
    """
    Run Supabase fallback sync every 30 minutes (local Postgres -> Supabase).
    Run Notion CRM sync at 10am and 1pm MT as scheduled fallback.
    Primary Notion sync is triggered by Supabase LISTEN notifications.
    """
    tz = pytz.timezone(TIMEZONE)
    notion_sync_hours = {10, 13}  # 10am and 1pm MT
    last_notion_sync_date = {}  # hour -> date last synced

    while True:
        time.sleep(60)  # check every minute
        _run_supabase_sync()

        now = datetime.now(tz)
        if now.hour in notion_sync_hours:
            last = last_notion_sync_date.get(now.hour)
            if last != now.date():
                logger.info(f"NOTION SYNC: Scheduled sync at {now.hour:02d}:00 MT")
                _run_notion_sync()
                last_notion_sync_date[now.hour] = now.date()


def _listen_for_supabase_changes():
    """
    Listen on the Supabase 'leads_changed' channel via Postgres LISTEN/NOTIFY.
    Triggers a Notion sync whenever a lead is inserted or updated.
    Reconnects automatically on failure.
    """
    import select as _select
    import sys
    if "/app" not in sys.path:
        sys.path.insert(0, "/app")

    logger.info("LISTEN: Starting Supabase leads change listener.")
    while True:
        try:
            from db import get_crm_connection
            conn = get_crm_connection()
            conn.set_isolation_level(0)  # autocommit required for LISTEN
            cur = conn.cursor()
            cur.execute("LISTEN leads_changed;")
            logger.info("LISTEN: Subscribed to leads_changed channel.")

            while True:
                if _select.select([conn], [], [], 60)[0]:
                    conn.poll()
                    while conn.notifies:
                        notify = conn.notifies.pop(0)
                        logger.info(f"LISTEN: leads_changed notification received: {notify.payload}")
                        _run_notion_sync()
        except Exception as e:
            logger.error(f"LISTEN: Supabase listener error: {e}. Reconnecting in 30s.")
            time.sleep(30)

# ---------------------------------------------------------------------------
# Drive Watch -- NotebookLM document ingestion poller
# Enabled via DRIVE_WATCH_ENABLED=true env var (off by default)
# ---------------------------------------------------------------------------

def _run_drive_watch(scan_all: bool = False):
    """
    Poll the NotebookLM Library root folder for unclassified files.

    scan_all=False (scheduled): only files created in the last 65 minutes.
    scan_all=True  (/scan-drive): all files currently in root, regardless of age.
      In both cases, deduplication against notebooklm_pending_docs prevents re-processing.

    After classifying, files are moved out of root into their target Drive folder.
    A Telegram summary lists each file and where it was placed.
    """
    import subprocess
    import json as _json
    import psycopg2
    import httpx
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td

    # -- Folder path -> Drive ID lookup table (full taxonomy) -----------------
    FOLDER_ID_MAP = {
        "00_Review_Queue/":                         "1UJ81j0O_AewmmkqrocQ4g5tCVMOEE3x5",
        "01_Clients/":                              "1nXgYJ7Hnz6TBXBK0GtnZaxHwAHDsbTbS",
        "02_Catalyst_Works/":                       "1g1Zv70QaSmEluhc6jWm8ELfTmrorkPya",
        "02_Catalyst_Works/01_Offers/":             "1SSWsl8jYaWBQxD977nmgN3PXV_7_VdI8",
        "02_Catalyst_Works/02_Methodology/":        "1WgW6OLisvQP0cGrl_MNpJuXeyb6CJM-B",
        "02_Catalyst_Works/03_agentsHQ/":           "1XTKQ2k-GCDXWvyjOE_MLVJPrnqDCNl0t",
        "02_Catalyst_Works/04_Systems_and_SOPs/":   "1BKCHMQrXfQeKBaQK-iWL_6x_T_mpMzv4",
        "02_Catalyst_Works/05_Sales_and_Pipeline/": "18r4PDt_yyTlD-_tKaLcjYzfpC9upoOjY",
        "03_Research/":                             "1jjPUb5TXvoicJR_3h7n-HdQZl0JDGlJp",
        "03_Research/01_TOC_and_Constraints/":      "18UY-MvEkLgK104XsKL2Oc7_rxRfWJevM",
        "03_Research/02_AI_Strategy/":              "1DLAHqzl_3eGl4XjeNBKJZePmxE5CAFeG",
        "03_Research/03_SMB_and_Operators/":        "1fKDW_ENQnNRw5oLCTgaurB3UCeDizrvA",
        "03_Research/04_Behavioral_Science/":       "13GUfaom5uAQtK8ZKwWHKcXDy3Ezsj1oB",
        "03_Research/05_External_Sources/":         "1KFMPinQxmitCdxQ_K3Yh5QMktn5-BJ4W",
        "04_Content/":                              "1lS7VT4aMfo7eQc-zVdOfFfvWvevytwNs",
        "04_Content/01_LinkedIn/":                  "1UQX5tgrh1BYMRCBCDhhEhGwSEOoJa7qz",
        "04_Content/02_Longform/":                  "1Pg5rNnaQ360vkeuNeqKS4c0HpUx6AFyo",
        "04_Content/03_Lead_Magnets/":              "1Pi-UVVwcwtcIGkXRzMJx-kQ8Y6Ok9etn",
        "04_Content/04_Frameworks_and_IP/":         "18EHTT_eEkfNcLlEZS4I34EQ64Q-QI_3a",
        "05_Learning/":                             "1ob1UFXbmSf32BlDZnz6EqAhEkWXIyHB9",
        "05_Learning/01_Books/":                    "1wZH6dt96syjtORJ1bM6aTVqAy7ONilsW",
        "05_Learning/02_Courses/":                  "1ElDkzKAsaaWNT_iIqm12AEb9UBgwqwIY",
        "05_Learning/03_Transcripts/":              "19yxpuTwCbepaN7-S6QbPrcu2ZkgADu_4",
        "05_Learning/04_Notes/":                    "1QhcWrwm033_l6SQMJHA4p7h77OWmgbLq",
        "06_Ideas/":                                "1OKotZLVBKITkaHRo2ybN99f3_PAZ5-3A",
        "02_Catalyst_Works/06_Frameworks_and_IP/":  "1JpTg0zDWNicDoEQOz29NCJOqysQHI_Nl",
        "90_Archive/":                              "1P9cxCq6v4gBxfi_9kJeoIKbNe4EUocI-",
    }

    folder_id = os.environ.get("NOTEBOOKLM_LIBRARY_ROOT_ID", "1S0t78tojgA6VugqMtE3soZYFSEAcSvvH")
    review_queue_id = os.environ.get("NOTEBOOKLM_REVIEW_QUEUE_FOLDER_ID", "")
    registry_sheet_id = os.environ.get("NOTEBOOKLM_REGISTRY_SHEET_ID", "")
    token = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    # -- 1. Build Drive query -----------------------------------------------
    if scan_all:
        # All files in root, no time filter -- dedup handles re-processing
        q = f"'{folder_id}' in parents and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
        logger.info("DRIVE WATCH: scan_all mode -- processing all files in root folder.")
    else:
        cutoff = _dt.now(_tz.utc) - _td(minutes=65)
        cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%S")
        q = f"'{folder_id}' in parents and trashed=false and mimeType != 'application/vnd.google-apps.folder' and createdTime > '{cutoff_str}'"

    query_params = {
        "q": q,
        "fields": "files(id,name,mimeType,createdTime)",
        "orderBy": "createdTime desc",
        "pageSize": "50",  # higher limit for scan_all
    }
    try:
        list_result = subprocess.run(
            ["gws", "drive", "files", "list", "--params", _json.dumps(query_params)],
            capture_output=True, text=True, timeout=30,
            env={**os.environ},
        )
        raw = list_result.stdout.strip()
        if not raw:
            logger.debug("DRIVE WATCH: No output from gws drive files list.")
            return
        drive_data = _json.loads(raw)
    except Exception as e:
        logger.error(f"DRIVE WATCH: Failed to list Drive files: {e}")
        return

    files = drive_data.get("files", [])
    if not files:
        logger.debug("DRIVE WATCH: No new files found.")
        return

    logger.info(f"DRIVE WATCH: Found {len(files)} new file(s) to process.")

    # -- 2. Connect to Postgres --------------------------------------------
    try:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "orc-postgres"),
            database=os.environ.get("POSTGRES_DB", "postgres"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            port=int(os.environ.get("POSTGRES_PORT", 5432)),
        )
        conn.autocommit = False
    except Exception as e:
        logger.error(f"DRIVE WATCH: Postgres connection failed: {e}")
        return

    try:
        cur = conn.cursor()
        scan_summary = []  # collects one line per file processed

        for f in files:
            file_id = f.get("id", "")
            filename = f.get("name", "")
            mime_type = f.get("mimeType", "")

            if not file_id or not filename:
                continue

            # -- Check if already in pending docs --------------------------
            try:
                cur.execute(
                    "SELECT record_id FROM notebooklm_pending_docs WHERE drive_file_id = %s",
                    (file_id,),
                )
                if cur.fetchone():
                    logger.debug(f"DRIVE WATCH: Skipping already-processed file: {filename}")
                    continue
            except Exception as e:
                logger.error(f"DRIVE WATCH: DB lookup failed for {filename}: {e}")
                continue

            # -- Extract text (Google-native only) -------------------------
            extracted_text = ""
            if "google-apps" in mime_type:
                try:
                    export_params = {"fileId": file_id, "mimeType": "text/plain"}
                    export_result = subprocess.run(
                        ["gws", "drive", "files", "export", "--params", _json.dumps(export_params)],
                        capture_output=True, text=True, timeout=30,
                        env={**os.environ},
                    )
                    extracted_text = (export_result.stdout or "")[:2000]
                except Exception as e:
                    logger.warning(f"DRIVE WATCH: Text export failed for {filename}: {e}")

            # -- Run doc routing crew --------------------------------------
            try:
                import sys as _sys
                _orc_skills = "/app/orchestrator_skills"
                if _orc_skills not in _sys.path:
                    _sys.path.insert(0, _orc_skills)
                from doc_routing.doc_routing_crew import run_doc_routing_with_retry
                context = {
                    "record_id": None,
                    "filename": filename,
                    "extracted_text": extracted_text,
                    "mime_type": mime_type,
                    "source": "drive_watch",
                    "project_hint": "",
                }
                routing = run_doc_routing_with_retry(
                    user_request=f"Route this document: {filename}",
                    context=context,
                )
            except Exception as e:
                logger.error(f"DRIVE WATCH: Routing crew failed for {filename}: {e}")
                routing = {
                    "standardized_filename": filename,
                    "domain": "unknown",
                    "topic_or_client": "",
                    "doc_type": "unknown",
                    "target_folder_path": "",
                    "project_id": "",
                    "notebook_assignment": "",
                    "confidence": "low",
                    "confidence_score": 0.0,
                    "review_required": True,
                    "auto_file": False,
                    "routing_notes": f"Routing crew error: {e}",
                }

            standardized_filename = routing.get("standardized_filename", filename)
            domain = routing.get("domain", "")
            topic_or_client = routing.get("topic_or_client", "")
            doc_type = routing.get("doc_type", "")
            target_folder_path = routing.get("target_folder_path", "")
            project_id = routing.get("project_id", "")
            notebook_assignment = routing.get("notebook_assignment", "")
            confidence = routing.get("confidence", "low")
            confidence_score = float(routing.get("confidence_score", 0.0))
            review_required = bool(routing.get("review_required", True))
            auto_file = bool(routing.get("auto_file", False))
            routing_notes = routing.get("routing_notes", "")

            # -- Insert into notebooklm_pending_docs -----------------------
            telegram_message_id = ""
            try:
                cur.execute(
                    """
                    INSERT INTO notebooklm_pending_docs (
                        drive_file_id, original_filename, standardized_filename,
                        domain, topic_or_client, doc_type, target_folder_path,
                        project_id, notebook_assignment, confidence, confidence_score,
                        review_required, auto_file, routing_notes, source,
                        resolved, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                              %s, %s, %s, %s, %s, NOW())
                    RETURNING record_id
                    """,
                    (
                        file_id, filename, standardized_filename,
                        domain, topic_or_client, doc_type, target_folder_path,
                        project_id, notebook_assignment, confidence, confidence_score,
                        review_required, auto_file, routing_notes, "drive_watch",
                        False,
                    ),
                )
                row = cur.fetchone()
                record_id = row[0] if row else None
                conn.commit()
            except Exception as e:
                logger.error(f"DRIVE WATCH: DB insert failed for {filename}: {e}")
                try:
                    conn.rollback()
                except Exception:
                    pass
                continue

            # -- Resolve target Drive folder ID from path -------------------
            target_folder_id = FOLDER_ID_MAP.get(target_folder_path)
            if not target_folder_id:
                target_folder_id = FOLDER_ID_MAP.get(target_folder_path.rstrip("/") + "/")

            new_folder_created = None  # track if we created a new folder this pass

            if not target_folder_id:
                # Unknown path -- create the folder under its parent
                # e.g. "03_Research/05_NewTopic/" -> parent is "03_Research/"
                parts = target_folder_path.strip("/").split("/")
                folder_name = parts[-1]  # last segment is the new folder name
                parent_path = "/".join(parts[:-1]) + "/" if len(parts) > 1 else ""
                parent_id = FOLDER_ID_MAP.get(parent_path)
                if not parent_id:
                    # Parent also unknown -- fall back to Review Queue
                    logger.warning(f"DRIVE WATCH: Cannot resolve parent for '{target_folder_path}' -- routing to Review Queue.")
                    target_folder_id = review_queue_id
                    target_folder_path = "00_Review_Queue/"
                else:
                    try:
                        from skills.doc_routing.gws_cli_tools import GWSDriveCreateFolderTool
                        create_tool = GWSDriveCreateFolderTool()
                        result_str = create_tool._run(_json.dumps({
                            "name": folder_name,
                            "parent_id": parent_id,
                        }))
                        result_data = _json.loads(result_str)
                        if "error" in result_data:
                            raise ValueError(result_data["error"])
                        target_folder_id = result_data["id"]
                        new_folder_created = target_folder_path
                        logger.info(f"DRIVE WATCH: Created new folder '{target_folder_path}' (id={target_folder_id})")
                    except Exception as _e:
                        logger.error(f"DRIVE WATCH: Folder creation failed for '{target_folder_path}': {_e} -- routing to Review Queue.")
                        target_folder_id = review_queue_id
                        target_folder_path = "00_Review_Queue/"

            # -- Act on routing decision -----------------------------------
            from skills.doc_routing.gws_cli_tools import GWSDriveMoveRenameTool, GWSSheetsAppendRowTool
            move_tool = GWSDriveMoveRenameTool()

            if auto_file:
                # Move + rename into target folder
                move_result = move_tool._run(_json.dumps({
                    "file_id": file_id,
                    "new_name": standardized_filename,
                    "new_parent_id": target_folder_id,
                    "old_parent_id": folder_id,
                }))
                move_data = _json.loads(move_result)
                if "error" in move_data:
                    logger.error(f"DRIVE WATCH: Move failed for {filename}: {move_data['error']}")
                    scan_summary.append(f"FAILED {filename} -- {move_data['error']}")
                else:
                    logger.info(f"DRIVE WATCH: Auto-filed {standardized_filename} -> {target_folder_path}")
                    # Mark resolved in DB
                    try:
                        cur.execute(
                            "UPDATE notebooklm_pending_docs SET resolved=true WHERE record_id=%s",
                            (record_id,),
                        )
                        conn.commit()
                    except Exception as _e:
                        logger.error(f"DRIVE WATCH: DB resolve failed: {_e}")
                    # Append to Auto-Filed Log sheet
                    if registry_sheet_id:
                        try:
                            sheet_tool = GWSSheetsAppendRowTool()
                            sheet_tool._run(_json.dumps({
                                "spreadsheet_id": registry_sheet_id,
                                "range": "Auto-Filed Log!A:G",
                                "values": [[
                                    standardized_filename, domain, target_folder_path,
                                    notebook_assignment, str(confidence_score),
                                    _dt.now(_tz.utc).strftime("%Y-%m-%d"), "drive_watch",
                                ]],
                            }))
                        except Exception as _e:
                            logger.warning(f"DRIVE WATCH: Auto-Filed Log append failed: {_e}")
                    entry = f"Filed: {standardized_filename}\n  Folder: {target_folder_path}\n  Notebook: {notebook_assignment}"
                    if new_folder_created:
                        entry += f"\n  NEW FOLDER CREATED: {new_folder_created} -- add a matching notebook in NotebookLM and link it to this folder."
                    scan_summary.append(entry)

            elif not review_required:
                # Medium confidence -- ask for confirmation, leave file in root for now
                msg = (
                    f"Review needed: {filename}\n"
                    f"Suggested: {standardized_filename}\n"
                    f"Folder: {target_folder_path}\n"
                    f"Notebook: {notebook_assignment}\n"
                    f"Confidence: {confidence_score:.0%}\n\n"
                    f"Reply: confirm or flag"
                )
                try:
                    resp = httpx.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json={"chat_id": chat_id, "text": msg},
                        timeout=10,
                    )
                    result_data = resp.json()
                    telegram_message_id = str(result_data.get("result", {}).get("message_id", ""))
                    if record_id and telegram_message_id:
                        cur.execute(
                            "UPDATE notebooklm_pending_docs SET telegram_message_id=%s WHERE record_id=%s",
                            (telegram_message_id, record_id),
                        )
                        conn.commit()
                except Exception as _e:
                    logger.error(f"DRIVE WATCH: Telegram confirmation send failed: {_e}")
                scan_summary.append(f"Needs review: {filename} ({confidence_score:.0%}) -- reply sent")

            else:
                # Low confidence -- move to Review Queue immediately
                move_result = move_tool._run(_json.dumps({
                    "file_id": file_id,
                    "new_name": filename,
                    "new_parent_id": review_queue_id,
                    "old_parent_id": folder_id,
                }))
                move_data = _json.loads(move_result)
                if "error" in move_data:
                    logger.error(f"DRIVE WATCH: Review Queue move failed for {filename}: {move_data['error']}")
                scan_summary.append(f"Review Queue: {filename} ({confidence_score:.0%}) -- {routing_notes[:60]}")

        # -- Send scan summary Telegram message ----------------------------
        if scan_summary:
            total = len(scan_summary)
            summary_lines = [f"Scan complete -- {total} file(s) processed:"]
            for line in scan_summary:
                summary_lines.append(f"\n{line}")
            _send_telegram_alert("\n".join(summary_lines))
        else:
            if scan_all:
                _send_telegram_alert("Scan complete -- no new files found in Drive inbox.")

    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


def _drive_watch_loop():
    """Run _run_drive_watch() every 60 minutes on a dedicated thread."""
    logger.info("DRIVE WATCH: Starting drive watch loop (60 min interval).")
    while True:
        try:
            _run_drive_watch()
        except Exception as e:
            logger.error(f"DRIVE WATCH: Unhandled error: {e}")
        time.sleep(3600)


def _run_notebooklm_digest():
    """
    Send a daily Telegram digest of NotebookLM document routing activity.
    Queries notebooklm_pending_docs for yesterday's activity and current pending queue.
    Fires at 08:30 AM MT via _scheduler_loop().
    """
    import psycopg2
    from datetime import timedelta

    logger.info("DIGEST: Starting NotebookLM daily digest...")
    try:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "orc-postgres"),
            database=os.environ.get("POSTGRES_DB", "postgres"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            port=int(os.environ.get("POSTGRES_PORT", 5432)),
        )
        cur = conn.cursor()

        # Yesterday's auto-filed count
        cur.execute("""
            SELECT COUNT(*) FROM notebooklm_pending_docs
            WHERE auto_file = true AND resolved = true
              AND created_at >= NOW() - INTERVAL '24 hours'
        """)
        auto_filed = cur.fetchone()[0]

        # Current unresolved pending reviews
        cur.execute("""
            SELECT COUNT(*) FROM notebooklm_pending_docs
            WHERE resolved = false AND review_required = false
        """)
        pending_confirm = cur.fetchone()[0]

        # Current unresolved review queue items
        cur.execute("""
            SELECT COUNT(*) FROM notebooklm_pending_docs
            WHERE resolved = false AND review_required = true
        """)
        pending_review = cur.fetchone()[0]

        # Files in Review Queue (low confidence, unresolved, older than 1 hour)
        cur.execute("""
            SELECT original_filename, confidence_score, routing_notes, created_at
            FROM notebooklm_pending_docs
            WHERE resolved = false AND review_required = true
              AND created_at < NOW() - INTERVAL '1 hour'
            ORDER BY created_at ASC
            LIMIT 5
        """)
        stale_rows = cur.fetchall()

        cur.close()
        conn.close()

        # Build digest message
        lines = [
            "NotebookLM -- Daily Digest",
            f"Date: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            f"Auto-filed (last 24h): {auto_filed}",
            f"Pending confirmation: {pending_confirm}",
            f"Pending review queue: {pending_review}",
        ]

        if stale_rows:
            lines.append("")
            lines.append("Stale Review Queue (oldest first):")
            for filename, score, notes, created in stale_rows:
                age = datetime.utcnow() - created if created else None
                age_str = f"{int(age.total_seconds() // 3600)}h ago" if age else "?"
                lines.append(f"  - {filename} ({score:.0%}, {age_str})")
                if notes:
                    lines.append(f"    {notes[:80]}")

        if pending_confirm > 0:
            lines.append("")
            lines.append(f"Action needed: {pending_confirm} doc(s) waiting for your confirmation (send \u2705 reply).")

        _send_telegram_alert("\n".join(lines))
        logger.info(f"DIGEST: Sent. auto_filed={auto_filed}, pending_confirm={pending_confirm}, pending_review={pending_review}")

    except Exception as e:
        logger.error(f"DIGEST: Failed: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if "--test-quotes" in sys.argv:
        _run_quote_rotation()
    else:
        _run_daily_harvest()
