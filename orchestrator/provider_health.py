"""
provider_health.py - Circuit breaker state for LLM providers.

One row per provider in the provider_health table. Only 'openrouter' in v1.
All writes are to the local Postgres instance (same as agent_config).

States:
  healthy  - provider is responding normally
  tripped  - 3+ failures in 5 minutes; LLM calls are paused + Telegram alert sent
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger("agentsHQ.provider_health")

try:
    from db import get_local_connection
except ImportError:
    get_local_connection = None  # type: ignore[assignment]

_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS provider_health (
    id            SERIAL PRIMARY KEY,
    provider      TEXT NOT NULL UNIQUE DEFAULT 'openrouter',
    status        TEXT NOT NULL DEFAULT 'healthy',
    fail_count    INT  NOT NULL DEFAULT 0,
    window_start  TIMESTAMPTZ,
    tripped_at    TIMESTAMPTZ,
    recovered_at  TIMESTAMPTZ,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

_SEED_SQL = """
INSERT INTO provider_health (provider, status)
VALUES ('openrouter', 'healthy')
ON CONFLICT (provider) DO NOTHING;
"""

TRIP_THRESHOLD = 3        # failures before tripping
TRIP_WINDOW_SECONDS = 300 # 5 minutes


def ensure_table() -> None:
    """Create provider_health table and seed openrouter row (idempotent)."""
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(_TABLE_SQL)
        cur.execute(_SEED_SQL)
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning(f"provider_health.ensure_table failed: {e}")
    finally:
        conn.close()


def get_status(provider: str = "openrouter") -> dict:
    """Return the current row for provider as a dict. Returns defaults if missing."""
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT provider, status, fail_count, window_start, tripped_at, recovered_at "
            "FROM provider_health WHERE provider = %s",
            (provider,)
        )
        row = cur.fetchone()
        if not row:
            return {"provider": provider, "status": "healthy", "fail_count": 0,
                    "window_start": None, "tripped_at": None, "recovered_at": None}
        return {
            "provider": row[0], "status": row[1], "fail_count": row[2],
            "window_start": row[3], "tripped_at": row[4], "recovered_at": row[5],
        }
    except Exception as e:
        logger.warning(f"provider_health.get_status failed: {e}")
        return {"provider": provider, "status": "healthy", "fail_count": 0,
                "window_start": None, "tripped_at": None, "recovered_at": None}
    finally:
        conn.close()


def record_failure(provider: str = "openrouter") -> dict:
    """
    Increment fail_count. Start window on first failure.
    Return updated row dict. Does NOT send Telegram (caller handles alerting).
    """
    now = datetime.now(timezone.utc)
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT fail_count, window_start, status FROM provider_health WHERE provider = %s",
            (provider,)
        )
        row = cur.fetchone()
        if not row:
            ensure_table()
            fail_count, window_start, status = 0, None, "healthy"
        else:
            fail_count, window_start, status = row[0], row[1], row[2]

        # Start window on first failure; reset count only when window has expired
        if window_start is None:
            window_start = now
        elif (now - window_start).total_seconds() > TRIP_WINDOW_SECONDS:
            window_start = now
            fail_count = 0

        fail_count += 1
        new_status = status
        tripped_at = None

        if fail_count >= TRIP_THRESHOLD and status != "tripped":
            new_status = "tripped"
            tripped_at = now
            logger.warning(f"CIRCUIT TRIPPED: {provider} hit {fail_count} failures in window.")

        cur.execute(
            """
            UPDATE provider_health
               SET fail_count = %s,
                   window_start = %s,
                   status = %s,
                   tripped_at = COALESCE(%s, tripped_at),
                   updated_at = NOW()
             WHERE provider = %s
            """,
            (fail_count, window_start, new_status, tripped_at, provider)
        )
        conn.commit()
        cur.close()
        return {"provider": provider, "status": new_status, "fail_count": fail_count,
                "just_tripped": (new_status == "tripped" and tripped_at is not None)}
    except Exception as e:
        logger.warning(f"provider_health.record_failure failed: {e}")
        return {"provider": provider, "status": "unknown", "fail_count": 0, "just_tripped": False}
    finally:
        conn.close()


def record_recovery(provider: str = "openrouter") -> None:
    """Mark provider healthy after a successful probe."""
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE provider_health
               SET status = 'healthy',
                   fail_count = 0,
                   window_start = NULL,
                   recovered_at = NOW(),
                   updated_at = NOW()
             WHERE provider = %s
            """,
            (provider,)
        )
        conn.commit()
        cur.close()
        logger.info(f"CIRCUIT RECOVERED: {provider} marked healthy.")
    except Exception as e:
        logger.warning(f"provider_health.record_recovery failed: {e}")
    finally:
        conn.close()
