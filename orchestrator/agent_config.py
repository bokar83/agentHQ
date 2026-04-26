"""
agent_config.py - DB-driven runtime configuration (local Postgres).

Provides a two-layer config lookup:
  1. agent_config table in local Postgres (live overrides, no restart needed)
  2. Environment variable fallback
  3. Hardcoded default

Usage:
    from agent_config import get_config, set_config

    model = get_config("CHAT_MODEL", default="anthropic/claude-haiku-4.5")
    set_config("CHAT_MODEL", "anthropic/claude-sonnet-4-5")

All writes go to Postgres only. The env var layer is read-only fallback.
Container restart is never needed to change a config value.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger("agentsHQ.agent_config")

_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS agent_config (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    note       TEXT
);
"""


def ensure_table() -> None:
    """Create agent_config if it does not exist (idempotent)."""
    from db import get_local_connection

    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(_TABLE_SQL)
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning(f"ensure_table failed: {e}")
    finally:
        conn.close()


def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Look up a config value. Priority: DB row > env var > default.
    Non-fatal on DB error (falls through to env/default).
    """
    try:
        from db import get_local_connection

        conn = get_local_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT value FROM agent_config WHERE key = %s", (key,))
            row = cur.fetchone()
            cur.close()
            if row:
                return row["value"]
        finally:
            conn.close()
    except Exception as e:
        logger.debug(f"get_config DB lookup failed for {key}: {e}")

    env_val = os.environ.get(key)
    if env_val is not None:
        return env_val

    return default


def set_config(key: str, value: str, note: Optional[str] = None) -> bool:
    """
    Write or update a config value in Postgres.
    Returns True on success, False on error.
    """
    from db import get_local_connection

    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO agent_config (key, value, updated_at, note)
            VALUES (%s, %s, NOW(), %s)
            ON CONFLICT (key) DO UPDATE SET
                value      = EXCLUDED.value,
                updated_at = NOW(),
                note       = COALESCE(EXCLUDED.note, agent_config.note)
            """,
            (key, value, note),
        )
        conn.commit()
        cur.close()
        logger.info(f"set_config: {key}={value!r}")
        return True
    except Exception as e:
        logger.warning(f"set_config failed for {key}: {e}")
        return False
    finally:
        conn.close()


def delete_config(key: str) -> bool:
    """Remove a config override, reverting to env var or default."""
    from db import get_local_connection

    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM agent_config WHERE key = %s", (key,))
        conn.commit()
        deleted = cur.rowcount > 0
        cur.close()
        logger.info(f"delete_config: {key} ({'removed' if deleted else 'not found'})")
        return deleted
    except Exception as e:
        logger.warning(f"delete_config failed for {key}: {e}")
        return False
    finally:
        conn.close()


def list_config() -> list:
    """Return all config rows as list of dicts."""
    from db import get_local_connection

    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT key, value, updated_at, note FROM agent_config ORDER BY key")
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"list_config failed: {e}")
        return []
    finally:
        conn.close()
