"""
signal_works/bounce_scanner.py
Scans boubacar@catalystworks.consulting for mailer-daemon bounce notifications,
extracts the failed recipient addresses, and nulls those emails in Supabase
with a bounce note.

Run daily after sends, or on demand.

Usage:
  python -m signal_works.bounce_scanner
  python -m signal_works.bounce_scanner --dry-run    # show what would be updated
  python -m signal_works.bounce_scanner --days 14    # look back 14 days (default: 7)
"""
import argparse
import base64
import logging
import re
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signal_works.gmail_draft import _get_access_token
from orchestrator.db import get_crm_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

FINAL_RECIPIENT_RE = re.compile(r"Final-Recipient:\s*rfc822;\s*(\S+)", re.I)
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
SKIP_DOMAINS = {"googlemail.com", "gmail.com", "google.com", "mailer-daemon.com"}


def _fetch_bounce_emails(days: int = 7) -> list[str]:
    """Return list of bounced recipient addresses from the CW inbox."""
    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    resp = httpx.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
        headers=headers,
        params={
            "q": (
                f"from:mailer-daemon OR from:postmaster "
                f"newer_than:{days}d"
            ),
            "maxResults": 100,
        },
        timeout=20,
    )
    resp.raise_for_status()
    messages = resp.json().get("messages", [])

    if not messages:
        logger.info("No bounce messages found.")
        return []

    logger.info(f"Found {len(messages)} potential bounce messages -- extracting recipients...")
    bounced = []

    for msg in messages:
        r = httpx.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}",
            headers=headers,
            params={"format": "full"},
            timeout=20,
        )
        data = r.json()
        payload = data.get("payload", {})

        failed_email = ""

        # Parse all body parts for Final-Recipient header
        parts = payload.get("parts", [payload])
        for part in parts:
            body_data = part.get("body", {}).get("data", "")
            if not body_data:
                continue
            try:
                text = base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="replace")
                m = FINAL_RECIPIENT_RE.search(text)
                if m:
                    failed_email = m.group(1).strip().lower()
                    break
            except Exception:
                continue

        # Fallback: grep snippet for non-Google email addresses
        if not failed_email:
            snippet = data.get("snippet", "")
            for candidate in EMAIL_RE.findall(snippet):
                domain = candidate.split("@")[-1].lower()
                if domain not in SKIP_DOMAINS:
                    failed_email = candidate.lower()
                    break

        if failed_email:
            bounced.append(failed_email)
            logger.debug(f"  Bounce detected: {failed_email}")

    unique = list(set(bounced))
    logger.info(f"Unique bounced addresses: {len(unique)}")
    return unique


def _null_bounced_in_db(bounced_emails: list[str], dry_run: bool = False) -> int:
    """Null emails in leads table for any matching bounced address. Returns update count."""
    if not bounced_emails:
        return 0

    conn = get_crm_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, email, lead_type FROM leads WHERE LOWER(email) = ANY(%s)",
            (bounced_emails,),
        )
        found = cur.fetchall()

        if not found:
            logger.info("None of the bounced addresses are in the leads DB.")
            return 0

        logger.info(f"Found {len(found)} leads with bounced emails:")
        for r in found:
            logger.info(f"  ID {r['id']}: {r['name']} | {r['email']}")

        if dry_run:
            logger.info("[DRY RUN] Would null these emails. No DB changes made.")
            return len(found)

        cur.execute(
            """
            UPDATE leads
            SET email = NULL,
                notes = COALESCE(NULLIF(notes, '') || chr(10) || chr(10), '') ||
                        'Email bounced 2026-04-27: mailer-daemon failure from boubacar@catalystworks.consulting. Email nulled.',
                updated_at = NOW()
            WHERE LOWER(email) = ANY(%s)
            """,
            (bounced_emails,),
        )
        count = cur.rowcount
        conn.commit()
        cur.close()
        logger.info(f"Nulled email + added bounce note for {count} leads.")
        return count

    except Exception as e:
        logger.error(f"DB update failed: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()


def run(days: int = 7, dry_run: bool = False) -> int:
    """Scan for bounces and update DB. Returns number of leads updated."""
    bounced = _fetch_bounce_emails(days=days)
    if not bounced:
        return 0
    return _null_bounced_in_db(bounced, dry_run=dry_run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Signal Works bounce scanner")
    parser.add_argument("--days", type=int, default=7,
                        help="Look back this many days for bounces (default: 7)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be updated without changing DB")
    args = parser.parse_args()

    count = run(days=args.days, dry_run=args.dry_run)
    logger.info(f"Bounce scan complete. {count} leads updated.")
