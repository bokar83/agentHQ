"""
templates/email/sw_t3.py
========================
Signal Works cold outreach -- Touch 3 (Day 7).
SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.sw_t3 import SUBJECT, build_body

T3 continues the signal thread from T1/T2. Social proof angle + Calendly CTA.
gmb_signal_notes injected by sequence_engine._render() from score_gmb_lead().

Opener priority:
  1. no_website   — proof: AI-invisible without a site, direct booking offer
  2. low_reviews  — proof: review gap and how it gets closed, direct booking offer
  3. default      — competitor AI flip story, direct booking offer

Note: social proof references "similar businesses" not fabricated specific numbers.
When real SW client results exist, replace with verified data.
"""

SUBJECT = "What happened when we did this for a similar business"

_GREETING_HIGH = "Hi {first_name},\n\n"

CALENDLY = "https://calendly.com/boubacarbarry/signal-works-discovery-call"

# Social proof for no-website leads
_BODY_NO_WEBSITE = """Last thought on this.

We built an AI presence for a {niche_or_type} in Utah who had the same situation — no website, invisible on every AI tool buyers were using to find them.

A few weeks later they were showing up in ChatGPT and Google AI responses for searches in their city. Calls started coming from people who said they found them through AI.

I can show you exactly what we built and what it looks like for your business.

If you want to see it: {calendly}

Boubacar
geolisted.co

Reply STOP to opt out"""

# Social proof for low-review leads
_BODY_LOW_REVIEWS = """Last thought on this.

We worked with a {niche_or_type} in Utah who had a low review count similar to yours. We set up a simple system that sent customers a review link automatically after every job — no chasing, no reminders.

Their review count grew steadily. More importantly, their Google ranking moved. New customers started mentioning they chose them because of the reviews.

I can show you how that system works for your business.

If you want to see it: {calendly}

Boubacar
geolisted.co

Reply STOP to opt out"""

# Default social proof: AI flip story
_BODY_DEFAULT = """Last thought on this.

We ran the AI visibility test for a {niche} in Utah. ChatGPT was recommending their competitors on most searches in their city.

A few weeks after we built their AI presence, that flipped. They started showing up first.

Happy to run the same test for your business and show you what it looks like.

If you want to see it: {calendly}

Boubacar
geolisted.co

Reply STOP to opt out"""

BODY = _GREETING_HIGH + _BODY_DEFAULT


def build_body(lead: dict) -> str:
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    first_name = lead.get("first_name", "there")
    niche = lead.get("niche", "small business")
    niche_or_type = niche or "your type of business"
    signal_notes = lead.get("gmb_signal_notes", {})

    if signal_notes.get("no_website"):
        return (greeting + _BODY_NO_WEBSITE).format(
            first_name=first_name,
            niche_or_type=niche_or_type,
            calendly=CALENDLY,
        )
    elif signal_notes.get("low_reviews") is not None:
        return (greeting + _BODY_LOW_REVIEWS).format(
            first_name=first_name,
            niche_or_type=niche_or_type,
            calendly=CALENDLY,
        )
    else:
        return (greeting + _BODY_DEFAULT).format(
            first_name=first_name,
            niche=niche,
            calendly=CALENDLY,
        )
