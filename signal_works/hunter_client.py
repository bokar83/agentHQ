"""
signal_works/hunter_client.py
=============================
Hunter.io domain-search wrapper. Last-resort fallback for SW email
resolution when Firecrawl AND Apollo strict-match both fail.

Cost protection:
  - Hard daily cap: 5 calls per process lifetime (HUNTER_MAX_SEARCHES_PER_DAY env override)
  - Caller catches HunterCapReached to short-circuit and fire Telegram alert
  - 429 (rate limit) returns None gracefully, no crash
"""
import logging
import os

import httpx

logger = logging.getLogger(__name__)

HUNTER_API_URL = "https://api.hunter.io/v2/domain-search"
_OWNER_SENIORITIES = {"owner", "founder", "ceo", "executive", "c_suite"}

_call_count = 0


class HunterCapReached(Exception):
    """Raised when daily Hunter call cap is hit."""


def _max_calls() -> int:
    return int(os.environ.get("HUNTER_MAX_SEARCHES_PER_DAY", "5"))


def reset_daily_counter() -> None:
    """Used by tests and morning_runner at start of day."""
    global _call_count
    _call_count = 0


def domain_search(domain: str) -> str | None:
    """Return highest-confidence owner-tier email at `domain`, or None.

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

    _call_count += 1
    try:
        resp = httpx.get(
            HUNTER_API_URL,
            params={"domain": domain, "api_key": api_key, "limit": 10},
            timeout=15,
        )
    except Exception as e:
        logger.warning(f"hunter_client: request failed for {domain}: {e}")
        return None

    if resp.status_code == 429:
        logger.warning(f"hunter_client: 429 rate limited on {domain}")
        return None
    if resp.status_code != 200:
        logger.warning(f"hunter_client: status {resp.status_code} on {domain}")
        return None

    emails = resp.json().get("data", {}).get("emails", [])
    owner_emails = [
        e for e in emails
        if (e.get("seniority") or "").lower() in _OWNER_SENIORITIES
        and e.get("value")
    ]
    if not owner_emails:
        logger.info(f"hunter_client: no owner-tier email at {domain}")
        return None

    owner_emails.sort(key=lambda e: e.get("confidence", 0), reverse=True)
    return owner_emails[0]["value"]
