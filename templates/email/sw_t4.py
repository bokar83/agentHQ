"""
templates/email/sw_t4.py
========================
Signal Works cold outreach -- Touch 4 (Day 12). Breakup email.
SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.sw_t4 import SUBJECT, build_body
"""

SUBJECT = "Closing your file"

# Greeting rendered conditionally based on first_name_confidence.
# Low confidence drops the greeting entirely. See feedback_no_greeting_when_unknown.md.
_GREETING_HIGH = "Hi {first_name},\n\n"

CALENDLY = "https://calendly.com/boubacarbarry/signal-works-discovery-call"

_BODY_HOOK = """I will not follow up after this.

If AI visibility is not a priority right now, completely understood. The timing has to be right.

If it ever becomes relevant, the offer stands: free 15-minute walkthrough, your business, your city, your category.

{calendly}

Boubacar
geolisted.co

Reply STOP to opt out"""

# Legacy export for any caller still using the format-string path.
BODY = _GREETING_HIGH + _BODY_HOOK


def build_body(lead: dict) -> str:
    """Render SW T4 body with confidence-aware greeting."""
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(
        first_name=lead.get("first_name", "there"),
        calendly=CALENDLY,
    )
