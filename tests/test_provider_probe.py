"""Tests for provider_health circuit breaker and probe."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "orchestrator"))


def test_record_failure_increments_count():
    """record_failure increments fail_count and returns just_tripped=True on 3rd failure."""
    import provider_health as ph

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = {"fail_count": 2, "window_start": None, "status": "healthy"}

    with patch("provider_health.get_local_connection", return_value=mock_conn):
        result = ph.record_failure("openrouter")

    assert result["just_tripped"] is True
    assert result["status"] == "tripped"


def test_record_failure_below_threshold_not_tripped():
    import provider_health as ph

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = {"fail_count": 1, "window_start": None, "status": "healthy"}

    with patch("provider_health.get_local_connection", return_value=mock_conn):
        result = ph.record_failure("openrouter")

    assert result["just_tripped"] is False
    assert result["status"] == "healthy"


def test_record_recovery_marks_healthy():
    import provider_health as ph

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with patch("provider_health.get_local_connection", return_value=mock_conn):
        ph.record_recovery("openrouter")

    call_args = mock_cur.execute.call_args[0][0]
    assert "healthy" in call_args
    assert "fail_count = 0" in call_args
    assert "window_start = NULL" in call_args
    mock_conn.commit.assert_called_once()
