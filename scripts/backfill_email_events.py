#!/usr/bin/env python3
"""
scripts/backfill_email_events.py
================================
Backfill email_events from:
  1) sw_email_log (164 rows, 2026-05-11+)
  2) Gmail Sent folder of boubacar@catalystworks.consulting (lifetime, ~482 msgs)
  3) Gmail Inbox bounces (from:mailer-daemon)

Idempotent: uses (brand, gmail_message_id, event_type) unique index. Re-running
inserts ON CONFLICT DO NOTHING so a partial backfill can be resumed.

Run inside orc-crewai (data lives in orc-postgres; OAuth creds at /app/secrets):
  docker exec orc-crewai python3 /app/scripts/backfill_email_events.py

Or locally (set POSTGRES_* env to point at VPS):
  python3 scripts/backfill_email_events.py
"""

import argparse
import base64
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ── Brand classification ─────────────────────────────────────────────────────

SW_SUBJECT_HINTS = [
    "invisible on chatgpt",
    "customers find",
    "saas audit upsell",
    "reviews on google",
    "google reviews",
    "show up when",
]
STUDIO_SUBJECT_HINTS = [
    "searching ai",
    "1,500 website",
    "website is missing",
]
CW_SUBJECT_HINTS = [
    "margin",
    "closing the loop on",
    "constraint",
    "something i thought",
    "saas",
    "audit",
]


def classify_brand_from_subject(subject: str) -> str:
    """Best-effort brand classifier. Falls back to 'cw' when subject is generic
    (the cw OAuth account is the canonical outreach inbox, so unknown == cw)."""
    s = (subject or "").lower()
    for kw in SW_SUBJECT_HINTS:
        if kw in s:
            return "sw"
    for kw in STUDIO_SUBJECT_HINTS:
        if kw in s:
            return "studio"
    for kw in CW_SUBJECT_HINTS:
        if kw in s:
            return "cw"
    return "cw"  # safest default — outreach OAuth is cw account


# ── DB connection ────────────────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "orc-postgres"),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
    )


def ensure_table(conn) -> None:
    """Verify email_events table exists (migration 009 must be applied first)."""
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'email_events'
    """)
    if not cur.fetchone():
        raise RuntimeError(
            "email_events table not found. "
            "Apply migrations/009_email_events.sql first."
        )
    cur.close()


# ── Gmail helpers ────────────────────────────────────────────────────────────

def get_access_token(creds_path: str) -> str:
    with open(creds_path) as f:
        c = json.load(f)
    r = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": c["client_id"],
            "client_secret": c["client_secret"],
            "refresh_token": c["refresh_token"],
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def list_message_ids(token: str, q: str) -> list[str]:
    ids: list[str] = []
    page: Optional[str] = None
    while True:
        params = {"q": q, "maxResults": 500}
        if page:
            params["pageToken"] = page
        r = httpx.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        ids.extend(m["id"] for m in data.get("messages", []))
        page = data.get("nextPageToken")
        if not page:
            break
    return ids


def get_message_meta(token: str, msg_id: str) -> dict:
    r = httpx.get(
        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "format": "metadata",
            "metadataHeaders": ["From", "To", "Subject", "Date"],
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def parse_addr(raw: str) -> str:
    """Pull bare email out of 'Display Name <email@x.com>'."""
    if not raw:
        return ""
    m = re.search(r"<([^>]+)>", raw)
    return (m.group(1) if m else raw).strip().lower()


# ── Backfill steps ───────────────────────────────────────────────────────────

def backfill_from_sw_email_log(conn) -> int:
    """Copy existing sw_email_log rows into email_events.
    pipeline column maps to brand. status maps to event_type."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, lead_email, lead_id, touch, pipeline, status,
               subject, gmail_id, created_at
        FROM sw_email_log
        ORDER BY id
    """)
    rows = cur.fetchall()
    cur.close()
    logger.info(f"sw_email_log: {len(rows)} rows to backfill")

    ins = conn.cursor()
    n = 0
    for r in rows:
        brand = r["pipeline"] if r["pipeline"] in ("cw", "sw", "studio") else "cw"
        event_type = r["status"]
        if event_type == "drafted":
            event_type = "drafted"
        elif event_type == "sent":
            event_type = "sent"
        elif event_type == "failed":
            event_type = "failed"
        elif event_type == "dry-run":
            event_type = "dry-run"
        else:
            event_type = r["status"]

        ins.execute("""
            INSERT INTO email_events
                (brand, pipeline, direction, event_type,
                 to_addr, from_addr, subject,
                 gmail_message_id, lead_id, metadata,
                 occurred_at, recorded_at)
            VALUES (%s, %s, 'outbound', %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, NOW())
            ON CONFLICT (brand, gmail_message_id, event_type)
                WHERE gmail_message_id IS NOT NULL
            DO NOTHING
        """, (
            brand,
            f"sequence_t{r['touch']}",
            event_type,
            r["lead_email"],
            "boubacar@catalystworks.consulting",
            r["subject"],
            r["gmail_id"] or None,
            r["lead_id"],
            psycopg2.extras.Json({
                "source": "sw_email_log",
                "sw_email_log_id": r["id"],
                "touch": r["touch"],
            }),
            r["created_at"],
        ))
        n += 1
    conn.commit()
    ins.close()
    logger.info(f"sw_email_log: backfilled {n} rows into email_events")
    return n


def backfill_from_gmail_sent(conn, token: str, since_iso: str = "2026-04-01") -> int:
    """Pull every message in Gmail Sent (since `since_iso`) and write a
    'sent' event for each. Brand inferred from subject keywords."""
    q = f"in:sent after:{since_iso.replace('-','/')}"
    logger.info(f"Gmail query: {q}")
    ids = list_message_ids(token, q)
    logger.info(f"Gmail Sent: {len(ids)} messages to inspect")

    ins = conn.cursor()
    n_inserted = 0
    n_skipped_internal = 0
    INTERNAL_ADDRS = {
        "boubacar@catalystworks.consulting",
        "bokar83@gmail.com",
        "signal@catalystworks.consulting",
        "catalystworks.ai@gmail.com",
    }

    for i, mid in enumerate(ids):
        if i and i % 50 == 0:
            logger.info(f"  ...{i}/{len(ids)}")
        try:
            d = get_message_meta(token, mid)
        except Exception as e:
            logger.warning(f"  skip {mid}: {e}")
            continue
        ts = int(d.get("internalDate", "0")) / 1000
        occurred = datetime.fromtimestamp(ts, tz=timezone.utc)
        hdrs = {h["name"].lower(): h["value"]
                for h in d.get("payload", {}).get("headers", [])}
        from_addr = parse_addr(hdrs.get("from", ""))
        to_addr = parse_addr(hdrs.get("to", ""))
        subject = hdrs.get("subject", "")

        # Skip internal noise (self-sends to bokar83 / boubacar@cw)
        if to_addr in INTERNAL_ADDRS:
            n_skipped_internal += 1
            continue

        brand = classify_brand_from_subject(subject)
        thread_id = d.get("threadId", "")
        snippet = d.get("snippet", "")[:200]

        ins.execute("""
            INSERT INTO email_events
                (brand, pipeline, direction, event_type,
                 to_addr, from_addr, subject,
                 gmail_message_id, gmail_thread_id, body_preview,
                 metadata, occurred_at, recorded_at)
            VALUES (%s, NULL, 'outbound', 'sent',
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, NOW())
            ON CONFLICT (brand, gmail_message_id, event_type)
                WHERE gmail_message_id IS NOT NULL
            DO NOTHING
        """, (
            brand,
            to_addr,
            from_addr or "boubacar@catalystworks.consulting",
            subject,
            mid,
            thread_id,
            snippet,
            psycopg2.extras.Json({
                "source": "gmail_backfill",
                "label_ids": d.get("labelIds", []),
            }),
            occurred,
        ))
        if ins.rowcount > 0:
            n_inserted += 1

    conn.commit()
    ins.close()
    logger.info(
        f"Gmail Sent backfill: inserted {n_inserted} 'sent' events, "
        f"skipped {n_skipped_internal} internal/self-sends"
    )
    return n_inserted


def backfill_bounces(conn, token: str, since_iso: str = "2026-04-01") -> int:
    """Find bounces in Inbox (from:mailer-daemon) and write 'bounced' events.
    Best-effort: the bounce message's body contains the original recipient;
    we extract that and try to match it to a 'sent' row by to_addr."""
    q = f"(from:mailer-daemon OR from:postmaster) after:{since_iso.replace('-','/')}"
    ids = list_message_ids(token, q)
    logger.info(f"Bounce messages found: {len(ids)}")
    ins = conn.cursor()
    n = 0
    for mid in ids:
        try:
            d = get_message_meta(token, mid)
        except Exception:
            continue
        ts = int(d.get("internalDate", "0")) / 1000
        occurred = datetime.fromtimestamp(ts, tz=timezone.utc)
        snippet = d.get("snippet", "") or ""
        # Try to extract the failed recipient from snippet
        m = re.search(r"([\w\.\-\+]+@[\w\.\-]+\.\w+)", snippet)
        failed_to = (m.group(1) if m else "").lower()
        thread_id = d.get("threadId", "")

        ins.execute("""
            INSERT INTO email_events
                (brand, pipeline, direction, event_type,
                 to_addr, from_addr, subject,
                 gmail_message_id, gmail_thread_id, body_preview,
                 metadata, occurred_at, recorded_at)
            VALUES ('cw', NULL, 'inbound', 'bounced',
                    %s, 'mailer-daemon', 'BOUNCE',
                    %s, %s, %s,
                    %s, %s, NOW())
            ON CONFLICT (brand, gmail_message_id, event_type)
                WHERE gmail_message_id IS NOT NULL
            DO NOTHING
        """, (
            failed_to or "unknown@unknown",
            mid,
            thread_id,
            snippet[:200],
            psycopg2.extras.Json({"source": "gmail_bounce_scan"}),
            occurred,
        ))
        if ins.rowcount > 0:
            n += 1
    conn.commit()
    ins.close()
    logger.info(f"Bounce backfill: inserted {n} 'bounced' events")
    return n


def backfill_replies(conn, token: str) -> int:
    """For each unique thread we have a 'sent' event for, check if the thread
    has any inbound (INBOX-labeled) messages. Each inbound message -> 'replied'.
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT DISTINCT gmail_thread_id, brand
        FROM email_events
        WHERE event_type = 'sent'
          AND gmail_thread_id IS NOT NULL
          AND gmail_thread_id != ''
    """)
    threads = cur.fetchall()
    cur.close()
    logger.info(f"Threads to scan for replies: {len(threads)}")

    ins = conn.cursor()
    n_replies = 0
    for i, t in enumerate(threads):
        tid = t["gmail_thread_id"]
        brand = t["brand"]
        if i and i % 100 == 0:
            logger.info(f"  ...{i}/{len(threads)}")
        try:
            r = httpx.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/threads/{tid}",
                headers={"Authorization": f"Bearer {token}"},
                params={"format": "metadata",
                        "metadataHeaders": ["From", "To", "Subject", "Date"]},
                timeout=20,
            )
            r.raise_for_status()
            th = r.json()
        except Exception as e:
            logger.warning(f"  thread {tid} fetch failed: {e}")
            continue
        for m in th.get("messages", []):
            labels = m.get("labelIds", [])
            if "INBOX" not in labels:
                continue
            hdrs = {h["name"].lower(): h["value"]
                    for h in m.get("payload", {}).get("headers", [])}
            from_addr = parse_addr(hdrs.get("from", ""))
            # Skip self-replies / cron noise
            if from_addr in ("boubacar@catalystworks.consulting",
                             "bokar83@gmail.com"):
                continue
            ts = int(m.get("internalDate", "0")) / 1000
            occurred = datetime.fromtimestamp(ts, tz=timezone.utc)
            snippet = m.get("snippet", "")[:200]

            ins.execute("""
                INSERT INTO email_events
                    (brand, pipeline, direction, event_type,
                     to_addr, from_addr, subject,
                     gmail_message_id, gmail_thread_id, body_preview,
                     metadata, occurred_at, recorded_at)
                VALUES (%s, NULL, 'inbound', 'replied',
                        'boubacar@catalystworks.consulting', %s, %s,
                        %s, %s, %s,
                        %s, %s, NOW())
                ON CONFLICT (brand, gmail_message_id, event_type)
                    WHERE gmail_message_id IS NOT NULL
                DO NOTHING
            """, (
                brand,
                from_addr or "unknown",
                hdrs.get("subject", ""),
                m["id"],
                tid,
                snippet,
                psycopg2.extras.Json({"source": "thread_reply_scan"}),
                occurred,
            ))
            if ins.rowcount > 0:
                n_replies += 1
    conn.commit()
    ins.close()
    logger.info(f"Reply backfill: inserted {n_replies} 'replied' events")
    return n_replies


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-sw-log", action="store_true")
    parser.add_argument("--skip-gmail-sent", action="store_true")
    parser.add_argument("--skip-bounces", action="store_true")
    parser.add_argument("--skip-replies", action="store_true")
    parser.add_argument("--since", default="2026-04-01",
                        help="Lower bound for Gmail backfill (YYYY-MM-DD)")
    parser.add_argument(
        "--creds",
        default=os.environ.get(
            "GOOGLE_OAUTH_CREDENTIALS_JSON_CW",
            "/app/secrets/gws-oauth-credentials-cw.json",
        ),
    )
    args = parser.parse_args()

    conn = get_conn()
    ensure_table(conn)

    if not args.skip_sw_log:
        backfill_from_sw_email_log(conn)
    if not args.skip_gmail_sent:
        token = get_access_token(args.creds)
        backfill_from_gmail_sent(conn, token, since_iso=args.since)
    if not args.skip_bounces:
        token = get_access_token(args.creds)
        backfill_bounces(conn, token, since_iso=args.since)
    if not args.skip_replies:
        token = get_access_token(args.creds)
        backfill_replies(conn, token)

    # Final summary
    cur = conn.cursor()
    cur.execute("SELECT brand, event_type, COUNT(*) FROM email_events "
                "GROUP BY brand, event_type ORDER BY brand, event_type")
    logger.info("Final email_events counts:")
    for row in cur.fetchall():
        logger.info(f"  {row[0]:8s} {row[1]:12s} {row[2]}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
