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
