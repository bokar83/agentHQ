"""
templates/email/sw_t5.py
========================
Signal Works cold outreach, Touch 5 (Day 17). SaaS audit upsell.
Fires only for non-responders (no reply after T4 breakup).
SINGLE SOURCE OF TRUTH. Edit this file only.

Import:
  from templates.email.sw_t5 import SUBJECT, build_body
"""

SAAS_AUDIT_PDF_URL = "https://drive.google.com/file/d/132_DHAct81kC6Obhrksyixq9lFuCSYQD/view"

SUBJECT = "Different angle: the software question"

_GREETING_HIGH = "Hi {first_name},\n\n"

_BODY_HOOK = (
    "Most {niche}s I talk to are paying $700-$900/month for five SaaS tools that "
    "overlap, half-work, and auto-renew. Zapier, HubSpot, Monday, ActiveCampaign: the usual stack.\n\n"
    "I put together a one-page breakdown showing what each one costs, what an agent replaces it with, "
    "and what you recover in year one.\n\n"
    "You can see it here: {pdf_url}\n\n"
    "If you want me to run it against your actual stack (not the generic example), that is the "
    "$500 SaaS Audit. You send me your tool list. I tell you exactly what to cut, what to keep, "
    "and what a custom agent does instead. Most clients recover the $500 in the first month from "
    "subscriptions they cancel.\n\n"
    "No retainer. No upsell after that.\n\n"
    "Boubacar\n"
    "geolisted.co\n\n"
    "Reply STOP to opt out"
)

BODY = _GREETING_HIGH + _BODY_HOOK


def build_body(lead: dict) -> str:
    """Render SW T5 body with confidence-aware greeting."""
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(
        first_name=lead.get("first_name", "there"),
        niche=lead.get("niche", "small businesses"),
        pdf_url=SAAS_AUDIT_PDF_URL,
    )
