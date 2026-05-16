#!/usr/bin/env python3
"""
scripts/sync_replies_from_gmail.py
====================================
Cron-driven reply + bounce + STOP-intent scanner.

Three jobs per run, all idempotent:
  1. scan_stop_replies -> classify body of new inbound messages. If
     STOP / UNSUBSCRIBE / "remove me" / "do not contact" / "stop emailing"
     fires (word-bounded, case-insensitive) we:
        (a) INSERT into email_suppressions  (canonical do-not-contact ledger)
        (b) UPDATE leads SET opt_out=TRUE   (Supabase canonical, case-insensitive)
        (c) INSERT 'unsubscribed' email_events row
        (d) emit one Telegram alert per new suppression (best-effort, non-fatal)
  2. backfill_bounces  -> 'bounced' events in email_events
  3. backfill_replies  -> 'replied' events in email_events for any new inbound
     messages on threads we have outbound rows for

State is implicit: ON CONFLICT DO NOTHING on each table guards re-runs. The
script can run every 15 min indefinitely.

Cron (on VPS host -- NOT inside the container, host owns the cron):
  */15 * * * *  docker exec orc-crewai python3 /app/scripts/sync_replies_from_gmail.py >> /var/log/sync_replies.log 2>&1
"""

import logging
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import httpx
import psycopg2.extras

# Reuse helpers from the backfill script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backfill_email_events import (  # noqa: E402
    get_conn, ensure_table, get_access_token,
    backfill_bounces, backfill_replies, parse_addr,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


# ── STOP-intent classification ────────────────────────────────────────────────

# Word-bounded patterns. Ordered by specificity; first match wins so the
# reason/matched_pattern recorded is the canonical trigger.
STOP_PATTERNS: list[tuple[str, "re.Pattern[str]", str]] = [
    # reason            pattern                                              label
    ("reply_stop",        re.compile(r"\bSTOP\b"),                            "STOP"),
    ("reply_unsubscribe", re.compile(r"\bunsubscribe\b", re.I),               "unsubscribe"),
    ("reply_remove",      re.compile(r"\bremove me\b", re.I),                 "remove me"),
    ("reply_remove",      re.compile(r"\btake me off\b", re.I),               "take me off"),
    ("reply_stop",        re.compile(r"\bstop emailing\b", re.I),             "stop emailing"),
    ("reply_remove",      re.compile(r"\bdo not contact\b", re.I),            "do not contact"),
    ("reply_remove",      re.compile(r"\bdon'?t (email|contact) me\b", re.I), "dont contact me"),
    ("reply_remove",      re.compile(r"\bopt[ -]?out\b", re.I),               "opt out"),
]


def classify_stop_intent(body: str) -> Optional[tuple[str, str]]:
    """Return (reason, matched_label) if the body signals STOP intent, else None.

    Body matching is intentionally conservative. The user-facing rule is a
    single bare 'STOP' (RFC-style) in a reply must trigger suppression, so
    we match \\bSTOP\\b on the literal uppercase token (most common form).
    All other phrases are case-insensitive.

    Only the first ~1000 chars are scanned: STOP is universally at the top
    of a reply, and looking deeper risks matching quoted text from our own
    outbound body.

    Bias: false positives are recoverable (human clears the row, prospect can
    reply again). False negatives are CAN-SPAM violations. We over-suppress.
    """
    if not body:
        return None
    head = body[:1000]
    for reason, pat, label in STOP_PATTERNS:
        if pat.search(head):
            return reason, label
    return None


# ── Lead lookup (canonical = Supabase via orchestrator/db.py) ─────────────────

def _supabase_conn():
    """Return a Supabase connection (preferred) or local fallback."""
    try:
        from orchestrator.db import get_crm_connection_with_fallback  # type: ignore
    except ModuleNotFoundError:
        sys.path.insert(0, "/app")
        from db import get_crm_connection_with_fallback  # type: ignore
    conn, _is_fb = get_crm_connection_with_fallback()
    return conn


def _mark_lead_opted_out(email: str, conn=None) -> Optional[int]:
    """Set opt_out=TRUE on the matching lead row (case-insensitive email).
    Returns the lead id flipped (or None if no match)."""
    owns_conn = conn is None
    try:
        if owns_conn:
            conn = _supabase_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE leads SET opt_out=TRUE, updated_at=NOW() "
            "WHERE lower(email) = lower(%s) "
            "  AND (opt_out IS NULL OR opt_out = FALSE) "
            "RETURNING id",
            (email,),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        if row is None:
            return None
        return row[0] if isinstance(row, tuple) else row.get("id")
    except Exception as e:
        logger.warning(f"mark_lead_opted_out({email}): {e}")
        return None
    finally:
        if owns_conn and conn is not None:
            try:
                conn.close()
            except Exception:
                pass


# ── STOP scanner core ─────────────────────────────────────────────────────────

INTERNAL_FROM = {
    "boubacar@catalystworks.consulting",
    "bokar83@gmail.com",
    "signal@catalystworks.consulting",
    "catalystworks.ai@gmail.com",
    "mailer-daemon",
    "postmaster",
}


def _get_message_full(token: str, msg_id: str) -> dict:
    """Get a full message including body (format=full)."""
    r = httpx.get(
        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"format": "full"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def _extract_text_body(msg: dict) -> str:
    """Walk the MIME tree and return the best-effort plaintext body."""
    import base64

    def _walk(part) -> str:
        mime = part.get("mimeType", "")
        body = part.get("body", {}) or {}
        data = body.get("data")
        if data and mime.startswith("text/"):
            try:
                return base64.urlsafe_b64decode(data + "===").decode("utf-8", errors="replace")
            except Exception:
                return ""
        out = ""
        for child in part.get("parts", []) or []:
            out += _walk(child)
        return out

    body_text = _walk(msg.get("payload", {}))
    if not body_text:
        body_text = msg.get("snippet", "") or ""
    return body_text


def _telegram_alert(text: str) -> None:
    """Best-effort Telegram alert. Non-fatal."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = (os.environ.get("TELEGRAM_CHAT_ID_BOUBACAR")
            or os.environ.get("TELEGRAM_CHAT_ID", ""))
    if not (token and chat):
        return
    try:
        httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat, "text": text, "parse_mode": "Markdown",
                  "disable_web_page_preview": True},
            timeout=10,
        )
    except Exception:
        pass


def scan_stop_replies(conn, token: str, since_iso: str) -> int:
    """Scan inbox replies since `since_iso`, classify STOP intent, write to
    email_suppressions + email_events + leads.opt_out.

    Returns the number of NEW suppressions created (existing rows skipped via
    ON CONFLICT)."""
    q = f"in:inbox after:{since_iso.replace('-','/')}"
    logger.info(f"STOP scan query: {q}")
    r = httpx.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": q, "maxResults": 500},
        timeout=30,
    )
    r.raise_for_status()
    ids = [m["id"] for m in r.json().get("messages", [])]
    logger.info(f"STOP scan: inspecting {len(ids)} inbound messages")

    if not ids:
        return 0

    # Single Supabase connection reused across all UPDATE lead rows in this run.
    supa = _supabase_conn()

    ins = conn.cursor()
    new_suppressions = 0
    for mid in ids:
        try:
            m = _get_message_full(token, mid)
        except Exception as e:
            logger.warning(f"  skip {mid}: {e}")
            continue

        hdrs = {h["name"].lower(): h["value"]
                for h in m.get("payload", {}).get("headers", [])}
        from_addr = parse_addr(hdrs.get("from", ""))
        if not from_addr or from_addr in INTERNAL_FROM:
            continue
        subject = hdrs.get("subject", "")
        tid = m.get("threadId", "")
        body = _extract_text_body(m)

        intent = classify_stop_intent(body)
        if intent is None:
            continue
        reason, matched = intent

        # Brand inferred from outbound rows on the same thread. Falls back to
        # 'cw' (the canonical CW outreach inbox).
        brand = "cw"
        try:
            cur2 = conn.cursor()
            cur2.execute(
                "SELECT brand FROM email_events "
                "WHERE gmail_thread_id=%s AND direction='outbound' "
                "ORDER BY occurred_at DESC LIMIT 1",
                (tid,),
            )
            row = cur2.fetchone()
            if row and row[0]:
                brand = row[0]
            cur2.close()
        except Exception:
            pass

        # 1. Suppression row (idempotent via partial unique index)
        ins.execute(
            """
            INSERT INTO email_suppressions
                (email, brand, reason, source, gmail_message_id,
                 gmail_thread_id, body_preview, matched_pattern, lead_id)
            VALUES (%s, %s, %s, 'reply_scanner', %s,
                    %s, %s, %s, NULL)
            ON CONFLICT (lower(email), COALESCE(brand, 'global'))
                WHERE unsuppressed_at IS NULL
            DO NOTHING
            RETURNING id
            """,
            (from_addr, brand, reason, mid, tid, body[:200], matched),
        )
        result = ins.fetchone()
        if not result:
            # Already suppressed; do not re-alert
            continue
        suppression_id = result[0]
        new_suppressions += 1

        # 2. Flip lead's opt_out in canonical DB (if a matching lead exists)
        lead_id = _mark_lead_opted_out(from_addr, conn=supa)
        if lead_id is not None:
            cur3 = conn.cursor()
            cur3.execute(
                "UPDATE email_suppressions SET lead_id=%s WHERE id=%s",
                (lead_id, suppression_id),
            )
            cur3.close()

        # 3. Log unsubscribed event into canonical email_events
        ts = int(m.get("internalDate", "0")) / 1000
        occurred = datetime.fromtimestamp(ts, tz=timezone.utc)
        ins.execute(
            """
            INSERT INTO email_events
                (brand, pipeline, direction, event_type,
                 to_addr, from_addr, subject,
                 gmail_message_id, gmail_thread_id, body_preview,
                 lead_id, metadata, occurred_at, recorded_at)
            VALUES (%s, NULL, 'inbound', 'unsubscribed',
                    'boubacar@catalystworks.consulting', %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, NOW())
            ON CONFLICT (brand, gmail_message_id, event_type)
                WHERE gmail_message_id IS NOT NULL
            DO NOTHING
            """,
            (
                brand,
                from_addr,
                subject,
                mid,
                tid,
                body[:200],
                lead_id,
                psycopg2.extras.Json({
                    "source": "scan_stop_replies",
                    "reason": reason,
                    "matched_pattern": matched,
                    "suppression_id": suppression_id,
                }),
                occurred,
            ),
        )

        # 4. Telegram alert (one-shot per new suppression)
        _telegram_alert(
            f"*STOP captured* (suppression id `{suppression_id}`)\n"
            f"`{from_addr}` -> brand `{brand}` reason `{reason}` matched `{matched}`\n"
            f"Subject: _{subject[:80]}_\n"
            f"Lead row flipped: "
            f"{('yes (#%s)' % lead_id) if lead_id else 'no -- not in leads table'}"
        )
        logger.info(
            f"SUPPRESSED {from_addr} brand={brand} reason={reason} "
            f"matched={matched} lead_id={lead_id}"
        )

    conn.commit()
    ins.close()
    try:
        supa.close()
    except Exception:
        pass
    logger.info(f"scan_stop_replies: {new_suppressions} new suppression(s) this run")
    return new_suppressions


# ── Main ──────────────────────────────────────────────────────────────────────

def _iso_n_days_ago(n: int) -> str:
    d = datetime.now(timezone.utc) - timedelta(days=n)
    return d.strftime("%Y-%m-%d")


def main():
    creds = os.environ.get(
        "GOOGLE_OAUTH_CREDENTIALS_JSON_CW",
        "/app/secrets/gws-oauth-credentials-cw.json",
    )
    conn = get_conn()
    ensure_table(conn)
    token = get_access_token(creds)

    # STOP scan FIRST so suppression lands before any downstream consumer of
    # 'replied'. Last 2 days, ON CONFLICT dedups across runs.
    n_stop = scan_stop_replies(conn, token, since_iso=_iso_n_days_ago(2))

    # Bounces: last 7d on every run. Cheap (typically < 50 messages).
    n_b = backfill_bounces(conn, token, since_iso=_iso_n_days_ago(7))

    # Replies: walk threads we have outbound rows for.
    n_r = backfill_replies(conn, token)

    logger.info(
        f"sync_replies: +{n_r} replies, +{n_b} bounces, +{n_stop} STOP-suppressions"
    )
    conn.close()


if __name__ == "__main__":
    main()
