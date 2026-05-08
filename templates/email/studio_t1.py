"""
templates/email/studio_t1.py
============================
Studio web presence outreach -- Touch 1 (Day 0).
Subject is niche-aware: trades get visibility framing, professionals get AI angle.
SINGLE SOURCE OF TRUTH. Edit this file only.
"""

_TRADES = {
    "roofing", "roofer", "plumbing", "plumber", "hvac", "electrician", "electrical",
    "contractor", "construction", "landscaping", "landscaper", "painter", "painting",
    "pest control", "cleaning", "barber", "salon", "auto", "mechanic", "storage",
    "moving", "catering", "baker", "chef",
}

def _subject(lead: dict) -> str:
    """Return a niche-aware subject line."""
    industry = (lead.get("industry") or lead.get("niche") or "").lower()
    if any(t in industry for t in _TRADES):
        name = lead.get("company") or lead.get("business_name") or ""
        if name:
            return f"Can customers find {name} online?"
        return "Can customers find your business online?"
    return "Your customers are searching AI now, not Google"

SUBJECT = "Your customers are searching AI now, not Google"  # static fallback

_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = """Quick question: when someone types your business name into ChatGPT or Google's AI overview, what shows up?

If your website is outdated, slow, or just a social media profile -- the answer is: nothing useful. And that's a real problem now, because AI-powered search is how people find local businesses in 2025.

I'm Boubacar Barry. I build fast, modern websites and AI-ready web presences for business owners who are ready to stop being invisible online.

What I do isn't complicated: I take your story, your services, and your reputation -- and I build a site that actually works in today's search landscape. Most projects are live in 2 weeks. Pricing starts at $1,500.

One question: is your current web presence getting you leads, or just sitting there?

If it's the second one, worth a 15-minute conversation.

Boubacar
catalystworks.consulting

P.S. Even if you're not ready now, happy to give you a free audit of what your site is missing. No strings.

Reply STOP to opt out"""

BODY = _GREETING_HIGH + _BODY_HOOK


def build_body(lead: dict) -> str:
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(
        first_name=lead.get("first_name", "there"),
    )
