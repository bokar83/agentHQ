"""
templates/email/cw_t3.py
========================
Catalyst Works cold outreach -- Touch 3 (Day 9).
Friction/bottleneck angle. Short bump after PDF.
SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.cw_t3 import SUBJECT, build_body
"""

SUBJECT = "The thing slowing your business down"

# Greeting rendered conditionally based on first_name_confidence.
# Low confidence drops the greeting entirely. See feedback_no_greeting_when_unknown.md.
_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = """Most owners I talk to already know where the friction is. They just haven't had time to name it precisely or build a path around it.

That's the 90 minutes. Nothing more.

Still worth it?

Boubacar
catalystworks.consulting

Reply STOP to opt out"""

# Legacy export for any caller still using the format-string path.
BODY = _GREETING_HIGH + _BODY_HOOK


def build_body(lead: dict) -> str:
    """Render CW T3 body with confidence-aware greeting."""
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(
        first_name=lead.get("first_name", "there"),
    )
