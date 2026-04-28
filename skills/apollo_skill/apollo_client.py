"""
skills/apollo_skill/apollo_client.py
Shared Apollo.io client for all agentsHQ lead pipelines.

Credit policy: search is free; reveal costs 1 credit per person.
Only reveal email when the lead passes ICP scoring (score >= MIN_SCORE).

Pipelines that use this:
  - Catalyst Works cold outreach  (CW_ICP)
  - Signal Works AI presence      (SW_ICP)
  - Studio faceless agency        (STUDIO_ICP)
"""

import os
import logging
import time
import httpx

logger = logging.getLogger(__name__)

APOLLO_API_URL = "https://api.apollo.io/v1"
MIN_SCORE = 2       # minimum ICP score to spend a credit on email reveal
RATE_SLEEP = 0.3    # seconds between API calls


def _key() -> str:
    from dotenv import load_dotenv
    load_dotenv(override=True)
    k = os.environ.get("APOLLO_API_KEY", "")
    if not k:
        raise RuntimeError("APOLLO_API_KEY not set in environment.")
    return k


def _headers() -> dict:
    return {"Content-Type": "application/json", "X-Api-Key": _key()}


# ── ICP definitions ──────────────────────────────────────────────────────────

# Catalyst Works: professional service SMB owners who need AI strategy help
CW_ICP = {
    "name": "catalyst_works",
    "person_locations": [
        "Salt Lake City, Utah", "Provo, Utah", "Ogden, Utah",
        "Sandy, Utah", "Lehi, Utah", "St. George, Utah",
    ],
    "person_titles": [
        "Owner", "Founder", "CEO", "President", "Managing Partner",
        "Principal", "Partner",
    ],
    "organization_num_employees_ranges": ["1,80"],
    # Score signals: +1 each if true
    "score_industries": [
        "legal", "accounting", "marketing", "financial", "insurance",
        "real estate", "consulting", "dental", "chiropractic", "hvac",
        "plumbing", "roofing", "construction", "landscaping",
    ],
    "score_titles": ["owner", "founder", "ceo", "president", "managing partner"],
}

# Signal Works: local service businesses with no/weak AI presence
SW_ICP = {
    "name": "signal_works",
    "person_locations": [
        "Salt Lake City, Utah", "Provo, Utah", "Ogden, Utah",
        "Sandy, Utah", "Murray, Utah", "West Jordan, Utah",
        "Lehi, Utah", "American Fork, Utah", "St. George, Utah",
    ],
    "person_titles": ["Owner", "Founder", "CEO", "President", "Operator"],
    "organization_num_employees_ranges": ["1,30"],
    "score_industries": [
        "roofing", "hvac", "plumbing", "dental", "pediatric", "chiropractic",
        "landscaping", "pest control", "cleaning", "electrical", "construction",
    ],
    "score_titles": ["owner", "founder", "ceo", "president", "operator"],
}

# Studio: businesses that need video/content (faceless agency)
STUDIO_ICP = {
    "name": "studio",
    "person_locations": [
        "Salt Lake City, Utah", "Provo, Utah", "Denver, Colorado",
        "Phoenix, Arizona", "Las Vegas, Nevada",
    ],
    "person_titles": [
        "Owner", "Founder", "CEO", "Marketing Director", "Brand Manager",
        "Content Manager", "President",
    ],
    "organization_num_employees_ranges": ["5,200"],
    "score_industries": [
        "ecommerce", "retail", "restaurant", "fitness", "beauty",
        "real estate", "mortgage", "insurance", "marketing", "agency",
        "food", "beverage", "health", "wellness",
    ],
    "score_titles": ["owner", "founder", "ceo", "marketing", "brand", "content"],
}


# ── Scoring ──────────────────────────────────────────────────────────────────

def _score_person(person: dict, icp: dict) -> int:
    """Score 0-3. Spend credit only if >= MIN_SCORE."""
    score = 0
    title = (person.get("title") or "").lower()
    industry = (person.get("organization") or {}).get("industry", "") or ""
    industry = industry.lower()

    if any(t in title for t in icp["score_titles"]):
        score += 1
    if any(ind in industry for ind in icp["score_industries"]):
        score += 1
    if person.get("has_email"):
        score += 1
    return score


# ── Search (free, no credits) ────────────────────────────────────────────────

def search_leads(icp: dict, page: int = 1, per_page: int = 20) -> list[dict]:
    """
    Search Apollo for people matching the ICP. Returns obfuscated records.
    No credits spent. Call reveal_emails() on the results you want.
    contact_email_status=verified ensures has_email=True on every result,
    so we only spend credits on people Apollo has confirmed emails for.
    """
    data = {
        "person_locations": icp["person_locations"],
        "person_titles": icp["person_titles"],
        "organization_num_employees_ranges": icp["organization_num_employees_ranges"],
        "contact_email_status": ["verified"],
        "page": page,
        "per_page": per_page,
    }
    try:
        r = httpx.post(
            f"{APOLLO_API_URL}/mixed_people/api_search",
            json=data, headers=_headers(), timeout=20
        )
        r.raise_for_status()
        return r.json().get("people", [])
    except Exception as e:
        logger.error(f"Apollo search failed: {e}")
        return []


# ── Reveal (costs 1 credit per person) ───────────────────────────────────────

def reveal_emails(apollo_ids: list[str]) -> list[dict]:
    """
    Bulk reveal email for a list of Apollo person IDs.
    Costs 1 credit per ID. Returns list of dicts with name + email.
    Max 10 per call (Apollo limit).
    """
    results = []
    for chunk_start in range(0, len(apollo_ids), 10):
        chunk = apollo_ids[chunk_start:chunk_start + 10]
        try:
            r = httpx.post(
                f"{APOLLO_API_URL}/people/bulk_match",
                json={"details": [{"id": pid} for pid in chunk]},
                headers=_headers(),
                timeout=20,
            )
            r.raise_for_status()
            for match in r.json().get("matches", []):
                email = match.get("email")
                if email:
                    results.append({
                        "apollo_id": match.get("id"),
                        "name": f"{match.get('first_name','')} {match.get('last_name','')}".strip(),
                        "email": email,
                        "title": match.get("title", ""),
                        "company": (match.get("organization") or {}).get("name", ""),
                        "linkedin_url": match.get("linkedin_url", ""),
                        "industry": (match.get("organization") or {}).get("industry", ""),
                        "city": match.get("city", ""),
                    })
        except Exception as e:
            logger.error(f"Apollo bulk_match failed: {e}")
        time.sleep(RATE_SLEEP)
    return results


# ── Combined harvest (search + score + reveal) ────────────────────────────────

def harvest_leads(icp: dict, target: int = 10, max_pages: int = 5) -> list[dict]:
    """
    Full pipeline: search → score → reveal email only for good matches.
    Returns up to `target` leads with confirmed emails.
    Spends at most `target` credits.
    """
    leads = []
    for page in range(1, max_pages + 1):
        if len(leads) >= target:
            break

        people = search_leads(icp, page=page, per_page=20)
        if not people:
            break

        # Score and filter
        candidates = [p for p in people if _score_person(p, icp) >= MIN_SCORE]
        logger.info(f"Page {page}: {len(people)} found, {len(candidates)} passed ICP score")

        if not candidates:
            continue

        # Only reveal people Apollo confirms have an email in their DB
        ids_to_reveal = [p["id"] for p in candidates if p.get("id") and p.get("has_email")]
        logger.info(f"  {len(candidates)} passed ICP score, {len(ids_to_reveal)} have email -- revealing")
        revealed = reveal_emails(ids_to_reveal)

        for r in revealed:
            if r.get("email") and len(leads) < target:
                r["source"] = f"apollo_{icp['name']}"
                leads.append(r)
                logger.info(f"  Got: {r['name']} <{r['email']}> | {r['company']}")

        time.sleep(RATE_SLEEP)

    logger.info(f"harvest_leads({icp['name']}): {len(leads)}/{target} leads with email")
    return leads
