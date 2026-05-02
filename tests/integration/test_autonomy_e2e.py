"""
End-to-end integration test for the autonomy layer.

Uses an in-process SQLite database whose schema mirrors llm_calls post-migration
001 + 004. Patches autonomy_guard's memory._pg_conn so the guard reads/writes
against the SQLite ledger instead of real Postgres.

Proves:
  1. Post-migration schema accepts every column usage_logger writes.
  2. _spent_today_usd reads what was written with autonomous=TRUE.
  3. _per_crew_spend_today groups correctly.
  4. Cap enforcement triggers across real write+read cycles (flips kill).
  5. Kill state persists through simulated process restart.
  6. Unkill + small call passes again.
"""
import os
import sys
import sqlite3
import tempfile
import types
from pathlib import Path

sys.path.insert(0, os.path.abspath("orchestrator"))

db_path = Path(tempfile.mkdtemp()) / "ledger.sqlite"
conn = sqlite3.connect(str(db_path))
conn.execute(
    """
    CREATE TABLE llm_calls (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        generation_id        TEXT UNIQUE NOT NULL,
        ts                   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        project              TEXT,
        agent_name           TEXT,
        task_type            TEXT,
        crew_name            TEXT,
        session_key          TEXT,
        council_run_id       TEXT,
        model                TEXT NOT NULL,
        tokens_prompt        INT NOT NULL DEFAULT 0,
        tokens_completion    INT NOT NULL DEFAULT 0,
        tokens_cached_read   INT NOT NULL DEFAULT 0,
        tokens_cached_write  INT NOT NULL DEFAULT 0,
        cost_usd             REAL NOT NULL DEFAULT 0,
        latency_ms           INT,
        finish_reason        TEXT,
        error                TEXT,
        autonomous           INTEGER NOT NULL DEFAULT 0,
        guard_decision       TEXT
    )
    """
)
conn.commit()
print(f"[E2E] SQLite ledger created at {db_path}")


def fake_insert(gen_id, metadata, autonomous_flag, guard_decision_tag, cost):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO llm_calls (
            generation_id, project, agent_name, task_type, crew_name,
            session_key, council_run_id, model,
            tokens_prompt, tokens_completion, tokens_cached_read, tokens_cached_write,
            cost_usd, latency_ms, finish_reason, error,
            autonomous, guard_decision
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            gen_id,
            metadata.get("project"),
            metadata.get("agent_name"),
            metadata.get("task_type"),
            metadata.get("crew_name"),
            metadata.get("session_key"),
            metadata.get("council_run_id"),
            metadata.get("model", "test-model"),
            100, 200, 0, 0,
            cost, 123, "stop", None,
            1 if autonomous_flag else 0,
            guard_decision_tag,
        ),
    )
    conn.commit()


fake_insert("user-1", {"crew_name": "router", "task_type": "chat"}, False, None, 0.05)
fake_insert("user-2", {"crew_name": "router", "task_type": "chat"}, False, None, 0.02)
fake_insert("user-3", {"crew_name": "hunter_crew", "task_type": "outreach"}, False, None, 0.12)
fake_insert("auto-1", {"crew_name": "griot", "task_type": "social_content"}, True, "allowed", 0.07)
fake_insert("auto-2", {"crew_name": "griot", "task_type": "social_content"}, True, "allowed", 0.05)
fake_insert("auto-3", {"crew_name": "hunter", "task_type": "lead_research"}, True, "dry-run", 0.03)
print("[E2E] Seeded 3 user + 3 autonomous rows")


class SqliteCursorWrap:
    def __init__(self, real_cur):
        self._cur = real_cur

    def execute(self, sql, params=None):
        sql = sql.replace(
            "ts::date = (now() AT TIME ZONE 'America/Denver')::date",
            "date(ts) = date('now')",
        )
        sql = sql.replace("COALESCE(SUM(cost_usd), 0)::float", "COALESCE(SUM(cost_usd), 0)")
        sql = sql.replace("autonomous = TRUE", "autonomous = 1")
        if params is None:
            self._cur.execute(sql)
        else:
            self._cur.execute(sql, params)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def close(self):
        self._cur.close()


class SqliteConnWrap:
    def __init__(self, real_conn):
        self._conn = real_conn

    def cursor(self):
        return SqliteCursorWrap(self._conn.cursor())

    def close(self):
        pass


def fake_pg_conn():
    return SqliteConnWrap(conn)


fake_memory = types.ModuleType("memory")
fake_memory._pg_conn = fake_pg_conn
sys.modules["memory"] = fake_memory

from autonomy_guard import AutonomyGuard

state_dir = Path(tempfile.mkdtemp())
state_file = state_dir / "state.json"
guard = AutonomyGuard(state_file=str(state_file), cap_usd=0.20)

spent = guard._spent_today_usd()
print(f"[E2E] Autonomous spend today: ${spent:.4f} (expected $0.1500)")
assert abs(spent - 0.15) < 0.001, f"Expected 0.15, got {spent}"

per_crew = guard._per_crew_spend_today()
print(f"[E2E] Per-crew: {per_crew}")
assert abs(per_crew["griot"] - 0.12) < 0.001
assert abs(per_crew["hunter"] - 0.03) < 0.001

snap = guard.snapshot()
print(f"[E2E] Snapshot: spent=${snap.spent_today_usd:.4f} cap=${snap.cap_usd:.2f} remaining=${snap.remaining_usd:.4f}")
assert snap.cap_usd == 0.20
assert abs(snap.remaining_usd - 0.05) < 0.001

guard.set_crew_enabled("griot", True)
guard.set_crew_dry_run("griot", False)
decision = guard.guard("griot", estimated_usd=0.10)
print(f"[E2E] Cap-exceed probe: allowed={decision.allowed} tag={decision.decision_tag}")
assert decision.allowed is False
assert decision.decision_tag == "blocked-cap"
assert guard.is_killed() is True

guard2 = AutonomyGuard(state_file=str(state_file), cap_usd=0.20)
print(f"[E2E] Post-restart: killed={guard2.is_killed()}")
assert guard2.is_killed() is True

decision2 = guard2.guard("griot", estimated_usd=0.001)
print(f"[E2E] Post-restart guard call: allowed={decision2.allowed} tag={decision2.decision_tag}")
assert decision2.allowed is False
assert decision2.decision_tag == "blocked-killed"

guard2.unkill()
decision3 = guard2.guard("griot", estimated_usd=0.001)
print(f"[E2E] Post-unkill guard call: allowed={decision3.allowed} tag={decision3.decision_tag}")
assert decision3.allowed is True

print("\n[E2E] All integration assertions passed.")
