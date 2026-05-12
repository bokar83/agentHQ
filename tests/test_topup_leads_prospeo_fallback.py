"""Tests for the Apollo -> Hunter -> Prospeo fallback chain added 2026-05-12
to fix the SW harvest enrichment gap. See:
  - signal_works/topup_leads.py::_resolve_email
  - docs/handoff/2026-05-12-* (harvest RCA)

Mocks all three vendors so tests cost zero credits and run offline.
"""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signal_works.topup_leads import topup, _resolve_email
from signal_works.email_gate import reset_verify_cache


def setup_function():
    reset_verify_cache()


def _passthrough_gate(email, source="unknown", allow_webmail=False, skip_verifier=False):
    return email


def _fake_lead(name: str, website: str = "https://example.com") -> dict:
    return {
        "business_name": name,
        "website_url": website,
        "no_website": False,
        "rating": 4.7,
        "reviews": 50,
        "address": "1 Main St",
        "phone": "555-0001",
        "city": "Provo",
    }


# ── Layer-4 Prospeo fallback ────────────────────────────────────


def test_prospeo_fires_when_apollo_and_hunter_both_miss():
    """Apollo owner-less + Hunter empty -> Prospeo is called and its email saved."""
    with patch("signal_works.topup_leads.scrape_google_maps_leads") as mock_scrape, \
         patch("signal_works.topup_leads.find_email_from_website", return_value=""), \
         patch("signal_works.topup_leads.gate_email", side_effect=_passthrough_gate), \
         patch("signal_works.topup_leads.find_owner_by_company") as mock_apollo, \
         patch("signal_works.topup_leads.domain_search", return_value=None) as mock_hunter, \
         patch("signal_works.topup_leads.prospeo_enrich_company") as mock_prospeo, \
         patch("signal_works.topup_leads._save_lead", return_value=True):
        mock_apollo.return_value = {"domain": "example.com", "email": None, "name": None}
        mock_prospeo.return_value = {
            "email": "owner@example.com",
            "phone": None,
            "name": "Jane Owner",
            "domain": "example.com",
        }
        mock_scrape.return_value = [_fake_lead("OneBiz")]
        topup(minimum=1, dry_run=True)

    assert mock_apollo.call_count == 1, "Apollo must be called first"
    assert mock_hunter.call_count == 1, "Hunter must be called after Apollo owner-less"
    assert mock_prospeo.call_count == 1, "Prospeo must fire when Hunter returns None"


def test_prospeo_skipped_when_hunter_returns_email():
    """Hunter wins -> Prospeo never called (credit budget protected)."""
    with patch("signal_works.topup_leads.scrape_google_maps_leads") as mock_scrape, \
         patch("signal_works.topup_leads.find_email_from_website", return_value=""), \
         patch("signal_works.topup_leads.gate_email", side_effect=_passthrough_gate), \
         patch("signal_works.topup_leads.find_owner_by_company") as mock_apollo, \
         patch("signal_works.topup_leads.domain_search", return_value="hunter@example.com") as mock_hunter, \
         patch("signal_works.topup_leads.prospeo_enrich_company") as mock_prospeo, \
         patch("signal_works.topup_leads._save_lead", return_value=True):
        mock_apollo.return_value = {"domain": "example.com", "email": None, "name": None}
        mock_scrape.return_value = [_fake_lead("OneBiz")]
        topup(minimum=1, dry_run=True)

    assert mock_hunter.call_count == 1
    assert mock_prospeo.call_count == 0, "Prospeo must not fire when Hunter wins"


def test_prospeo_skipped_when_apollo_returns_email():
    """Apollo wins -> neither Hunter nor Prospeo called."""
    with patch("signal_works.topup_leads.scrape_google_maps_leads") as mock_scrape, \
         patch("signal_works.topup_leads.find_email_from_website", return_value=""), \
         patch("signal_works.topup_leads.gate_email", side_effect=_passthrough_gate), \
         patch("signal_works.topup_leads.find_owner_by_company") as mock_apollo, \
         patch("signal_works.topup_leads.domain_search") as mock_hunter, \
         patch("signal_works.topup_leads.prospeo_enrich_company") as mock_prospeo, \
         patch("signal_works.topup_leads._save_lead", return_value=True):
        mock_apollo.return_value = {"domain": "example.com", "email": "owner@example.com", "name": "Owner"}
        mock_scrape.return_value = [_fake_lead("OneBiz")]
        topup(minimum=1, dry_run=True)

    assert mock_hunter.call_count == 0
    assert mock_prospeo.call_count == 0


def test_prospeo_resolve_returns_source_tag():
    """_resolve_email returns ("...", "prospeo", name) when Prospeo is the winner."""
    biz = _fake_lead("ProspeoBiz")
    with patch("signal_works.topup_leads.find_email_from_website", return_value=""), \
         patch("signal_works.topup_leads.gate_email", side_effect=_passthrough_gate), \
         patch("signal_works.topup_leads.find_owner_by_company", return_value=None), \
         patch("signal_works.topup_leads.domain_search", return_value=None), \
         patch("signal_works.topup_leads.prospeo_enrich_company") as mock_prospeo:
        mock_prospeo.return_value = {
            "email": "ceo@prospeo-biz.com",
            "phone": None,
            "name": "Pat CEO",
            "domain": "prospeo-biz.com",
        }
        email, source, name = _resolve_email(biz, hunter_disabled=False)
    assert email == "ceo@prospeo-biz.com"
    assert source == "prospeo"
    assert name == "Pat CEO"


def test_prospeo_skipped_when_no_candidate_domain():
    """No Apollo domain + no website -> Prospeo not called (needs a hint)."""
    biz = _fake_lead("NoWebsite", website="")
    biz["no_website"] = True
    with patch("signal_works.topup_leads.find_email_from_website", return_value=""), \
         patch("signal_works.topup_leads.gate_email", side_effect=_passthrough_gate), \
         patch("signal_works.topup_leads.find_owner_by_company", return_value=None), \
         patch("signal_works.topup_leads.domain_search") as mock_hunter, \
         patch("signal_works.topup_leads.prospeo_enrich_company") as mock_prospeo:
        email, source, _ = _resolve_email(biz, hunter_disabled=False)
    assert email == ""
    assert mock_hunter.call_count == 0
    assert mock_prospeo.call_count == 0


# ── Hunter cap raise + wall-clock ────────────────────────────────


def test_topup_raises_hunter_cap_to_400():
    """Bare topup() invocation sets HUNTER_MAX_SEARCHES_PER_DAY=400 in env."""
    import os
    os.environ.pop("HUNTER_MAX_SEARCHES_PER_DAY", None)
    with patch("signal_works.topup_leads.scrape_google_maps_leads", return_value=[]):
        topup(minimum=1, dry_run=True)
    assert os.environ.get("HUNTER_MAX_SEARCHES_PER_DAY") == "400"


def test_topup_honors_lower_caller_cap():
    """If caller pinned a lower cap (e.g. test=9), topup must NOT raise it to 400."""
    import os
    os.environ["HUNTER_MAX_SEARCHES_PER_DAY"] = "9"
    try:
        with patch("signal_works.topup_leads.scrape_google_maps_leads", return_value=[]):
            topup(minimum=1, dry_run=True)
        assert os.environ.get("HUNTER_MAX_SEARCHES_PER_DAY") == "9"
    finally:
        os.environ.pop("HUNTER_MAX_SEARCHES_PER_DAY", None)


def test_topup_wall_clock_constant_is_45min():
    """WALL_CLOCK_SECONDS must be exactly 45 minutes (2700s)."""
    from signal_works.topup_leads import WALL_CLOCK_SECONDS
    assert WALL_CLOCK_SECONDS == 45 * 60


def test_topup_docstring_mentions_400_and_45min():
    """python -c verify clause: docstring must surface both protections."""
    assert "400" in (topup.__doc__ or "")
    assert "45" in (topup.__doc__ or "") or "45-min" in (topup.__doc__ or "")
