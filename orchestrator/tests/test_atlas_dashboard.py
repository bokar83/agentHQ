# orchestrator/tests/test_atlas_dashboard.py
import json
import os
import sys

import pytest

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)

from unittest.mock import MagicMock, patch
import atlas_dashboard


def test_get_state_returns_expected_shape():
    state = {
        "killed": False,
        "killed_reason": None,
        "crews": {"griot": {"enabled": True, "dry_run": False}},
        "cap_usd": 1.0,
    }
    with patch("autonomy_guard.get_guard") as mock_guard:
        mock_guard.return_value.state_summary.return_value = state
        result = atlas_dashboard.get_state()

    assert result["killed"] is False
    assert "crews" in result
    assert "griot" in result["crews"]
    assert result["cap_usd"] == 1.0


def test_get_queue_returns_pending_rows():
    from datetime import datetime
    mock_row = MagicMock()
    mock_row.id = 42
    mock_row.ts_created = datetime(2026, 4, 25, 10, 0, 0)
    mock_row.crew_name = "griot"
    mock_row.proposal_type = "linkedin_post"
    mock_row.payload = {"title": "Test post"}
    mock_row.status = "pending"

    with patch("approval_queue.list_pending", return_value=[mock_row]):
        result = atlas_dashboard.get_queue()

    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["id"] == 42
    assert item["crew_name"] == "griot"
    assert item["proposal_type"] == "linkedin_post"
    assert "ts_created" in item
