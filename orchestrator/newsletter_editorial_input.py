"""
newsletter_editorial_input.py - Postgres CRUD for the weekly editorial reply.

The Sunday 18:00 MT prompt asks Boubacar one question. Any free-text reply
between Sun 18:00 and Mon 06:00 in the operator chat is captured here, keyed
by the upcoming Monday's date. Last write wins.

Mon 06:00 anchor selection reads this; if a row exists, the reply text becomes
the newsletter user request.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

logger = logging.getLogger("agentsHQ.newsletter_editorial_input")


def _conn():
    """Open a Postgres connection lazily for easier test patching."""
    from memory import _pg_conn
    return _pg_conn()


def upsert_reply(week_start_date: date, reply_text: str, chat_id: str) -> None:
    """Insert or replace the weekly editorial reply. Last write wins."""
    conn = _conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO newsletter_editorial_input
                (week_start_date, reply_text, chat_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (week_start_date)
            DO UPDATE SET
                reply_text = EXCLUDED.reply_text,
                received_at = NOW(),
                chat_id = EXCLUDED.chat_id
            """,
            (week_start_date, reply_text, chat_id),
        )
    conn.commit()
    logger.info(
        "newsletter_editorial_input: upsert week_start=%s chat=%s text_len=%s",
        week_start_date,
        chat_id,
        len(reply_text),
    )


def get_reply_for_week(week_start_date: date) -> Optional[str]:
    """Return the stored reply for the given Monday, or None."""
    conn = _conn()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT reply_text FROM newsletter_editorial_input WHERE week_start_date = %s",
            (week_start_date,),
        )
        row = cur.fetchone()
    return row[0] if row else None
