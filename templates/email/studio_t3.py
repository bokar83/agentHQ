"""
templates/email/studio_t3.py
============================
Studio web presence outreach -- Touch 3 (Day 11).
Social proof + urgency. Short.
SINGLE SOURCE OF TRUTH. Edit this file only.
"""

SUBJECT = "What a $1,500 website actually gets you"

_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = """Reached out a couple times. Last one, I promise.

I'll be direct: most of the business owners I work with waited too long to fix their web presence. They watched competitors who got online first take market share that's now very hard to reclaim — especially with AI search changing how people discover local businesses.

What $1,500 buys you with me:
- A fast, modern, mobile-first website
- Built for AI search (GEO-ready, structured data, proper indexing)
- Live in 2 weeks
- Includes 30 days of support post-launch
- Ongoing maintenance from $500/month if you want it

No agency overhead. No upsell. Just a site that works.

If now isn't the right time, I get it. But if you're thinking about it, I'd rather you work with someone who'll actually move fast than see you wait another year.

Book a free 15-minute call: https://calendly.com/catalystworks

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
