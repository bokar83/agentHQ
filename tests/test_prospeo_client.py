"""Schema tests for signal_works.prospeo_client.

Regression cover for the 2026-05-12 INVALID_DATAPOINTS bug: the prior
client sent only company_* fields to /enrich-person, which Prospeo
rejected 100% of the time. These tests pin the corrected schema so the
bug cannot silently return.

Asserts:
  - /enrich-person payloads always carry a valid person identifier
    (first_name+last_name, full_name, linkedin_url, email, or person_id)
  - company_only payloads route through /search-person first, then
    /enrich-person with the resolved person_id
  - only_verified_email=True is set to prevent credit burn on guesses
  - PROSPEO_KEY missing -> returns None without making a request
  - error responses (INVALID_DATAPOINTS, NO_MATCH) return None cleanly
"""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signal_works.prospeo_client import (
    PROSPEO_ENRICH_URL,
    PROSPEO_SEARCH_URL,
    _build_enrich_payload,
    _split_name,
    prospeo_enrich_company,
)


# ── helpers ──────────────────────────────────────────────────────


class _FakeResp:
    def __init__(self, payload: dict):
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    """Captures POST payloads in order for assertion."""

    def __init__(self, responses: list[dict]):
        self.responses = list(responses)
        self.calls: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def post(self, url: str, headers: dict | None = None, json: dict | None = None):
        self.calls.append({"url": url, "headers": headers or {}, "json": json or {}})
        if not self.responses:
            raise AssertionError(f"Unexpected POST to {url}")
        return _FakeResp(self.responses.pop(0))


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("PROSPEO_KEY", "test-key-abc")
    yield


# ── _split_name ──────────────────────────────────────────────────


def test_split_name_two_tokens():
    assert _split_name("Jane Owner") == ("Jane", "Owner")


def test_split_name_three_tokens_joins_last():
    assert _split_name("Maria De La Cruz") == ("Maria", "De La Cruz")


def test_split_name_single_token_returns_empty_last():
    # Single-token names like "Owner" can't satisfy /enrich-person
    assert _split_name("Owner") == ("Owner", "")


def test_split_name_empty():
    assert _split_name("") == ("", "")
    assert _split_name("   ") == ("", "")


# ── _build_enrich_payload ────────────────────────────────────────


def test_build_payload_with_full_name_includes_required_fields():
    payload = _build_enrich_payload(
        owner_name="Jane Owner",
        business_name="Aspen Roofing",
        domain="aspenroofing.com",
    )
    assert payload is not None
    assert payload["only_verified_email"] is True
    data = payload["data"]
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Owner"
    assert data["company_website"] == "aspenroofing.com"
    assert data["company_name"] == "Aspen Roofing"
    # CRITICAL: no orphan company_only fields without person identifier
    assert "company_city" not in data


def test_build_payload_with_person_id_skips_name_fields():
    payload = _build_enrich_payload(
        owner_name="",
        business_name="Aspen Roofing",
        domain="aspenroofing.com",
        person_id="prospeo_pid_42",
    )
    assert payload is not None
    assert payload["data"] == {"person_id": "prospeo_pid_42"}
    assert payload["only_verified_email"] is True


def test_build_payload_single_token_name_returns_none():
    # Apollo sometimes returns "Owner" as the placeholder name -- this is
    # NOT a valid person identifier for Prospeo.
    payload = _build_enrich_payload(
        owner_name="Owner",
        business_name="Aspen Roofing",
        domain="aspenroofing.com",
    )
    assert payload is None


def test_build_payload_empty_owner_returns_none():
    # Empty owner_name without person_id -> caller must use /search-person
    payload = _build_enrich_payload(
        owner_name="",
        business_name="Aspen Roofing",
        domain="aspenroofing.com",
    )
    assert payload is None


# ── prospeo_enrich_company integration ───────────────────────────


def test_no_api_key_returns_none(monkeypatch):
    monkeypatch.delenv("PROSPEO_KEY", raising=False)
    result = prospeo_enrich_company(
        business_name="Aspen Roofing",
        domain="aspenroofing.com",
        owner_name="Jane Owner",
    )
    assert result is None


def test_with_owner_name_goes_straight_to_enrich():
    """Apollo found the person -> Prospeo skips /search-person, calls
    /enrich-person directly with first/last + company."""
    fake_client = _FakeClient([
        {
            "error": False,
            "person": {
                "first_name": "Jane",
                "last_name": "Owner",
                "email": {"revealed": True, "email": "jane@aspenroofing.com"},
                "mobile": {"revealed": False},
            },
            "company": {"domain": "aspenroofing.com"},
        }
    ])
    with patch("signal_works.prospeo_client.httpx.Client", return_value=fake_client):
        result = prospeo_enrich_company(
            business_name="Aspen Roofing",
            domain="aspenroofing.com",
            owner_name="Jane Owner",
        )
    assert result is not None
    assert result["email"] == "jane@aspenroofing.com"
    assert result["name"] == "Jane Owner"

    # Exactly one HTTP call -- /enrich-person, no /search-person hop
    assert len(fake_client.calls) == 1
    call = fake_client.calls[0]
    assert call["url"] == PROSPEO_ENRICH_URL
    assert call["headers"]["X-KEY"] == "test-key-abc"
    assert call["headers"]["Content-Type"] == "application/json"

    data = call["json"]["data"]
    # SCHEMA REGRESSION GUARD: person identifier MUST be present
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Owner"
    assert data["company_website"] == "aspenroofing.com"
    assert data["company_name"] == "Aspen Roofing"
    assert call["json"]["only_verified_email"] is True


def test_no_owner_name_falls_back_to_search_then_enrich():
    """No Apollo name -> /search-person first to find a decision-maker,
    then /enrich-person with person_id."""
    fake_client = _FakeClient([
        # /search-person response
        {
            "error": False,
            "results": [
                {
                    "person": {"id": "prospeo_pid_999"},
                    "company": {"domain": "aspenroofing.com"},
                }
            ],
            "pagination": {"current_page": 1, "total_count": 1},
        },
        # /enrich-person response
        {
            "error": False,
            "person": {
                "first_name": "Pat",
                "last_name": "CEO",
                "email": {"revealed": True, "email": "pat@aspenroofing.com"},
                "mobile": {"revealed": False},
            },
            "company": {"domain": "aspenroofing.com"},
        },
    ])
    with patch("signal_works.prospeo_client.httpx.Client", return_value=fake_client):
        result = prospeo_enrich_company(
            business_name="Aspen Roofing",
            domain="aspenroofing.com",
            owner_name="",
        )
    assert result is not None
    assert result["email"] == "pat@aspenroofing.com"

    # Two HTTP calls in order: search -> enrich
    assert len(fake_client.calls) == 2
    assert fake_client.calls[0]["url"] == PROSPEO_SEARCH_URL
    assert fake_client.calls[1]["url"] == PROSPEO_ENRICH_URL

    # /search-person filters: company website + decision-maker seniority
    search_filters = fake_client.calls[0]["json"]["filters"]
    assert "aspenroofing.com" in search_filters["company"]["websites"]["include"]
    assert "Founder/Owner" in search_filters["person_seniority"]["include"]

    # /enrich-person second call uses person_id (NOT company-only fields)
    enrich_data = fake_client.calls[1]["json"]["data"]
    assert enrich_data == {"person_id": "prospeo_pid_999"}


def test_search_no_match_returns_none_without_enrich():
    """If /search-person finds no decision-maker, we MUST NOT call
    /enrich-person with a busted payload (the original bug)."""
    fake_client = _FakeClient([
        {"error": False, "results": []},
    ])
    with patch("signal_works.prospeo_client.httpx.Client", return_value=fake_client):
        result = prospeo_enrich_company(
            business_name="Obscure LLC",
            domain="obscurellc.com",
            owner_name="",
        )
    assert result is None
    # Only /search-person was called, never /enrich-person
    assert len(fake_client.calls) == 1
    assert fake_client.calls[0]["url"] == PROSPEO_SEARCH_URL


def test_search_error_returns_none():
    fake_client = _FakeClient([
        {"error": True, "error_code": "NO_RESULTS"},
    ])
    with patch("signal_works.prospeo_client.httpx.Client", return_value=fake_client):
        result = prospeo_enrich_company(
            business_name="Obscure LLC",
            domain="obscurellc.com",
            owner_name="",
        )
    assert result is None


def test_enrich_invalid_datapoints_error_returns_none():
    """If Prospeo somehow returns INVALID_DATAPOINTS, we log and return
    None (don't crash). Regression guard: this is what 100% of harvest
    calls were returning before the fix."""
    fake_client = _FakeClient([
        {"error": True, "error_code": "INVALID_DATAPOINTS"},
    ])
    with patch("signal_works.prospeo_client.httpx.Client", return_value=fake_client):
        result = prospeo_enrich_company(
            business_name="Aspen Roofing",
            domain="aspenroofing.com",
            owner_name="Jane Owner",
        )
    assert result is None


def test_enrich_no_match_returns_none():
    fake_client = _FakeClient([
        {"error": True, "error_code": "NO_MATCH"},
    ])
    with patch("signal_works.prospeo_client.httpx.Client", return_value=fake_client):
        result = prospeo_enrich_company(
            business_name="Aspen Roofing",
            domain="aspenroofing.com",
            owner_name="Jane Owner",
        )
    assert result is None


def test_no_company_hint_returns_none_without_request():
    """Both business_name AND domain empty -> can't search or enrich.
    Must short-circuit before any HTTP call (saves the credit)."""
    fake_client = _FakeClient([])
    with patch("signal_works.prospeo_client.httpx.Client", return_value=fake_client):
        result = prospeo_enrich_company(
            business_name="",
            domain="",
            owner_name="",
        )
    assert result is None
    assert len(fake_client.calls) == 0


def test_want_phone_false_omits_enrich_mobile():
    """Harvest path defaults want_phone=False; payload must NOT include
    enrich_mobile (else 10 credits per call)."""
    fake_client = _FakeClient([
        {
            "error": False,
            "person": {
                "first_name": "Jane",
                "last_name": "Owner",
                "email": {"revealed": True, "email": "jane@aspenroofing.com"},
                "mobile": {"revealed": False},
            },
        }
    ])
    with patch("signal_works.prospeo_client.httpx.Client", return_value=fake_client):
        prospeo_enrich_company(
            business_name="Aspen Roofing",
            domain="aspenroofing.com",
            owner_name="Jane Owner",
            want_phone=False,
        )
    assert "enrich_mobile" not in fake_client.calls[0]["json"]


def test_want_phone_true_sets_enrich_mobile():
    fake_client = _FakeClient([
        {
            "error": False,
            "person": {
                "first_name": "Jane",
                "last_name": "Owner",
                "email": {"revealed": True, "email": "jane@aspenroofing.com"},
                "mobile": {
                    "revealed": True,
                    "mobile": "5558675309",
                    "mobile_international": "+15558675309",
                },
            },
        }
    ])
    with patch("signal_works.prospeo_client.httpx.Client", return_value=fake_client):
        result = prospeo_enrich_company(
            business_name="Aspen Roofing",
            domain="aspenroofing.com",
            owner_name="Jane Owner",
            want_phone=True,
        )
    assert fake_client.calls[0]["json"]["enrich_mobile"] is True
    assert result["phone"] == "+15558675309"


def test_request_exception_returns_none():
    """Transient network failures must NOT crash the harvest loop."""
    class _Boom:
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def post(self, *a, **kw):
            raise RuntimeError("connection reset")

    with patch("signal_works.prospeo_client.httpx.Client", return_value=_Boom()):
        result = prospeo_enrich_company(
            business_name="Aspen Roofing",
            domain="aspenroofing.com",
            owner_name="Jane Owner",
        )
    assert result is None
