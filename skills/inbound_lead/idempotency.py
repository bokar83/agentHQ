"""Postgres idempotency for inbound lead enrichment."""
from __future__ import annotations
import os
from datetime import datetime
from typing import Optional, Literal
import psycopg2


def _get_conn():
    """Return a new psycopg2 connection. Caller owns lifetime."""
    dsn = os.environ.get("POSTGRES_DSN") or os.environ.get("SUPABASE_DB_URL")
    if not dsn:
        raise RuntimeError("POSTGRES_DSN or SUPABASE_DB_URL must be set")
    return psycopg2.connect(dsn)


def has_been_enriched(email: str) -> Optional[dict]:
    """Return the enrichment row for this email, or None if never enriched."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT email, first_booking, enriched_at, last_booking,
                       last_meeting_at, status
                FROM inbound_lead_enrichment
                WHERE email = %s
                """,
                (email,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return {
                "email": row[0],
                "first_booking": row[1],
                "enriched_at": row[2],
                "last_booking": row[3],
                "last_meeting_at": row[4],
                "status": row[5],
            }
    finally:
        conn.close()


def mark_enriched(
    email: str,
    booking_id: str,
    meeting_time: Optional[datetime],
    status: Literal["enriched", "partial", "failed"],
) -> None:
    """Insert or update the enrichment row."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO inbound_lead_enrichment
                    (email, first_booking, last_booking, last_meeting_at, status)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    last_booking = EXCLUDED.last_booking,
                    last_meeting_at = EXCLUDED.last_meeting_at,
                    status = EXCLUDED.status
                """,
                (email, booking_id, booking_id, meeting_time, status),
            )
        conn.commit()
    finally:
        conn.close()


def mark_rebook(
    email: str,
    booking_id: str,
    meeting_time: Optional[datetime],
) -> None:
    """Update last_booking and last_meeting_at on a known email."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE inbound_lead_enrichment
                SET last_booking = %s,
                    last_meeting_at = %s
                WHERE email = %s
                """,
                (booking_id, meeting_time, email),
            )
        conn.commit()
    finally:
        conn.close()
