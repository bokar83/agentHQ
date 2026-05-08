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
    cur.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
    )
    tables = cur.fetchall()
    print("Available tables in Postgres public schema:")
    for t in tables:
        print(f" - {t[0]}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error querying public schema: {e}")
