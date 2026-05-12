#!/usr/bin/env python3
"""
scripts/sync_replies_from_gmail.py
====================================
Cron-driven reply + bounce scanner. Inserts 'replied' and 'bounced' events
into email_events for any new inbound messages since the last run.

State is implicit: ON CONFLICT DO NOTHING on (brand, gmail_message_id, event_type)
makes the script idempotent. It can run every 15 min indefinitely without
deduplication logic of its own.

Cron (on VPS host):
  */15 * * * *  docker exec orc-crewai python3 /app/scripts/sync_replies_from_gmail.py >> /var/log/sync_replies.log 2>&1

This is the smaller incremental version of backfill_email_events.py. It only
scans recent inbox messages (last 24h) so the cron run is fast.
"""

import logging
import os
import sys
from pathlib import Path

# Reuse helpers from the backfill script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backfill_email_events import (
    get_conn, ensure_table, get_access_token,
    backfill_bounces, backfill_replies,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    creds = os.environ.get(
        "GOOGLE_OAUTH_CREDENTIALS_JSON_CW",
        "/app/secrets/gws-oauth-credentials-cw.json",
    )
    conn = get_conn()
    ensure_table(conn)
    token = get_access_token(creds)

    # Bounces: scan the last 7d on every run; ON CONFLICT dedups.
    # Cheap (typically < 50 messages).
    n_b = backfill_bounces(conn, token, since_iso=_iso_n_days_ago(7))
    # Replies: walk threads we've sent to. Naturally bounded by the size of
    # the outbound thread set, currently ~450.
    n_r = backfill_replies(conn, token)

    logger.info(f"sync_replies: +{n_r} replies, +{n_b} bounces this run")
    conn.close()


def _iso_n_days_ago(n: int) -> str:
    from datetime import datetime, timedelta, timezone
    d = datetime.now(timezone.utc) - timedelta(days=n)
    return d.strftime("%Y-%m-%d")


if __name__ == "__main__":
    main()
