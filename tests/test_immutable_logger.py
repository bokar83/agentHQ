"""
test_immutable_logger.py
========================
Verifies that the immutable_audit schema enforces INSERT-only access for the
audit_logger role.

Requires:
    - Local Postgres reachable on localhost:5432 (or via SSH tunnel).
    - Migration scripts/setup_immutable_audit.sql already applied.
    - AUDIT_PG_PASSWORD env var set to the audit_logger password.

Run:
    AUDIT_PG_PASSWORD=<pw> pytest tests/test_immutable_logger.py -v
"""

from __future__ import annotations

import json
import os
import time
import threading

import psycopg2
import psycopg2.errors
import psycopg2.extras
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _superuser_conn():
    """Open a connection as the Postgres superuser for setup/teardown."""
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        dbname=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        cursor_factory=psycopg2.extras.RealDictCursor,
        connect_timeout=5,
    )


def _audit_conn():
    """Open a connection as audit_logger."""
    pw = os.environ.get("AUDIT_PG_PASSWORD")
    if not pw:
        pytest.skip("AUDIT_PG_PASSWORD not set — skipping immutable audit tests")
    return psycopg2.connect(
        host=os.environ.get("AUDIT_PG_HOST", "localhost"),
        port=int(os.environ.get("AUDIT_PG_PORT", 5432)),
        dbname=os.environ.get("AUDIT_PG_DB", "postgres"),
        user=os.environ.get("AUDIT_PG_USER", "audit_logger"),
        password=pw,
        cursor_factory=psycopg2.extras.RealDictCursor,
        connect_timeout=5,
        sslmode=os.environ.get("AUDIT_PG_SSLMODE", "prefer"),
    )


@pytest.fixture(scope="module")
def superconn():
    conn = _superuser_conn()
    conn.autocommit = True
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def auditconn():
    conn = _audit_conn()
    conn.autocommit = False
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_rows(superconn, agent_id: str) -> int:
    with superconn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM immutable_audit.agent_audit_trail WHERE agent_id = %s",
            (agent_id,),
        )
        row = cur.fetchone()
        return int(row["n"])


def _insert_via_function(auditconn, agent_id: str, action: str = "heartbeat") -> int:
    """Call append_audit_event() and return the new row id."""
    with auditconn.cursor() as cur:
        cur.execute(
            """
            SELECT immutable_audit.append_audit_event(
                %s, %s, NULL, %s::jsonb, 'ok'
            ) AS new_id
            """,
            (agent_id, action, json.dumps({"test": True})),
        )
        row = cur.fetchone()
    auditconn.commit()
    return int(row["new_id"])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSchemaExists:
    def test_schema_exists(self, superconn):
        with superconn.cursor() as cur:
            cur.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'immutable_audit'"
            )
            assert cur.fetchone() is not None, "immutable_audit schema not found"

    def test_table_exists(self, superconn):
        with superconn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'immutable_audit' AND table_name = 'agent_audit_trail'
                """
            )
            assert cur.fetchone() is not None, "agent_audit_trail table not found"

    def test_role_exists(self, superconn):
        with superconn.cursor() as cur:
            cur.execute("SELECT rolname FROM pg_roles WHERE rolname = 'audit_logger'")
            assert cur.fetchone() is not None, "audit_logger role not found"


class TestInsertAllowed:
    def test_insert_via_function(self, superconn, auditconn):
        before = _count_rows(superconn, "test_agent")
        new_id = _insert_via_function(auditconn, "test_agent", "heartbeat")
        after = _count_rows(superconn, "test_agent")

        assert new_id > 0, "append_audit_event returned non-positive id"
        assert after == before + 1, "Row count did not increase after INSERT"

    def test_insert_all_actions(self, superconn, auditconn):
        from orchestrator.logger import AUDIT_ACTIONS  # type: ignore[import]
        before = _count_rows(superconn, "test_all_actions")
        for action in sorted(AUDIT_ACTIONS):
            _insert_via_function(auditconn, "test_all_actions", action)
        after = _count_rows(superconn, "test_all_actions")
        assert after - before == len(AUDIT_ACTIONS)

    def test_payload_stored_as_jsonb(self, superconn, auditconn):
        _insert_via_function(auditconn, "test_payload_agent", "file_edit")
        with superconn.cursor() as cur:
            cur.execute(
                """
                SELECT payload FROM immutable_audit.agent_audit_trail
                WHERE agent_id = 'test_payload_agent'
                ORDER BY ts DESC LIMIT 1
                """
            )
            row = cur.fetchone()
        assert row is not None
        # psycopg2 auto-deserialises JSONB to dict
        assert isinstance(row["payload"], dict)
        assert row["payload"].get("test") is True


class TestUpdateProhibited:
    """audit_logger must NOT be able to UPDATE rows."""

    def test_direct_update_denied(self, auditconn):
        """Direct UPDATE on the table raises InsufficientPrivilege."""
        # First insert a row so there is something to target.
        row_id = _insert_via_function(auditconn, "test_update_agent", "heartbeat")

        with pytest.raises(psycopg2.errors.InsufficientPrivilege):
            with auditconn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE immutable_audit.agent_audit_trail
                    SET status = 'blocked'
                    WHERE id = %s
                    """,
                    (row_id,),
                )
            auditconn.commit()

        auditconn.rollback()

    def test_trigger_blocks_superuser_update(self, superconn):
        """Even the superuser cannot UPDATE via the trigger."""
        # Insert a row as superuser directly (bypasses INSERT privilege check).
        with superconn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO immutable_audit.agent_audit_trail (agent_id, action, payload)
                VALUES ('test_su_update', 'heartbeat', '{}'::jsonb)
                RETURNING id
                """
            )
            row = cur.fetchone()
            row_id = row["id"]

        # Attempt to UPDATE via superuser connection — trigger must block it.
        with pytest.raises(psycopg2.errors.InsufficientPrivilege):
            with superconn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE immutable_audit.agent_audit_trail
                    SET status = 'blocked'
                    WHERE id = %s
                    """,
                    (row_id,),
                )


class TestDeleteProhibited:
    """audit_logger must NOT be able to DELETE rows."""

    def test_direct_delete_denied(self, auditconn):
        """Direct DELETE raises InsufficientPrivilege."""
        row_id = _insert_via_function(auditconn, "test_delete_agent", "heartbeat")

        with pytest.raises(psycopg2.errors.InsufficientPrivilege):
            with auditconn.cursor() as cur:
                cur.execute(
                    "DELETE FROM immutable_audit.agent_audit_trail WHERE id = %s",
                    (row_id,),
                )
            auditconn.commit()

        auditconn.rollback()

    def test_trigger_blocks_superuser_delete(self, superconn):
        """Even the superuser cannot DELETE via the trigger."""
        with superconn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO immutable_audit.agent_audit_trail (agent_id, action, payload)
                VALUES ('test_su_delete', 'heartbeat', '{}'::jsonb)
                RETURNING id
                """
            )
            row = cur.fetchone()
            row_id = row["id"]

        with pytest.raises(psycopg2.errors.InsufficientPrivilege):
            with superconn.cursor() as cur:
                cur.execute(
                    "DELETE FROM immutable_audit.agent_audit_trail WHERE id = %s",
                    (row_id,),
                )


class TestSelectProhibited:
    """audit_logger has no SELECT privilege on the table."""

    def test_direct_select_denied(self, auditconn):
        with pytest.raises(psycopg2.errors.InsufficientPrivilege):
            with auditconn.cursor() as cur:
                cur.execute("SELECT * FROM immutable_audit.agent_audit_trail LIMIT 1")
            auditconn.commit()

        auditconn.rollback()


class TestLoggerModule:
    """Integration test: orchestrator/logger.py enqueues and flushes to DB."""

    def test_audit_enqueue_and_flush(self, superconn):
        """
        Call audit() and verify a row appears in the DB within 5 seconds.
        Requires AUDIT_PG_PASSWORD env var to be set.
        """
        pw = os.environ.get("AUDIT_PG_PASSWORD")
        if not pw:
            pytest.skip("AUDIT_PG_PASSWORD not set")

        # Import after env var is confirmed present so degraded mode isn't hit.
        import importlib
        import sys

        # Force re-import to pick up env var state from this test run.
        if "orchestrator.logger" in sys.modules:
            del sys.modules["orchestrator.logger"]
        if "logger" in sys.modules:
            del sys.modules["logger"]

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "orchestrator"))
        from logger import audit  # type: ignore[import]

        unique_agent = f"pytest_{int(time.time())}"
        before = _count_rows(superconn, unique_agent)

        audit(
            agent_id=unique_agent,
            action="heartbeat",
            target="test_run",
            payload={"source": "test_immutable_logger"},
        )

        # Give the background worker time to drain.
        deadline = time.time() + 5.0
        after = before
        while time.time() < deadline:
            after = _count_rows(superconn, unique_agent)
            if after > before:
                break
            time.sleep(0.2)

        assert after > before, (
            f"audit() enqueue did not produce a DB row within 5 s "
            f"(agent_id={unique_agent})"
        )

    def test_audit_degraded_mode_no_crash(self, monkeypatch):
        """When AUDIT_PG_PASSWORD is absent the module logs a warning, never raises."""
        import importlib
        import sys

        monkeypatch.delenv("AUDIT_PG_PASSWORD", raising=False)

        # Force re-import in degraded state.
        for mod in list(sys.modules):
            if "logger" in mod and "agentsHQ" not in mod and "usage" not in mod:
                del sys.modules[mod]

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "orchestrator"))
        import logger as lg  # type: ignore[import]

        # Should not raise even with no DB.
        lg.audit("degraded_agent", "error", status="error")
