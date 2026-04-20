"""Inbound lead researcher: delegates to orchestrator.research_engine.run_research.

Why this shape: research_engine already runs an Anthropic tool-use loop with
Firecrawl search and scrape. Duplicating that here would be MUDA. Instead we
ask research_engine for a ResearchBrief JSON via the system prompt, then parse
the answer. Fail-soft: every failure path returns a valid ResearchBrief with
research_confidence downgraded.
"""
from __future__ import annotations
import json
import logging
import re
from typing import Optional
from urllib.parse import urlparse

from pydantic import ValidationError
from skills.inbound_lead.schema import ResearchBrief
from orchestrator.research_engine import run_research

logger = logging.getLogger("agentsHQ.inbound_lead.researcher")

_FREE_PROVIDERS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "icloud.com", "proton.me", "protonmail.com", "aol.com",
}

_ALLOWED_LENSES = [
    "Theory of Constraints",
    "Jobs to Be Done",
    "Lean",
    "Behavioral Economics",
    "Systems Thinking",
    "Design Thinking",
    "Organizational Development",
    "AI Strategy",
]

_SYSTEM_PROMPT = (
    "You are agentsHQ's inbound lead researcher. Your job: research the prospect's "
    "company using web_search and web_scrape, then return a single strict JSON "
    "object matching this schema:\n\n"
    "{\n"
    '  "company_domain": string or null,\n'
    '  "what_they_do": string (one or two sentences),\n'
    '  "industry_signals": array of up to 5 short strings,\n'
    '  "likely_friction": array of up to 3 short strings,\n'
    '  "conversation_hooks": array of up to 3 short strings (real, specific),\n'
    '  "lens_entry_point": one of [Theory of Constraints, Jobs to Be Done, Lean, '
    "Behavioral Economics, Systems Thinking, Design Thinking, "
    "Organizational Development, AI Strategy],\n"
    '  "sources": array of URLs you actually read,\n'
    '  "research_confidence": one of [high, medium, low, none],\n'
    '  "notes": string or null\n'
    "}\n\n"
    "Rules:\n"
    "- Return ONLY the JSON object, nothing else. No markdown fences, no prose.\n"
    "- Use plain English in every field. Do NOT mention framework names anywhere "
    "except in lens_entry_point.\n"
    "- If the company has no discoverable web presence, set research_confidence to "
    '"none" and explain in notes.\n'
    "- Never fabricate. If you cannot verify a claim, do not include it.\n"
    "- conversation_hooks must be specific and real, not generic openers."
)


def _strip_www_and_subdomains(host: str) -> str:
    host = host.lower().lstrip(".")
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    if len(parts) > 2:
        return ".".join(parts[-2:])
    return host


def _resolve_domain(email: str, raw_company_url: Optional[str]) -> Optional[str]:
    """Derive a company domain from the explicit URL or the email host."""
    if raw_company_url:
        host = urlparse(raw_company_url).hostname or ""
        return _strip_www_and_subdomains(host) or None
    host = email.split("@", 1)[1].lower() if "@" in email else ""
    if host in _FREE_PROVIDERS:
        return None
    return _strip_www_and_subdomains(host) or None


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _extract_json_object(text: str) -> Optional[dict]:
    """Pull the first JSON object out of a possibly-noisy answer."""
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    match = _JSON_FENCE_RE.search(text)
    if match:
        try:
            return json.loads(match.group(1))
        except (json.JSONDecodeError, ValueError):
            pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except (json.JSONDecodeError, ValueError):
            return None
    return None


def _minimal_brief(
    domain: Optional[str],
    company: Optional[str],
    note: str,
) -> ResearchBrief:
    return ResearchBrief(
        company_domain=domain,
        what_they_do=company or (f"Company at {domain}." if domain else "Unknown company."),
        industry_signals=[],
        likely_friction=[],
        conversation_hooks=[],
        lens_entry_point="AI Strategy",
        sources=[],
        research_confidence="none",
        notes=note,
    )


def _low_confidence_brief(
    domain: Optional[str],
    company: Optional[str],
    note: str,
) -> ResearchBrief:
    return ResearchBrief(
        company_domain=domain,
        what_they_do=company or (f"Company at {domain}." if domain else "Unknown company."),
        industry_signals=[],
        likely_friction=[],
        conversation_hooks=[],
        lens_entry_point="AI Strategy",
        sources=[],
        research_confidence="low",
        notes=note,
    )


def research(
    name: str,
    email: str,
    company: Optional[str],
    raw_company_url: Optional[str],
) -> ResearchBrief:
    """Entry point. Returns a ResearchBrief. Never raises: degrades to confidence=none or low."""
    domain = _resolve_domain(email, raw_company_url)
    if domain is None:
        return _minimal_brief(
            None, company,
            "Could not resolve company domain (free email provider and no company URL).",
        )

    user_prompt = (
        f"Prospect: {name} <{email}>\n"
        f"Company (claimed): {company or 'unknown'}\n"
        f"Company domain: {domain}\n"
        f"Company URL: {raw_company_url or f'https://{domain}'}\n\n"
        "Research this company and produce the JSON brief per the system prompt."
    )

    try:
        result = run_research(user_prompt=user_prompt, system_prompt=_SYSTEM_PROMPT)
    except Exception as exc:
        logger.warning(f"run_research raised for {domain}: {exc}")
        return _minimal_brief(domain, company, f"Research engine raised: {exc}")

    if not result.get("success"):
        return _minimal_brief(
            domain, company,
            f"Research engine reported failure: {result.get('error') or 'unknown'}",
        )

    answer = result.get("answer", "")
    parsed = _extract_json_object(answer)
    if parsed is None:
        return _low_confidence_brief(
            domain, company,
            "Research ran but returned unparseable output. Review the Gmail draft context before sending.",
        )

    if parsed.get("lens_entry_point") not in _ALLOWED_LENSES:
        parsed["lens_entry_point"] = "AI Strategy"

    try:
        return ResearchBrief(**parsed)
    except ValidationError as exc:
        logger.warning(f"ResearchBrief validation failed for {domain}: {exc}")
        return _low_confidence_brief(
            domain, company,
            f"Research answer failed schema validation: {exc.errors()[:1]}",
        )
