"""Email drafter with post-draft linter. Regenerates once on lint failure.

The generator uses the Anthropic SDK directly (same pattern as
orchestrator.research_engine) with a strict JSON system prompt. The lint
step enforces voice guardrails that the model sometimes ignores: blocked
framework names, blocked sales phrases, em dashes, double hyphens, length
caps. If the second draft still fails, we ship partial so the Gmail draft
exists for Boubacar to edit by hand.
"""
from __future__ import annotations
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

from skills.inbound_lead.schema import DraftedEmail, ResearchBrief

logger = logging.getLogger("agentsHQ.inbound_lead.drafter")

MODEL = "anthropic/claude-sonnet-4.6"

BLOCKED_FRAMEWORKS = [
    "theory of constraints", "toc",
    "jobs to be done", "jtbd",
    "lean", "lean methodology",
    "behavioral economics",
    "systems thinking",
    "design thinking",
    "organizational development", "od framework",
    "constraints theory",
]

BLOCKED_SALES_PHRASES = [
    "circle back", "touch base", "just wanted to", "reach out",
    "synergy", "leverage your", "unlock", "transform your business",
    "game-changer", "game changer", "thought leadership",
]


@dataclass
class DraftResult:
    email: DraftedEmail
    status: Literal["clean", "partial"]
    lint_errors: list[str]


def _word_boundary_contains(text: str, term: str) -> bool:
    """Return True if `term` appears in `text` surrounded by non-alnum boundaries.

    Multi-word terms: each word separated by \\s+ in the pattern. Prevents
    'clean' from matching 'lean'.
    """
    parts = [re.escape(p) for p in term.split()]
    pattern = r"(?<![A-Za-z0-9])" + r"\s+".join(parts) + r"(?![A-Za-z0-9])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def lint_draft(email: DraftedEmail) -> tuple[bool, list[str]]:
    """Return (ok, errors). Errors are short codes, not user-facing."""
    errors: list[str] = []
    body = email.body_markdown

    for term in BLOCKED_FRAMEWORKS:
        if _word_boundary_contains(body, term):
            errors.append(f"framework_name:{term}")

    if "\u2014" in body or "\u2013" in body or "--" in body:
        errors.append("em_dash")

    for phrase in BLOCKED_SALES_PHRASES:
        if _word_boundary_contains(body, phrase):
            errors.append(f"sales_phrase:{phrase}")

    word_count = len(body.split())
    if word_count > 150:
        errors.append("too_long")

    if len(email.subject) > 60:
        errors.append("subject_too_long")

    return (len(errors) == 0, errors)


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _extract_json_object(text: str) -> Optional[dict]:
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


def _build_drafter_prompt(
    name: str,
    brief: ResearchBrief,
    meeting_time: Optional[datetime],
    correction_hint: Optional[str],
) -> str:
    frictions = "\n".join(f"- {f}" for f in brief.likely_friction) or "- (none identified)"
    hooks = "\n".join(f"- {h}" for h in brief.conversation_hooks) or "- (none)"
    correction = (
        f"\n\nFIX THESE LINT ISSUES FROM THE PREVIOUS DRAFT: {correction_hint}"
        if correction_hint else ""
    )
    meeting_line = f"They booked for {meeting_time.isoformat()}." if meeting_time else ""
    return (
        f"You are Boubacar Barry writing a short welcome email to {name}, who just booked a discovery call.\n"
        f"{meeting_line}\n\n"
        "Research brief:\n"
        f"- What they do: {brief.what_they_do}\n"
        "- Likely friction:\n"
        f"{frictions}\n"
        "- Conversation hooks:\n"
        f"{hooks}\n\n"
        "Voice: an analyst who happened to see their submission and did some quick homework. "
        "Calm, curious, direct. Not a sales bot.\n\n"
        "Constraints:\n"
        "- Body: 80 to 150 words max\n"
        "- Subject: 60 chars max\n"
        "- No framework names (no Theory of Constraints, Jobs to Be Done, Lean, etc.)\n"
        "- No em dashes (U+2014) or double hyphens\n"
        "- No sales phrases: circle back, touch base, just wanted to, reach out, synergy, "
        "leverage, unlock, transform, game-changer, thought leadership\n"
        "- Do not mention you researched them\n"
        "- No calendar links or attachments\n"
        "- End with ONE specific question tied to one friction hypothesis\n\n"
        "Structure:\n"
        "1. One line acknowledging the booking (not a generic thanks).\n"
        "2. One line showing you understand their context (phrased as knowledge, not research).\n"
        "3. One line naming a friction worth exploring on the call (plain English, no framework names).\n"
        "4. One specific question.\n\n"
        "Return ONLY a JSON object with fields: subject, body_markdown, tone_note. "
        f"No markdown fences, no prose outside the JSON.{correction}"
    )


def _generate_draft(
    name: str,
    brief: ResearchBrief,
    meeting_time: Optional[datetime],
    correction_hint: Optional[str] = None,
) -> DraftedEmail:
    """Call Anthropic directly. Isolated so tests can mock it."""
    import anthropic

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set; cannot draft email.")

    client = anthropic.Anthropic(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "https://agentshq.io"},
    )
    prompt = _build_drafter_prompt(name, brief, meeting_time, correction_hint)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(
        getattr(block, "text", "")
        for block in response.content
        if getattr(block, "type", "") == "text"
    ).strip()

    parsed = _extract_json_object(text)
    if not parsed:
        raise ValueError(f"Drafter LLM returned unparseable JSON: {text[:200]}")
    return DraftedEmail(**parsed)


def draft_email(
    name: str,
    brief: ResearchBrief,
    meeting_time: Optional[datetime],
) -> DraftResult:
    """Generate an email. If lint fails, regenerate once. Then ship clean or partial."""
    first = _generate_draft(name, brief, meeting_time)
    ok, errors = lint_draft(first)
    if ok:
        return DraftResult(email=first, status="clean", lint_errors=[])

    logger.info(f"First draft lint failed: {errors}. Regenerating.")
    hint = "; ".join(errors)
    second = _generate_draft(name, brief, meeting_time, correction_hint=hint)
    ok2, errors2 = lint_draft(second)
    if ok2:
        return DraftResult(email=second, status="clean", lint_errors=[])

    logger.warning(f"Second draft still dirty: {errors2}. Shipping partial.")
    return DraftResult(email=second, status="partial", lint_errors=errors2)
