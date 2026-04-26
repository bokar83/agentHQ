"""Tests for content_approvals table writes from griot approval flow."""
from __future__ import annotations

import os
import sys
from unittest.mock import patch, MagicMock, call

import pytest

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)


def test_record_approval_inserts_row():
    """record_content_approval() inserts a row into content_approvals."""
    from griot import record_content_approval

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with patch("griot._pg_conn", return_value=mock_conn):
        record_content_approval(
            notion_page_id="abc123",
            attempt_number=1,
            decision="approved",
            evergreen=False,
            platform="linkedin",
            griot_score=0.87,
        )

    mock_cur.execute.assert_called_once()
    call_args = mock_cur.execute.call_args[0]
    assert "content_approvals" in call_args[0]
    assert "abc123" in call_args[1]
    assert 1 in call_args[1]
    assert "approved" in call_args[1]
    mock_conn.commit.assert_called_once()


def test_record_approval_non_fatal_on_db_error():
    """record_content_approval() does not raise if DB is unavailable."""
    from griot import record_content_approval

    with patch("griot._pg_conn", side_effect=Exception("DB down")):
        record_content_approval(
            notion_page_id="abc123",
            attempt_number=1,
            decision="approved",
            evergreen=False,
            platform="linkedin",
            griot_score=0.87,
        )
