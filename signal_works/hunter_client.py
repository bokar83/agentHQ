"""
signal_works/hunter_client.py
=============================
Hunter.io domain-search wrapper. Primary fallback for SW email
resolution when Firecrawl scrape fails or Apollo has no record.

Cost protection:
  - Daily cap: 200 calls per process lifetime (HUNTER_MAX_SEARCHES_PER_DAY env override)
  - Caller catches HunterCapReached to short-circuit and fire Telegram alert
  - 429 (rate limit) returns None gracefully, no crash
  - Was 5/run -- raised 2026-05-05 because it killed the only working SW
    fallback path. Apollo people DB has near-zero coverage of trades-SMBs,
    so Hunter is the actual workhorse, not the last resort.
"""
import logging
import os

import httpx

from signal_works.email_gate import gate_email, EmailGateDrop

logger = logging.getLogger(__name__)

HUNTER_API_URL = "https://api.hunter.io/v2/domain-search"
# Was {"owner","founder","ceo","executive","c_suite"} only -- too narrow for
# trades-SMBs where the owner is often tagged generic or has no seniority field.
# Now: owner-tier first, fallback to manager/director/senior, then ANY email
# at the domain (since trade businesses with 1-5 employees often have one
# email and that one IS the decision maker).
_OWNER_SENIORITIES = {"owner", "founder", "ceo", "executive", "c_suite"}
_FALLBACK_SENIORITIES = {"manager", "director", "senior", "vp"}

_call_count = 0


class HunterCapReached(Exception):
    """Raised when daily Hunter call cap is hit."""


def _max_calls() -> int:
    return int(os.environ.get("HUNTER_MAX_SEARCHES_PER_DAY", "200"))


def reset_daily_counter() -> None:
    """Used by tests and morning_runner at start of day."""
    global _call_count
    _call_count = 0


def _hunter_get(api_key: str, params: dict) -> dict | None:
    """Single Hunter domain-search call. Returns parsed JSON data or None on error."""
    try:
        resp = httpx.get(HUNTER_API_URL, params={**params, "api_key": api_key}, timeout=15)
    except Exception as e:
        logger.warning(f"hunter_client: request failed for {params.get('domain')}: {e}")
        return None
    if resp.status_code == 429:
        logger.warning(f"hunter_client: 429 rate limited on {params.get('domain')}")
        return None
    if resp.status_code != 200:
        logger.warning(f"hunter_client: status {resp.status_code} on {params.get('domain')}")
        return None
    return resp.json().get("data", {})


def domain_search(domain: str) -> str | None:
    """Return highest-confidence owner-tier email at `domain`, or None.

    Three-tier server-side filter cascade (Hunter API supports seniority,
    department, type, required_field as native query params -- prior code
    fetched limit=10 unfiltered then filtered client-side, wasting credits
    and frequently returning generic role mailboxes instead of owner emails):

      Tier 1: type=personal + seniority=executive + department=executive
              (one credit, returns owner/founder/CEO personal addresses)
      Tier 2: type=personal + seniority=senior (manager/director fallback)
      Tier 3: any deliverable email at domain (catch-all for 1-5 employee
              shops where one inbox IS the owner)

    Raises HunterCapReached if daily cap exceeded -- caller decides whether
    to skip Hunter for the rest of the run (recommended) or surface alert.
    """
    global _call_count
    if _call_count >= _max_calls():
        raise HunterCapReached(f"Hunter daily cap of {_max_calls()} reached")

    api_key = os.environ.get("HUNTER_API_KEY", "")
    if not api_key:
        logger.warning("hunter_client: HUNTER_API_KEY not set, returning None")
        return None

    base_params = {"domain": domain, "limit": 10, "required_field": "full_name"}

    # Tier 1: executive-level personal emails
    _call_count += 1
    data = _hunter_get(api_key, {
        **base_params,
        "type": "personal",
        "seniority": "executive",
        "department": "executive",
    })
    if data is None:
        return None

    emails = data.get("emails", [])
    owner_hits = [e for e in emails if e.get("value") and e.get("confidence", 0) >= 80]
    if owner_hits:
        owner_hits.sort(key=lambda e: e.get("confidence", 0), reverse=True)
        for hit in owner_hits:
            try:
                return gate_email(hit["value"], source="hunter_tier1")
            except EmailGateDrop as e:
                logger.info(f"hunter_client: tier1 dropped {hit['value']} ({e.reason})")
                continue

    # Tier 2: senior fallback (only fires if tier 1 returned nothing useful)
    if not emails:
        _call_count += 1
        data = _hunter_get(api_key, {
            **base_params,
            "type": "personal",
            "seniority": "senior",
        })
        if data is None:
            return None
        emails = data.get("emails", [])

    senior_hits = [
        e for e in emails
        if (e.get("seniority") or "").lower() in (_OWNER_SENIORITIES | _FALLBACK_SENIORITIES)
        and e.get("value")
        and e.get("confidence", 0) >= 60
    ]
    if senior_hits:
        senior_hits.sort(key=lambda e: e.get("confidence", 0), reverse=True)
        for hit in senior_hits:
            try:
                vetted = gate_email(hit["value"], source="hunter_tier2")
                logger.info(f"hunter_client: senior-tier email used at {domain}")
                return vetted
            except EmailGateDrop as e:
                logger.info(f"hunter_client: tier2 dropped {hit['value']} ({e.reason})")
                continue

    # Tier 3: catch-all -- unfiltered domain search for tiny shops
    _call_count += 1
    data = _hunter_get(api_key, {"domain": domain, "limit": 10})
    if data is None:
        return None
    any_emails = [
        e for e in data.get("emails", [])
        if e.get("value") and e.get("confidence", 0) >= 60
    ]
    if any_emails:
        any_emails.sort(key=lambda e: e.get("confidence", 0), reverse=True)
        for hit in any_emails:
            try:
                vetted = gate_email(hit["value"], source="hunter_tier3")
                logger.info(f"hunter_client: any-tier email used at {domain}")
                return vetted
            except EmailGateDrop as e:
                logger.info(f"hunter_client: tier3 dropped {hit['value']} ({e.reason})")
                continue

    logger.info(f"hunter_client: no deliverable email at {domain}")
    return None
