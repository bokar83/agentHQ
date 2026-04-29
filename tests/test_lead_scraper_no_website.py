import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signal_works.lead_scraper import scrape_google_maps_leads


def test_scraped_lead_has_no_website_field():
    with patch("signal_works.lead_scraper._fetch_maps_results") as mock_fetch:
        # Return values in the normalized format that _fetch_maps_results produces
        # (name, review_count, website, has_website, rating, phone, address, maps_url)
        mock_fetch.return_value = [
            {"name": "Biz With Site", "website": "https://biz.com", "has_website": True,
             "rating": 4.7, "review_count": 50, "address": "1 Main St", "phone": "555-0001", "maps_url": ""},
            {"name": "Biz No Site", "website": "", "has_website": False,
             "rating": 4.5, "review_count": 30, "address": "2 Main St", "phone": "555-0002", "maps_url": ""},
        ]
        with patch("signal_works.lead_scraper.find_email_from_website", return_value=""):
            leads = scrape_google_maps_leads(niche="dental", city="SLC, UT", limit=2, save_to_supabase=False)

    assert len(leads) == 2
    by_name = {l["business_name"]: l for l in leads}
    assert by_name["Biz With Site"]["no_website"] is False
    assert by_name["Biz No Site"]["no_website"] is True
