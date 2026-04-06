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
import httpx
from typing import List, Optional

logger = logging.getLogger(__name__)

# ── Default ICP constants — change here to change everywhere ──
DEFAULT_LOCATIONS = [
    "Salt Lake City Utah",
    "Provo Utah",
    "Orem Utah",
    "Lehi Utah",
    "Murray Utah",
    "Sandy Utah",
]
DEFAULT_INDUSTRIES = [
    "Legal", "Accounting", "Marketing Agency",
    "HVAC", "Plumbing", "Roofing",
]
DEFAULT_TITLES = ["Owner", "Founder", "CEO", "President", "Managing Partner"]
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

        leads = []
        for result in results:
            title_parts = result.get("title", "").split(" - ")
            name = title_parts[0].strip() if title_parts else "Unknown"
            snippet = result.get("snippet", "")
            leads.append({
                "name": name,
                "linkedin_url": result.get("link"),
                "industry": industry,
                "location": location,
                "source": "serper_linkedin",
                "snippet": snippet,
                "company": title_parts[2].strip() if len(title_parts) > 2 else "",
                "title": title_parts[1].strip() if len(title_parts) > 1 else "",
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
# STEP 2 — FIRECRAWL: Scrape Business Website
# ══════════════════════════════════════════════════════════════

def _firecrawl_scrape_contact(website_url: str) -> dict:
    """
    Scrape a business website and extract owner name, phone, email.
    Returns partial dict — only fields successfully extracted.
    """
    if not website_url:
        return {}
    try:
        from firecrawl import V1FirecrawlApp
        api_key = os.environ.get("FIRECRAWL_API_KEY")
        if not api_key:
            return {}
        client = V1FirecrawlApp(api_key=api_key)
        response = client.scrape_url(website_url, formats=["markdown"])
        if not response.success or not response.markdown:
            return {}

        content = response.markdown[:3000]  # cap to avoid token waste
        extracted = {}

        # Extract phone — look for common patterns
        import re
        phone_match = re.search(
            r'(\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4})', content
        )
        if phone_match:
            extracted["phone"] = phone_match.group(1)

        # Extract email
        email_match = re.search(
            r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', content
        )
        if email_match:
            email = email_match.group(0)
            # Skip generic emails
            if not any(x in email.lower() for x in ["noreply", "info@", "support@", "hello@"]):
                extracted["email"] = email

        # Try to extract owner name from about/team sections
        owner_patterns = [
            r'(?:Owner|Founder|CEO|President)[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)[,\s]+(?:Owner|Founder|CEO|President)',
        ]
        for pattern in owner_patterns:
            match = re.search(pattern, content)
            if match:
                extracted["name"] = match.group(1)
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
            # domain search — return first verified email
            emails = data.get("emails", [])
            verified = [e for e in emails if e.get("confidence", 0) > 70]
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
    for industry in industries[:3]:  # top 3 industries to avoid burning too many credits
        for location in locations[:2]:  # top 2 locations
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
    for industry in industries[:2]:
        for location in locations[:2]:
            batch = _serper_local_business(
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
    for lead in local_leads[:10]:  # cap scraping to 10 sites
        website = lead.get("website", "")
        if website:
            enriched = _firecrawl_scrape_contact(website)
            lead.update({k: v for k, v in enriched.items() if v})
            # Only add if we got something useful
            if lead.get("phone") or lead.get("email") or lead.get("name") != "Unknown":
                company = lead.get("company", "").lower()
                if company not in seen_companies:
                    seen_companies.add(company)
                    leads.append(lead)

    # Step 4: Hunter.io email enrichment for leads missing email
    logger.info("Hunter: Step 4 — Hunter.io email enrichment")
    for lead in leads:
        if not lead.get("email"):
            website = lead.get("website", "") or lead.get("linkedin_url", "")
            domain = _extract_domain(website)
            if domain and "linkedin.com" not in domain:
                name_parts = lead.get("name", "").split()
                first = name_parts[0] if name_parts else ""
                last = name_parts[-1] if len(name_parts) > 1 else ""
                email = _hunter_find_email(domain, first, last)
                if email:
                    lead["email"] = email

    # Step 4b: Apollo email enrichment (Always-on per user request)
    if APOLLO_API_KEY:
        logger.info("Hunter: Step 4b — Apollo email enrichment fallback")
        for lead in leads:
            if not lead.get("email") and lead.get("linkedin_url"):
                email = reveal_email_for_lead(
                    name=lead.get("name", ""),
                    linkedin_url=lead.get("linkedin_url", "")
                )
                if email:
                    lead["email"] = email


    # Step 5: Apollo fallback if not enough leads
    if len(leads) < 5:
        logger.info(f"Hunter: Step 5 — Apollo fallback (only {len(leads)} leads so far)")
        apollo_leads = _apollo_search(query=query, count=count - len(leads))
        for lead in apollo_leads:
            url = lead.get("linkedin_url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                leads.append(lead)

    logger.info(f"Hunter: Discovery complete — {len(leads)} leads found")
    return leads[:count]


def reveal_email_for_lead(name: str, company: str = "", linkedin_url: str = "") -> Optional[str]:
    """
    On-demand email reveal for a specific named lead.
    Called when Boubacar says 'reveal email for [name]'.
    Tries Hunter.io first (free), Apollo as fallback (costs 1 credit).
    """
    # Try Hunter.io first — free
    if linkedin_url:
        domain = _extract_domain(linkedin_url)
        if domain and "linkedin.com" not in domain:
            name_parts = name.split()
            first = name_parts[0] if name_parts else ""
            last = name_parts[-1] if len(name_parts) > 1 else ""
            email = _hunter_find_email(domain, first, last)
            if email:
                return email

    # Apollo fallback — costs 1 credit
    if APOLLO_API_KEY and linkedin_url:
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": APOLLO_API_KEY,
                "Cache-Control": "no-cache",
            }
            with httpx.Client(timeout=10) as client:
                r = client.post(
                    f"{APOLLO_API_URL}/people/match",
                    json={"linkedin_url": linkedin_url},
                    headers=headers
                )
                r.raise_for_status()
            email = r.json().get("person", {}).get("email")
            if email:
                logger.info(f"Apollo revealed email for {name}: {email}")
                return email
        except Exception as e:
            logger.warning(f"Apollo email reveal failed for {name}: {e}")

    return None
