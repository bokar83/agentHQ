"""
templates/email/cw_t5.py
========================
Catalyst Works cold outreach -- Touch 5 (Day 19). Breakup email.
SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.cw_t5 import SUBJECT, build_body
"""

SUBJECT = "Last note from me"

# Greeting rendered conditionally based on first_name_confidence.
# Low confidence drops the greeting entirely. See feedback_no_greeting_when_unknown.md.
_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = """I won't follow up after this.

If the timing isn't right, completely understood.

If it ever is, the diagnostic is still available: 90 minutes, one named constraint, one clear path forward. The SaaS audit is $500 flat if that's the more useful starting point.

Boubacar
catalystworks.consulting

Reply STOP to opt out"""

# Legacy export for any caller still using the format-string path.
BODY = _GREETING_HIGH + _BODY_HOOK


def build_body(lead: dict) -> str:
    """Render CW T5 body with confidence-aware greeting."""
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(
        first_name=lead.get("first_name", "there"),
    )
