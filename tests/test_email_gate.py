"""
tests/test_email_gate.py
========================
Ship 2c — role-mailbox + deliverability gate. Verifies:

  - Role-prefix step-1 drops (info@, sales@, dispatcher@, info2@ -> info)
  - Webmail drop unless allow_webmail=True
  - Hunter Email Verifier step-2 drops (accept_all, disposable, low_score,
    invalid, gibberish, webmail)
  - In-run verifier cache reuses results within one process
  - Trailing-digit stripping (info2@ matches role)
  - skip_verifier flag runs only step 1
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from signal_works.email_gate import (
    gate_email,
    EmailGateDrop,
    ROLE_PREFIXES,
    reset_verify_cache,
)


def setup_function():
    reset_verify_cache()


# ── Step 1: role-prefix local drops (free, no Hunter call) ────────

def test_drops_info_prefix():
    with pytest.raises(EmailGateDrop) as exc:
        gate_email("info@elevateroofing.com", skip_verifier=True)
    assert exc.value.reason == "role_prefix"


def test_drops_sales_prefix():
    with pytest.raises(EmailGateDrop) as exc:
        gate_email("sales@biz.com", skip_verifier=True)
    assert exc.value.reason == "role_prefix"


def test_drops_dispatcher_prefix():
    with pytest.raises(EmailGateDrop) as exc:
        gate_email("dispatcher@biz.com", skip_verifier=True)
    assert exc.value.reason == "role_prefix"


def test_strips_trailing_digits_and_drops():
    # info2@biz.com -> info -> role match
    with pytest.raises(EmailGateDrop) as exc:
        gate_email("info2@biz.com", skip_verifier=True)
    assert exc.value.reason == "role_prefix"
    assert "matched=info" in exc.value.detail


def test_personal_local_passes_step1():
    # No Hunter call needed when skip_verifier=True; just verifies step 1.
    out = gate_email("derek@elevateroofing.com", skip_verifier=True)
    assert out == "derek@elevateroofing.com"


def test_role_prefixes_set_includes_canonical():
    # Sanity check: spec-mandated prefixes must all be in the set.
    must_have = {"info", "sales", "support", "dispatcher", "scheduling",
                 "frontdesk", "admin", "noreply", "billing", "legal"}
    assert must_have.issubset(ROLE_PREFIXES)


# ── Webmail handling ───────────────────────────────────────────────

def test_drops_gmail_by_default():
    with pytest.raises(EmailGateDrop) as exc:
        gate_email("derek@gmail.com", skip_verifier=True)
    assert exc.value.reason == "webmail"


def test_allow_webmail_lets_gmail_through_step1():
    out = gate_email("derek@gmail.com", skip_verifier=True, allow_webmail=True)
    assert out == "derek@gmail.com"


# ── Step 2: Hunter Email Verifier (mocked) ─────────────────────────

def _mock_verify(payload):
    return MagicMock(status_code=200, json=lambda: {"data": payload})


def test_accept_all_dropped():
    with patch.dict("os.environ", {"HUNTER_API_KEY": "test"}):  # pragma: allowlist secret
        with patch("signal_works.email_gate.httpx.get") as mock_get:
            mock_get.return_value = _mock_verify({
                "status": "accept_all", "score": 85, "accept_all": True,
                "disposable": False, "gibberish": False, "webmail": False,
                "smtp_check": True,
            })
            with pytest.raises(EmailGateDrop) as exc:
                gate_email("derek@biz.com", source="t")
    assert exc.value.reason == "accept_all"


def test_disposable_dropped():
    with patch.dict("os.environ", {"HUNTER_API_KEY": "test"}):  # pragma: allowlist secret
        with patch("signal_works.email_gate.httpx.get") as mock_get:
            mock_get.return_value = _mock_verify({
                "status": "valid", "score": 90, "accept_all": False,
                "disposable": True, "gibberish": False, "webmail": False,
                "smtp_check": True,
            })
            with pytest.raises(EmailGateDrop) as exc:
                gate_email("derek@trashmail.com", source="t")
    assert exc.value.reason == "disposable"


def test_low_score_dropped_when_not_valid():
    with patch.dict("os.environ", {"HUNTER_API_KEY": "test"}):  # pragma: allowlist secret
        with patch("signal_works.email_gate.httpx.get") as mock_get:
            mock_get.return_value = _mock_verify({
                "status": "risky", "score": 60, "accept_all": False,
                "disposable": False, "gibberish": False, "webmail": False,
                "smtp_check": True,
            })
            with pytest.raises(EmailGateDrop) as exc:
                gate_email("derek@biz.com", source="t")
    assert exc.value.reason == "low_score"


def test_low_score_passes_when_valid_status():
    # status=='valid' overrides the score<80 drop -- Hunter says it's good
    with patch.dict("os.environ", {"HUNTER_API_KEY": "test"}):  # pragma: allowlist secret
        with patch("signal_works.email_gate.httpx.get") as mock_get:
            mock_get.return_value = _mock_verify({
                "status": "valid", "score": 70, "accept_all": False,
                "disposable": False, "gibberish": False, "webmail": False,
                "smtp_check": True,
            })
            out = gate_email("derek@biz.com", source="t")
    assert out == "derek@biz.com"


def test_invalid_status_dropped():
    with patch.dict("os.environ", {"HUNTER_API_KEY": "test"}):  # pragma: allowlist secret
        with patch("signal_works.email_gate.httpx.get") as mock_get:
            mock_get.return_value = _mock_verify({
                "status": "invalid", "score": 0, "accept_all": False,
                "disposable": False, "gibberish": False, "webmail": False,
                "smtp_check": False,
            })
            with pytest.raises(EmailGateDrop) as exc:
                gate_email("derek@biz.com", source="t")
    assert exc.value.reason == "invalid"


def test_smtp_check_false_dropped_as_invalid():
    with patch.dict("os.environ", {"HUNTER_API_KEY": "test"}):  # pragma: allowlist secret
        with patch("signal_works.email_gate.httpx.get") as mock_get:
            mock_get.return_value = _mock_verify({
                "status": "risky", "score": 90, "accept_all": False,
                "disposable": False, "gibberish": False, "webmail": False,
                "smtp_check": False,
            })
            with pytest.raises(EmailGateDrop) as exc:
                gate_email("derek@biz.com", source="t")
    assert exc.value.reason == "invalid"


def test_clean_email_passes():
    with patch.dict("os.environ", {"HUNTER_API_KEY": "test"}):  # pragma: allowlist secret
        with patch("signal_works.email_gate.httpx.get") as mock_get:
            mock_get.return_value = _mock_verify({
                "status": "valid", "score": 95, "accept_all": False,
                "disposable": False, "gibberish": False, "webmail": False,
                "smtp_check": True,
            })
            out = gate_email("derek@elevateroofing.com", source="t")
    assert out == "derek@elevateroofing.com"


def test_in_run_cache_reuses_verify_result():
    """Same email queried twice in one run should call Hunter exactly once."""
    with patch.dict("os.environ", {"HUNTER_API_KEY": "test"}):  # pragma: allowlist secret
        with patch("signal_works.email_gate.httpx.get") as mock_get:
            mock_get.return_value = _mock_verify({
                "status": "valid", "score": 95, "accept_all": False,
                "disposable": False, "gibberish": False, "webmail": False,
                "smtp_check": True,
            })
            gate_email("derek@biz.com", source="t")
            gate_email("derek@biz.com", source="t")
            gate_email("derek@biz.com", source="t")
    assert mock_get.call_count == 1


def test_cache_remembers_drops_too():
    """Drop result is cached so we don't burn a credit re-verifying a known-bad."""
    with patch.dict("os.environ", {"HUNTER_API_KEY": "test"}):  # pragma: allowlist secret
        with patch("signal_works.email_gate.httpx.get") as mock_get:
            mock_get.return_value = _mock_verify({
                "status": "accept_all", "score": 85, "accept_all": True,
                "disposable": False, "gibberish": False, "webmail": False,
                "smtp_check": True,
            })
            with pytest.raises(EmailGateDrop):
                gate_email("derek@biz.com", source="t")
            with pytest.raises(EmailGateDrop):
                gate_email("derek@biz.com", source="t")
    assert mock_get.call_count == 1


def test_verifier_down_when_429():
    with patch.dict("os.environ", {"HUNTER_API_KEY": "test"}):  # pragma: allowlist secret
        with patch("signal_works.email_gate.httpx.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=429, text="rate limited")
            with pytest.raises(EmailGateDrop) as exc:
                gate_email("derek@biz.com", source="t")
    assert exc.value.reason == "verifier_down"


def test_verifier_down_when_no_api_key():
    os.environ.pop("HUNTER_API_KEY", None)
    with pytest.raises(EmailGateDrop) as exc:
        gate_email("derek@biz.com", source="t")
    assert exc.value.reason == "verifier_down"
