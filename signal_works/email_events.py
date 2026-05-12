"""
signal_works/email_events.py
============================
Shared writer for the email_events ledger (migration 009).

Every send-call site in the codebase should call log_event() after a successful
send / draft / bounce / reply detection. This is the only path that writes to
email_events outside the backfill script and the reply-sync cron.

All inserts are best-effort: any DB error is logged at warning level and
swallowed so the caller's send path is never broken by a logging failure.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def _connect():
    import psycopg2
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "orc-postgres"),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
    )


def log_event(
    *,
    brand: str,                          # 'cw' | 'sw' | 'studio' | 'gw' | 'unknown'
    event_type: str,                     # 'sent' | 'drafted' | 'replied' | 'bounced' | 'failed' | 'dry-run' | ...
    to_addr: str,
    from_addr: str = "boubacar@catalystworks.consulting",
    subject: Optional[str] = None,
    gmail_message_id: Optional[str] = None,
    gmail_thread_id: Optional[str] = None,
    pipeline: Optional[str] = None,      # e.g. 'sequence_t1', 'cold_teardown'
    direction: str = "outbound",
    lead_id: Optional[int] = None,
    body_preview: Optional[str] = None,
    metadata: Optional[dict] = None,
    occurred_at: Optional[datetime] = None,
) -> bool:
    """Insert one row into email_events. Returns True on success, False on (logged) failure.

    Idempotent: hits the (brand, gmail_message_id, event_type) unique partial
    index when gmail_message_id is non-NULL, so re-sends of the same event id
    silently no-op."""
    try:
        import psycopg2.extras
    except Exception as e:
        logger.warning(f"email_events.log_event: psycopg2 not available, skip ({e})")
        return False

    if occurred_at is None:
        occurred_at = datetime.now(timezone.utc)

    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO email_events
                (brand, pipeline, direction, event_type,
                 to_addr, from_addr, subject,
                 gmail_message_id, gmail_thread_id, body_preview,
                 lead_id, metadata,
                 occurred_at, recorded_at)
            VALUES (%s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, NOW())
            ON CONFLICT (brand, gmail_message_id, event_type)
                WHERE gmail_message_id IS NOT NULL
            DO NOTHING
        """, (
            brand, pipeline, direction, event_type,
            to_addr, from_addr, (subject or "")[:500],
            gmail_message_id, gmail_thread_id,
            (body_preview or "")[:200],
            lead_id,
            psycopg2.extras.Json(metadata) if metadata else None,
            occurred_at,
        ))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.warning(f"email_events.log_event failed (non-fatal): {e}")
        return False
