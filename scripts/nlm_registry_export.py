"""
nlm_registry_export.py — Daily Postgres-to-Sheets audit mirror for notebooklm_pending_docs.

Runs daily at 06:00 UTC via VPS cron. Appends yesterday's rows to a Google Sheet
in the agentsHQ Drive folder so there's a human-readable audit trail independent
of Postgres. Also useful for crash recovery.

Sheet: created on first run, ID saved to NLM_REGISTRY_SHEET_ID in .env reminder.
Cron: 0 6 * * * cd /root/agentsHQ && set -a && . .env && set +a && python3 scripts/nlm_registry_export.py >> /var/log/nlm_registry_export.log 2>&1

Env vars required:
  POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
  GOOGLE_OAUTH_CREDENTIALS_JSON   -- path to gws OAuth credentials JSON
  NLM_EXPORT_SHEET_ID             -- Google Sheet ID (create once, reuse forever)
                                     If not set, script prints a reminder to create it.
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("nlm_registry_export")

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_DB   = os.environ.get("POSTGRES_DB", "postgres")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASS = os.environ.get("POSTGRES_PASSWORD", "")
SHEET_ID      = os.environ.get("NLM_EXPORT_SHEET_ID", "")
OAUTH_PATH    = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON", "")

SHEET_HEADERS = [
    "record_id", "drive_file_id", "original_filename", "standardized_filename",
    "notebook_assignment", "target_folder_path", "confidence_score",
    "review_required", "auto_file", "resolved", "routing_notes",
    "source", "created_at", "export_date",
]


def fetch_rows(since_hours: int = 25) -> list[dict]:
    """Fetch rows created or updated in the last N hours from Postgres."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=POSTGRES_HOST, dbname=POSTGRES_DB,
            user=POSTGRES_USER, password=POSTGRES_PASS,
        )
        cur = conn.cursor()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        cur.execute(
            """SELECT record_id, drive_file_id, original_filename, standardized_filename,
                      notebook_assignment, target_folder_path, confidence_score,
                      review_required, auto_file, resolved, routing_notes,
                      source, created_at
               FROM notebooklm_pending_docs
               WHERE created_at >= %s
               ORDER BY created_at ASC""",
            (cutoff,),
        )
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"Postgres fetch failed: {e}")
        return []


def append_to_sheet(rows: list[dict]) -> bool:
    """Append rows to the Google Sheet via gws CLI."""
    if not SHEET_ID:
        logger.warning(
            "NLM_EXPORT_SHEET_ID not set. Create a Google Sheet in the agentsHQ Drive folder, "
            "copy its ID from the URL, and add NLM_EXPORT_SHEET_ID=<id> to /root/agentsHQ/.env"
        )
        return False
    if not rows:
        logger.info("No new rows to export.")
        return True

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    values = []
    for row in rows:
        values.append([
            str(row.get("record_id", "")),
            str(row.get("drive_file_id", "")),
            str(row.get("original_filename", "")),
            str(row.get("standardized_filename", "")),
            str(row.get("notebook_assignment", "")),
            str(row.get("target_folder_path", "")),
            str(row.get("confidence_score", "")),
            str(row.get("review_required", "")),
            str(row.get("auto_file", "")),
            str(row.get("resolved", "")),
            str(row.get("routing_notes", "") or ""),
            str(row.get("source", "")),
            str(row.get("created_at", "")),
            today,
        ])

    params = {
        "spreadsheetId": SHEET_ID,
        "range": "Sheet1!A1",
        "valueInputOption": "RAW",
        "insertDataOption": "INSERT_ROWS",
        "resource": {"values": values},
    }

    result = subprocess.run(
        ["gws", "sheets", "spreadsheets", "values", "append",
         "--params", json.dumps(params)],
        capture_output=True, text=True, timeout=30,
        env={**os.environ},
    )
    if result.returncode != 0:
        logger.error(f"gws append failed: {result.stderr[:500]}")
        return False

    logger.info(f"Exported {len(rows)} rows to sheet {SHEET_ID}")
    return True


def ensure_header_row() -> None:
    """Write header row if sheet is empty (first run)."""
    if not SHEET_ID:
        return
    check = subprocess.run(
        ["gws", "sheets", "spreadsheets", "values", "get",
         "--params", json.dumps({"spreadsheetId": SHEET_ID, "range": "Sheet1!A1:A1"})],
        capture_output=True, text=True, timeout=15, env={**os.environ},
    )
    try:
        data = json.loads(check.stdout)
        if data.get("values"):
            return
    except Exception:
        pass

    params = {
        "spreadsheetId": SHEET_ID,
        "range": "Sheet1!A1",
        "valueInputOption": "RAW",
        "resource": {"values": [SHEET_HEADERS]},
    }
    subprocess.run(
        ["gws", "sheets", "spreadsheets", "values", "update",
         "--params", json.dumps(params)],
        capture_output=True, text=True, timeout=15, env={**os.environ},
    )
    logger.info("Header row written to sheet.")


def main():
    logger.info("Starting NLM registry export...")
    rows = fetch_rows(since_hours=25)
    logger.info(f"Found {len(rows)} rows from last 25 hours.")
    ensure_header_row()
    success = append_to_sheet(rows)
    if not success and not SHEET_ID:
        sys.exit(0)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
