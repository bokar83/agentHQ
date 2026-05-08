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


def test_group_by_signature_deduplicates_same_error():
    """Two lines with same normalized text become one group."""
    import concierge_crew as cc

    lines = [
        "2026-05-08 01:00:00 [ERROR] griot_tick: NoneType 'get' uuid=abc123",
        "2026-05-08 02:00:00 [ERROR] griot_tick: NoneType 'get' uuid=def456",
        "2026-05-08 03:00:00 [ERROR] studio_tick: connection refused",
    ]
    groups = cc.group_by_signature(lines)

    assert len(groups) == 2
    sigs = [g["signature"] for g in groups]
    assert len(set(sigs)) == 2
    counts = {g["signature"]: g["count"] for g in groups}
    griot_sig = next(s for s in sigs if "griot" in s)
    assert counts[griot_sig] == 2


def test_group_by_signature_strips_timestamps_and_uuids():
    """Normalized signature has no timestamps or UUIDs."""
    import concierge_crew as cc

    lines = [
        "2026-05-08T12:34:56 [ERROR] worker: task uuid=550e8400-e29b-41d4-a716-446655440000 failed",
    ]
    groups = cc.group_by_signature(lines)

    assert len(groups) == 1
    sig = groups[0]["signature"]
    assert "2026" not in sig
    assert "550e8400" not in sig


def test_propose_fix_returns_expected_shape():
    """propose_fix returns dict with summary, severity, proposed_fix."""
    import concierge_crew as cc

    group = {
        "signature": "[ERROR] griot_tick: NoneType 'get'",
        "count": 3,
        "samples": ["2026-05-08 [ERROR] griot_tick: NoneType 'get'"],
    }

    fake_response = MagicMock()
    fake_response.content = [MagicMock(text='{"summary": "griot NoneType", "severity": "med", "proposed_fix": "Add null check"}')]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = fake_response

    with patch("concierge_crew.anthropic.Anthropic", return_value=mock_client):
        result = cc.propose_fix(group)

    assert result["summary"] == "griot NoneType"
    assert result["severity"] in ("low", "med", "high")
    assert isinstance(result["proposed_fix"], str)
    assert len(result["proposed_fix"]) > 0


def test_propose_fix_handles_malformed_json():
    """If Haiku returns non-JSON, propose_fix returns fallback dict."""
    import concierge_crew as cc

    group = {
        "signature": "[ERROR] unknown: crash",
        "count": 1,
        "samples": ["[ERROR] unknown: crash"],
    }

    fake_response = MagicMock()
    fake_response.content = [MagicMock(text="Sorry I cannot help with that.")]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = fake_response

    with patch("concierge_crew.anthropic.Anthropic", return_value=mock_client):
        result = cc.propose_fix(group)

    assert "summary" in result
    assert "severity" in result
    assert "proposed_fix" in result
