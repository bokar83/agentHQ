"""
templates/email/sw_t2.py
========================
Signal Works cold outreach -- Touch 2 (Day 3).
SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.sw_t2 import SUBJECT, build_body

T2 continues the same signal thread as T1. Never resets to a generic hook.
gmb_signal_notes injected by sequence_engine._render() from score_gmb_lead().

Opener priority (mirrors T1, escalates the same gap):
  1. no_website   — still no website, buyers going elsewhere
  2. low_reviews  — still {N} reviews, gap not closing itself
  3. default      — AI window closing, move-first angle
"""

SUBJECT = "Still thinking about this"

_GREETING_HIGH = "Hi {first_name},\n\n"

# Escalates no_website thread
_BODY_NO_WEBSITE = """Quick follow-up on {business_name}.

Still no website on your Google listing — which means ChatGPT, Gemini, and Google AI are pointing buyers in {city} to whoever has one.

The businesses that move first on this are the ones that lock in that search position. The ones that wait find it harder to displace whoever already claimed it.

Still interested in seeing what that looks like for your business?

Boubacar
geolisted.co

Reply STOP to opt out"""

# Escalates low_reviews thread
_BODY_LOW_REVIEWS = """Quick follow-up.

{review_count} review{review_plural} is still where {business_name} sits — and that gap does not close on its own.

The businesses ranking at the top of your category in {city} got there because they made it easy for customers to leave reviews. There is a simple system for that. Happy to show you how it works before you decide anything.

Still interested?

Boubacar
geolisted.co

Reply STOP to opt out"""

# Default: AI window angle, no fabricated scarcity
_BODY_DEFAULT = """Quick follow-up.

Most {niche}s in {city} have not built their AI search presence yet. The ones that move first tend to hold that position — it compounds the same way Google rankings did ten years ago.

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
            business_name=business_name,
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
