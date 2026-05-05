"""
templates/email/sw_t1.py
========================
Signal Works cold outreach Touch 1 (Day 0).
SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.sw_t1 import SUBJECT, build_body

Body has two openers, selected by lead["no_website"]:
  - True  -> business is not online at all (highest-signal SW prospect)
  - False -> default ChatGPT-search hook

niche resolution order:
  1. lead["niche"] if set (SW Serper-scraped leads always have this)
  2. lead["industry"] mapped to human label (Apollo leads)
  3. None -> skip the ChatGPT prompt, use generic hook instead
"""

SUBJECT = "Is your business invisible on ChatGPT?"

_GREETING_HIGH = "Hi {first_name},\n\n"
_GREETING_LOW = ""

# Used when we have a concrete niche/industry label
_BODY_CHATGPT_HOOK = """Open ChatGPT and type: "who is the best {niche} in {city}?"

If your business is not in the answer, someone ready to hire just called your competitor instead.

Most local businesses are invisible on AI right now. That window closes fast once one business in your category claims it.

I build that presence in two weeks. You see a free demo of your specific business before you decide anything.

Worth a look?

Boubacar
geolisted.co
South Jordan, UT | Reply STOP to opt out"""

# Used when we have NO reliable niche label (prevents "best small business in X" nonsense)
_BODY_GENERIC_HOOK = """AI tools like ChatGPT and Google's AI overviews are now how people find local businesses. If your business does not show up there, you are invisible to buyers who never make it to page 2 of Google.

Most local businesses have not claimed that space yet. The ones that move first lock it in.

I build that presence in two weeks. You see a free demo of your specific business before you decide anything.

Worth a look?

Boubacar
geolisted.co
South Jordan, UT | Reply STOP to opt out"""

_BODY_NO_WEBSITE_HOOK = """I went looking for {business_name} on Google and could not find a website. That means ChatGPT, Gemini, and Perplexity also have nothing to point at when someone in {city} asks for a {niche_or_type}.

In 2026, no website means invisible to the AI tools 60% of buyers now use first.

I build the kind of online presence that makes you the first answer in those tools, not just on Google. Two-week build, free demo of your business before you decide.

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

    # Industry present but not mapped — use it directly if it looks real
    # (not a generic catch-all that would produce a nonsense sentence)
    if len(industry) > 3 and industry not in ("other", "n/a", "unknown"):
        return industry

    return None


def build_body(lead: dict) -> str:
    """Render the SW T1 body.

    - Selects no-website opener when lead.no_website is True.
    - Uses ChatGPT hook only when a real niche/industry label is available.
    - Falls back to generic AI-visibility hook when niche cannot be determined.
    - Greeting rendered only when first_name_confidence == "high".
    """
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else _GREETING_LOW

    niche = _resolve_niche(lead)
    city = lead.get("city", "your area")
    first_name = lead.get("first_name", "there")
    business_name = lead.get("business_name") or lead.get("company", "your business")
    niche_or_type = niche or "your type of business"

    if lead.get("no_website"):
        body = (greeting + _BODY_NO_WEBSITE_HOOK).format(
            first_name=first_name,
            niche_or_type=niche_or_type,
            city=city,
            business_name=business_name,
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
