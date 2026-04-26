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
