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

# Greeting line is rendered conditionally based on first_name_confidence.
# When confidence is "low" (parsed from a mashed email handle like robsnow@x
# or no usable name at all), we drop the greeting entirely. Cold-email best
# practice: opening with a generic "Hi there," signals automation and tanks
# reply rates more than no greeting at all. See feedback_no_greeting_when_unknown.md.
_GREETING_HIGH = "Hi {first_name},\n\n"
_GREETING_LOW = ""

_BODY_DEFAULT_HOOK = """Open ChatGPT and type: "who is the best {niche} in {city}?"

If your business is not in the answer, someone ready to hire just called your competitor instead.

Most local businesses are invisible on AI right now. That window closes fast once one business in your category claims it.

I build that presence in two weeks. You see a free demo of your specific business before you decide anything.

Worth a look?

Boubacar
geolisted.co
South Jordan, UT | Reply STOP to opt out"""

_BODY_NO_WEBSITE_HOOK = """I went looking for {business_name} on Google and could not find a website. That means ChatGPT, Gemini, and Perplexity also have nothing to point at when someone in {city} asks for a {niche}.

In 2026, no website means invisible to the AI tools 60% of buyers now use first.

I build the kind of online presence that makes you the first answer in those tools, not just on Google. Two-week build, free demo of your business before you decide.

Worth a look?

Boubacar
geolisted.co
South Jordan, UT | Reply STOP to opt out"""


def build_body(lead: dict) -> str:
    """Render the SW T1 body.

    - Selects opener based on lead.no_website flag.
    - Renders "Hi {first_name},\n\n" only when first_name_confidence == "high".
      Low confidence drops the greeting entirely so the email opens with the
      hook (which is already personalized by business_name or city).
    """
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else _GREETING_LOW
    hook = _BODY_NO_WEBSITE_HOOK if lead.get("no_website") else _BODY_DEFAULT_HOOK
    return (greeting + hook).format(
        first_name=lead.get("first_name", "there"),
        niche=lead.get("niche", "small business"),
        city=lead.get("city", "your area"),
        business_name=lead.get("business_name", "your business"),
    )
