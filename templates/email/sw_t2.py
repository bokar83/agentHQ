"""
templates/email/sw_t2.py
========================
Signal Works cold outreach -- Touch 2 (Day 3).
SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.sw_t2 import SUBJECT, build_body
"""

SUBJECT = "One business per city gets this"

# Greeting rendered conditionally based on first_name_confidence.
# Low confidence drops the greeting entirely. See feedback_no_greeting_when_unknown.md.
_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = """Quick follow-up.

We only build one AI presence per service category per city. Once a {niche} in {city} claims that position, it is theirs.

Still interested in the free demo?

Boubacar
geolisted.co

Reply STOP to opt out"""

# Legacy export for any caller still using the format-string path.
BODY = _GREETING_HIGH + _BODY_HOOK


def build_body(lead: dict) -> str:
    """Render SW T2 body with confidence-aware greeting."""
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(
        first_name=lead.get("first_name", "there"),
        niche=lead.get("niche", "small business"),
        city=lead.get("city", "your area"),
    )
