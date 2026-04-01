"""
db.py — Centralized Database Connection Utility
================================================
Single source of truth for all database connections in agentsHQ.

CRM data (leads, lead_interactions) → Supabase (SUPABASE_DB_URL)
System data (conversation history, job queue, logs) → VPS Postgres (POSTGRES_HOST)

Never import psycopg2 directly in skill files — always use this module.
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def get_crm_connection():
    """
    Returns a psycopg2 connection to Supabase (CRM data).
    Uses the Transaction Pooler URL for container-safe connection management.
    Reads: SUPABASE_DB_URL environment variable.
    """
    url = os.environ.get("SUPABASE_DB_URL")
    if not url:
        raise RuntimeError("SUPABASE_DB_URL is not set. Add it to your .env file.")
    return psycopg2.connect(url, cursor_factory=RealDictCursor)


def get_system_connection():
    """
    Returns a psycopg2 connection to VPS Postgres (system/log data).
    Used for: conversation_archive, job_queue, council_runs, security_events.
    """
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "orc-postgres"),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        port=5432,
    )
