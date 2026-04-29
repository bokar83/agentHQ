import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestrator.db import get_local_connection, ensure_leads_columns


def test_ensure_leads_columns_creates_no_website():
    conn = get_local_connection()
    ensure_leads_columns(conn)
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='leads' AND column_name IN
        ('no_website', 'email_source', 'last_drafted_at')
    """)
    rows = {r["column_name"] for r in cur.fetchall()}
    conn.close()
    assert rows == {"no_website", "email_source", "last_drafted_at"}


def test_get_resend_queue_returns_oldest_uncontacted():
    from orchestrator.db import get_resend_queue, get_local_connection
    conn = get_local_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS apollo_revealed (
            apollo_id TEXT PRIMARY KEY,
            revealed_at TIMESTAMPTZ DEFAULT NOW(),
            email TEXT, name TEXT
        )
    """)
    cur.execute("DELETE FROM apollo_revealed WHERE apollo_id LIKE 'test_%'")
    cur.execute("""
        INSERT INTO apollo_revealed (apollo_id, revealed_at, email, name) VALUES
        ('test_old', NOW() - INTERVAL '120 days', 'old@example.com', 'Old Person'),
        ('test_recent', NOW() - INTERVAL '30 days', 'recent@example.com', 'Recent Person')
    """)
    conn.commit()
    conn.close()
    try:
        queue = get_resend_queue(limit=5, days_back=60)
        emails = [r["email"] for r in queue]
        assert "old@example.com" in emails
        assert "recent@example.com" not in emails
    finally:
        conn2 = get_local_connection()
        cur2 = conn2.cursor()
        cur2.execute("DELETE FROM apollo_revealed WHERE apollo_id LIKE 'test_%'")
        conn2.commit()
        conn2.close()
