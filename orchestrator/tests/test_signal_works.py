"""Tests for Signal Works pipeline modules."""
import pytest
from unittest.mock import patch, MagicMock


def test_upsert_signal_works_lead_calls_supabase():
    """upsert_signal_works_lead should insert a row tagged signal_works."""
    from orchestrator.db import upsert_signal_works_lead
    lead = {
        "name": "Valley Dental",
        "email": "owner@valleydental.com",
        "phone": "801-555-1234",
        "website_url": "https://valleydental.com",
        "review_count": 47,
        "google_maps_url": "https://maps.google.com/?cid=12345",
        "niche": "pediatric dentist",
        "city": "Salt Lake City",
        "ai_score": 12,
    }
    with patch("orchestrator.db.get_crm_connection") as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value.__enter__ = lambda s: mock_conn.return_value
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.return_value.cursor.return_value.__enter__ = lambda s: mock_cursor
        mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)
        upsert_signal_works_lead(lead)
        assert mock_cursor.execute.called
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "leads" in sql_call.lower()
        assert "signal_works" in mock_cursor.execute.call_args[0][1]
