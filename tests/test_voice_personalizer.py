"""Tests for the voice personalizer single-lead helper."""
from unittest.mock import patch


def test_personalize_one_returns_none_when_no_website():
    from signal_works.voice_personalizer import _personalize_one
    assert _personalize_one({"id": 1, "name": "Foo", "website_url": None}) is None


def test_personalize_one_returns_none_when_empty_site_text():
    from signal_works.voice_personalizer import _personalize_one
    with patch("signal_works.voice_personalizer.fetch_site_text", return_value=""):
        out = _personalize_one({
            "id": 1, "name": "Foo", "website_url": "https://foo.example",
            "niche": "roofer", "city": "Salt Lake City",
        })
    assert out is None


def test_personalize_one_returns_opener_on_happy_path():
    from signal_works.voice_personalizer import _personalize_one
    fake_text = "We've roofed Salt Lake homes for three generations. " * 10
    fake_profile = {
        "opener_line": "Three generations of Salt Lake roofs is hard to fake.",
        "confidence": "high",
    }
    with patch("signal_works.voice_personalizer.fetch_site_text", return_value=fake_text), \
         patch("signal_works.voice_personalizer.extract", return_value=fake_profile):
        out = _personalize_one({
            "id": 1, "name": "Acme", "website_url": "https://acme.example",
            "niche": "roofer", "city": "Salt Lake City",
        })
    assert out == "Three generations of Salt Lake roofs is hard to fake."


def test_personalize_one_strips_em_dashes():
    from signal_works.voice_personalizer import _personalize_one
    fake_profile = {"opener_line": "Three generations — hard to fake.", "confidence": "high"}
    with patch("signal_works.voice_personalizer.fetch_site_text", return_value="x" * 200), \
         patch("signal_works.voice_personalizer.extract", return_value=fake_profile):
        out = _personalize_one({
            "id": 1, "name": "Acme", "website_url": "https://x.example",
            "niche": "roofer", "city": "Salt Lake City",
        })
    assert "—" not in out
    assert "–" not in out


def test_personalize_one_returns_none_on_extract_exception():
    from signal_works.voice_personalizer import _personalize_one
    with patch("signal_works.voice_personalizer.fetch_site_text", return_value="x" * 200), \
         patch("signal_works.voice_personalizer.extract", side_effect=ValueError("boom")):
        out = _personalize_one({
            "id": 1, "name": "Acme", "website_url": "https://x.example",
            "niche": "roofer", "city": "Salt Lake City",
        })
    assert out is None


def test_personalize_one_returns_none_when_text_too_short():
    from signal_works.voice_personalizer import _personalize_one, MIN_TEXT_CHARS
    with patch("signal_works.voice_personalizer.fetch_site_text", return_value="x" * (MIN_TEXT_CHARS - 1)):
        out = _personalize_one({
            "id": 1, "name": "Acme", "website_url": "https://x.example",
            "niche": "roofer", "city": "Salt Lake City",
        })
    assert out is None
