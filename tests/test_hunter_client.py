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
from signal_works.email_gate import reset_verify_cache


def _gate_valid(**overrides):
    """Default 'valid, clean, business' verifier payload. Override fields per test."""
    base = {
        "status": "valid", "score": 95, "accept_all": False,
        "disposable": False, "gibberish": False, "webmail": False,
        "smtp_check": True,
    }
    base.update(overrides)
    return MagicMock(status_code=200, json=lambda: {"data": base})


def _split_httpx_get(domain_data, verifier_data=None):
    """Return a side_effect that routes Hunter calls by URL:
       /domain-search  -> domain_data payload
       /email-verifier -> verifier_data payload (clean valid by default)

    Both hunter_client and email_gate import httpx as the same module
    object, so a single httpx.get patch must dispatch on URL.
    """
    verifier_payload = verifier_data if verifier_data is not None else {
        "status": "valid", "score": 95, "accept_all": False,
        "disposable": False, "gibberish": False, "webmail": False,
        "smtp_check": True,
    }

    def _route(url, *args, **kwargs):
        if "email-verifier" in url:
            return MagicMock(status_code=200, json=lambda: {"data": verifier_payload})
        return MagicMock(status_code=200, json=lambda: {"data": {"emails": domain_data}})

    return _route


def setup_function():
    reset_daily_counter()
    reset_verify_cache()


def test_domain_search_returns_owner_email():
    with patch.dict("os.environ", {"HUNTER_API_KEY": "test-key"}):  # pragma: allowlist secret
        with patch("signal_works.hunter_client.httpx.get") as mock_get:
            mock_get.side_effect = _split_httpx_get([
                {"value": "owner@biz.com", "seniority": "executive", "confidence": 90},
                {"value": "info@biz.com", "seniority": None, "confidence": 80},
            ])
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


def test_daily_cap_raises_after_max_calls():
    # Each domain_search with no results increments the call counter up to
    # 3 times (tier-1 -> tier-2 -> tier-3). Set cap to 9 so exactly 3 full
    # cascades fit and the 4th raises.
    with patch.dict("os.environ", {
        "HUNTER_API_KEY": "test-key",  # pragma: allowlist secret
        "HUNTER_MAX_SEARCHES_PER_DAY": "9",
    }):
        with patch("signal_works.hunter_client.httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"data": {"emails": []}},
            )
            for _ in range(3):
                domain_search("biz.com")
            with pytest.raises(HunterCapReached):
                domain_search("biz.com")


def test_domain_search_returns_none_when_no_api_key():
    """Without HUNTER_API_KEY, return None gracefully and do not consume cap."""
    os.environ.pop("HUNTER_API_KEY", None)
    email = domain_search("biz.com")
    assert email is None
