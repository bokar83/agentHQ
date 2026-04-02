"""Tests for notifier.py — all HTTP calls are mocked."""
import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("ORCHESTRATOR_TELEGRAM_BOT_TOKEN", "123:test")
os.environ.setdefault("TELEGRAM_CHAT_ID", "7792432594")

import sys
sys.path.insert(0, "orchestrator")
from notifier import send_message, send_ack, send_progress_ping, send_result


def test_send_message_calls_telegram_api():
    with patch("notifier.requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        send_message("7792432594", "hello")
        mock_post.assert_called_once()
        call_url = mock_post.call_args[0][0]
        assert "sendMessage" in call_url
        call_json = mock_post.call_args[1]["json"]
        assert call_json["chat_id"] == "7792432594"
        assert call_json["text"] == "hello"


def test_send_message_truncates_long_text():
    long_text = "x" * 5000
    with patch("notifier.requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        send_message("7792432594", long_text)
        sent_text = mock_post.call_args[1]["json"]["text"]
        assert len(sent_text) <= 4096


def test_send_ack_sends_task_label():
    with patch("notifier.send_message") as mock_send:
        send_ack("7792432594", "research_report")
        mock_send.assert_called_once()
        text = mock_send.call_args[0][1]
        assert "Research" in text or "research" in text.lower()


def test_send_progress_ping_sends_simpsons_quote():
    with patch("notifier.send_message") as mock_send:
        send_progress_ping("7792432594")
        mock_send.assert_called_once()
        text = mock_send.call_args[0][1]
        assert len(text) > 10


def test_send_progress_ping_never_repeats_consecutively():
    sent = []
    with patch("notifier.send_message") as mock_send:
        mock_send.side_effect = lambda chat_id, text: sent.append(text)
        send_progress_ping("7792432594")
        send_progress_ping("7792432594")
        if len(sent) == 2:
            assert sent[0] != sent[1]


def test_send_result_includes_drive_and_github_links():
    with patch("notifier.send_message") as mock_send:
        send_result("7792432594", "The report is ready.", "https://drive.google.com/abc", "https://github.com/bokar83/agentHQ/blob/main/outputs/research/report.md")
        mock_send.assert_called_once()
        text = mock_send.call_args[0][1]
        assert "drive.google.com" in text
        assert "github.com" in text
