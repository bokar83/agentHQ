"""Agent coordination layer.

One table, two operating modes:

1. Resource locks. claim()/complete() with a stringly-typed `resource` key
   like 'git:main' or 'task:morning-runner'. Race-free via partial unique
   index. One holder at a time per resource.

2. Work-item queue (no-checkout fix). enqueue(kind, payload) writes a row
   in status='queued'. claim_next(kind, holder, ttl) atomically pops the
   oldest queued row of that kind and marks it running. fail(task_id) marks
   it failed (won't be re-queued). complete(task_id, result) marks it done.

The same table holds both. Resource locks always have status in
{'running','done','failed'}. Queued work items go through 'queued' first.

DSN: TEST_COORD_DSN, POSTGRES_DSN, or POSTGRES_HOST/USER/PASSWORD/DB.
"""

from __future__ import annotations

import contextlib
import os
import uuid
from typing import Iterator, Optional

import psycopg2
import psycopg2.extras


def _connect():
    dsn = (
        os.environ.get("TEST_COORD_DSN")
        or os.environ.get("POSTGRES_DSN")
        or os.environ.get("SUPABASE_DB_URL")
    )
    if dsn:
        return psycopg2.connect(dsn)
    host = os.environ.get("POSTGRES_HOST")
    user = os.environ.get("POSTGRES_USER")
    pw = os.environ.get("POSTGRES_PASSWORD")
    db = os.environ.get("POSTGRES_DB")
    if host and user and pw and db:
        return psycopg2.connect(host=host, user=user, password=pw, dbname=db)
    raise RuntimeError(
        "Set TEST_COORD_DSN, POSTGRES_DSN, or all of "
        "POSTGRES_HOST/USER/PASSWORD/DB"
    )


def init_schema() -> None:
    """Create the tasks table if missing, then add queue columns. Idempotent."""
    with _connect() as c, c.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id text PRIMARY KEY,
                resource text NOT NULL,
                status text NOT NULL,
                claimed_by text,
                claimed_at timestamptz,
                lease_expires_at timestamptz,
                result jsonb,
                created_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS tasks_resource_running_uniq "
            "ON tasks (resource) WHERE status = 'running'"
        )
        cur.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS kind text")
        cur.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS payload jsonb")
        cur.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS error text")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS tasks_kind_queued_idx "
            "ON tasks (kind, created_at) WHERE status = 'queued'"
        )
        c.commit()


def claim(resource: str, holder: str, ttl_seconds: int) -> Optional[dict]:
    """Atomically claim a resource. Return task row dict or None if held.

    Race-free via the partial unique index on (resource) WHERE status='running'.
    Stale rows (lease_expires_at < now) are taken over by the new holder.
    """
    task_id = uuid.uuid4().hex
    with _connect() as c, c.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            DELETE FROM tasks
            WHERE resource = %s
              AND status = 'running'
              AND lease_expires_at < now()
            """,
            (resource,),
        )
        try:
            cur.execute(
                """
                INSERT INTO tasks (id, resource, status, claimed_by,
                                   claimed_at, lease_expires_at)
                VALUES (%s, %s, 'running', %s, now(),
                        now() + make_interval(secs => %s))
                RETURNING id, resource, status, claimed_by,
                          claimed_at, lease_expires_at
                """,
                (task_id, resource, holder, ttl_seconds),
            )
            row = cur.fetchone()
            c.commit()
            return dict(row)
        except psycopg2.errors.UniqueViolation:
            c.rollback()
            return None


def complete(task_id: str, result: Optional[dict] = None) -> None:
    """Mark a task done and release its resource."""
    with _connect() as c, c.cursor() as cur:
        cur.execute(
            "UPDATE tasks SET status = 'done', result = %s WHERE id = %s",
            (psycopg2.extras.Json(result or {}), task_id),
        )
        c.commit()


def list_running() -> list[dict]:
    """Return all currently-held resources. The comms primitive."""
    with _connect() as c, c.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, kind, resource, claimed_by, claimed_at, lease_expires_at
            FROM tasks
            WHERE status = 'running' AND lease_expires_at > now()
            ORDER BY claimed_at
            """
        )
        return [dict(r) for r in cur.fetchall()]


def enqueue(kind: str, payload: dict) -> str:
    """Queue a work item. Returns the task id. Status starts as 'queued'."""
    task_id = uuid.uuid4().hex
    with _connect() as c, c.cursor() as cur:
        cur.execute(
            """
            INSERT INTO tasks (id, resource, status, kind, payload)
            VALUES (%s, %s, 'queued', %s, %s)
            """,
            (task_id, f"work:{task_id}", kind, psycopg2.extras.Json(payload)),
        )
        c.commit()
    return task_id


def claim_next(kind: str, holder: str, ttl_seconds: int) -> Optional[dict]:
    """Atomically claim the oldest queued work item of this kind. None if empty.

    Race-free across concurrent workers via FOR UPDATE SKIP LOCKED. Also
    revives stale-running rows of this kind whose lease has expired.
    """
    with _connect() as c, c.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            UPDATE tasks SET status = 'queued', claimed_by = NULL,
                             claimed_at = NULL, lease_expires_at = NULL
            WHERE kind = %s AND status = 'running' AND lease_expires_at < now()
            """,
            (kind,),
        )
        cur.execute(
            """
            WITH next AS (
                SELECT id FROM tasks
                WHERE kind = %s AND status = 'queued'
                ORDER BY created_at
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE tasks t
            SET status = 'running',
                claimed_by = %s,
                claimed_at = now(),
                lease_expires_at = now() + make_interval(secs => %s)
            FROM next
            WHERE t.id = next.id
            RETURNING t.id, t.kind, t.resource, t.payload,
                      t.claimed_by, t.claimed_at, t.lease_expires_at
            """,
            (kind, holder, ttl_seconds),
        )
        row = cur.fetchone()
        c.commit()
        return dict(row) if row else None


def renew(task_id: str, ttl_seconds: int) -> bool:
    """Extend the lease on an in-flight task. Heartbeat for long jobs.

    Returns True if the task is still 'running' and was extended.
    Returns False if the task has been reclaimed by someone else (lease
    expired) or already completed/failed. A False return means the caller
    has lost ownership and should abort cleanly.
    """
    with _connect() as c, c.cursor() as cur:
        cur.execute(
            """
            UPDATE tasks
            SET lease_expires_at = now() + make_interval(secs => %s)
            WHERE id = %s AND status = 'running'
            """,
            (ttl_seconds, task_id),
        )
        c.commit()
        return cur.rowcount == 1


def fail(task_id: str, error: str) -> None:
    """Mark a task failed. Won't be re-queued by claim_next."""
    with _connect() as c, c.cursor() as cur:
        cur.execute(
            "UPDATE tasks SET status = 'failed', error = %s WHERE id = %s",
            (error, task_id),
        )
        c.commit()


def recent_completed(kind: str, since_seconds: int = 3600, limit: int = 50) -> list[dict]:
    """Recent finished work items of this kind. Lets agents pick up handoffs."""
    with _connect() as c, c.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, kind, status, payload, result, claimed_by, claimed_at
            FROM tasks
            WHERE kind = %s AND status IN ('done', 'failed')
              AND claimed_at > now() - make_interval(secs => %s)
            ORDER BY claimed_at DESC
            LIMIT %s
            """,
            (kind, since_seconds, limit),
        )
        return [dict(r) for r in cur.fetchall()]


@contextlib.contextmanager
def lock(resource: str, holder: str, ttl_seconds: int) -> Iterator[dict]:
    """Context manager. Raises RuntimeError if resource already held."""
    task = claim(resource, holder, ttl_seconds)
    if task is None:
        raise RuntimeError(f"resource '{resource}' is held by another agent")
    try:
        yield task
    finally:
        complete(task["id"])
