"""
templates/email/sw_t2.py
========================
Signal Works cold outreach -- Touch 2 (Day 3).
SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.sw_t2 import SUBJECT, build_body

T2 continues the same signal thread as T1 — never resets to a generic hook.
gmb_signal_notes injected by sequence_engine._render() from score_gmb_lead().

Opener priority (mirrors T1, escalates the same gap):
  1. no_website   — "still no website" angle, scarcity close
  2. low_reviews  — "still {N} reviews" angle, scarcity close
  3. default      — "one business per city" scarcity close (original)
"""

SUBJECT = "One business per city gets this"

_GREETING_HIGH = "Hi {first_name},\n\n"

# Escalates no_website thread: they already know the gap, scarcity closes
_BODY_NO_WEBSITE = """Quick follow-up on {business_name}.

Still no website on your Google listing — which means ChatGPT, Gemini, and Google AI are pointing buyers in {city} to whoever has one.

We build one AI presence per {niche_or_type} per city. Once it is claimed, it is claimed.

Still interested in seeing what that looks like for your business?

Boubacar
geolisted.co

Reply STOP to opt out"""

# Escalates low_reviews thread: same number, scarcity close
_BODY_LOW_REVIEWS = """Quick follow-up.

The {review_count} review{review_plural} situation is still the same — and the top-ranked {niche_or_type} in {city} is not slowing down.

We build one AI presence per category per city. Happy to show you exactly how the review gap is affecting your search placement before you decide anything.

Still interested?

Boubacar
geolisted.co

Reply STOP to opt out"""

# Default: scarcity close, no specific signal
_BODY_DEFAULT = """Quick follow-up.

We only build one AI presence per service category per city. Once a {niche} in {city} claims that position, it is theirs.

Still interested in the free demo?

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
    business_name = lead.get("business_name") or lead.get("company", "your business")
    niche_or_type = niche or "your type of business"
    signal_notes = lead.get("gmb_signal_notes", {})
    review_count = int(lead.get("review_count", 0) or 0)

    if signal_notes.get("no_website"):
        return (greeting + _BODY_NO_WEBSITE).format(
            first_name=first_name,
            business_name=business_name,
            city=city,
            niche_or_type=niche_or_type,
        )
    elif signal_notes.get("low_reviews") is not None and review_count > 0:
        plural = "s" if review_count != 1 else ""
        return (greeting + _BODY_LOW_REVIEWS).format(
            first_name=first_name,
            review_count=review_count,
            review_plural=plural,
            niche_or_type=niche_or_type,
            city=city,
        )
    else:
        return (greeting + _BODY_DEFAULT).format(
            first_name=first_name,
            niche=niche,
            city=city,
        )
