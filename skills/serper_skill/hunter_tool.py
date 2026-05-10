"""
hunter_tool.py — Unified Lead Discovery Engine
===============================================
Primary prospecting tool for the Growth Hunter agent.

Discovery pipeline (in order):
  1. Serper — LinkedIn dorking for Utah SMB owners/founders
  2. Serper — Google Maps / local business search for direct contact info
  3. Firecrawl — scrape business website for phone, email, owner name
  4. Hunter.io — email lookup by domain + name when site scraping fails
  5. Apollo — fallback search if Serper returns insufficient results

Default ICP (override via query string):
  Locations : Salt Lake City, Provo, Orem, Lehi, Murray, Sandy (Utah)
  Industries: Legal, Accounting, Marketing Agency, HVAC, Plumbing, Roofing
  Titles    : Owner, Founder, CEO, President, Managing Partner
  Size      : 5-80 employees
"""

import os
import json
import logging
import time
import httpx
from typing import List, Optional

logger = logging.getLogger(__name__)

# ── GMB qualification gate — thresholds from m0h absorb 2026-05-09 ──────────
GMB_LOW_REVIEW_THRESHOLD = 30      # under 30 = invisible vs top-ranked competitors
GMB_LOW_RATING_THRESHOLD = 4.0     # below 4.0 = poor review management signal
GMB_REQUIRED_FIELDS = {"phone", "website_url", "google_address"}  # missing = gap

def score_gmb_lead(lead: dict) -> tuple[int, dict]:
    """Score a GMB lead 0-4 based on qualification signals.

    Returns (score, notes) where:
      score  int 0-4. Leads scoring >= 2 are qualified prospects.
      notes  dict with fired signal names and their actual values, used by
             sw_t1.py to pick a specific opener (e.g. "low_reviews" branch
             gets the exact review_count to say "only 8 reviews").

    Signals (one point each):
      1. review_count below GMB_LOW_REVIEW_THRESHOLD
      2. has_website is False (no website linked on GMB listing)
      3. google_rating below GMB_LOW_RATING_THRESHOLD (or absent)
      4. one or more GMB_REQUIRED_FIELDS missing / empty in the lead record
    """
    score = 0
    notes: dict = {}

    review_count = int(lead.get("review_count", 0) or 0)
    if review_count < GMB_LOW_REVIEW_THRESHOLD:
        score += 1
        notes["low_reviews"] = review_count

    no_website = not lead.get("has_website") and not lead.get("website_url")
    if no_website:
        score += 1
        notes["no_website"] = True

    rating = lead.get("google_rating")
    if rating is None or float(rating) < GMB_LOW_RATING_THRESHOLD:
        score += 1
        notes["low_rating"] = float(rating) if rating is not None else None

    for field in GMB_REQUIRED_FIELDS:
        if not lead.get(field):
            score += 1
            notes["missing_fields"] = True
            break

    return score, notes

# ── Default ICP constants — change here to change everywhere ──
DEFAULT_LOCATIONS = [
    # Utah — by county + key cities (Boubacar based in SLC, ~1-2hr drive to all)
    # Salt Lake County
    "Salt Lake City Utah",
    "Sandy Utah",
    "Murray Utah",
    "West Jordan Utah",
    "Taylorsville Utah",
    # Utah County
    "Provo Utah",
    "Orem Utah",
    "Lehi Utah",
    "American Fork Utah",
    "Springville Utah",
    # Davis County
    "Bountiful Utah",
    "Layton Utah",
    "Kaysville Utah",
    # Summit County
    "Park City Utah",
    # Northern Utah
    "Ogden Utah",
    "Logan Utah",
    # Southern Utah
    "St George Utah",
    # Idaho — southern corridor
    "Boise Idaho",
    "Twin Falls Idaho",
    "Pocatello Idaho",
    # Adjacent states — 1-day travel
    "Las Vegas Nevada",
    "Henderson Nevada",
    "Phoenix Arizona",
    "Scottsdale Arizona",
    "Denver Colorado",
]
DEFAULT_INDUSTRIES = [
    # Original core
    "Legal", "Accounting", "Marketing Agency",
    "HVAC", "Plumbing", "Roofing",
    # AI-disrupted trades and services — high operational complexity, low tech adoption
    "Electrical Contractor",
    "General Contractor",
    "Landscaping",
    "Commercial Cleaning",
    "Pest Control",
    # Professional services — billing models under threat from AI
    "Insurance Agency",
    "Financial Advisory",
    "Mortgage Broker",
    "Real Estate Agency",
    "HR Consulting",
    # Healthcare practices — documentation burden, coding, patient comms all ripe
    "Dental Practice",
    "Chiropractic",
    "Physical Therapy",
    "Optometry",
    "Veterinary Practice",
    # Ops-heavy businesses where margin is thin and AI can find savings
    "Freight Brokerage",
    "Auto Repair",
    "Property Management",
    "Staffing Agency",
    "IT Managed Services",
]
DEFAULT_TITLES = ["Owner", "Founder", "CEO", "President", "Managing Partner", "Principal", "COO"]
DEFAULT_LEAD_COUNT = 20

SERPER_API_KEY = os.environ.get("SERPER_API_KEY")
SERPER_URL = "https://google.serper.dev/search"
HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY")
HUNTER_URL = "https://api.hunter.io/v2"
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY")
APOLLO_API_URL = "https://api.apollo.io/v1"


# ══════════════════════════════════════════════════════════════
# STEP 1 — SERPER: LinkedIn Dorking
# ══════════════════════════════════════════════════════════════

def _serper_linkedin_dork(industry: str, location: str, count: int = 10) -> List[dict]:
    """Search LinkedIn profiles via Google dorking."""
    if not SERPER_API_KEY:
        return []

    titles = " OR ".join([f'"{t}"' for t in DEFAULT_TITLES])
    query = f'site:linkedin.com/in/ ({titles}) "{industry}" "{location}"'

    try:
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        payload = {"q": query, "num": count}
        with httpx.Client(timeout=15) as client:
            r = client.post(SERPER_URL, headers=headers, json=payload)
            r.raise_for_status()
        results = r.json().get("organic", [])

        COMPANY_SIGNALS = (
            " llc", " inc", " corp", " ltd", " consulting", " legal",
            " law", " group", " firm", " services", " co.", " &",
        )

        def _is_person_name(s: str) -> bool:
            """Return True if the string looks like a person's name, not a company."""
            low = s.lower()
            if any(sig in low for sig in COMPANY_SIGNALS):
                return False
            # Person names are typically 2-3 words, no special chars
            words = s.split()
            return 1 < len(words) <= 4

        def _name_from_url(url: str) -> str:
            """Extract a capitalised name guess from a LinkedIn /in/ URL slug."""
            slug = url.rstrip("/").split("/in/")[-1].split("?")[0]
            parts = slug.split("-")
            # Drop numeric/hash suffixes (e.g. a0337929) and keep only short alpha words
            words = [p.capitalize() for p in parts if p.isalpha() and len(p) <= 12]
            # A real name slug is 2-3 short words; longer slugs are companies
            if len(words) > 3:
                return "Unknown"
            return " ".join(words[:3]) if words else "Unknown"

        leads = []
        for result in results:
            title_parts = result.get("title", "").split(" - ")
            raw_name = title_parts[0].strip() if title_parts else ""
            snippet = result.get("snippet", "")
            link = result.get("link", "")

            # If first segment looks like a company, skip or fall back to URL slug
            if not _is_person_name(raw_name):
                name = _name_from_url(link)
                job_title = raw_name  # first segment was actually the company/role
                company = title_parts[1].strip() if len(title_parts) > 1 else ""
            else:
                name = raw_name
                job_title = title_parts[1].strip() if len(title_parts) > 1 else ""
                company = title_parts[2].strip() if len(title_parts) > 2 else ""

            # Strip trailing "| LinkedIn" noise from company field
            company = company.split(" | ")[0].strip()

            # Skip results where we couldn't resolve a real person name
            if name in ("Unknown", "") or not _is_person_name(name):
                continue

            leads.append({
                "name": name,
                "linkedin_url": link,
                "industry": industry,
                "location": location,
                "source": "serper_linkedin",
                "snippet": snippet,
                "company": company,
                "title": job_title,
            })
        return leads

    except Exception as e:
        logger.error(f"Serper LinkedIn dork failed ({industry}, {location}): {e}")
        return []


def _serper_local_business(industry: str, location: str) -> List[dict]:
    """Search Google Maps / local business listings for direct contact info."""
    if not SERPER_API_KEY:
        return []

    query = f'"{industry}" company "{location}" owner contact'

    try:
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        payload = {"q": query, "num": 10}
        with httpx.Client(timeout=15) as client:
            r = client.post(SERPER_URL, headers=headers, json=payload)
            r.raise_for_status()

        results = r.json()
        leads = []

        # Pull from local pack (Google Maps results) if present
        for place in results.get("places", []):
            leads.append({
                "name": "Unknown",  # will be enriched by Firecrawl
                "company": place.get("title", ""),
                "location": place.get("address", location),
                "industry": industry,
                "phone": place.get("phoneNumber", ""),
                "website": place.get("website", ""),
                "source": "serper_local",
                "title": "Owner",
            })

        # Also pull organic results for business websites
        for result in results.get("organic", [])[:5]:
            link = result.get("link", "")
            if link and "linkedin.com" not in link:
                leads.append({
                    "name": "Unknown",
                    "company": result.get("title", "").split("|")[0].strip(),
                    "location": location,
                    "industry": industry,
                    "website": link,
                    "source": "serper_organic",
                    "title": "Owner",
                })

        return leads

    except Exception as e:
        logger.error(f"Serper local business search failed: {e}")
        return []


# ══════════════════════════════════════════════════════════════
# STEP 1b — SERPER MAPS: Dedicated Google Maps search
# ══════════════════════════════════════════════════════════════

SERPER_MAPS_URL = "https://google.serper.dev/maps"

def _serper_maps_search(industry: str, location: str) -> List[dict]:
    """
    Hit Serper /maps endpoint directly for Google Business profiles.
    Returns leads with website, phone, and address — all ready for Firecrawl.
    Better email coverage than organic search for trades/SMB.
    """
    if not SERPER_API_KEY:
        return []
    try:
        query = f"{industry} {location}"
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        with httpx.Client(timeout=15) as client:
            r = client.post(SERPER_MAPS_URL, headers=headers, json={"q": query, "num": 10})
            r.raise_for_status()
        places = r.json().get("places", [])
        leads = []
        for place in places:
            website = place.get("website", "")
            if not website:
                continue
            leads.append({
                "name": "Unknown",
                "company": place.get("title", ""),
                "location": place.get("address", location),
                "industry": industry,
                "phone": place.get("phoneNumber", ""),
                "website": website,
                "maps_url": place.get("cid", ""),
                "source": "serper_maps",
                "title": "Owner",
            })
        logger.info(f"Serper Maps: {len(leads)} places with websites for {industry} in {location}")
        return leads
    except Exception as e:
        logger.error(f"Serper Maps search failed ({industry}, {location}): {e}")
        return []


# ══════════════════════════════════════════════════════════════
# STEP 2 — FIRECRAWL: Scrape Business Website
# ══════════════════════════════════════════════════════════════

def _firecrawl_scrape_contact(website_url: str) -> dict:
    """
    Scrape a business website and extract owner name, phone, email.
    Tries the homepage first, then /contact and /about if nothing useful found.
    Returns partial dict — only fields successfully extracted.
    """
    if not website_url:
        return {}
    try:
        from firecrawl import V1FirecrawlApp
        import re

        api_key = os.environ.get("FIRECRAWL_API_KEY")
        if not api_key:
            return {}
        client = V1FirecrawlApp(api_key=api_key)

        base = website_url.rstrip("/")
        # Pages to try in order — stop as soon as we get phone or email
        pages_to_try = [base, f"{base}/contact", f"{base}/about"]

        phone_re = re.compile(r'(\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4})')
        email_re = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
        owner_re = re.compile(
            r'(?:Owner|Founder|CEO|President|Managing Partner)[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)'
            r'|([A-Z][a-z]+ [A-Z][a-z]+)[,\s]+(?:Owner|Founder|CEO|President|Managing Partner)'
        )
        SKIP_EMAILS = ("noreply", "info@", "support@", "hello@", "admin@", "contact@", "no-reply")

        extracted = {}

        for page_url in pages_to_try:
            try:
                resp = client.scrape_url(page_url, formats=["markdown"])
            except Exception:
                continue
            if not resp.success or not resp.markdown:
                continue

            content = resp.markdown[:4000]

            if not extracted.get("phone"):
                m = phone_re.search(content)
                if m:
                    extracted["phone"] = m.group(1)

            if not extracted.get("email"):
                m = email_re.search(content)
                if m:
                    email = m.group(0)
                    if not any(s in email.lower() for s in SKIP_EMAILS):
                        extracted["email"] = email

            if not extracted.get("name"):
                m = owner_re.search(content)
                if m:
                    extracted["name"] = (m.group(1) or m.group(2) or "").strip()

            # Stop early if we have the key fields
            if extracted.get("phone") or extracted.get("email"):
                break

        return extracted

    except Exception as e:
        logger.warning(f"Firecrawl scrape failed for {website_url}: {e}")
        return {}


# ══════════════════════════════════════════════════════════════
# STEP 3 — HUNTER.IO: Email by Domain + Name
# ══════════════════════════════════════════════════════════════

def _hunter_find_email(domain: str, first_name: str = "", last_name: str = "") -> Optional[str]:
    """Look up email via Hunter.io. Uses 1 search credit."""
    if not HUNTER_API_KEY or not domain:
        return None
    try:
        params = {"domain": domain, "api_key": HUNTER_API_KEY}
        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name

        endpoint = f"{HUNTER_URL}/email-finder" if first_name else f"{HUNTER_URL}/domain-search"
        with httpx.Client(timeout=10) as client:
            r = client.get(endpoint, params=params)
            r.raise_for_status()

        data = r.json().get("data", {})
        if first_name:
            return data.get("email")
        else:
            # domain search -- return first deliverable email.
            # Hunter treats confidence >= 50 as deliverable. 70 was too strict
            # and dropped ~60% of valid leads (2026-05-05 daily report: 0/7).
            emails = data.get("emails", [])
            verified = [e for e in emails if e.get("confidence", 0) > 50]
            return verified[0]["value"] if verified else None

    except Exception as e:
        logger.warning(f"Hunter.io lookup failed for {domain}: {e}")
        return None


def _extract_domain(url: str) -> str:
    """Extract domain from a URL."""
    if not url:
        return ""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        domain = parsed.netloc.replace("www.", "")
        return domain
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════
# STEP 4 — APOLLO FALLBACK
# ══════════════════════════════════════════════════════════════

def _apollo_search(query: str = "", count: int = 10) -> List[dict]:
    """Apollo fallback — used only when Serper returns insufficient results."""
    if not APOLLO_API_KEY:
        return []
    try:
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": APOLLO_API_KEY,
            "Cache-Control": "no-cache",
        }
        data = {
            "q_keywords": query if query else ", ".join(DEFAULT_INDUSTRIES),
            "person_locations": DEFAULT_LOCATIONS,
            "person_titles": DEFAULT_TITLES,
            "organization_num_employees_ranges": ["1,80"],
            "page": 1,
            "per_page": count,
        }
        with httpx.Client(timeout=20) as client:
            r = client.post(f"{APOLLO_API_URL}/mixed_people/search", json=data, headers=headers)

        if r.status_code == 403:
            err = r.json().get("error_code", "")
            if err == "API_INACCESSIBLE":
                logger.warning("Apollo: endpoint not available on free plan — skipping fallback. Upgrade at app.apollo.io to enable.")
                return []
        r.raise_for_status()

        leads = []
        for person in r.json().get("people", []):
            phone = ""
            phones = person.get("phone_numbers", [])
            if phones:
                phone = phones[0].get("sanitized_number", "")
            leads.append({
                "name": person.get("name", ""),
                "company": person.get("organization", {}).get("name", ""),
                "title": person.get("title", ""),
                "location": person.get("city", ""),
                "linkedin_url": person.get("linkedin_url", ""),
                "phone": phone,
                "source": "apollo",
                "industry": query or "Unknown",
            })
        return leads

    except Exception as e:
        logger.error(f"Apollo fallback search failed: {e}")
        return []


# ══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════

def discover_leads(query: str = "", count: int = DEFAULT_LEAD_COUNT) -> List[dict]:
    """
    Main discovery function called by the hunter agent.

    Workflow:
      1. Serper LinkedIn dorking across ICP industries + locations
      2. Serper local business search for website URLs + phones
      3. Firecrawl scrapes websites to extract direct contact info
      4. Hunter.io fills in missing emails by domain
      5. Apollo fallback if Serper returns < 5 results

    Args:
        query: Optional override string from user (e.g. "HVAC Park City")
        count: Number of leads to find (default 20)

    Returns:
        List of lead dicts ready for add_lead()
    """
    leads = []
    seen_urls = set()
    seen_companies = set()

    # Parse query for location/industry overrides
    industries = DEFAULT_INDUSTRIES
    locations = DEFAULT_LOCATIONS
    if query:
        # Simple override: if user mentioned a specific industry/location,
        # use it as the search query directly
        logger.info(f"Hunter: custom query override — '{query}'")

    # Step 1: LinkedIn dorking
    logger.info("Hunter: Step 1 — Serper LinkedIn dorking")
    for industry in industries[:8]:  # top 8 industries
        for location in locations[:6]:  # top 6 locations
            if len(leads) >= count:
                break
            batch = _serper_linkedin_dork(
                query if query else industry,
                location,
                count=5
            )
            for lead in batch:
                url = lead.get("linkedin_url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    leads.append(lead)
        if len(leads) >= count:
            break

    # Step 2: Local business search for website-based leads
    logger.info("Hunter: Step 2 — Serper local business search")
    local_leads = []
    for industry in industries[:6]:
        for location in locations[:4]:
            batch = _serper_local_business(
                query if query else industry,
                location
            )
            for lead in batch:
                company = lead.get("company", "").lower()
                if company and company not in seen_companies:
                    seen_companies.add(company)
                    local_leads.append(lead)

    # Step 2b: Google Maps dedicated search — better email coverage for trades/SMB
    logger.info("Hunter: Step 2b — Serper Maps search")
    for industry in industries[:6]:
        for location in locations[:4]:
            batch = _serper_maps_search(
                query if query else industry,
                location
            )
            for lead in batch:
                company = lead.get("company", "").lower()
                if company and company not in seen_companies:
                    seen_companies.add(company)
                    local_leads.append(lead)

    # Step 3: Firecrawl — enrich local leads with contact info from websites
    logger.info("Hunter: Step 3 — Firecrawl website scraping")
    for lead in local_leads[:40]:  # higher cap to match expanded geography
        website = lead.get("website", "")
        if website:
            enriched = _firecrawl_scrape_contact(website)
            lead.update({k: v for k, v in enriched.items() if v})

        company = lead.get("company", "").lower()
        if not company or company in seen_companies:
            continue

        # Step 3b: Hunter.io domain search immediately after Firecrawl
        # catches sites where Firecrawl found no email but domain is known
        if not lead.get("email") and website:
            domain = _extract_domain(website)
            if domain:
                name_parts = (lead.get("name") or "").split()
                first = name_parts[0] if name_parts else ""
                last = name_parts[-1] if len(name_parts) > 1 else ""
                email = _hunter_find_email(domain, first, last)
                if email:
                    lead["email"] = email

        # Save the lead if it has any useful signal — company + website is enough
        # even without email/phone; email enrichment can retry later
        if lead.get("company") and (website or lead.get("phone") or lead.get("email")):
            seen_companies.add(company)
            leads.append(lead)

    # Step 4: Hunter.io email enrichment for LinkedIn leads missing email
    # 0.5s delay between calls to avoid 429 rate-limit errors
    logger.info("Hunter: Step 4 — Hunter.io email enrichment for LinkedIn leads")
    for lead in leads:
        if not lead.get("email"):
            # For LinkedIn leads, look up company domain via Serper then try Hunter
            if lead.get("source") == "serper_linkedin" and lead.get("company"):
                email = reveal_email_for_lead(
                    name=lead.get("name", ""),
                    company=lead.get("company", ""),
                    linkedin_url=lead.get("linkedin_url", ""),
                )
                if email:
                    lead["email"] = email
                time.sleep(0.5)
            # For any lead with a company name but no website, look up domain via Serper
            elif lead.get("company") and not lead.get("email"):
                company_domain = _serper_find_company_domain(lead["company"])
                if company_domain:
                    name_parts = lead.get("name", "").split()
                    first = name_parts[0] if name_parts else ""
                    last = name_parts[-1] if len(name_parts) > 1 else ""
                    email = _hunter_find_email(company_domain, first, last)
                    if email:
                        lead["email"] = email
                time.sleep(0.5)

    # Step 5: Apollo fallback for leads still missing email.
    # 2026-05-05: enabled (we have a paid plan; CW pipeline already uses it).
    # find_owner_by_company is a 1-credit Apollo call per company.
    try:
        from skills.apollo_skill.apollo_client import find_owner_by_company
        apollo_attempts = 0
        apollo_hits = 0
        for lead in leads:
            if lead.get("email") or not lead.get("company"):
                continue
            if apollo_attempts >= 30:  # cap per run to protect Apollo budget
                break
            city = lead.get("city") or lead.get("location") or ""
            apollo_attempts += 1
            try:
                owner = find_owner_by_company(lead["company"], city)
                if owner and owner.get("email"):
                    lead["email"] = owner["email"]
                    if not lead.get("name") and owner.get("name"):
                        lead["name"] = owner["name"]
                    apollo_hits += 1
            except Exception as e:
                logger.warning(f"Hunter: Apollo fallback failed for {lead.get('company')}: {e}")
        logger.info(f"Hunter: Apollo fallback -- {apollo_hits}/{apollo_attempts} leads enriched")
    except ImportError:
        logger.warning("Hunter: apollo_client unavailable, skipping Apollo fallback")

    if len(leads) < 5:
        logger.warning(
            f"Hunter: only {len(leads)} leads found after Serper + Hunter.io + Apollo."
        )

    logger.info(f"Hunter: Discovery complete -- {len(leads)} leads found")
    return leads[:count]


def _serper_find_company_domain(company: str) -> Optional[str]:
    """Use Serper to find a company's website domain from its name."""
    if not SERPER_API_KEY or not company:
        return None
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post(
                SERPER_URL,
                headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                json={"q": f"{company} official website", "num": 3},
            )
            r.raise_for_status()
        results = r.json().get("organic", [])
        for result in results:
            link = result.get("link", "")
            domain = _extract_domain(link)
            # Skip generic directories
            if domain and not any(skip in domain for skip in [
                "linkedin", "facebook", "yelp", "yellowpages", "bbb.org",
                "indeed", "glassdoor", "crunchbase", "bloomberg", "wikipedia"
            ]):
                return domain
    except Exception as e:
        logger.warning(f"Serper domain lookup failed for {company}: {e}")
    return None


def reveal_email_for_lead(name: str, company: str = "", linkedin_url: str = "") -> Optional[str]:
    """
    On-demand email reveal for a specific named lead.
    Pipeline: Hunter.io on company domain → Hunter.io on LinkedIn domain → skip Apollo (403 on free plan).
    """
    name_parts = name.split()
    first = name_parts[0] if name_parts else ""
    last = name_parts[-1] if len(name_parts) > 1 else ""

    # Step 1 — if we have a non-LinkedIn URL, try Hunter.io directly
    if linkedin_url:
        domain = _extract_domain(linkedin_url)
        if domain and "linkedin.com" not in domain:
            email = _hunter_find_email(domain, first, last)
            if email:
                return email

    # Step 2 — look up the company's website via Serper, then try Hunter.io
    if company:
        company_domain = _serper_find_company_domain(company)
        if company_domain:
            email = _hunter_find_email(company_domain, first, last)
            if email:
                logger.info(f"Hunter.io found email for {name} via company domain {company_domain}: {email}")
                return email

    return None
