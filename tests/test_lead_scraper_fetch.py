"""Tests for fetch_site_text helper in signal_works.lead_scraper."""
from unittest.mock import patch, Mock


def test_fetch_site_text_returns_markdown_on_success():
    from signal_works.lead_scraper import fetch_site_text

    fake_response = Mock(status_code=200)
    fake_response.json.return_value = {
        "success": True,
        "data": {"markdown": "# Acme Roofing\n\nFamily-owned since 1987."},
    }
    with patch("signal_works.lead_scraper.requests.post", return_value=fake_response):
        out = fetch_site_text("https://acmeroofing.example")
    assert "Acme Roofing" in out
    assert "Family-owned" in out


def test_fetch_site_text_returns_empty_on_no_url():
    from signal_works.lead_scraper import fetch_site_text
    assert fetch_site_text("") == ""
    assert fetch_site_text(None) == ""


def test_fetch_site_text_returns_empty_on_firecrawl_failure():
    from signal_works.lead_scraper import fetch_site_text
    fake_response = Mock(status_code=500)
    with patch("signal_works.lead_scraper.requests.post", return_value=fake_response):
        out = fetch_site_text("https://acmeroofing.example")
    assert out == ""


def test_fetch_site_text_returns_empty_when_no_api_key(monkeypatch):
    from signal_works import lead_scraper
    monkeypatch.setattr(lead_scraper, "FIRECRAWL_API_KEY", "")
    assert lead_scraper.fetch_site_text("https://example.com") == ""
