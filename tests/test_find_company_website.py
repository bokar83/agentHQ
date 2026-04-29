"""Tests for find_company_website helper in signal_works.lead_scraper."""
from unittest.mock import patch, Mock


def _serper_response(organic_results):
    """Build a fake Serper response with the given organic-results list."""
    fake = Mock(status_code=200)
    fake.json.return_value = {"organic": organic_results}
    return fake


def test_find_company_website_returns_top_organic_url():
    from signal_works.lead_scraper import find_company_website
    fake = _serper_response([
        {"link": "https://acmeroofing.com", "title": "Acme Roofing"},
        {"link": "https://yelp.com/acme", "title": "Yelp listing"},
    ])
    with patch("signal_works.lead_scraper.requests.post", return_value=fake):
        out = find_company_website("Acme Roofing", "Salt Lake City")
    assert out == "https://acmeroofing.com"


def test_find_company_website_skips_aggregators():
    from signal_works.lead_scraper import find_company_website
    fake = _serper_response([
        {"link": "https://linkedin.com/company/acme", "title": "Acme on LinkedIn"},
        {"link": "https://yelp.com/biz/acme", "title": "Acme on Yelp"},
        {"link": "https://facebook.com/acmeroofing", "title": "Acme on Facebook"},
        {"link": "https://acmeroofing.com", "title": "Acme Roofing"},
    ])
    with patch("signal_works.lead_scraper.requests.post", return_value=fake):
        out = find_company_website("Acme Roofing", "Salt Lake City")
    assert out == "https://acmeroofing.com"


def test_find_company_website_returns_empty_on_no_results():
    from signal_works.lead_scraper import find_company_website
    fake = _serper_response([])
    with patch("signal_works.lead_scraper.requests.post", return_value=fake):
        out = find_company_website("No Such Co", "Nowhere")
    assert out == ""


def test_find_company_website_returns_empty_when_all_results_are_aggregators():
    from signal_works.lead_scraper import find_company_website
    fake = _serper_response([
        {"link": "https://linkedin.com/company/x", "title": "X"},
        {"link": "https://crunchbase.com/x", "title": "X"},
    ])
    with patch("signal_works.lead_scraper.requests.post", return_value=fake):
        out = find_company_website("X", "Nowhere")
    assert out == ""


def test_find_company_website_returns_empty_on_no_company_name():
    from signal_works.lead_scraper import find_company_website
    assert find_company_website("", "Salt Lake City") == ""
    assert find_company_website(None, "Salt Lake City") == ""


def test_find_company_website_returns_empty_on_no_api_key(monkeypatch):
    from signal_works import lead_scraper
    monkeypatch.setattr(lead_scraper, "SERPER_API_KEY", "")
    assert lead_scraper.find_company_website("Acme", "SLC") == ""


def test_find_company_website_returns_empty_on_serper_error():
    from signal_works.lead_scraper import find_company_website
    fake = Mock(status_code=500)
    with patch("signal_works.lead_scraper.requests.post", return_value=fake):
        assert find_company_website("Acme", "SLC") == ""
