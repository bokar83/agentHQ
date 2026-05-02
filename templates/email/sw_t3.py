"""
templates/email/sw_t3.py
========================
Signal Works cold outreach -- Touch 3 (Day 7).
SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.sw_t3 import SUBJECT, build_body
"""

SUBJECT = "What the AI said about a local competitor"

# Greeting rendered conditionally based on first_name_confidence.
# Low confidence drops the greeting entirely. See feedback_no_greeting_when_unknown.md.
_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = """We ran the test for a {niche} nearby. ChatGPT was recommending their competitor on most queries.

A few weeks after we built their AI presence, that flipped.

Happy to run the same test for your business. Free, no commitment.

Boubacar
geolisted.co

Reply STOP to opt out"""

# Legacy export for any caller still using the format-string path.
BODY = _GREETING_HIGH + _BODY_HOOK


def build_body(lead: dict) -> str:
    """Render SW T3 body with confidence-aware greeting."""
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(
        first_name=lead.get("first_name", "there"),
        niche=lead.get("niche", "small business"),
    )
