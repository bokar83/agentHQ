"""Agent coordination layer.

One table, claim/lease semantics. Solves the agentsHQ collision problems:
two agents pushing the same branch, restarting the same container, editing
the same file, or picking up the same task.

Resource = stringly-typed key like 'git:main', 'container:orc-crewai',
'file:signal_works/foo.py', 'task:enrich-lead-jane'.

DSN: TEST_COORD_DSN or POSTGRES_DSN.
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
    """Create the tasks table if missing. Idempotent."""
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
            SELECT id, resource, claimed_by, claimed_at, lease_expires_at
            FROM tasks
            WHERE status = 'running' AND lease_expires_at > now()
            ORDER BY claimed_at
            """
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
