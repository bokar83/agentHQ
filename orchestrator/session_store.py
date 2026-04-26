"""
session_store.py - Agent session persistence (local Postgres).

Provides upsert/touch/get operations on the agent_sessions table
so session state survives container restarts.

All functions use get_local_connection() per the hard rule:
local Postgres only (not Supabase) for operational agentsHQ data.
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("agentsHQ.session_store")


def ensure_table() -> None:
    """Create agent_sessions if it does not exist (idempotent)."""
    from db import get_local_connection

    sql = """
    CREATE TABLE IF NOT EXISTS agent_sessions (
        session_id     TEXT PRIMARY KEY,
        agent_name     TEXT NOT NULL DEFAULT 'chat',
        from_number    TEXT,
        channel        TEXT NOT NULL DEFAULT 'telegram',
        started_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        last_active_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        turn_count     INTEGER NOT NULL DEFAULT 0,
        meta           JSONB NOT NULL DEFAULT '{}'
    );
    CREATE INDEX IF NOT EXISTS idx_agent_sessions_from_number
        ON agent_sessions (from_number, last_active_at DESC);
    CREATE INDEX IF NOT EXISTS idx_agent_sessions_agent_name
        ON agent_sessions (agent_name, last_active_at DESC);
    """
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        cur.close()
    finally:
        conn.close()


def upsert_session(
    session_id: str,
    agent_name: str = "chat",
    from_number: Optional[str] = None,
    channel: str = "telegram",
    meta: Optional[dict] = None,
) -> None:
    """
    Create or update a session row. On conflict (same session_id),
    updates last_active_at and increments turn_count.
    """
    import json
    from db import get_local_connection

    meta_json = json.dumps(meta or {})
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO agent_sessions
                (session_id, agent_name, from_number, channel, meta)
            VALUES (%s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (session_id) DO UPDATE SET
                last_active_at = NOW(),
                turn_count     = agent_sessions.turn_count + 1,
                meta           = EXCLUDED.meta
            """,
            (session_id, agent_name, from_number, channel, meta_json),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning(f"upsert_session failed for {session_id}: {e}")
    finally:
        conn.close()


def touch_session(session_id: str) -> None:
    """Update last_active_at and increment turn_count for an existing session."""
    from db import get_local_connection

    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE agent_sessions
               SET last_active_at = NOW(),
                   turn_count     = turn_count + 1
             WHERE session_id = %s
            """,
            (session_id,),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning(f"touch_session failed for {session_id}: {e}")
    finally:
        conn.close()


def get_session(session_id: str) -> Optional[dict]:
    """Return the session row as a dict, or None if not found."""
    from db import get_local_connection

    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM agent_sessions WHERE session_id = %s",
            (session_id,),
        )
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None
    except Exception as e:
        logger.warning(f"get_session failed for {session_id}: {e}")
        return None
    finally:
        conn.close()


def list_active_sessions(agent_name: Optional[str] = None, limit: int = 20) -> list:
    """
    Return the most recently active sessions, optionally filtered by agent_name.
    """
    from db import get_local_connection

    conn = get_local_connection()
    try:
        cur = conn.cursor()
        if agent_name:
            cur.execute(
                """
                SELECT * FROM agent_sessions
                 WHERE agent_name = %s
                 ORDER BY last_active_at DESC
                 LIMIT %s
                """,
                (agent_name, limit),
            )
        else:
            cur.execute(
                "SELECT * FROM agent_sessions ORDER BY last_active_at DESC LIMIT %s",
                (limit,),
            )
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"list_active_sessions failed: {e}")
        return []
    finally:
        conn.close()
