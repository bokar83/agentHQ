# tests/test_concierge_crew.py
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "orchestrator"))


def test_fetch_recent_errors_returns_lines_from_log():
    """fetch_recent_errors returns non-empty list when log has error lines."""
    import concierge_crew as cc

    fake_log = (
        "2026-05-08 01:00:00 [ERROR] griot_tick: NoneType has no attribute 'get'\n"
        "2026-05-08 01:00:01 Traceback (most recent call last):\n"
        "2026-05-08 01:00:02   File 'griot.py', line 42, in run\n"
        "2026-05-08 01:02:00 [INFO] heartbeat: ok\n"
        "2026-05-08 02:00:00 [ERROR] studio_tick: connection refused\n"
    )

    mock_client = MagicMock()
    mock_sftp = MagicMock()
    mock_file = MagicMock()
    mock_file.read.return_value = fake_log.encode()
    mock_sftp.open.return_value.__enter__ = lambda s: mock_file
    mock_sftp.open.return_value.__exit__ = MagicMock(return_value=False)
    mock_client.open_sftp.return_value.__enter__ = lambda s: mock_sftp
    mock_client.open_sftp.return_value.__exit__ = MagicMock(return_value=False)

    with patch("concierge_crew._ssh_client", return_value=mock_client):
        lines = cc.fetch_recent_errors(hours=24)

    assert len(lines) == 3  # 2 ERROR lines + 1 Traceback line
    assert any("[ERROR]" in l for l in lines)
    assert any("Traceback" in l for l in lines)
    assert all("[INFO]" not in l for l in lines)


def test_fetch_recent_errors_returns_empty_on_ssh_failure():
    """SSH failure is non-fatal: returns empty list."""
    import concierge_crew as cc
    import paramiko

    with patch("concierge_crew._ssh_client", side_effect=paramiko.SSHException("timeout")):
        lines = cc.fetch_recent_errors(hours=24)

    assert lines == []
