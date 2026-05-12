"""
templates/email/constraints_ai_t2.py
====================================
Constraints AI capture follow-up, Touch 2 (Day 2).

SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.constraints_ai_t2 import SUBJECT, build_body

Job: add one piece of context the demo and T1 could not give. The visitor saw
the protocol name a constraint. T1 delivered the artifact. T2 shows what happens
when the same lens-stack hits a real engagement — a short case beat. Not a
client name, not a logo, just the texture of one named constraint and what the
operator did about it.

Lead dict keys expected:
  - email, first_name, first_name_confidence
  - pain_text
  - response_constraint
"""

SUBJECT = "What this looks like when it goes deeper"

_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = """A founder I worked with last quarter ran the same protocol you did. The constraint the diagnostic named for them was: "operations sees real-time margin, finance sees it 30 days later, decisions get made on stale numbers."

That sentence is small. What it cost them was not.

They had been hiring for the wrong role for four months. They thought they needed a controller. The real gap was a daily margin readout that two existing people could have assembled in a week if anyone had named the bottleneck out loud. The protocol named it. The 90 minutes built the readout. The hire never happened.

Most consulting engagements ship a deck and a recommendation. This one shipped a sentence and a meeting on a Tuesday. The deliverable was the deliverable.

Your constraint was: {response_constraint}

If that sentence is doing work in your head right now — turning over, finding edges, surfacing things you have not said out loud — that is the signal. The 90 minutes turns that into a written page you keep.

If it is doing nothing, that is also a signal. Hit reply and tell me what is off about it. I read every one.

Book the session: {calendly_url}

Boubacar
catalystworks.consulting"""

BODY = _GREETING_HIGH + _BODY_HOOK


def build_body(lead: dict) -> str:
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(
        first_name=lead.get("first_name", "there"),
        response_constraint=(lead.get("response_constraint") or "the one named in your diagnosis").strip()[:400],
        calendly_url=lead.get(
            "calendly_url",
            "https://calendly.com/boubacarbarry/signal-session-ai-data-exposure-audit",
        ),
    )
