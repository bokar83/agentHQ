"""
templates/email/studio_t2.py
============================
Studio web presence outreach -- Touch 2 (Day 5).
Value-add: free website audit offer. No pitch.
SINGLE SOURCE OF TRUTH. Edit this file only.
"""

SUBJECT = "Free audit: what your website is missing"

_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = """Followed up last week. No worries if the timing wasn't right.

Different angle today: I'll audit your current web presence for free and tell you exactly what's keeping you out of AI search results. Takes me 10 minutes. Costs you nothing.

What I look at:
- Whether your site loads in under 2 seconds (most don't)
- Whether Google and AI tools can actually index your content
- Whether your business shows up when someone asks ChatGPT to recommend a service like yours in your city
- Whether your contact/booking flow is losing you leads

Most business owners I talk to are surprised by what I find. The problems are almost always fixable — and usually faster than expected.

Want me to run it? Just reply with your website URL (or let me know if you don't have one — that's useful information too).

Boubacar
catalystworks.consulting

Reply STOP to opt out"""

BODY = _GREETING_HIGH + _BODY_HOOK


def build_body(lead: dict) -> str:
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(
        first_name=lead.get("first_name", "there"),
    )
