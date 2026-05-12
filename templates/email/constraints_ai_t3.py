"""
templates/email/constraints_ai_t3.py
====================================
Constraints AI capture follow-up, Touch 3 (Day 4, breakup).

SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.constraints_ai_t3 import SUBJECT, build_body

Job: low-friction CTA that respects their time. The two prior touches delivered
the artifact (T1) and the texture (T2). T3 collapses the ask to a single line
and gives them a clean exit. No guilt, no scarcity theatre, no "last chance."
The Signal Session is genuinely capped at 3/month so the limit is real, but the
T3 frame is: you have what you came for, here is the door.
"""

SUBJECT = "Three ways to use what you got"

_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = """You ran the diagnostic. You have a sentence. Three things you can do with it:

1. Read it to the person closest to the operation. If they push back, the constraint is real. If they nod and change the subject, the constraint is real and protected.

2. Write it on a sticky note on your monitor for two weeks. Notice every decision that touches it. That is your audit.

3. Book the 90 minutes and walk out with a one-page written diagnosis: {calendly_url}

If none of those, no follow-up from me. You took the protocol for a spin, you have the output, the door is open whenever the timing fits.

If something in the diagnosis felt off or incomplete, reply to this email with one sentence about what is missing. I read every one and it sharpens the protocol.

Boubacar
catalystworks.consulting

P.S. Reply with "remove" if you would prefer no further follow-up. Done in one click."""

BODY = _GREETING_HIGH + _BODY_HOOK


def build_body(lead: dict) -> str:
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(
        first_name=lead.get("first_name", "there"),
        calendly_url=lead.get(
            "calendly_url",
            "https://calendly.com/boubacarbarry/signal-session-ai-data-exposure-audit",
        ),
    )
