"""
absorb_inbound.py -- ingress for the absorb_crew agent.

Two callers today:
  - Telegram bot handler (forward a URL/post to the @CCagentsHQ_bot)
  - CC skill (skills/agentshq-absorb in AGENT MODE; calls the CLI below)

A third class (scout adapters) lands in Phase 2.

Every ingress writes one row to absorb_queue with status=pending. The
absorb_crew heartbeat tick picks pending rows up on its next wake.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Optional

logger = logging.getLogger("agentsHQ.absorb_inbound")

VALID_SOURCES = (
    "telegram", "cc",
    "scout-x", "scout-reddit", "scout-gh", "scout-hn",
)


def _conn():
    from memory import _pg_conn
    return _pg_conn()


def enqueue(
    url: str,
    source: str,
    submitted_by: Optional[str] = None,
) -> int:
    """Insert one pending row. Returns absorb_queue.id."""
    if source not in VALID_SOURCES:
        raise ValueError(f"unknown source {source!r}; valid: {VALID_SOURCES}")
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"url must start with http(s)://, got {url!r}")

    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO absorb_queue (source, url, submitted_by, status)
        VALUES (%s, %s, %s, 'pending')
        RETURNING id
        """,
        (source, url, submitted_by),
    )
    row_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    logger.info(f"absorb_inbound: enqueued #{row_id} ({source}) {url}")
    return row_id


def find_duplicate(url: str) -> Optional[int]:
    """Return the id of the most recent done row with this URL, or None.
    Caller uses this to avoid re-processing the same artifact silently.
    """
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id FROM absorb_queue
         WHERE url = %s AND status = 'done'
         ORDER BY ts_received DESC
         LIMIT 1
        """,
        (url,),
    )
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None


def _main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="absorb_inbound")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_enq = sub.add_parser("enqueue", help="Queue an artifact for absorb_crew")
    p_enq.add_argument("url")
    p_enq.add_argument("--source", required=True, choices=VALID_SOURCES)
    p_enq.add_argument("--by", default=None, help="submitted_by tag (optional)")

    args = parser.parse_args(argv)
    if args.cmd == "enqueue":
        prior = find_duplicate(args.url)
        if prior is not None:
            print(json.dumps({"status": "duplicate", "prior_id": prior, "url": args.url}))
            return 0
        row_id = enqueue(args.url, args.source, submitted_by=args.by)
        print(json.dumps({"status": "queued", "id": row_id, "url": args.url, "source": args.source}))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(_main())
