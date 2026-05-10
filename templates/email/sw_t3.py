"""
templates/email/sw_t3.py
========================
Signal Works cold outreach -- Touch 3 (Day 7).
SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.sw_t3 import SUBJECT, build_body

T3 continues the signal thread from T1/T2. Social proof angle.
gmb_signal_notes injected by sequence_engine._render() from score_gmb_lead().

Opener priority:
  1. no_website   — proof: client with no website, now getting AI-driven calls
  2. low_reviews  — proof: client with low reviews, now ranked higher
  3. default      — proof: competitor in their category flipped via AI presence
"""

SUBJECT = "What happened when we did this for a similar business"

_GREETING_HIGH = "Hi {first_name},\n\n"

# Social proof for no-website leads
_BODY_NO_WEBSITE = """Last thought on this.

We recently built an AI presence for a {niche_or_type} in {city} who had the same situation — no website, invisible on every AI tool.

Eight weeks later they were showing up in ChatGPT and Google AI responses for their top searches. They told us three of their last five new clients found them through AI, not Google.

I can show you exactly what we built and what it looks like for your business. Free, no commitment.

Worth 15 minutes?

Boubacar
geolisted.co

Reply STOP to opt out"""

# Social proof for low-review leads
_BODY_LOW_REVIEWS = """Last thought on this.

We worked with a {niche_or_type} in {city} who had a similar review count. We set up a simple system that automatically sent customers a review link after every job.

In 60 days they went from 12 reviews to 47. Their Google ranking moved from page 2 to the local pack.

Happy to show you how that system works for your business. Free, no commitment.

Worth 15 minutes?

Boubacar
geolisted.co

Reply STOP to opt out"""

# Default social proof: AI flip story
_BODY_DEFAULT = """Last thought on this.

We ran the test for a {niche} nearby. ChatGPT was recommending their competitor on most queries.

A few weeks after we built their AI presence, that flipped.

Happy to run the same test for your business. Free, no commitment.

Worth 15 minutes?

Boubacar
geolisted.co

Reply STOP to opt out"""

BODY = _GREETING_HIGH + _BODY_DEFAULT


def build_body(lead: dict) -> str:
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    first_name = lead.get("first_name", "there")
    niche = lead.get("niche", "small business")
    city = lead.get("city", "your area")
    niche_or_type = niche or "your type of business"
    signal_notes = lead.get("gmb_signal_notes", {})

    if signal_notes.get("no_website"):
        return (greeting + _BODY_NO_WEBSITE).format(
            first_name=first_name,
            niche_or_type=niche_or_type,
            city=city,
        )
    elif signal_notes.get("low_reviews") is not None:
        return (greeting + _BODY_LOW_REVIEWS).format(
            first_name=first_name,
            niche_or_type=niche_or_type,
            city=city,
        )
    else:
        return (greeting + _BODY_DEFAULT).format(
            first_name=first_name,
            niche=niche,
        )
