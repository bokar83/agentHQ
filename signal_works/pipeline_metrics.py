"""
signal_works/pipeline_metrics.py
================================
Per-step instrumentation for the daily harvest+outreach pipeline.

Two tables:
  pipeline_metrics  -- (run_date, step, attempted, succeeded, skipped, reason, ts)
  apollo_credits    -- (date, credits_used, source) -- daily Apollo budget tracking

Why:
  Without this, we diagnose volume problems by tail-grepping logs. With it,
  we can answer "yesterday CW personalize ran on 15 leads, 7 succeeded,
  8 skipped with reason='thin_text'" via SQL.

Apollo budget guard:
  Read today's credits_used. If +cost would exceed APOLLO_DAILY_BUDGET (env
  override; default 500), refuse the call. Prevents runaway spend.
"""
import logging
import os
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger(__name__)


def _conn():
    """Get DB connection. Container path first, dev path second."""
    try:
        from orchestrator.db import get_crm_connection
    except ModuleNotFoundError:
        import sys
        sys.path.insert(0, "/app")
        from db import get_crm_connection  # type: ignore
    return get_crm_connection()


def _ensure_tables() -> None:
    """Idempotent table creation. Safe to call every run."""
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_metrics (
                id          SERIAL PRIMARY KEY,
                run_date    DATE NOT NULL DEFAULT CURRENT_DATE,
                step        TEXT NOT NULL,
                attempted   INTEGER NOT NULL DEFAULT 0,
                succeeded   INTEGER NOT NULL DEFAULT 0,
                skipped     INTEGER NOT NULL DEFAULT 0,
                reason      TEXT,
                ts          TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS pipeline_metrics_run_date_idx
            ON pipeline_metrics(run_date, step)
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS apollo_credits (
                id           SERIAL PRIMARY KEY,
                used_date    DATE NOT NULL DEFAULT CURRENT_DATE,
                credits_used INTEGER NOT NULL,
                source       TEXT NOT NULL,
                ts           TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS apollo_credits_used_date_idx
            ON apollo_credits(used_date)
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"pipeline_metrics: ensure_tables failed: {e}")


def log_step(step: str, attempted: int = 0, succeeded: int = 0,
             skipped: int = 0, reason: Optional[str] = None) -> None:
    """Log one row of step-level metrics. Best-effort, never raises."""
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO pipeline_metrics (step, attempted, succeeded, skipped, reason)
            VALUES (%s, %s, %s, %s, %s)
        """, (step, attempted, succeeded, skipped, reason))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"pipeline_metrics: log_step({step}) failed: {e}")


def log_apollo_credits(credits: int, source: str) -> None:
    """Record Apollo credits consumed by source. Best-effort."""
    if credits <= 0:
        return
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO apollo_credits (credits_used, source)
            VALUES (%s, %s)
        """, (credits, source))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"pipeline_metrics: log_apollo_credits failed: {e}")


def apollo_credits_used_today() -> int:
    """Return total Apollo credits used today. 0 on failure (fail-open)."""
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(credits_used), 0) AS total
            FROM apollo_credits
            WHERE used_date = CURRENT_DATE
        """)
        row = cur.fetchone()
        conn.close()
        return int(row["total"] if row else 0)
    except Exception as e:
        logger.warning(f"pipeline_metrics: apollo_credits_used_today failed: {e}")
        return 0


def apollo_check_budget(cost: int = 1) -> bool:
    """
    True = safe to spend. False = would exceed daily budget.
    Default budget = 500/day (override via APOLLO_DAILY_BUDGET env).

    Fail-open: if DB is unreachable, return True. Prevents the budget guard
    itself from breaking the pipeline.
    """
    try:
        budget = int(os.environ.get("APOLLO_DAILY_BUDGET", "500"))
    except (TypeError, ValueError):
        budget = 500
    used = apollo_credits_used_today()
    if used + cost > budget:
        logger.warning(
            f"apollo_check_budget: would exceed daily budget ({used}+{cost} > {budget}). Skipping."
        )
        return False
    return True


# Auto-create tables on import (idempotent).
_ensure_tables()
