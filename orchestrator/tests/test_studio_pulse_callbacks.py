"""Regression tests for the studio_pulse:ack / studio_pulse:snooze
Telegram callback handlers wired in handlers_approvals.handle_callback_query.

Why: production_tick._alert_silence posts an inline-keyboard alert. Before
2026-05-15 the buttons were dead — callback_data hit the dispatcher but
no branch matched, so pressing them silently no-oped. This file pins the
contract:
  - ack    -> last_alert_sent reset to 0 (re-arm)
  - snooze -> snoozed_until set ~6h in the future
  - both   -> answer_callback_query toast + editMessageText edit
"""
from __future__ import annotations

import json
import os
import sys
import time
import types
from unittest.mock import MagicMock, patch

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)


def _make_callback_update(cb_data: str, chat_id: str = "99999",
                          sender_id: str = "42", message_id: int = 7) -> dict:
    return {
        "callback_query": {
            "id": "cb-id-123",
            "data": cb_data,
            "from": {"id": sender_id},
            "message": {"chat": {"id": chat_id}, "message_id": message_id},
        }
    }


def _install_mock_notifier(monkeypatch):
    mock_notifier = types.ModuleType("notifier")
    mock_notifier.answer_callback_query = MagicMock()
    mock_notifier.send_message = MagicMock()
    mock_notifier.TELEGRAM_API_BASE = "https://api.telegram.org/botFAKE"
    monkeypatch.setitem(sys.modules, "notifier", mock_notifier)
    return mock_notifier


def test_studio_pulse_ack_clears_last_alert_sent(monkeypatch, tmp_path):
    import handlers_approvals

    pulse_path = tmp_path / "studio_pipeline_pulse.json"
    pulse_path.write_text(json.dumps({
        "last_seen_with_candidates": 1778800000,
        "last_alert_sent": 1778808334,
    }))
    monkeypatch.setenv("STUDIO_PULSE_STATE_PATH", str(pulse_path))
    mock_notifier = _install_mock_notifier(monkeypatch)

    with patch("requests.post") as mock_post:
        result = handlers_approvals.handle_callback_query(
            _make_callback_update("studio_pulse:ack")
        )

    assert result is True
    state = json.loads(pulse_path.read_text())
    assert state["last_alert_sent"] == 0, "ack must zero last_alert_sent so next tick can re-alert"
    assert state["last_seen_with_candidates"] == 1778800000, "ack must not touch last_seen"
    mock_notifier.answer_callback_query.assert_called_once()
    toast = mock_notifier.answer_callback_query.call_args.args[1]
    assert "ack" in toast.lower()
    # editMessageText must be called so the buttons disappear from the chat.
    edit_calls = [c for c in mock_post.call_args_list if "editMessageText" in c.args[0]]
    assert len(edit_calls) == 1, "ack must edit the original alert message"


def test_studio_pulse_snooze_sets_snoozed_until_six_hours(monkeypatch, tmp_path):
    import handlers_approvals

    pulse_path = tmp_path / "studio_pipeline_pulse.json"
    pulse_path.write_text(json.dumps({
        "last_seen_with_candidates": 1778800000,
        "last_alert_sent": 1778808334,
    }))
    monkeypatch.setenv("STUDIO_PULSE_STATE_PATH", str(pulse_path))
    mock_notifier = _install_mock_notifier(monkeypatch)

    before = int(time.time())
    with patch("requests.post"):
        result = handlers_approvals.handle_callback_query(
            _make_callback_update("studio_pulse:snooze")
        )
    after = int(time.time())

    assert result is True
    state = json.loads(pulse_path.read_text())
    six_hours = 6 * 60 * 60
    assert state["snoozed_until"] >= before + six_hours
    assert state["snoozed_until"] <= after + six_hours + 5
    # snooze must NOT clear last_alert_sent — only ack does.
    assert state["last_alert_sent"] == 1778808334
    mock_notifier.answer_callback_query.assert_called_once()
    toast = mock_notifier.answer_callback_query.call_args.args[1]
    assert "snooze" in toast.lower() or "6h" in toast.lower()


def test_studio_pulse_snooze_creates_state_when_missing(monkeypatch, tmp_path):
    """If pulse file does not yet exist, snooze should still write a fresh one."""
    import handlers_approvals

    pulse_path = tmp_path / "subdir" / "studio_pipeline_pulse.json"
    monkeypatch.setenv("STUDIO_PULSE_STATE_PATH", str(pulse_path))
    _install_mock_notifier(monkeypatch)

    with patch("requests.post"):
        result = handlers_approvals.handle_callback_query(
            _make_callback_update("studio_pulse:snooze")
        )

    assert result is True
    assert pulse_path.exists()
    state = json.loads(pulse_path.read_text())
    assert "snoozed_until" in state


def test_alert_silence_skipped_when_snoozed(monkeypatch, tmp_path):
    """The watchdog must respect snoozed_until and skip the alert call."""
    import studio_production_crew as spc

    pulse_path = tmp_path / "studio_pipeline_pulse.json"
    now = int(time.time())
    # 3h of silence (above 90 min threshold); cooldown not blocking;
    # snoozed for another 4h.
    pulse_path.write_text(json.dumps({
        "last_seen_with_candidates": now - (3 * 60 * 60),
        "last_alert_sent": 0,
        "snoozed_until": now + (4 * 60 * 60),
    }))
    monkeypatch.setattr(spc, "_PULSE_STATE_PATH", str(pulse_path))
    monkeypatch.setattr(spc, "_fetch_qa_passed_candidates", lambda: [])
    monkeypatch.setattr(spc, "_alert_silence", MagicMock())

    spc.studio_production_tick(dry_run=True)

    spc._alert_silence.assert_not_called()
    state = json.loads(pulse_path.read_text())
    assert state["last_alert_sent"] == 0, "snoozed tick must not bump last_alert_sent"


def test_alert_silence_fires_when_snooze_expired(monkeypatch, tmp_path):
    """Once snoozed_until is in the past, the watchdog must alert again."""
    import studio_production_crew as spc

    pulse_path = tmp_path / "studio_pipeline_pulse.json"
    now = int(time.time())
    pulse_path.write_text(json.dumps({
        "last_seen_with_candidates": now - (3 * 60 * 60),
        "last_alert_sent": 0,
        "snoozed_until": now - 60,  # expired 1 min ago
    }))
    monkeypatch.setattr(spc, "_PULSE_STATE_PATH", str(pulse_path))
    monkeypatch.setattr(spc, "_fetch_qa_passed_candidates", lambda: [])
    monkeypatch.setattr(spc, "_alert_silence", MagicMock())

    spc.studio_production_tick(dry_run=True)

    spc._alert_silence.assert_called_once()
