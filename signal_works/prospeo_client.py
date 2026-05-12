"""
signal_works/prospeo_client.py
==============================
Thin Prospeo /enrich-person wrapper for the SW harvest path. Mirrors the
existing client in skills/email_enrichment/enrichment_tool.py but is
callable independently so topup_leads can invoke Prospeo as the
layer-4 fallback after Apollo+Hunter both miss.

Credit cost:
  - Email only: 1 credit per match (no match = 0 credits)
  - Phone (mobile_international): 10 credits per match
  - want_phone=False keeps the cheap path; harvest path uses email-only

Why a separate module from enrichment_tool:
  - enrichment_tool is wired into the post-harvest enrichment pass and
    operates on leads already in DB (lead_id present, conn live).
  - Harvest path resolves emails BEFORE save, has no DB conn yet, and
    enriches by company/domain hint rather than name/linkedin.
  - Different signature, different idempotency model -> separate client.

Env: PROSPEO_KEY (matches enrichment_tool naming). Returns None if unset.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

PROSPEO_API_URL = "https://api.prospeo.io/enrich-person"


def prospeo_enrich_company(
    business_name: str,
    domain: str,
    city: str = "",
    want_phone: bool = False,
    timeout: int = 20,
) -> Optional[dict]:
    """Enrich by company name + domain. Returns dict with email/name/phone or None.

    Returns:
        None if PROSPEO_KEY unset, request fails, or Prospeo returns error_code.
        {"email": str|None, "phone": str|None, "name": str|None, "domain": str|None}
        on success (any field may be None if Prospeo didn't reveal it).

    The harvest layer only consumes "email" and "name" today; "phone" returned
    for forward-compat with a higher-tier path (e.g. cw_resend re-enrichment).
    """
    api_key = os.environ.get("PROSPEO_KEY")
    if not api_key:
        logger.debug("prospeo_client: PROSPEO_KEY not set, skipping")
        return None

    # Prospeo /enrich-person wants person hints. For a harvest path where we
    # only have a company name, the most reliable shape is company_name +
    # company_domain. Prospeo returns one decision-maker if found.
    data: dict = {"company_name": business_name}
    if domain:
        data["company_domain"] = domain
    if city:
        data["company_city"] = city

    payload = {"data": data}
    if want_phone:
        payload["enrich_mobile"] = True

    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(
                PROSPEO_API_URL,
                headers={"X-KEY": api_key, "Content-Type": "application/json"},
                json=payload,
            )
        resp = r.json()
    except Exception as e:
        logger.warning(f"prospeo_client: request failed for {business_name}/{domain}: {e}")
        return None

    if resp.get("error"):
        code = resp.get("error_code", "unknown")
        logger.info(f"prospeo_client: no match for {business_name}/{domain} ({code})")
        return None

    person = resp.get("person", {}) or {}
    email_data = person.get("email", {}) or {}
    mobile_data = person.get("mobile", {}) or {}

    found_email = None
    if email_data.get("revealed") and email_data.get("email"):
        found_email = email_data["email"].lower().strip()

    found_phone = None
    if mobile_data.get("revealed") and mobile_data.get("mobile"):
        found_phone = mobile_data.get("mobile_international") or mobile_data.get("mobile")

    name = " ".join(
        p for p in (person.get("first_name"), person.get("last_name")) if p
    ).strip() or None

    company = resp.get("company", {}) or {}
    company_domain = company.get("domain") or company.get("website") or domain

    if not (found_email or found_phone or name):
        # Empty response -> treat as miss for caller logging clarity.
        return None

    return {
        "email": found_email,
        "phone": found_phone,
        "name": name,
        "domain": company_domain,
    }
