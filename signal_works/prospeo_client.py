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
  - /search-person: 1 credit per page returning >=1 result
  - want_phone=False keeps the cheap path; harvest path uses email-only

Why a separate module from enrichment_tool:
  - enrichment_tool is wired into the post-harvest enrichment pass and
    operates on leads already in DB (lead_id present, conn live).
  - Harvest path resolves emails BEFORE save, has no DB conn yet, and
    enriches by company/domain hint rather than name/linkedin.
  - Different signature, different idempotency model -> separate client.

Schema fix 2026-05-12 (INVALID_DATAPOINTS RCA):
  Prospeo's /enrich-person REQUIRES a person identifier. Valid combos:
    - first_name + last_name + company identifier
    - full_name + company identifier
    - linkedin_url (standalone)
    - email (standalone)
    - person_id (from /search-person)
  The prior schema sent ONLY company_name/company_domain/company_city
  with no person hint -> 100% INVALID_DATAPOINTS rejection rate
  (~30 attempts, 0 matches across SLC/ABQ/SEA SMB trades 2026-05-12
  17:54-18:48 UTC).

  Fix: when caller provides owner_name (e.g. Apollo found the person
  but the email reveal failed), pass first_name/last_name +
  company_name/company_website to /enrich-person directly. When no
  owner_name is available, call /search-person filtered by company
  website to locate a Founder/Owner, then /enrich-person with that
  person_id. only_verified_email=True guards against credit burn on
  unverified guesses.

Env: PROSPEO_KEY (matches enrichment_tool naming). Returns None if unset.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

PROSPEO_ENRICH_URL = "https://api.prospeo.io/enrich-person"
PROSPEO_SEARCH_URL = "https://api.prospeo.io/search-person"

# Seniority filter for /search-person when we have no Apollo name to seed
# Prospeo with. Mirrors the Apollo decision-maker filter so we don't waste
# credits revealing an IC contact's email.
_DECISION_MAKER_SENIORITIES = ["Founder/Owner", "C-Suite", "Director"]


def _split_name(full_name: str) -> tuple[str, str]:
    """Split 'First Middle Last' into ('First', 'Last'). Empty parts ok."""
    parts = (full_name or "").strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _build_enrich_payload(
    *,
    owner_name: str,
    business_name: str,
    domain: str,
    person_id: Optional[str] = None,
) -> Optional[dict]:
    """Construct a valid /enrich-person payload or return None if no
    valid identifier combo can be assembled.

    Priority order (highest match-rate first):
      1. person_id (from /search-person hit) -- single field, free
      2. first_name + last_name + company hint -- 1 credit, ~70% hit
      3. None -- caller should skip Prospeo entirely
    """
    if person_id:
        return {
            "only_verified_email": True,
            "data": {"person_id": person_id},
        }

    first, last = _split_name(owner_name)
    if not (first and last):
        # Single-token name (e.g. "Owner" placeholder from Apollo) isn't
        # enough -- /enrich-person rejects with INVALID_DATAPOINTS.
        return None

    data: dict = {
        "first_name": first,
        "last_name": last,
    }
    # /enrich-person accepts company_name OR company_website; sending both
    # raises match rate. company_website is the higher-signal field.
    if domain:
        data["company_website"] = domain
    if business_name:
        data["company_name"] = business_name

    return {
        "only_verified_email": True,
        "data": data,
    }


def _search_person_id(
    *,
    business_name: str,
    domain: str,
    timeout: int,
    api_key: str,
) -> Optional[str]:
    """Call /search-person filtered by company website (preferred) or
    name to locate a decision-maker. Returns the first matching
    person_id or None on no match.

    Cost: 1 credit per page returning >=1 result (covers up to 25
    contacts; we only need 1).
    """
    filters: dict = {
        "person_seniority": {"include": _DECISION_MAKER_SENIORITIES},
    }
    company_filter: dict = {}
    if domain:
        company_filter["websites"] = {"include": [domain]}
    if business_name:
        company_filter["names"] = {"include": [business_name]}
    if not company_filter:
        return None
    filters["company"] = company_filter

    payload = {"page": 1, "filters": filters}
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(
                PROSPEO_SEARCH_URL,
                headers={"X-KEY": api_key, "Content-Type": "application/json"},
                json=payload,
            )
        resp = r.json()
    except Exception as e:
        logger.warning(f"prospeo_client: /search-person failed for {business_name}/{domain}: {e}")
        return None

    if resp.get("error"):
        code = resp.get("error_code", "unknown")
        logger.info(f"prospeo_client: /search-person no match for {business_name}/{domain} ({code})")
        return None

    results = resp.get("results") or []
    if not results:
        return None

    first_result = results[0] or {}
    person = first_result.get("person") or {}
    return person.get("id") or person.get("person_id")


def prospeo_enrich_company(
    business_name: str,
    domain: str,
    city: str = "",
    owner_name: str = "",
    want_phone: bool = False,
    timeout: int = 20,
) -> Optional[dict]:
    """Enrich a decision-maker email from a company hint.

    Args:
        business_name: Company display name (e.g. "Aspen Roofing").
        domain: Company domain or website (e.g. "aspenroofing.com").
        city: Unused by Prospeo /enrich-person (kept in signature for
            forward-compat; Prospeo has no company_city field).
        owner_name: Full name of the decision-maker if known (Apollo
            often returns name even when email reveal misses). Empty
            string triggers the /search-person fallback.
        want_phone: If True, requests mobile enrichment (10 credits).
            Harvest path locks this to False per memory rule
            feedback_enrichment_hunter_not_wired.md.
        timeout: Per-request HTTP timeout in seconds.

    Returns:
        None if PROSPEO_KEY unset, request fails, no valid payload can
        be assembled, or Prospeo returns error_code.
        {"email": str|None, "phone": str|None, "name": str|None,
         "domain": str|None} on success (any field may be None if
        Prospeo didn't reveal it).
    """
    api_key = os.environ.get("PROSPEO_KEY")
    if not api_key:
        logger.debug("prospeo_client: PROSPEO_KEY not set, skipping")
        return None

    # Step 1: build initial /enrich-person payload from owner_name if present
    payload = _build_enrich_payload(
        owner_name=owner_name,
        business_name=business_name,
        domain=domain,
    )

    # Step 2: if no owner_name was usable, call /search-person to find one
    if payload is None:
        if not (business_name or domain):
            logger.debug(
                f"prospeo_client: no owner_name and no company hint for {business_name}/{domain}, skipping"
            )
            return None
        person_id = _search_person_id(
            business_name=business_name,
            domain=domain,
            timeout=timeout,
            api_key=api_key,
        )
        if not person_id:
            logger.info(
                f"prospeo_client: no decision-maker found via /search-person for {business_name}/{domain}"
            )
            return None
        payload = _build_enrich_payload(
            owner_name="",
            business_name=business_name,
            domain=domain,
            person_id=person_id,
        )
        if payload is None:
            # Defensive: _build_enrich_payload always returns a dict when
            # person_id is set; this branch is unreachable in practice.
            return None

    if want_phone:
        payload["enrich_mobile"] = True
        # only_verified_email + mobile -> still 10 credits if mobile revealed.
        # Caller controls cost via want_phone flag.

    # Step 3: call /enrich-person with the validated payload
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(
                PROSPEO_ENRICH_URL,
                headers={"X-KEY": api_key, "Content-Type": "application/json"},
                json=payload,
            )
        resp = r.json()
    except Exception as e:
        logger.warning(f"prospeo_client: /enrich-person failed for {business_name}/{domain}: {e}")
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
