"""
templates/email/constraints_ai_t1.py
====================================
Constraints AI capture follow-up, Touch 1 (Day 0, sent within minutes of submit).

SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.constraints_ai_t1 import SUBJECT, build_body

Audience: a visitor who ran the Constraints AI demo on catalystworks.consulting,
read the diagnosis, then handed over their email to receive it.

Lead dict keys expected:
  - email                     (str, required)
  - first_name                (str, optional — most captures will be email-only)
  - first_name_confidence     ("high" | "low")
  - pain_text                 (str, what they typed into the demo)
  - response_constraint       (str, the named constraint the diagnostic returned)
  - response_action           (str, the one-action recommendation)

The send is a transactional value-delivery, not a sales pitch. It re-states the
diagnosis in writing (so they have it in their inbox to forward / re-read), then
adds one piece of context the demo could not give: what the gap is between the
30-second protocol and the 90-minute Signal Session.
"""

SUBJECT = "Your constraint, in writing"

_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = """You typed something specific into the demo. The protocol returned a named constraint. Now you have it in writing.

What you typed:
{pain_text}

What the protocol named:
{response_constraint}

The action it suggested before Friday:
{response_action}

That is the 30-second version. It is real, it is structured, and it is what the protocol thinks based on one sentence of input.

The 90-minute version is different in three ways. We trace the constraint across all five lenses, not one. We hear the texture of how it shows up in your operation, in your words. And the deliverable is a one-page written diagnosis you keep, not a paragraph in a browser.

The price is $497. Limited to three sessions a month so the work stays sharp.

If the demo named something that feels right, the next step is to book the session: {calendly_url}

If it named something that feels close but not quite, hit reply with what is off. I read every one of these.

Boubacar
catalystworks.consulting"""

# Legacy export.
BODY = _GREETING_HIGH + _BODY_HOOK


def build_body(lead: dict) -> str:
    """Render T1 body with confidence-aware greeting and capture-specific fields.

    - first_name_confidence == "high": include "Hi {first_name},"
    - first_name_confidence == "low" (default for email-only captures): drop greeting
    """
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(
        first_name=lead.get("first_name", "there"),
        pain_text=(lead.get("pain_text") or "").strip()[:600],
        response_constraint=(lead.get("response_constraint") or "").strip()[:400],
        response_action=(lead.get("response_action") or "").strip()[:400],
        calendly_url=lead.get(
            "calendly_url",
            "https://calendly.com/boubacarbarry/signal-session-ai-data-exposure-audit",
        ),
    )
