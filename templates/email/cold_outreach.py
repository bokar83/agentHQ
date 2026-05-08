"""
templates/email/cold_outreach.py
=================================
SINGLE SOURCE OF TRUTH for the cold outreach email.

TO UPDATE THE TEMPLATE: edit this file only.
  - Change BODY, SUBJECT, or SIGNATURE as needed.
  - Do NOT change the variable names -- everything imports by name.
  - Do NOT copy this text into any other file, crew, or agent prompt.

All tools call this file:
  from templates.email.cold_outreach import SUBJECT, BODY
"""

SUBJECT = "What your team is not telling you"

# Greeting is rendered conditionally based on first_name_confidence.
# Low confidence (no usable name) drops the greeting entirely. Cold-email
# best practice: a generic "Hi there," signals automation and depresses
# reply rates. See feedback_no_greeting_when_unknown.md for full rationale.
_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = """Most consultants will tell you the bottleneck is in your strategy.

Most of the time it is not. The biggest constraint I see in SMBs is that the founder cannot get straight answers from the people closest to them. Performance replaces truth. Loyalty replaces honesty. By the time the numbers tell the story, the team has been protecting the founder from it for six months.

I am Boubacar, founder of Catalyst Works. I spent 15 years inside leadership teams across three continents watching the same loop. I have been on both sides of it. The lesson cost me people I cared about.

One question before I ask for anything:

Is there a place in your operation where work slows down or disappears, and the people you trust most have not given you a clean explanation?

If yes, worth a reply.

Boubacar
catalystworks.consulting"""

# Legacy export for any caller still using the format-string path. The new
# build_body() callable is what sequence_engine prefers when present.
BODY = _GREETING_HIGH + _BODY_HOOK


def build_body(lead: dict) -> str:
    """Render CW T1 body with confidence-aware greeting.

    - first_name_confidence == "high": include "Hi {first_name},"
    - first_name_confidence == "low":  drop greeting entirely; open with hook
    """
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(
        first_name=lead.get("first_name", "there"),
    )
