import os
import sys

sys.path.append("orchestrator")
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["POSTGRES_USER"] = "postgres"
os.environ["POSTGRES_DB"] = "postgres"

from skills.coordination import _connect

try:
    conn = _connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'daily_scoreboard';
    """)
    cols = cur.fetchall()
    print("Columns in daily_scoreboard:")
    for col in cols:
        print(f" - {col[0]} ({col[1]})")

    cur.execute("SELECT COUNT(*) FROM daily_scoreboard;")
    print(f"Row count: {cur.fetchone()[0]}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
