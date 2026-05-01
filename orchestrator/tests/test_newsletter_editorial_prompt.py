"""Tests for the Sunday 18:00 editorial prompt callback."""
import os
import sys
from datetime import datetime
from unittest.mock import patch

import pytz

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_callback_skips_non_sunday():
    from newsletter_editorial_prompt import newsletter_editorial_prompt_tick

    fake_now = pytz.timezone("America/Denver").localize(datetime(2026, 5, 4, 18, 0))
    with patch("newsletter_editorial_prompt._now", return_value=fake_now), patch(
        "newsletter_editorial_prompt.send_message"
    ) as mock_send:
        newsletter_editorial_prompt_tick()

    mock_send.assert_not_called()


def test_callback_sends_on_sunday():
    from newsletter_editorial_prompt import newsletter_editorial_prompt_tick

    fake_now = pytz.timezone("America/Denver").localize(datetime(2026, 5, 3, 18, 0))
    with patch("newsletter_editorial_prompt._now", return_value=fake_now), patch(
        "newsletter_editorial_prompt._chat_id", return_value="12345"
    ), patch("newsletter_editorial_prompt.send_message") as mock_send:
        newsletter_editorial_prompt_tick()

    mock_send.assert_called_once()
    args = mock_send.call_args[0]
    assert args[0] == "12345"
    assert "newsletter" in args[1].lower()
    assert "one sentence" in args[1].lower()


def test_callback_skips_when_no_chat_id():
    from newsletter_editorial_prompt import newsletter_editorial_prompt_tick

    fake_now = pytz.timezone("America/Denver").localize(datetime(2026, 5, 3, 18, 0))
    with patch("newsletter_editorial_prompt._now", return_value=fake_now), patch(
        "newsletter_editorial_prompt._chat_id", return_value=None
    ), patch("newsletter_editorial_prompt.send_message") as mock_send:
        newsletter_editorial_prompt_tick()

    mock_send.assert_not_called()
