from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import pytest
from skills.inbound_lead.idempotency import (
    has_been_enriched, mark_enriched, mark_rebook,
)


@pytest.fixture
def fake_conn():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    return conn, cursor


def test_has_been_enriched_returns_none_when_no_row(fake_conn):
    conn, cursor = fake_conn
    cursor.fetchone.return_value = None
    with patch("skills.inbound_lead.idempotency._get_conn", return_value=conn):
        result = has_been_enriched("jane@acme.com")
    assert result is None


def test_has_been_enriched_returns_row_when_exists(fake_conn):
    conn, cursor = fake_conn
    cursor.fetchone.return_value = (
        "jane@acme.com", "evt_1",
        datetime(2026, 5, 1, tzinfo=timezone.utc),
        "evt_1",
        datetime(2026, 5, 5, tzinfo=timezone.utc),
        "enriched",
    )
    with patch("skills.inbound_lead.idempotency._get_conn", return_value=conn):
        result = has_been_enriched("jane@acme.com")
    assert result is not None
    assert result["email"] == "jane@acme.com"
    assert result["status"] == "enriched"


def test_mark_enriched_executes_upsert(fake_conn):
    conn, cursor = fake_conn
    with patch("skills.inbound_lead.idempotency._get_conn", return_value=conn):
        mark_enriched(
            email="jane@acme.com",
            booking_id="evt_1",
            meeting_time=datetime(2026, 5, 1, tzinfo=timezone.utc),
            status="enriched",
        )
    args, _ = cursor.execute.call_args
    sql = args[0]
    assert "INSERT INTO inbound_lead_enrichment" in sql
    assert "ON CONFLICT (email)" in sql
    conn.commit.assert_called_once()


def test_mark_rebook_updates_booking_and_meeting(fake_conn):
    conn, cursor = fake_conn
    with patch("skills.inbound_lead.idempotency._get_conn", return_value=conn):
        mark_rebook(
            email="jane@acme.com",
            booking_id="evt_2",
            meeting_time=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
    args, _ = cursor.execute.call_args
    sql = args[0]
    assert "UPDATE inbound_lead_enrichment" in sql
    assert "last_booking" in sql
    assert "last_meeting_at" in sql
    conn.commit.assert_called_once()
