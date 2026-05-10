"""
templates/email/sw_t1.py
========================
Signal Works cold outreach Touch 1 (Day 0).
SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.sw_t1 import SUBJECT, build_body

Opener priority (highest specificity wins):
  1. no_website   — business has zero web presence; most specific gap
  2. low_reviews  — business has reviews but under threshold; uses exact count
  3. chatgpt_hook — business has website + ok reviews; AI visibility angle
  4. generic      — fallback when niche cannot be determined

Signal notes come from score_gmb_lead() via sequence_engine._render():
  lead["gmb_signal_notes"] = {"no_website": True, "low_reviews": 8, ...}
  lead["review_count"] = 8

niche resolution order:
  1. lead["niche"] if set (SW Serper-scraped leads always have this)
  2. lead["industry"] mapped to human label (Apollo leads)
  3. None -> skip the ChatGPT prompt, use generic hook instead
"""

SUBJECT = "noticed something on your Google listing"

_GREETING_HIGH = "Hi {first_name},\n\n"
_GREETING_LOW = ""

# Opener 1: no website — most specific, highest signal
_BODY_NO_WEBSITE_HOOK = """I went looking for {business_name} on Google and could not find a website. That means ChatGPT, Gemini, and Perplexity have nothing to point at when someone in {city} searches for a {niche_or_type}.

In 2026, no website means invisible to the AI tools 60% of buyers now use before they call anyone.

I build the kind of online presence that makes you the first answer — not just on Google, but in those AI tools. Two-week build, free demo of your business before you decide anything.

Worth a look?

Boubacar
geolisted.co
South Jordan, UT | Reply STOP to opt out"""

# Opener 2: low reviews — specific count, competitor contrast
_BODY_LOW_REVIEWS_HOOK = """I was looking at {business_name} on Google and noticed you have {review_count} review{review_plural}. The top-ranked {niche_or_type} in {city} typically has 200 or more.

When someone searches and compares, they pick the business with 200 reviews every time — even if yours does better work. Low review count makes you invisible before the conversation even starts.

I help {niche_or_type}s fix that fast, and I build the AI presence that makes you show up first in ChatGPT and Google's AI overviews. Free demo of your business before you decide anything.

Worth a look?

Boubacar
geolisted.co
South Jordan, UT | Reply STOP to opt out"""

# Opener 3: ChatGPT hook — has website, ok reviews, but AI gap
_BODY_CHATGPT_HOOK = """Open ChatGPT and type: "who is the best {niche} in {city}?"

If your business is not in the answer, someone ready to hire just called your competitor instead.

Most local businesses are invisible on AI right now. That window closes fast once one business in your category claims it.

I build that presence in two weeks. You see a free demo of your specific business before you decide anything.

Worth a look?

Boubacar
geolisted.co
South Jordan, UT | Reply STOP to opt out"""

# Opener 4: generic fallback — no reliable niche label
_BODY_GENERIC_HOOK = """AI tools like ChatGPT and Google's AI overviews are now how people find local businesses. If your business does not show up there, you are invisible to buyers who never make it to page 2 of Google.

Most local businesses have not claimed that space yet. The ones that move first lock it in.

I build that presence in two weeks. You see a free demo of your specific business before you decide anything.

Worth a look?

Boubacar
geolisted.co
South Jordan, UT | Reply STOP to opt out"""

# Map Apollo industry strings to human-readable niche labels
_INDUSTRY_TO_NICHE = {
    "legal": "lawyer",
    "accounting": "accountant",
    "marketing": "marketing agency",
    "financial": "financial advisor",
    "insurance": "insurance agency",
    "real estate": "real estate agent",
    "dental": "dentist",
    "chiropractic": "chiropractor",
    "hvac": "HVAC company",
    "plumbing": "plumber",
    "roofing": "roofer",
    "construction": "contractor",
    "landscaping": "landscaper",
    "cleaning": "cleaning service",
    "photography": "photographer",
    "fitness": "personal trainer",
    "restaurant": "restaurant",
    "retail": "retailer",
    "beauty": "salon",
    "wellness": "wellness coach",
    "coaching": "coach",
    "consulting": "consultant",
    "technology": "tech company",
    "medical": "medical practice",
    "education": "tutoring service",
    "events": "event planner",
    "wedding": "wedding planner",
    "automotive": "auto shop",
    "electrical": "electrician",
    "pest control": "pest control service",
    "painting": "painter",
}


def _resolve_niche(lead: dict) -> str | None:
    """Return a human-readable niche label or None if we cannot determine one."""
    niche = (lead.get("niche") or "").strip()
    if niche and niche.lower() not in ("small business", "local business", "business", ""):
        return niche

    industry = (lead.get("industry") or "").lower().strip()
    if not industry:
        return None

    for key, label in _INDUSTRY_TO_NICHE.items():
        if key in industry:
            return label

    if len(industry) > 3 and industry not in ("other", "n/a", "unknown"):
        return industry

    return None


def build_body(lead: dict) -> str:
    """Render the SW T1 body.

    Opener priority (highest specificity wins):
      1. no_website signal   — lead has no web presence at all
      2. low_reviews signal  — lead has reviews but under threshold; uses exact count
      3. chatgpt_hook        — has website + ok reviews; AI visibility angle + niche
      4. generic             — fallback when niche cannot be resolved

    Signal notes injected by sequence_engine._render() via score_gmb_lead():
      lead["gmb_signal_notes"] — dict of fired signals with values
      lead["review_count"]     — raw int for the low_reviews opener

    Greeting rendered only when first_name_confidence == "high".
    """
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else _GREETING_LOW

    niche = _resolve_niche(lead)
    city = lead.get("city", "your area")
    first_name = lead.get("first_name", "there")
    business_name = lead.get("business_name") or lead.get("company", "your business")
    niche_or_type = niche or "your type of business"
    signal_notes = lead.get("gmb_signal_notes", {})
    review_count = int(lead.get("review_count", 0) or 0)

    if signal_notes.get("no_website"):
        body = (greeting + _BODY_NO_WEBSITE_HOOK).format(
            first_name=first_name,
            niche_or_type=niche_or_type,
            city=city,
            business_name=business_name,
        )
    elif signal_notes.get("low_reviews") is not None and review_count > 0:
        plural = "s" if review_count != 1 else ""
        body = (greeting + _BODY_LOW_REVIEWS_HOOK).format(
            first_name=first_name,
            business_name=business_name,
            review_count=review_count,
            review_plural=plural,
            niche_or_type=niche_or_type,
            city=city,
        )
    elif niche:
        body = (greeting + _BODY_CHATGPT_HOOK).format(
            first_name=first_name,
            niche=niche,
            city=city,
        )
    else:
        body = (greeting + _BODY_GENERIC_HOOK).format(
            first_name=first_name,
        )

    return body


# Legacy BODY export for any caller still using format-string path
BODY = _GREETING_HIGH + _BODY_CHATGPT_HOOK
