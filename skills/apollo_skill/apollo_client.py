"""
skills/apollo_skill/apollo_client.py
Shared Apollo.io client for all agentsHQ lead pipelines.

Credit policy:
  - Search is FREE (no credits).
  - Reveal costs 1 credit per person, but ONLY if not already revealed.
  - We track revealed Apollo IDs in Supabase (apollo_revealed table) to
    guarantee we never spend a credit on the same person twice.
  - contact_email_status=verified pre-filters search to people Apollo
    has a verified email for -- maximises reveal yield per credit spent.
  - person_seniorities=['owner','founder','c_suite'] narrows to
    decision-makers only before any credits are spent.

Pipelines:
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
MIN_SCORE = 2       # minimum ICP score to spend a credit
RATE_SLEEP = 0.25   # seconds between API calls


# ── Auth ─────────────────────────────────────────────────────────────────────

def _key() -> str:
    from dotenv import load_dotenv
    load_dotenv(override=True)
    k = os.environ.get("APOLLO_API_KEY", "")
    if not k:
        raise RuntimeError("APOLLO_API_KEY not set.")
    return k


def _headers() -> dict:
    return {"Content-Type": "application/json", "X-Api-Key": _key()}


# ── ICP definitions ──────────────────────────────────────────────────────────

# Seniority values confirmed working with Apollo API Basic plan
_DECISION_MAKER_SENIORITIES = ["owner", "founder", "c_suite"]

CW_ICP = {
    "name": "catalyst_works",
    "person_locations": [
        "Salt Lake City, Utah", "Provo, Utah", "Ogden, Utah",
        "Sandy, Utah", "Lehi, Utah", "St. George, Utah",
        "West Jordan, Utah", "Murray, Utah", "Draper, Utah",
    ],
    "person_titles": [
        "Owner", "Founder", "CEO", "President", "Managing Partner",
        "Principal", "Partner", "Managing Director",
    ],
    "person_seniorities": _DECISION_MAKER_SENIORITIES,
    "organization_num_employees_ranges": ["1,80"],
    "score_industries": [
        "legal", "accounting", "marketing", "financial", "insurance",
        "real estate", "consulting", "dental", "chiropractic", "hvac",
        "plumbing", "roofing", "construction", "landscaping", "staffing",
        "recruiting", "medical", "health", "publishing", "retail",
        "technology", "software", "education", "research",
    ],
    "score_titles": ["owner", "founder", "ceo", "president", "managing partner", "principal"],
}

# Widened variant used for the daily 5-fresh Apollo slot.
# Expands geography to include neighbouring metro areas and raises
# the employee ceiling so we always have enough candidates.
CW_ICP_WIDENED = {
    "name": "catalyst_works_widened",
    "person_locations": [
        "Salt Lake City, Utah", "Provo, Utah", "Ogden, Utah",
        "Sandy, Utah", "Lehi, Utah", "St. George, Utah",
        "West Jordan, Utah", "Murray, Utah", "Draper, Utah",
        "American Fork, Utah", "Orem, Utah", "Layton, Utah",
        "Bountiful, Utah", "Logan, Utah",
        "Denver, Colorado", "Phoenix, Arizona", "Las Vegas, Nevada",
        "Boise, Idaho",
    ],
    "person_titles": [
        "Owner", "Founder", "CEO", "President", "Managing Partner",
        "Principal", "Partner", "Managing Director",
        "Director", "VP", "Vice President", "General Manager",
    ],
    "person_seniorities": _DECISION_MAKER_SENIORITIES,
    "organization_num_employees_ranges": ["1,200"],
    "score_industries": [
        "legal", "accounting", "marketing", "financial", "insurance",
        "real estate", "consulting", "dental", "chiropractic", "hvac",
        "plumbing", "roofing", "construction", "landscaping", "staffing",
        "recruiting", "medical", "health", "publishing", "retail",
        "technology", "software", "education", "research",
    ],
    "score_titles": ["owner", "founder", "ceo", "president", "managing partner", "principal"],
}

SW_ICP = {
    "name": "signal_works",
    "person_locations": [
        "Salt Lake City, Utah", "Provo, Utah", "Ogden, Utah",
        "Sandy, Utah", "Murray, Utah", "West Jordan, Utah",
        "Lehi, Utah", "American Fork, Utah", "St. George, Utah",
    ],
    "person_titles": ["Owner", "Founder", "CEO", "President", "Operator"],
    "person_seniorities": _DECISION_MAKER_SENIORITIES,
    "organization_num_employees_ranges": ["1,30"],
    "score_industries": [
        "roofing", "hvac", "plumbing", "dental", "pediatric", "chiropractic",
        "landscaping", "pest control", "cleaning", "electrical", "construction",
    ],
    "score_titles": ["owner", "founder", "ceo", "president", "operator"],
}

STUDIO_ICP = {
    "name": "studio",
    "person_locations": [
        "Salt Lake City, Utah", "Provo, Utah", "Denver, Colorado",
        "Phoenix, Arizona", "Las Vegas, Nevada", "Scottsdale, Arizona",
    ],
    "person_titles": [
        "Owner", "Founder", "CEO", "President",
        "Marketing Director", "Brand Manager", "Content Manager",
    ],
    "person_seniorities": _DECISION_MAKER_SENIORITIES + ["vp", "director"],
    "organization_num_employees_ranges": ["5,200"],
    "score_industries": [
        "ecommerce", "retail", "restaurant", "fitness", "beauty",
        "real estate", "mortgage", "insurance", "marketing", "agency",
        "food", "beverage", "health", "wellness",
    ],
    "score_titles": ["owner", "founder", "ceo", "marketing", "brand", "content"],
}


# ── Dedup: track revealed Apollo IDs in Supabase ─────────────────────────────

def _ensure_revealed_table() -> None:
    """Create apollo_revealed table if it doesn't exist."""
    try:
        from orchestrator.db import get_crm_connection
        conn = get_crm_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS apollo_revealed (
                apollo_id TEXT PRIMARY KEY,
                revealed_at TIMESTAMPTZ DEFAULT NOW(),
                email TEXT,
                name TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not ensure apollo_revealed table: {e}")


def _get_already_revealed(apollo_ids: list[str]) -> set[str]:
    """Return set of IDs already revealed (skip to save credits)."""
    if not apollo_ids:
        return set()
    try:
        from orchestrator.db import get_crm_connection
        conn = get_crm_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT apollo_id FROM apollo_revealed WHERE apollo_id = ANY(%s)",
            (apollo_ids,)
        )
        revealed = {row["apollo_id"] for row in cur.fetchall()}
        conn.close()
        return revealed
    except Exception as e:
        logger.warning(f"Could not check apollo_revealed: {e}")
        return set()


def _mark_revealed(apollo_id: str, email: str, name: str) -> None:
    """Record a revealed contact so we never spend credits on them again."""
    try:
        from orchestrator.db import get_crm_connection
        conn = get_crm_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO apollo_revealed (apollo_id, email, name)
               VALUES (%s, %s, %s) ON CONFLICT (apollo_id) DO NOTHING""",
            (apollo_id, email, name)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not mark apollo_revealed: {e}")


# ── Scoring ───────────────────────────────────────────────────────────────────

def _score_person(person: dict, icp: dict) -> int:
    """Score 0-3. Only spend credits if >= MIN_SCORE."""
    score = 0
    title = (person.get("title") or "").lower()
    industry = ((person.get("organization") or {}).get("industry") or "").lower()

    if any(t in title for t in icp["score_titles"]):
        score += 1
    if any(ind in industry for ind in icp["score_industries"]):
        score += 1
    if person.get("has_email"):
        score += 1
    return score


# ── Search (FREE -- no credits consumed) ────────────────────────────────────

def search_leads(icp: dict, page: int = 1, per_page: int = 20) -> list[dict]:
    """
    Search Apollo for ICP-matching people. No credits spent.
    Uses seniority + title + location + verified-email filter so every
    result is a decision-maker with a confirmed email in Apollo's DB.
    """
    data = {
        "person_locations": icp["person_locations"],
        "person_titles": icp["person_titles"],
        "person_seniorities": icp.get("person_seniorities", _DECISION_MAKER_SENIORITIES),
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


# ── Reveal (costs 1 credit per NEW person) ───────────────────────────────────

def reveal_emails(apollo_ids: list[str]) -> list[dict]:
    """
    Reveal emails for Apollo IDs. Skips already-revealed IDs (no credit spent).
    Returns list of enriched lead dicts. Max 10 per API call.
    """
    if not apollo_ids:
        return []

    _ensure_revealed_table()
    already_done = _get_already_revealed(apollo_ids)
    new_ids = [pid for pid in apollo_ids if pid not in already_done]

    if already_done:
        logger.info(f"  Skipping {len(already_done)} already-revealed IDs (saving credits)")
    if not new_ids:
        logger.info("  All IDs already revealed -- 0 credits spent")
        return []

    results = []
    for i in range(0, len(new_ids), 10):
        chunk = new_ids[i:i + 10]
        try:
            r = httpx.post(
                f"{APOLLO_API_URL}/people/bulk_match",
                json={"details": [{"id": pid} for pid in chunk]},
                headers=_headers(),
                timeout=20,
            )
            r.raise_for_status()
            resp = r.json()
            credits_used = resp.get("credits_consumed", "?")
            logger.info(f"  bulk_match: {len(chunk)} requested, credits_consumed={credits_used}")

            for match in resp.get("matches", []):
                email = match.get("email")
                name = f"{match.get('first_name','')} {match.get('last_name','')}".strip()
                apollo_id = match.get("id", "")
                _mark_revealed(apollo_id, email or "", name)
                if email:
                    results.append({
                        "apollo_id": apollo_id,
                        "name": name,
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


# ── Combined harvest ──────────────────────────────────────────────────────────

def harvest_leads(icp: dict, target: int = 10, max_pages: int = 5) -> list[dict]:
    """
    Full pipeline: search (free) → score → dedup → reveal (credit only for new).
    Returns up to `target` leads with confirmed emails.
    """
    _ensure_revealed_table()
    leads = []

    for page in range(1, max_pages + 1):
        if len(leads) >= target:
            break

        people = search_leads(icp, page=page, per_page=20)
        if not people:
            logger.info(f"Page {page}: no results returned")
            break

        # Score filter
        candidates = [p for p in people if _score_person(p, icp) >= MIN_SCORE]
        # Only people Apollo confirmed have an email
        email_candidates = [p for p in candidates if p.get("has_email") and p.get("id")]

        logger.info(
            f"Page {page}: {len(people)} found, {len(candidates)} passed score, "
            f"{len(email_candidates)} have verified email"
        )

        if not email_candidates:
            continue

        ids_to_reveal = [p["id"] for p in email_candidates]
        revealed = reveal_emails(ids_to_reveal)

        for lead in revealed:
            if lead.get("email") and len(leads) < target:
                lead["source"] = f"apollo_{icp['name']}"
                leads.append(lead)
                logger.info(f"  Got: {lead['name']} <{lead['email']}> | {lead['company']}")

        time.sleep(RATE_SLEEP)

    logger.info(f"harvest_leads({icp['name']}): {len(leads)}/{target} leads with email")
    return leads
