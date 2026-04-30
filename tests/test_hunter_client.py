import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from signal_works.hunter_client import (
    domain_search,
    HunterCapReached,
    reset_daily_counter,
)


def setup_function():
    reset_daily_counter()


def test_domain_search_returns_owner_email():
    with patch.dict("os.environ", {"HUNTER_API_KEY": "test-key"}):  # pragma: allowlist secret
        with patch("signal_works.hunter_client.httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"data": {"emails": [
                    {"value": "owner@biz.com", "seniority": "executive", "confidence": 90},
                    {"value": "info@biz.com", "seniority": None, "confidence": 80},
                ]}},
            )
            email = domain_search("biz.com")
    assert email == "owner@biz.com"


def test_domain_search_skips_non_owner_seniority():
    with patch.dict("os.environ", {"HUNTER_API_KEY": "test-key"}):  # pragma: allowlist secret
        with patch("signal_works.hunter_client.httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"data": {"emails": [
                    {"value": "intern@biz.com", "seniority": "junior", "confidence": 95},
                ]}},
            )
            email = domain_search("biz.com")
    assert email is None


def test_domain_search_returns_none_on_429():
    with patch.dict("os.environ", {"HUNTER_API_KEY": "test-key"}):  # pragma: allowlist secret
        with patch("signal_works.hunter_client.httpx.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=429, text="rate limited")
            email = domain_search("biz.com")
    assert email is None


def test_daily_cap_raises_after_5_calls():
    with patch.dict("os.environ", {"HUNTER_API_KEY": "test-key"}):  # pragma: allowlist secret
        with patch("signal_works.hunter_client.httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"data": {"emails": []}},
            )
            for _ in range(5):
                domain_search("biz.com")
            with pytest.raises(HunterCapReached):
                domain_search("biz.com")


def test_domain_search_returns_none_when_no_api_key():
    """Without HUNTER_API_KEY, return None gracefully and do not consume cap."""
    os.environ.pop("HUNTER_API_KEY", None)
    email = domain_search("biz.com")
    assert email is None
