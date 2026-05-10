# tests/test_minion_integration.py
"""Integration tests: spawn -> worker claims -> result in DB.

Requires SSH tunnel to VPS Postgres (see Pre-flight). Skipped if unreachable.
"""
from __future__ import annotations
import asyncio
import os
import sys

import psycopg2
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../orchestrator")))

DSN = os.environ.get(
    "TEST_COORD_DSN",
    "host=127.0.0.1 port=55432 user=postgres password=postgres dbname=postgres",
)


def _can_connect() -> bool:
    try:
        psycopg2.connect(DSN, connect_timeout=2).close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _can_connect(), reason="VPS Postgres tunnel not reachable at TEST_COORD_DSN"
)


@pytest.fixture(autouse=True)
def _set_dsn(monkeypatch):
    monkeypatch.setenv("TEST_COORD_DSN", DSN)
    yield


def test_spawn_creates_queued_row():
    """spawn() must write a queued row to tasks within 1 second."""
    from skills.coordination import init_schema
    from skills.coordination.spawner import spawn
    init_schema()

    task_id = spawn("minion:test", {"msg": "hello"})
    assert isinstance(task_id, str) and len(task_id) > 0

    conn = psycopg2.connect(DSN)
    with conn.cursor() as cur:
        cur.execute("SELECT status, kind FROM tasks WHERE id = %s", (task_id,))
        row = cur.fetchone()
    conn.close()

    assert row is not None, "row not found in tasks table"
    assert row[0] == "queued"
    assert row[1] == "minion:test"


def test_spawn_depth_exceeded_no_db_write():
    """spawn() at max depth must not write any row."""
    from skills.coordination.spawner import spawn, SpawnDepthExceeded, MAX_SPAWN_DEPTH

    conn = psycopg2.connect(DSN)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM tasks")
        _row = cur.fetchone()
        assert _row is not None
        before = _row[0]
    conn.close()

    with pytest.raises(SpawnDepthExceeded):
        spawn("minion:test", {}, depth=MAX_SPAWN_DEPTH)

    conn = psycopg2.connect(DSN)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM tasks")
        _row = cur.fetchone()
        assert _row is not None
        after = _row[0]
    conn.close()

    assert before == after


def test_worker_picks_up_and_completes_task():
    """Worker loop must claim queued task and mark done within 5 seconds."""
    import minion_worker
    from skills.coordination import init_schema
    from skills.coordination.spawner import spawn
    init_schema()

    minion_worker._HANDLERS.clear()
    minion_worker.register("minion:test", lambda p: {"echoed": p.get("msg")})

    task_id = spawn("minion:test", {"msg": "world"})

    async def run_worker_briefly():
        try:
            await asyncio.wait_for(minion_worker.run(), timeout=5.0)
        except asyncio.TimeoutError:
            # Drain any create_task()s that were still in-flight when the
            # timeout cancelled run().  One yield is enough for the executor
            # callbacks to land.
            await asyncio.sleep(1.0)

    asyncio.run(run_worker_briefly())

    conn = psycopg2.connect(DSN)
    with conn.cursor() as cur:
        cur.execute("SELECT status, result FROM tasks WHERE id = %s", (task_id,))
        row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "done", f"expected done, got {row[0]}"
    assert row[1]["echoed"] == "world"
