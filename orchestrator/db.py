"""
db.py — Database connection utilities for agentsHQ
===================================================
Supabase is the primary CRM database.
Local Postgres is the fallback -- used only when Supabase is unreachable.
A background sync job moves any local fallback data to Supabase when it recovers.

Rule: Local Postgres leads table should always be empty.
      If it has rows, Supabase was unreachable and a sync is needed.
"""

import os
import logging

logger = logging.getLogger(__name__)


def get_crm_connection():
    """
    Return a psycopg2 connection to the Supabase CRM database.
    Builds connection from SUPABASE_HOST, SUPABASE_USER, SUPABASE_PASSWORD, SUPABASE_DB
    to avoid shell escaping issues with special characters in the password.
    """
    import psycopg2
    import psycopg2.extras

    import base64
    host = os.environ.get("SUPABASE_HOST")
    user = os.environ.get("SUPABASE_USER")
    # Password stored as base64 to survive Docker/shell variable interpolation of special chars
    password_b64 = os.environ.get("SUPABASE_PASSWORD_B64")
    password = base64.b64decode(password_b64).decode("utf-8") if password_b64 else None
    dbname = os.environ.get("SUPABASE_DB", "postgres")
    port = int(os.environ.get("SUPABASE_PORT", 6543))

    if not all([host, user, password]):
        raise RuntimeError("Supabase connection vars not set (SUPABASE_HOST, SUPABASE_USER, SUPABASE_PASSWORD_B64).")

    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        connect_timeout=5,
        cursor_factory=psycopg2.extras.RealDictCursor,
        sslmode="require",
    )
    return conn


def get_local_connection():
    """
    Return a psycopg2 connection to the local Postgres database.
    Used as fallback when Supabase is unreachable, and for task queue / chat history.
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


def get_crm_connection_with_fallback() -> tuple:
    """
    Try Supabase first. If unavailable, fall back to local Postgres.
    Returns (conn, is_fallback) tuple.
    Callers should log a warning if is_fallback is True.
    """
    try:
        conn = get_crm_connection()
        return conn, False
    except Exception as e:
        logger.warning(f"Supabase unavailable ({e}), falling back to local Postgres.")
        conn = get_local_connection()
        return conn, True


def sync_fallback_to_supabase() -> int:
    """
    Move any leads written to local Postgres fallback back to Supabase.
    Called on orchestrator startup and periodically by the scheduler.
    Returns number of rows synced.
    """
    import psycopg2.extras

    try:
        local_conn = get_local_connection()
        local_cur = local_conn.cursor()

        # Check for any leads in local fallback
        local_cur.execute("SELECT * FROM leads ORDER BY created_at ASC")
        rows = local_cur.fetchall()

        if not rows:
            local_cur.close()
            local_conn.close()
            return 0

        logger.info(f"Sync: found {len(rows)} fallback lead(s) to sync to Supabase.")

        supabase_conn = get_crm_connection()
        supabase_cur = supabase_conn.cursor()

        synced = 0
        for row in rows:
            try:
                supabase_cur.execute("""
                    INSERT INTO leads
                        (name, company, title, location, phone, linkedin_url, email,
                         industry, source, status, last_contacted_at, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    row['name'], row['company'], row['title'], row['location'],
                    row['phone'], row['linkedin_url'], row['email'],
                    row['industry'], row['source'], row['status'],
                    row.get('last_contacted_at'), row['created_at'], row['updated_at'],
                ))
                synced += 1
            except Exception as e:
                logger.error(f"Sync: failed to insert lead {row.get('name')}: {e}")

        supabase_conn.commit()
        supabase_cur.close()
        supabase_conn.close()

        # Clear local fallback rows that were synced
        local_cur.execute("DELETE FROM leads WHERE id = ANY(%s)", ([r['id'] for r in rows],))
        local_conn.commit()
        local_cur.close()
        local_conn.close()

        logger.info(f"Sync: {synced} lead(s) moved from local Postgres to Supabase.")
        return synced

    except Exception as e:
        logger.error(f"sync_fallback_to_supabase failed: {e}")
        return 0
