from unittest.mock import patch
import pytest
from skills.inbound_lead.researcher import (
    research, _resolve_domain,
)
from skills.inbound_lead.schema import ResearchBrief


def test_resolve_domain_from_email():
    assert _resolve_domain("jane@acme.com", None) == "acme.com"


def test_resolve_domain_prefers_explicit_url():
    assert _resolve_domain("jane@acme.com", "https://acmecorp.io/") == "acmecorp.io"


def test_resolve_domain_strips_subdomains():
    assert _resolve_domain("jane@mail.acme.com", None) == "acme.com"


def test_resolve_domain_rejects_free_provider():
    assert _resolve_domain("jane@gmail.com", None) is None
    assert _resolve_domain("jane@yahoo.com", None) is None
    assert _resolve_domain("jane@outlook.com", None) is None


def test_research_returns_minimal_brief_on_no_domain():
    """Free-email prospect with no company URL: skip research, return minimal brief."""
    result = research(
        name="Jane", email="jane@gmail.com", company=None, raw_company_url=None,
    )
    assert isinstance(result, ResearchBrief)
    assert result.research_confidence == "none"
    assert result.what_they_do  # must not be empty


def test_research_degrades_when_research_engine_fails():
    """If run_research returns success=False, fall back to minimal brief."""
    with patch("skills.inbound_lead.researcher.run_research") as rr:
        rr.return_value = {"success": False, "answer": "", "error": "boom", "tool_calls": 0, "turns": 0}
        result = research(
            name="Jane", email="jane@acme.com", company="Acme", raw_company_url=None,
        )
    assert result.research_confidence == "none"
    assert result.company_domain == "acme.com"


def test_research_parses_json_from_answer():
    """If run_research returns a valid JSON payload, parse it into ResearchBrief."""
    brief_json = (
        '{"company_domain": "acme.com", '
        '"what_they_do": "Boutique mid-market consulting.", '
        '"industry_signals": ["Mid-market focus"], '
        '"likely_friction": ["Margin pressure"], '
        '"conversation_hooks": ["What changed last year?"], '
        '"lens_entry_point": "Theory of Constraints", '
        '"sources": ["https://acme.com/"], '
        '"research_confidence": "medium", '
        '"notes": null}'
    )
    with patch("skills.inbound_lead.researcher.run_research") as rr:
        rr.return_value = {"success": True, "answer": brief_json, "error": None, "tool_calls": 3, "turns": 4}
        result = research(
            name="Jane", email="jane@acme.com", company="Acme", raw_company_url=None,
        )
    assert result.research_confidence == "medium"
    assert result.what_they_do == "Boutique mid-market consulting."
    assert result.sources == ["https://acme.com/"]


def test_research_extracts_json_from_markdown_fence():
    """Claude often wraps JSON in ```json fences. Parse it anyway."""
    fenced = (
        "Here is the brief:\n\n"
        "```json\n"
        '{"company_domain": "acme.com", "what_they_do": "Consulting firm.", '
        '"industry_signals": [], "likely_friction": [], "conversation_hooks": [], '
        '"lens_entry_point": "Lean", "sources": [], "research_confidence": "low", '
        '"notes": null}\n'
        "```\n"
    )
    with patch("skills.inbound_lead.researcher.run_research") as rr:
        rr.return_value = {"success": True, "answer": fenced, "error": None, "tool_calls": 2, "turns": 3}
        result = research(
            name="Jane", email="jane@acme.com", company="Acme", raw_company_url=None,
        )
    assert result.research_confidence == "low"
    assert result.company_domain == "acme.com"


def test_research_degrades_on_unparseable_answer():
    """If the answer cannot be parsed as JSON, fall back to low-confidence brief."""
    with patch("skills.inbound_lead.researcher.run_research") as rr:
        rr.return_value = {"success": True, "answer": "I could not find much.", "error": None, "tool_calls": 1, "turns": 2}
        result = research(
            name="Jane", email="jane@acme.com", company="Acme", raw_company_url=None,
        )
    assert result.research_confidence in ("low", "none")
    assert result.company_domain == "acme.com"
