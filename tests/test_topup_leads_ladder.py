import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signal_works.topup_leads import topup


def _fake_lead(name: str, has_website: bool = True) -> dict:
    return {
        "business_name": name,
        "website_url": "https://example.com" if has_website else None,
        "no_website": not has_website,
        "rating": 4.7, "reviews": 50, "address": "1 Main St", "phone": "555-0001",
    }


def test_ladder_stops_at_target():
    """Hits target=10 in tier 1, never advances to tier 2."""
    with patch("signal_works.topup_leads.scrape_google_maps_leads") as mock_scrape, \
         patch("signal_works.topup_leads.find_email_from_website", return_value="found@biz.com"), \
         patch("signal_works.topup_leads._save_lead", return_value=True):
        mock_scrape.return_value = [_fake_lead(f"Biz{i}") for i in range(15)]
        n = topup(minimum=10, dry_run=True)
    assert n == 10
    # Should not have walked more than 1 niche/city pair (which yielded 15 fakes -> first 10 saved)
    assert mock_scrape.call_count == 1


def test_circuit_breaker_after_5_double_failures():
    """If 5 consecutive businesses fail Firecrawl AND Apollo, Hunter is short-circuited."""
    with patch("signal_works.topup_leads.scrape_google_maps_leads") as mock_scrape, \
         patch("signal_works.topup_leads.find_email_from_website", return_value=""), \
         patch("signal_works.topup_leads.find_owner_by_company", return_value=None), \
         patch("signal_works.topup_leads.domain_search") as mock_hunter, \
         patch("signal_works.topup_leads._save_lead"), \
         patch("signal_works.topup_leads._telegram_alert"):
        mock_scrape.return_value = [_fake_lead(f"Biz{i}") for i in range(20)]
        topup(minimum=10, dry_run=True)
    # Hunter should have been called 0 times after circuit breaker trips
    assert mock_hunter.call_count == 0


def test_firecrawl_email_used_when_found():
    with patch("signal_works.topup_leads.scrape_google_maps_leads") as mock_scrape, \
         patch("signal_works.topup_leads.find_email_from_website", return_value="real@biz.com"), \
         patch("signal_works.topup_leads.find_owner_by_company") as mock_apollo, \
         patch("signal_works.topup_leads.domain_search") as mock_hunter, \
         patch("signal_works.topup_leads._save_lead", return_value=True):
        mock_scrape.return_value = [_fake_lead("OneBiz")]
        topup(minimum=1, dry_run=True)
    assert mock_apollo.call_count == 0  # Apollo not called when Firecrawl wins
    assert mock_hunter.call_count == 0


def test_apollo_used_when_firecrawl_misses():
    with patch("signal_works.topup_leads.scrape_google_maps_leads") as mock_scrape, \
         patch("signal_works.topup_leads.find_email_from_website", return_value=""), \
         patch("signal_works.topup_leads.find_owner_by_company") as mock_apollo, \
         patch("signal_works.topup_leads.domain_search") as mock_hunter, \
         patch("signal_works.topup_leads._save_lead", return_value=True):
        mock_apollo.return_value = {"domain": "biz.com", "email": "owner@biz.com", "name": "Owner"}
        mock_scrape.return_value = [_fake_lead("OneBiz")]
        topup(minimum=1, dry_run=True)
    assert mock_apollo.call_count == 1
    assert mock_hunter.call_count == 0


def test_hunter_used_when_apollo_finds_domain_but_no_owner():
    with patch("signal_works.topup_leads.scrape_google_maps_leads") as mock_scrape, \
         patch("signal_works.topup_leads.find_email_from_website", return_value=""), \
         patch("signal_works.topup_leads.find_owner_by_company") as mock_apollo, \
         patch("signal_works.topup_leads.domain_search", return_value="found@biz.com") as mock_hunter, \
         patch("signal_works.topup_leads._save_lead", return_value=True):
        mock_apollo.return_value = {"domain": "biz.com", "email": None, "name": None}
        mock_scrape.return_value = [_fake_lead("OneBiz")]
        topup(minimum=1, dry_run=True)
    assert mock_hunter.call_count == 1
