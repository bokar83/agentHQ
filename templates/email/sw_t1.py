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
"""

SUBJECT = "Is your business invisible on ChatGPT?"

_BODY_DEFAULT = """Hi {first_name},

Open ChatGPT and type: "who is the best {niche} in {city}?"

If your business is not in the answer, someone ready to hire just called your competitor instead.

Most local businesses are invisible on AI right now. That window closes fast once one business in your category claims it.

I build that presence in two weeks. You see a free demo of your specific business before you decide anything.

Worth a look?

Boubacar
geolisted.co
South Jordan, UT | Reply STOP to opt out"""

_BODY_NO_WEBSITE = """Hi {first_name},

I went looking for {business_name} on Google and could not find a website. That means ChatGPT, Gemini, and Perplexity also have nothing to point at when someone in {city} asks for a {niche}.

In 2026, no website means invisible to the AI tools 60% of buyers now use first.

I build the kind of online presence that makes you the first answer in those tools, not just on Google. Two-week build, free demo of your business before you decide.

Worth a look?

Boubacar
geolisted.co
South Jordan, UT | Reply STOP to opt out"""


def build_body(lead: dict) -> str:
    """Render the SW T1 body, selecting opener based on lead.no_website flag."""
    template = _BODY_NO_WEBSITE if lead.get("no_website") else _BODY_DEFAULT
    return template.format(
        first_name=lead.get("first_name", "there"),
        niche=lead.get("niche", "small business"),
        city=lead.get("city", "your area"),
        business_name=lead.get("business_name", "your business"),
    )
