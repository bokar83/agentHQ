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

SUBJECT = "Where is your margin actually going?"

# Greeting is rendered conditionally based on first_name_confidence.
# Low confidence (no usable name) drops the greeting entirely. Cold-email
# best practice: a generic "Hi there," signals automation and depresses
# reply rates. See feedback_no_greeting_when_unknown.md for full rationale.
_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = """Most businesses aren't losing margin to bad strategy. They're losing it to one bottleneck: a handoff, an approval loop, a pricing gap quietly taxing everything downstream.

The frustrating part: it's almost always findable. And almost always fixable faster than people expect.

I'm Boubacar Barry, founder of Catalyst Works. I spent 15 years working with leadership teams across three continents watching the same pattern repeat: the thing slowing the business down is rarely what anyone is looking at.

What I do differently: I don't hand you a report. I find the constraint and build a clear, executable path to removing it. One that the people running the business can actually use without me in the room.

One question before I ask for anything:

Is there a place in your operation right now where work slows down or disappears that you haven't been able to fully fix?

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
