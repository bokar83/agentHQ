"""
templates/email/cw_t2.py
========================
Catalyst Works cold outreach -- Touch 2 (Day 6).
SaaS Audit PDF value-add. No pitch, no ask beyond the doc.
SINGLE SOURCE OF TRUTH. Edit this file only.

PDF Drive link: https://drive.google.com/file/d/1GQ3rCelBy83YaPf0AYVuaWf5LAE5k4O4/view?usp=drivesdk

Import:
  from templates.email.cw_t2 import SUBJECT, build_body
"""

SUBJECT = "Something I thought you'd want to see"

# Greeting rendered conditionally based on first_name_confidence.
# Low confidence drops the greeting entirely. See feedback_no_greeting_when_unknown.md.
_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = """Sent you a note last week about AI strategy. No worries if the timing was off.

Separate thing -- I put together a one-page breakdown of the five SaaS tools most professional services firms are overpaying for right now, and what replaces each one. The average bleed is $9,660/year. Most of it is fixable.

Your SaaS Stack Is Working Against You: https://drive.google.com/file/d/1GQ3rCelBy83YaPf0AYVuaWf5LAE5k4O4/view?usp=drivesdk

If you want me to run the same audit on your actual stack, it's $500 flat. Delivered in 5 business days. No retainer.

Either way, the doc is yours.

Boubacar
catalystworks.consulting

Reply STOP to opt out"""

# Legacy export for any caller still using the format-string path.
BODY = _GREETING_HIGH + _BODY_HOOK


def build_body(lead: dict) -> str:
    """Render CW T2 body with confidence-aware greeting.

    - first_name_confidence == "high": include "Hi {first_name},"
    - first_name_confidence == "low":  drop greeting entirely
    """
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(
        first_name=lead.get("first_name", "there"),
    )
