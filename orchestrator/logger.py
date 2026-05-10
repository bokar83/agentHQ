"""
logger.py — Immutable out-of-band audit trail
==============================================
Opens a dedicated connection pool under the `audit_logger` Postgres role,
which holds INSERT-only privileges on the `immutable_audit.agent_audit_trail`
table.  No agent running as `audit_logger` can UPDATE or DELETE audit rows.

Public API
----------
    from logger import audit

    audit(
        agent_id="spawner",
        action="agent_spawn",
        target="feat/atlas-m23-agent-spawning",
        payload={"child_agent": "gate_agent", "depth": 1},
        status="ok",
    )

All calls are fire-and-forget: they enqueue to a thread-safe queue and return
immediately.  A single daemon thread drains the queue in the background.
Failures write a WARNING to the standard log and drop the event — the audit
trail must never block or crash the calling agent.

Environment variables
---------------------
    AUDIT_PG_HOST        (default: localhost for direct / postgres for container)
    AUDIT_PG_PORT        (default: 5432)
    AUDIT_PG_DB          (default: postgres)
    AUDIT_PG_USER        (default: audit_logger)
    AUDIT_PG_PASSWORD    (required — no default for security)
    AUDIT_QUEUE_MAXSIZE  (default: 20000)

If AUDIT_PG_PASSWORD is absent the module initialises in degraded mode: every
audit() call logs a WARNING and drops, so the rest of the system keeps running.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
from typing import Any

_log = logging.getLogger("agentsHQ.audit")

# ---------------------------------------------------------------------------
# Allowed action verbs — kept in sync with the SQL CHECK in setup_immutable_audit.sql
# ---------------------------------------------------------------------------
AUDIT_ACTIONS: frozenset[str] = frozenset({
    "agent_spawn",
    "agent_self_heal",
    "gate_proposal",
    "gate_approve",
    "gate_reject",
    "file_edit",
    "task_claim",
    "task_complete",
    "branch_push",
    "heartbeat",
    "error",
})

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------
_QUEUE: "queue.Queue[dict[str, Any] | None]" = queue.Queue(
    maxsize=int(os.environ.get("AUDIT_QUEUE_MAXSIZE", 20_000))
)
_WORKER_LOCK = threading.Lock()
_WORKER_STARTED = False
_DEGRADED = False  # True when AUDIT_PG_PASSWORD is absent


def _get_dsn() -> dict[str, Any]:
    """Build connection kwargs from environment variables."""
    password = os.environ.get("AUDIT_PG_PASSWORD")
    if not password:
        raise RuntimeError(
            "AUDIT_PG_PASSWORD not set — audit trail running in degraded mode"
        )
    return {
        "host": os.environ.get("AUDIT_PG_HOST", "localhost"),
        "port": int(os.environ.get("AUDIT_PG_PORT", 5432)),
        "dbname": os.environ.get("AUDIT_PG_DB", "postgres"),
        "user": os.environ.get("AUDIT_PG_USER", "audit_logger"),
        "password": password,
        "connect_timeout": 5,
        "application_name": "agentsHQ-audit",
        # TLS is optional for local Postgres; set sslmode=require in prod.
        "sslmode": os.environ.get("AUDIT_PG_SSLMODE", "prefer"),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def audit(
    agent_id: str,
    action: str,
    target: str | None = None,
    payload: dict[str, Any] | None = None,
    status: str = "ok",
) -> None:
    """
    Enqueue one audit event.  Fire-and-forget — never raises.

    Parameters
    ----------
    agent_id : str
        Identifier of the agent or subsystem producing the event
        (e.g. "spawner", "gate_agent", "self_healer").
    action : str
        One of AUDIT_ACTIONS.  Unknown values are passed through with a WARNING
        (the SQL function also warns but records them).
    target : str, optional
        The subject of the action (branch name, file path, proposal id, …).
    payload : dict, optional
        Structured context.  Must be JSON-serialisable.
    status : str
        One of "ok", "warn", "error", "blocked".
    """
    global _DEGRADED

    if _DEGRADED:
        _log.warning(
            "audit DEGRADED — dropping event agent=%s action=%s target=%s",
            agent_id, action, target,
        )
        return

    if action not in AUDIT_ACTIONS:
        _log.warning("audit: unknown action %r — recording but check AUDIT_ACTIONS", action)

    if status not in ("ok", "warn", "error", "blocked"):
        _log.warning("audit: unknown status %r — defaulting to 'error'", status)
        status = "error"

    event: dict[str, Any] = {
        "agent_id": str(agent_id),
        "action": action,
        "target": target,
        "payload": payload or {},
        "status": status,
    }

    _ensure_worker()
    try:
        _QUEUE.put_nowait(event)
    except queue.Full:
        _log.warning(
            "audit queue full (%d items) — dropping event agent=%s action=%s",
            _QUEUE.qsize(), agent_id, action,
        )


# ---------------------------------------------------------------------------
# Worker thread
# ---------------------------------------------------------------------------

def _ensure_worker() -> None:
    global _WORKER_STARTED, _DEGRADED

    if _WORKER_STARTED:
        return

    with _WORKER_LOCK:
        if _WORKER_STARTED:
            return

        try:
            _get_dsn()  # validate password is present before spawning thread
        except RuntimeError as exc:
            _log.warning("%s", exc)
            _DEGRADED = True
            _WORKER_STARTED = True  # prevent repeated lock acquisition
            return

        t = threading.Thread(
            target=_worker_loop,
            name="audit_logger",
            daemon=True,
        )
        t.start()
        _WORKER_STARTED = True
        _log.info("audit_logger worker thread started")


def _connect():
    """Open a fresh psycopg2 connection using audit_logger credentials."""
    import psycopg2
    import psycopg2.extras

    dsn = _get_dsn()
    conn = psycopg2.connect(
        cursor_factory=psycopg2.extras.RealDictCursor,
        **dsn,
    )
    conn.autocommit = False
    return conn


def _worker_loop() -> None:
    """Drain the queue.  Reconnects automatically on connection loss."""
    conn = None
    consecutive_failures = 0
    MAX_CONSECUTIVE_FAILURES = 10
    BACKOFF_CAP_S = 60.0

    while True:
        # --- drain one item ------------------------------------------------
        try:
            event = _QUEUE.get(timeout=2.0)
        except queue.Empty:
            # Periodically heartbeat the connection to detect silent drops.
            if conn is not None:
                try:
                    conn.cursor().execute("SELECT 1")
                except Exception:
                    try:
                        conn.close()
                    except Exception:
                        pass
                    conn = None
            continue

        # Sentinel None = graceful shutdown signal (tests use this).
        if event is None:
            break

        # --- ensure live connection ----------------------------------------
        if conn is None:
            conn = _reconnect(consecutive_failures, BACKOFF_CAP_S)
            if conn is None:
                # Back-pressure: re-queue the event (best-effort) and wait.
                try:
                    _QUEUE.put_nowait(event)
                except queue.Full:
                    _log.error(
                        "audit: queue full AND no DB — permanently losing event %s/%s",
                        event["agent_id"], event["action"],
                    )
                consecutive_failures += 1
                time.sleep(min(2 ** consecutive_failures, BACKOFF_CAP_S))
                continue

        # --- insert via SECURITY DEFINER function --------------------------
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT immutable_audit.append_audit_event(
                        %(agent_id)s,
                        %(action)s,
                        %(target)s,
                        %(payload)s::jsonb,
                        %(status)s
                    )
                    """,
                    {
                        "agent_id": event["agent_id"],
                        "action":   event["action"],
                        "target":   event.get("target"),
                        "payload":  json.dumps(event.get("payload") or {}),
                        "status":   event.get("status", "ok"),
                    },
                )
            conn.commit()
            consecutive_failures = 0

        except Exception as exc:
            _log.warning(
                "audit insert failed for agent=%s action=%s: %s",
                event["agent_id"], event["action"], exc,
            )
            consecutive_failures += 1
            # Attempt rollback; if it fails, discard the connection.
            try:
                conn.rollback()
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
                conn = None

            # Re-queue once only to avoid infinite retry storms.
            if consecutive_failures <= MAX_CONSECUTIVE_FAILURES:
                try:
                    _QUEUE.put_nowait(event)
                except queue.Full:
                    pass

            time.sleep(min(2 ** consecutive_failures, BACKOFF_CAP_S))


def _reconnect(consecutive_failures: int, cap: float):
    """Try to open a new connection.  Returns None on failure."""
    delay = min(2 ** consecutive_failures, cap)
    if delay > 1:
        time.sleep(delay)
    try:
        conn = _connect()
        _log.info("audit_logger reconnected to Postgres")
        return conn
    except Exception as exc:
        _log.warning("audit_logger reconnect failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Convenience wrappers for the most common agent actions
# ---------------------------------------------------------------------------

def audit_spawn(
    parent_agent_id: str,
    child_agent_id: str,
    branch: str,
    depth: int,
    extra: dict[str, Any] | None = None,
) -> None:
    audit(
        agent_id=parent_agent_id,
        action="agent_spawn",
        target=branch,
        payload={"child_agent_id": child_agent_id, "depth": depth, **(extra or {})},
    )


def audit_self_heal(
    agent_id: str,
    description: str,
    status: str = "ok",
    extra: dict[str, Any] | None = None,
) -> None:
    audit(
        agent_id=agent_id,
        action="agent_self_heal",
        target=description,
        payload=extra or {},
        status=status,
    )


def audit_gate(
    agent_id: str,
    decision: str,
    branch: str,
    reason: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """decision must be 'proposal', 'approve', or 'reject'."""
    action_map = {
        "proposal": "gate_proposal",
        "approve":  "gate_approve",
        "reject":   "gate_reject",
    }
    action = action_map.get(decision, "gate_proposal")
    audit(
        agent_id=agent_id,
        action=action,
        target=branch,
        payload={"reason": reason, **(extra or {})},
    )


def audit_file_edit(
    agent_id: str,
    file_path: str,
    commit_sha: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    audit(
        agent_id=agent_id,
        action="file_edit",
        target=file_path,
        payload={"commit_sha": commit_sha, **(extra or {})},
    )


def audit_task(
    agent_id: str,
    decision: str,
    task_id: str,
    extra: dict[str, Any] | None = None,
) -> None:
    """decision: 'claim' or 'complete'."""
    action = "task_claim" if decision == "claim" else "task_complete"
    audit(
        agent_id=agent_id,
        action=action,
        target=task_id,
        payload=extra or {},
    )
