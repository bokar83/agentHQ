"""
templates/email/studio_t4.py
============================
Studio web presence outreach -- Touch 4 (Day 18).
Break-up email + referral ask.
SINGLE SOURCE OF TRUTH. Edit this file only.
"""

SUBJECT = "Closing the loop"

_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = """Last email from me on this thread.

If the timing isn't right or this isn't a priority, no hard feelings. I'll stop reaching out.

One last ask: if you know someone who's been meaning to get their business online or fix a website that's not pulling its weight, I'd be grateful for the introduction. I make the process easy and fast, and I don't waste people's time.

If your situation changes, my calendar is always open: https://calendly.com/boubacarbarry/signal-works-discovery-call

Thanks for your time.

Boubacar
geolisted.co

Reply STOP to opt out"""

BODY = _GREETING_HIGH + _BODY_HOOK


def build_body(lead: dict) -> str:
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(
        first_name=lead.get("first_name", "there"),
    )
