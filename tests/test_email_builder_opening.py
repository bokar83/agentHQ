"""Tests for _opening() voice-line injection."""
from signal_works.email_builder import _opening


def _base_lead():
    return {
        "name": "Acme Roofing",
        "niche": "roofer",
        "city": "Salt Lake City",
        "ai_score": 42,
        "owner_name": "Bill",
        "has_website": True,
        "website_url": "https://acme.example",
    }


def _no_website_lead():
    base = _base_lead()
    base["has_website"] = False
    base["website_url"] = ""
    return base


def test_opening_falls_through_when_no_voice_line():
    """No voice_personalization_line -> existing template path runs unchanged."""
    out = _opening(_base_lead())
    assert "Right now, someone in Salt Lake City is asking ChatGPT" in out
    assert "Hi Bill," in out


def test_opening_uses_voice_line_when_present():
    lead = _base_lead()
    lead["voice_personalization_line"] = "Three generations of Salt Lake roofs is hard to fake."
    out = _opening(lead)
    lines = out.split("\n")
    assert lines[0] == "Hi Bill,"
    assert lines[1] == "Three generations of Salt Lake roofs is hard to fake."
    third = lines[2].lower()
    assert "scan" in third or "score" in third or "demo" in third


def test_opening_voice_line_works_for_no_website_leads():
    lead = _no_website_lead()
    lead["voice_personalization_line"] = "Word of mouth got us here. Let it carry online too."
    out = _opening(lead)
    lines = out.split("\n")
    assert lines[1] == "Word of mouth got us here. Let it carry online too."


def test_opening_strips_em_dash_if_voice_line_contains_one():
    """Defense in depth: scrub on read, not just on write."""
    lead = _base_lead()
    lead["voice_personalization_line"] = "Three generations — hard to fake."
    out = _opening(lead)
    assert "—" not in out


def test_opening_ignores_empty_voice_line():
    lead = _base_lead()
    lead["voice_personalization_line"] = ""
    out = _opening(lead)
    assert "Right now, someone in Salt Lake City is asking ChatGPT" in out


def test_opening_ignores_whitespace_only_voice_line():
    lead = _base_lead()
    lead["voice_personalization_line"] = "   \n  "
    out = _opening(lead)
    assert "Right now, someone in Salt Lake City is asking ChatGPT" in out
