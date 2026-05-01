"""Unit tests for newsletter_editorial_input module."""
import os
import sys
from datetime import date
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_upsert_inserts_row_when_missing():
    from newsletter_editorial_input import upsert_reply

    fake_conn = MagicMock()
    fake_cursor = MagicMock()
    fake_conn.cursor.return_value.__enter__.return_value = fake_cursor

    with patch("newsletter_editorial_input._conn", return_value=fake_conn):
        upsert_reply(date(2026, 5, 4), "we noticed clients want X this week", "12345")

    fake_cursor.execute.assert_called_once()
    args = fake_cursor.execute.call_args[0]
    assert "INSERT INTO newsletter_editorial_input" in args[0]
    assert "ON CONFLICT" in args[0]
    assert args[1] == (date(2026, 5, 4), "we noticed clients want X this week", "12345")
    fake_conn.commit.assert_called_once()


def test_get_for_week_returns_text_when_present():
    from newsletter_editorial_input import get_reply_for_week

    fake_conn = MagicMock()
    fake_cursor = MagicMock()
    fake_cursor.fetchone.return_value = ("here is what I noticed",)
    fake_conn.cursor.return_value.__enter__.return_value = fake_cursor

    with patch("newsletter_editorial_input._conn", return_value=fake_conn):
        result = get_reply_for_week(date(2026, 5, 4))

    assert result == "here is what I noticed"


def test_get_for_week_returns_none_when_missing():
    from newsletter_editorial_input import get_reply_for_week

    fake_conn = MagicMock()
    fake_cursor = MagicMock()
    fake_cursor.fetchone.return_value = None
    fake_conn.cursor.return_value.__enter__.return_value = fake_cursor

    with patch("newsletter_editorial_input._conn", return_value=fake_conn):
        result = get_reply_for_week(date(2026, 5, 4))

    assert result is None
