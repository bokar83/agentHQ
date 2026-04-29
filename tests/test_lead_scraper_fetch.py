"""Tests for fetch_site_text helper in signal_works.lead_scraper.

fetch_site_text uses plain requests.get + BeautifulSoup to extract readable
text from a website. Decision 2026-04-29: chose BeautifulSoup over Firecrawl
for the transcript-style-dna lift test (Firecrawl free tier exhausted; lift
test does not justify $16-20/mo Hobby plan yet). See
memory/reference_firecrawl_pricing_2026.md.
"""
from unittest.mock import patch, Mock


def _html_response(html: str, status_code: int = 200):
    fake = Mock(status_code=status_code)
    fake.text = html
    fake.content = html.encode("utf-8")
    fake.headers = {"Content-Type": "text/html; charset=utf-8"}
    return fake


def test_fetch_site_text_extracts_visible_text_from_html():
    from signal_works.lead_scraper import fetch_site_text
    html = """<html><head><title>T</title><style>body {color: red}</style>
    <script>alert('x')</script></head>
    <body><h1>Acme Roofing</h1>
    <p>Family-owned since 1987. We roof Salt Lake homes.</p>
    <nav><a>Home</a><a>About</a></nav>
    </body></html>"""
    with patch("signal_works.lead_scraper.requests.get", return_value=_html_response(html)):
        out = fetch_site_text("https://acmeroofing.example")
    assert "Acme Roofing" in out
    assert "Family-owned" in out
    assert "alert" not in out
    assert "color: red" not in out


def test_fetch_site_text_returns_empty_on_no_url():
    from signal_works.lead_scraper import fetch_site_text
    assert fetch_site_text("") == ""
    assert fetch_site_text(None) == ""


def test_fetch_site_text_returns_empty_on_non_200():
    from signal_works.lead_scraper import fetch_site_text
    with patch("signal_works.lead_scraper.requests.get", return_value=_html_response("<html/>", 404)):
        assert fetch_site_text("https://x.example") == ""


def test_fetch_site_text_returns_empty_on_request_exception():
    from signal_works.lead_scraper import fetch_site_text
    import requests as rq
    with patch("signal_works.lead_scraper.requests.get", side_effect=rq.exceptions.ConnectionError("boom")):
        assert fetch_site_text("https://x.example") == ""


def test_fetch_site_text_returns_empty_on_non_html_content_type():
    """Don't try to extract text from PDFs, images, etc."""
    from signal_works.lead_scraper import fetch_site_text
    fake = Mock(status_code=200)
    fake.text = "(binary)"
    fake.content = b"%PDF-1.4"
    fake.headers = {"Content-Type": "application/pdf"}
    with patch("signal_works.lead_scraper.requests.get", return_value=fake):
        assert fetch_site_text("https://x.example/doc.pdf") == ""


def test_fetch_site_text_collapses_whitespace():
    from signal_works.lead_scraper import fetch_site_text
    html = "<html><body><p>Hello</p>\n\n\n<p>   World   </p></body></html>"
    with patch("signal_works.lead_scraper.requests.get", return_value=_html_response(html)):
        out = fetch_site_text("https://x.example")
    assert "\n\n\n" not in out
    assert "Hello" in out
    assert "World" in out
