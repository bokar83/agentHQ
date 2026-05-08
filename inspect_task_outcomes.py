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

    # Column inspection
    cur.execute(
        """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'task_outcomes';
    """
    )
    cols = cur.fetchall()
    print("Columns in task_outcomes:")
    for col in cols:
        print(f" - {col[0]} ({col[1]})")

    # Row count
    cur.execute("SELECT COUNT(*) FROM task_outcomes;")
    count = cur.fetchone()[0]
    print(f"\nTotal rows in task_outcomes: {count}")

    # Sample rows
    if count > 0:
        cur.execute("SELECT * FROM task_outcomes LIMIT 3;")
        import psycopg2.extras

        dict_cur = conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        dict_cur.execute("SELECT * FROM task_outcomes LIMIT 3;")
        samples = dict_cur.fetchall()
        print("\nSample rows:")
        for s in samples:
            print(dict(s))
        dict_cur.close()

    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
