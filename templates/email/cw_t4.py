"""
templates/email/cw_t4.py
========================
Catalyst Works cold outreach -- Touch 4 (Day 14).
Pattern recognition / social proof angle.
SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.cw_t4 import SUBJECT, build_body
"""

SUBJECT = "What I find in most businesses"

# Greeting rendered conditionally based on first_name_confidence.
# Low confidence drops the greeting entirely. See feedback_no_greeting_when_unknown.md.
_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = """Most businesses I work with have the same pattern: one decision point, one approval loop, or one pricing gap that quietly costs more than anyone realizes.

It's rarely where people are looking.

If that sounds familiar, I'm happy to run the diagnostic. You leave with a specific answer and a 90-day plan.

Worth 20 minutes to find out?

Boubacar
catalystworks.consulting

Reply STOP to opt out"""

# Legacy export for any caller still using the format-string path.
BODY = _GREETING_HIGH + _BODY_HOOK


def build_body(lead: dict) -> str:
    """Render CW T4 body with confidence-aware greeting."""
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(
        first_name=lead.get("first_name", "there"),
    )
