"""
db.py — Database connection utilities for agentsHQ
===================================================
Provides connections to Supabase (CRM) and local Postgres (task queue).
All agents and tools import from here.
"""

import os
import logging

logger = logging.getLogger(__name__)


def get_crm_connection():
    """
    Return a psycopg2 connection to the Supabase CRM database.
    Uses SUPABASE_DB_URL from environment.
    """
    import psycopg2
    import psycopg2.extras

    url = os.environ.get("SUPABASE_DB_URL")
    if not url:
        raise RuntimeError("SUPABASE_DB_URL environment variable is not set.")

    conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn


def get_local_connection():
    """
    Return a psycopg2 connection to the local Postgres database (task queue, chat history, etc).
    Uses individual POSTGRES_* env vars.
    """
    import psycopg2
    import psycopg2.extras

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        dbname=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    return conn
