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
import sys
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
        # Utah base
        "Salt Lake City, Utah", "Provo, Utah", "Ogden, Utah",
        "Sandy, Utah", "Lehi, Utah", "St. George, Utah",
        "West Jordan, Utah", "Murray, Utah", "Draper, Utah",
        "American Fork, Utah", "Orem, Utah", "Layton, Utah",
        "Bountiful, Utah", "Logan, Utah",
        # West
        "Denver, Colorado", "Phoenix, Arizona", "Las Vegas, Nevada",
        "Boise, Idaho", "Scottsdale, Arizona", "Tucson, Arizona",
        "Albuquerque, New Mexico", "Colorado Springs, Colorado",
        "Portland, Oregon", "Seattle, Washington",
        "Los Angeles, California", "San Diego, California",
        "Sacramento, California", "San Francisco, California",
        # South + Southeast
        "Dallas, Texas", "Houston, Texas", "Austin, Texas",
        "San Antonio, Texas", "Atlanta, Georgia",
        "Charlotte, North Carolina", "Nashville, Tennessee",
        "Miami, Florida", "Tampa, Florida", "Orlando, Florida",
        # Midwest
        "Chicago, Illinois", "Columbus, Ohio", "Indianapolis, Indiana",
        "Minneapolis, Minnesota", "Kansas City, Missouri",
        "Detroit, Michigan", "St. Louis, Missouri",
        # Northeast
        "New York, New York", "Philadelphia, Pennsylvania",
        "Boston, Massachusetts", "Washington, DC",
        "Baltimore, Maryland", "Pittsburgh, Pennsylvania",
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

# Studio ICP: any business owner in the US + Canada who could benefit from a
# web presence. No niche ceiling. Solopreneurs to 500-person firms all qualify.
# Score favors decision-makers with verified email — industry is not a filter.
STUDIO_ICP = {
    "name": "studio",
    "person_locations": [
        # Northeast
        "New York, New York", "Brooklyn, New York", "Philadelphia, Pennsylvania",
        "Boston, Massachusetts", "Washington, DC", "Baltimore, Maryland",
        "Pittsburgh, Pennsylvania", "Hartford, Connecticut", "Providence, Rhode Island",
        "Albany, New York", "Buffalo, New York",
        # Southeast
        "Atlanta, Georgia", "Charlotte, North Carolina", "Raleigh, North Carolina",
        "Nashville, Tennessee", "Memphis, Tennessee", "Miami, Florida",
        "Tampa, Florida", "Orlando, Florida", "Jacksonville, Florida",
        "Richmond, Virginia", "Virginia Beach, Virginia", "Louisville, Kentucky",
        "Columbia, South Carolina", "Greenville, South Carolina",
        # South + Texas
        "Dallas, Texas", "Houston, Texas", "Austin, Texas", "San Antonio, Texas",
        "Fort Worth, Texas", "El Paso, Texas", "New Orleans, Louisiana",
        "Oklahoma City, Oklahoma", "Tulsa, Oklahoma", "Little Rock, Arkansas",
        # Midwest
        "Chicago, Illinois", "Columbus, Ohio", "Indianapolis, Indiana",
        "Detroit, Michigan", "Minneapolis, Minnesota", "Kansas City, Missouri",
        "Cleveland, Ohio", "St. Louis, Missouri", "Milwaukee, Wisconsin",
        "Cincinnati, Ohio", "Omaha, Nebraska", "Des Moines, Iowa",
        "Grand Rapids, Michigan", "Madison, Wisconsin",
        # Mountain + Southwest
        "Denver, Colorado", "Phoenix, Arizona", "Scottsdale, Arizona",
        "Tucson, Arizona", "Las Vegas, Nevada", "Albuquerque, New Mexico",
        "Colorado Springs, Colorado", "Salt Lake City, Utah", "Provo, Utah",
        "Boise, Idaho", "Reno, Nevada", "El Paso, Texas",
        # West Coast
        "Los Angeles, California", "San Diego, California", "San Francisco, California",
        "Sacramento, California", "Fresno, California", "Oakland, California",
        "Portland, Oregon", "Seattle, Washington", "Spokane, Washington",
        "Anchorage, Alaska", "Honolulu, Hawaii",
        # Canada
        "Toronto, Ontario", "Vancouver, British Columbia", "Calgary, Alberta",
        "Montreal, Quebec", "Ottawa, Ontario", "Edmonton, Alberta",
        "Winnipeg, Manitoba", "Halifax, Nova Scotia",
    ],
    "person_titles": [
        # Solo operators
        "Owner", "Founder", "Co-Founder", "CEO", "President",
        "Operator", "Proprietor", "Self-Employed",
        # Professional services
        "Managing Partner", "Principal", "Partner",
        "Attorney", "Lawyer", "CPA", "Accountant", "Financial Advisor",
        "Realtor", "Real Estate Agent", "Broker",
        "Photographer", "Videographer", "Graphic Designer",
        "Interior Designer", "Architect", "Engineer",
        "Consultant", "Coach", "Therapist", "Counselor",
        "Nutritionist", "Personal Trainer", "Yoga Instructor",
        # Business managers
        "General Manager", "Managing Director",
        "Marketing Director", "CMO", "Director of Marketing",
        "Brand Manager", "Content Manager",
        # Event + creative
        "Wedding Planner", "Event Planner", "Event Coordinator",
        "Creative Director", "Art Director",
        # Trades + services
        "Contractor", "Plumber", "Electrician", "HVAC Technician",
        "Landscaper", "Roofer", "Painter",
    ],
    "person_seniorities": _DECISION_MAKER_SENIORITIES + ["vp", "director", "manager"],
    "organization_num_employees_ranges": ["1,1000"],
    "score_industries": [
        # Any industry scores — wide net
        "photography", "videography", "design", "media", "creative",
        "restaurant", "food", "beverage", "catering", "bakery",
        "fitness", "wellness", "beauty", "salon", "spa", "aesthetics",
        "real estate", "mortgage", "insurance", "financial",
        "legal", "accounting", "consulting", "coaching",
        "ecommerce", "retail", "fashion", "jewelry",
        "healthcare", "dental", "chiropractic", "medical",
        "events", "wedding", "entertainment", "hospitality", "travel",
        "education", "tutoring", "training",
        "construction", "roofing", "hvac", "plumbing", "landscaping",
        "cleaning", "pest control", "home services",
        "technology", "software", "agency", "marketing",
        "nonprofit", "church", "community", "arts",
        "automotive", "transportation", "logistics",
        "manufacturing", "wholesale", "distribution",
    ],
    "score_titles": [
        "owner", "founder", "ceo", "president", "partner", "principal",
        "operator", "director", "manager", "consultant", "coach",
        "photographer", "planner", "designer", "attorney", "realtor",
    ],
}

# Targeted sweep: highest-need segments — trades, solo professionals, local services.
# These are the people most likely to have NO website or a terrible one.
# Rotate with STUDIO_ICP to ensure both broad + high-need coverage every day.
STUDIO_ICP_TARGETED = {
    "name": "studio_targeted",
    "person_locations": STUDIO_ICP["person_locations"],  # same full US+Canada geo
    "person_titles": [
        # Trades (almost always no website or a 2005-era site)
        "Owner", "Founder", "CEO", "President", "Operator", "Proprietor",
        "Contractor", "General Contractor", "Roofer", "Plumber", "Electrician",
        "HVAC Technician", "Painter", "Landscaper", "Mason", "Carpenter",
        "Welder", "Pool Contractor",
        # Solo creatives
        "Photographer", "Videographer", "Graphic Designer", "Illustrator",
        "Muralist", "Artist",
        # Event + hospitality
        "Wedding Planner", "Event Planner", "Event Coordinator",
        "Caterer", "Baker", "Chef",
        # Personal services
        "Barber", "Hair Stylist", "Nail Technician", "Esthetician",
        "Personal Trainer", "Yoga Instructor", "Life Coach",
        "Nutritionist", "Massage Therapist",
        # Specialty services
        "Architect", "Interior Designer", "Landscape Architect",
        "Pet Groomer", "Dog Trainer", "Veterinarian",
        "Tutor", "Music Teacher", "Dance Instructor",
        "Tax Preparer", "Bookkeeper", "Notary",
        "Moving Company Owner", "Storage Facility Owner",
        "Auto Mechanic", "Detailer",
    ],
    "person_seniorities": _DECISION_MAKER_SENIORITIES,
    "organization_num_employees_ranges": ["1,50"],  # focused on small/solo operators
    "score_industries": [
        "photography", "videography", "construction", "roofing", "landscaping",
        "cleaning", "hvac", "plumbing", "electrical", "pest control",
        "beauty", "salon", "spa", "fitness", "wellness", "personal training",
        "events", "wedding", "catering", "food", "restaurant",
        "architecture", "interior design", "home services",
        "automotive", "storage", "transportation",
        "arts", "music", "education", "tutoring",
        "bookkeeping", "tax", "legal", "consulting",
    ],
    "score_titles": [
        "owner", "founder", "operator", "contractor", "photographer",
        "planner", "trainer", "barber", "stylist", "architect",
        "chef", "baker", "coach", "tutor", "mechanic",
    ],
}


# ── Dedup: track revealed Apollo IDs in Supabase ─────────────────────────────

def _import_get_crm_connection():
    """Dual-import for orchestrator.db. Host has orchestrator/ as a package;
    container has orchestrator code flat in /app."""
    try:
        from orchestrator.db import get_crm_connection
        return get_crm_connection
    except ModuleNotFoundError:
        if "/app" not in sys.path:
            sys.path.insert(0, "/app")
        from db import get_crm_connection  # type: ignore[no-redef]
        return get_crm_connection


def _ensure_revealed_table() -> None:
    """Create apollo_revealed table if it doesn't exist."""
    try:
        get_crm_connection = _import_get_crm_connection()
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
        get_crm_connection = _import_get_crm_connection()
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
        get_crm_connection = _import_get_crm_connection()
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
        "contact_email_status": ["verified", "likely_to_engage"],
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
                        "website_url": (match.get("organization") or {}).get("website_url", ""),
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


# Owner titles used for SW company match
_SW_OWNER_TITLES = ["Owner", "Founder", "CEO", "President", "Operator"]


def find_owner_by_company(name: str, city: str) -> dict | None:
    """Find an owner-tier email at a small business by company name + city.

    Uses mixed_people/api_search filtered by q_organization_name +
    organization_locations + owner-tier titles, then reveal_emails on the
    top match. Same shape as harvest_leads, scoped to one company.

    Returns:
      None if Apollo returns no candidates for this company at all.
      {"domain": str, "email": None, "name": None} if a person was found
        but reveal returned no email (caller can fall back to Hunter).
      {"domain": str, "email": str, "name": str} on full success.

    Cost: 0 credits if no match, ~1 credit per reveal on match.
    """
    try:
        headers = _headers()
    except RuntimeError as e:
        logger.warning(f"find_owner_by_company: {e}")
        return None

    payload = {
        "q_organization_name": name,
        "organization_locations": [city] if city else [],
        "person_titles": _SW_OWNER_TITLES,
        "person_seniorities": _DECISION_MAKER_SENIORITIES,
        "contact_email_status": ["verified", "likely_to_engage"],
        "page": 1,
        "per_page": 5,
    }
    try:
        r = httpx.post(
            f"{APOLLO_API_URL}/mixed_people/api_search",
            json=payload, headers=headers, timeout=20,
        )
        r.raise_for_status()
        people = r.json().get("people", [])
    except Exception as e:
        logger.warning(f"find_owner_by_company: search failed for {name}: {e}")
        return None

    if not people:
        logger.info(f"find_owner_by_company: no people match at {name} in {city}")
        return None

    candidate = people[0]
    domain = (candidate.get("organization") or {}).get("primary_domain") or ""

    revealed = reveal_emails([candidate["id"]])
    if revealed and revealed[0].get("email"):
        person = revealed[0]
        return {
            "domain": domain or person.get("organization", {}).get("primary_domain", ""),
            "email": person["email"],
            "name": person.get("name", ""),
        }

    return {"domain": domain, "email": None, "name": None}
