"""Reproduces the four collision cases the coordination layer must prevent.

Runs against a throwaway Postgres reachable at TEST_COORD_DSN (defaults to the
SSH-tunneled VPS test container on localhost:55432). Skipped if unreachable.

Success criterion for the whole build: this file passes.
"""

from __future__ import annotations

import os
import threading
import time

import psycopg2
import pytest

DSN = os.environ.get(
    "TEST_COORD_DSN",
    "host=127.0.0.1 port=55432 user=postgres password=testpw dbname=coord",
)


def _can_connect() -> bool:
    try:
        psycopg2.connect(DSN, connect_timeout=2).close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _can_connect(), reason="test Postgres not reachable at TEST_COORD_DSN"
)


@pytest.fixture(autouse=True)
def _reset_schema(monkeypatch):
    """Drop and recreate the tasks table before each test."""
    monkeypatch.setenv("TEST_COORD_DSN", DSN)
    from skills.coordination import init_schema, _connect

    with _connect() as c, c.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS tasks")
        c.commit()
    init_schema()
    yield


def test_concurrent_claim_same_resource_exactly_one_wins():
    """Three threads claim the same resource at once. Exactly one gets it."""
    from skills.coordination import claim

    winners: list[str] = []
    lock = threading.Lock()
    barrier = threading.Barrier(3)

    def worker(holder: str):
        barrier.wait()
        task = claim(resource="git:main", holder=holder, ttl_seconds=60)
        if task is not None:
            with lock:
                winners.append(holder)

    threads = [
        threading.Thread(target=worker, args=(f"agent-{i}",)) for i in range(3)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(winners) == 1, f"expected 1 winner, got {len(winners)}: {winners}"


def test_lease_expiry_allows_handover():
    """If holder dies, another agent gets the resource after TTL elapses."""
    from skills.coordination import claim

    first = claim(resource="container:orc-crewai", holder="agent-A", ttl_seconds=10)
    assert first is not None, "first claim should succeed"

    second_immediate = claim(
        resource="container:orc-crewai", holder="agent-B", ttl_seconds=60
    )
    assert second_immediate is None, "second claim before TTL should be denied"

    time.sleep(11)

    second_after_ttl = claim(
        resource="container:orc-crewai", holder="agent-B", ttl_seconds=60
    )
    assert second_after_ttl is not None, "claim after TTL should succeed"


def test_complete_releases_resource():
    """After complete(), another agent can claim immediately."""
    from skills.coordination import claim, complete

    task = claim(resource="file:signal_works/foo.py", holder="agent-A", ttl_seconds=60)
    assert task is not None
    complete(task["id"], result={"ok": True})

    next_task = claim(
        resource="file:signal_works/foo.py", holder="agent-B", ttl_seconds=60
    )
    assert next_task is not None, "resource should be claimable after complete()"


def test_visibility_query_lists_running_holders():
    """SELECT on running tasks shows who holds what (the comms requirement)."""
    from skills.coordination import claim, list_running

    claim(resource="git:main", holder="agent-A", ttl_seconds=60)
    claim(resource="container:orc-crewai", holder="agent-B", ttl_seconds=60)

    running = list_running()
    holders = {r["resource"]: r["claimed_by"] for r in running}
    assert holders.get("git:main") == "agent-A"
    assert holders.get("container:orc-crewai") == "agent-B"


def test_queue_two_workers_each_get_one_item():
    """Two queued items, two workers race claim_next: each gets exactly one."""
    from skills.coordination import enqueue, claim_next

    id1 = enqueue("enrich-lead", {"email": "alice@acme.com"})
    id2 = enqueue("enrich-lead", {"email": "bob@acme.com"})
    assert id1 != id2

    claimed_ids: list[str] = []
    lock = threading.Lock()
    barrier = threading.Barrier(2)

    def worker(holder: str):
        barrier.wait()
        t = claim_next(kind="enrich-lead", holder=holder, ttl_seconds=60)
        if t is not None:
            with lock:
                claimed_ids.append(t["id"])

    threads = [threading.Thread(target=worker, args=(f"w-{i}",)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(claimed_ids) == sorted([id1, id2]), \
        f"each worker should get one, got {claimed_ids}"


def test_queue_empty_returns_none():
    """claim_next on an empty queue returns None, doesn't block."""
    from skills.coordination import claim_next

    result = claim_next(kind="nothing-queued", holder="w-1", ttl_seconds=60)
    assert result is None


def test_queue_fifo_order():
    """Items are claimed oldest-first."""
    from skills.coordination import enqueue, claim_next

    first = enqueue("ordered", {"n": 1})
    time.sleep(0.05)
    second = enqueue("ordered", {"n": 2})

    a = claim_next(kind="ordered", holder="w-1", ttl_seconds=60)
    b = claim_next(kind="ordered", holder="w-2", ttl_seconds=60)
    assert a["id"] == first
    assert b["id"] == second


def test_queue_stale_lease_revives_for_next_claim():
    """If a worker dies (lease expires), the next claim_next picks the row up."""
    from skills.coordination import enqueue, claim_next

    enqueue("flaky", {"x": 1})
    first = claim_next(kind="flaky", holder="w-A", ttl_seconds=2)
    assert first is not None

    # Pretend w-A crashed: don't call complete or fail. Wait for lease expiry.
    time.sleep(2.5)

    second = claim_next(kind="flaky", holder="w-B", ttl_seconds=60)
    assert second is not None, "stale-lease item should be reclaimable"
    assert second["id"] == first["id"], "should be the SAME item, not a duplicate"


def test_queue_failed_items_stay_failed():
    """fail() marks done; claim_next does not re-issue."""
    from skills.coordination import enqueue, claim_next, fail

    enqueue("brittle", {"x": 1})
    t = claim_next(kind="brittle", holder="w-1", ttl_seconds=60)
    fail(t["id"], "synthetic error")

    next_t = claim_next(kind="brittle", holder="w-2", ttl_seconds=60)
    assert next_t is None, "failed items must not be re-issued"


def test_renew_extends_lease_and_blocks_competing_claim():
    """renew() pushes lease_expires_at out so the original claimer keeps the lock."""
    from skills.coordination import claim, renew

    first = claim(resource="long:render", holder="A", ttl_seconds=2)
    assert first is not None

    # Before TTL would expire, renew with a long extension
    time.sleep(1)
    assert renew(first["id"], ttl_seconds=60) is True

    # After original 2s TTL would have expired, second claim is still denied
    time.sleep(2)
    competing = claim(resource="long:render", holder="B", ttl_seconds=60)
    assert competing is None, "renew should have kept A's lock alive"


def test_renew_returns_false_after_reclaim():
    """If the lease did expire and someone else claimed, renew returns False."""
    from skills.coordination import claim, renew

    first = claim(resource="lost:lock", holder="A", ttl_seconds=1)
    assert first is not None

    time.sleep(2)
    second = claim(resource="lost:lock", holder="B", ttl_seconds=60)
    assert second is not None, "B should grab the stale lease"

    # A's task was DELETEd by B's claim - the row no longer exists, so renew is False
    assert renew(first["id"], ttl_seconds=60) is False, \
        "A's renew on a reclaimed/deleted task must return False"


def test_morning_runner_lock_serializes_concurrent_invocations(monkeypatch):
    """Two morning_runner.main() calls at once: only one runs the body.

    Proves the lock wired into signal_works/morning_runner.py at line 67-83
    actually does what the commit message claimed. Stubs _main_body so we
    don't fire Apollo/Firecrawl/Gmail.
    """
    from signal_works import morning_runner

    body_runs: list[str] = []
    body_runs_lock = threading.Lock()

    def fake_body():
        with body_runs_lock:
            body_runs.append("ran")
        time.sleep(2)
        return 0

    monkeypatch.setattr(morning_runner, "_main_body", fake_body)

    barrier = threading.Barrier(2)
    results: list[int] = []
    results_lock = threading.Lock()

    def invoke():
        barrier.wait()
        rc = morning_runner.main()
        with results_lock:
            results.append(rc)

    threads = [threading.Thread(target=invoke) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(body_runs) == 1, f"body must run exactly once, ran {len(body_runs)}"
    assert sorted(results) == [0, 0], f"both invocations exit clean rc=0, got {results}"


def test_outreach_runner_lock_serializes_concurrent_invocations(monkeypatch):
    """Same proof for outreach_runner: only one of two parallel runs executes."""
    from signal_works import outreach_runner

    runs: list[str] = []
    runs_lock = threading.Lock()

    def fake_run_outreach(**kwargs):
        with runs_lock:
            runs.append("ran")
        time.sleep(2)
        return {"drafted": 1, "skipped": 0}

    import skills.outreach.outreach_tool as outreach_tool
    monkeypatch.setattr(outreach_tool, "run_outreach", fake_run_outreach)

    barrier = threading.Barrier(2)
    results: list[int] = []
    results_lock = threading.Lock()

    def invoke():
        barrier.wait()
        rc = outreach_runner.run()
        with results_lock:
            results.append(rc)

    threads = [threading.Thread(target=invoke) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(runs) == 1, f"outreach body must run exactly once, ran {len(runs)}"


def test_recent_completed_returns_results():
    """recent_completed() lets agents read each other's output."""
    from skills.coordination import enqueue, claim_next, complete, recent_completed

    enqueue("handoff", {"step": 1})
    t = claim_next(kind="handoff", holder="upstream", ttl_seconds=60)
    complete(t["id"], result={"enriched": True})

    recent = recent_completed(kind="handoff")
    assert len(recent) == 1
    assert recent[0]["result"] == {"enriched": True}
    assert recent[0]["status"] == "done"
