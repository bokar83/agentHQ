"""
signal_works/lead_scraper.py
Scrapes Google Maps for local businesses matching Signal Works criteria.
Uses Serper.dev /maps endpoint (SERPER_API_KEY already in .env, 2500 free/month).
Email extraction uses Firecrawl to scrape business websites (FIRECRAWL_API_KEY in .env).
Falls back to manual CSV input mode if keys unavailable.
"""
import os
import re
import logging
import requests
from orchestrator.db import upsert_signal_works_lead

logger = logging.getLogger(__name__)

SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Domains that are never real business contact emails
SKIP_EMAIL_DOMAINS = {
    "example.com", "sentry.io", "wixpress.com", "squarespace.com",
    "godaddy.com", "hostinger.com", "namecheap.com", "bluehost.com",
    "wordpress.com", "shopify.com", "weebly.com", "jimdo.com",
    "yoast.com", "elementor.com", "gravatar.com", "mailchimp.com",
    "constantcontact.com", "hubspot.com", "zendesk.com", "freshdesk.com",
    "schema.org", "w3.org", "google.com", "googleapis.com", "googlemail.com",
    "yelp.com", "bbb.org", "angi.com", "houzz.com", "thumbtack.com",
    "maps.google.com",
}

# Prefixes that indicate generic/role emails unlikely to reach a real person
SKIP_EMAIL_PREFIXES = {
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "admin", "webmaster", "postmaster", "mailer-daemon",
    "info@info", "contact@contact", "hello@hello",
    "support@support", "sales@sales",
}

# Local parts that are placeholders, not real addresses
_PLACEHOLDER_RE = re.compile(r"^(your|name|email|address|user|username|test|sample|demo)@", re.I)
# Addresses with ellipsis prefix are truncated/invalid (e.g. ...@kelso-industries.com)
_TRUNCATED_RE = re.compile(r"^\.*\.\.\.")


def _is_valid_email(email: str) -> bool:
    """Return True only if email looks like a real, deliverable business address."""
    if not email or "@" not in email:
        return False
    local, domain = email.rsplit("@", 1)
    # Reject truncated addresses like ...@anything.com
    if local.startswith("...") or local.startswith(".."):
        return False
    # Reject placeholder patterns
    if _PLACEHOLDER_RE.match(email):
        return False
    # Reject known skip domains
    if domain in SKIP_EMAIL_DOMAINS:
        return False
    # Reject generic prefixes
    if local.lower() in SKIP_EMAIL_PREFIXES:
        return False
    # Must have a real TLD (at least 2 chars, not purely numeric)
    tld = domain.rsplit(".", 1)[-1]
    if len(tld) < 2 or tld.isdigit():
        return False
    # Domain must have at least one dot
    if "." not in domain:
        return False
    return True


def _fetch_maps_results(query: str, location: str, limit: int = 20) -> list[dict]:
    """
    Fetch Google Maps business listings via Serper.dev /maps endpoint.
    Returns list of raw business dicts. Falls back to empty list with warning.
    """
    if not SERPER_API_KEY:
        logger.warning("SERPER_API_KEY not set. Returning empty list -- use manual CSV mode.")
        return []
    try:
        resp = requests.post(
            "https://google.serper.dev/maps",
            headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": f"{query} in {location}", "num": min(limit, 20)},
            timeout=20,
        )
        resp.raise_for_status()
        places = resp.json().get("places", [])
        results = []
        for biz in places[:limit]:
            website = biz.get("website", "") or ""
            results.append({
                "name": biz.get("title", ""),
                "phone": biz.get("phoneNumber", ""),
                "website": website,
                "has_website": bool(website),
                "rating": float(biz.get("rating", 0.0) or 0.0),
                "review_count": int(biz.get("ratingCount", 0) or 0),
                "maps_url": biz.get("cid", "") or "",
                "address": biz.get("address", "") or "",
            })
        logger.info(f"Serper returned {len(results)} results for '{query}' in {location}")
        return results
    except Exception as exc:
        logger.warning(f"Serper Maps fetch failed: {exc}. Use manual CSV mode.")
        return []


def find_email_from_website(website_url: str) -> str:
    """
    Scrape a business website with Firecrawl and extract a contact email.
    Returns the first valid email found, or '' if none found or scrape fails.
    Skips generic/platform emails (wix, squarespace, etc).
    """
    if not website_url or not FIRECRAWL_API_KEY:
        return ""
    try:
        resp = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={
                "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "url": website_url,
                "formats": ["markdown"],
                "onlyMainContent": False,
                "timeout": 15000,
            },
            timeout=25,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data.get("data", {}).get("markdown", "") or ""

        for match in EMAIL_RE.finditer(text):
            email = match.group(0).lower()
            if _is_valid_email(email):
                logger.info(f"Found email {email} on {website_url}")
                return email
            else:
                logger.debug(f"Rejected email {email} from {website_url}")
    except Exception as exc:
        logger.debug(f"Email extraction failed for {website_url}: {exc}")
    return ""


# Domains that are not the company's own website. If the top organic result
# is from one of these, skip and try the next. If everything is aggregators,
# return empty (we'd rather fail closed than scrape a Yelp page as if it were
# the prospect's voice).
_AGGREGATOR_DOMAINS = (
    "linkedin.com", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "yelp.com", "crunchbase.com", "glassdoor.com", "indeed.com", "zoominfo.com",
    "bbb.org", "yellowpages.com", "manta.com", "bizjournals.com", "owler.com",
    "tiktok.com", "youtube.com", "pinterest.com", "reddit.com",
    "google.com", "bing.com", "wikipedia.org",
    "apollo.io", "rocketreach.co", "lusha.com", "signalhire.com",
)


def find_company_website(company_name: str, city: str = "") -> str:
    """
    Find the company's own website URL by Serper search on the company name.

    Skips known aggregator/social domains. Returns the first organic result
    that is plausibly the company's own site. Returns empty string on any
    failure (no API key, no results, all results are aggregators, network
    error). Best-effort: never raises.

    Used to derive a website_url for CW (Apollo) leads, which only have
    company name + linkedin_url out of the box.
    """
    if not company_name:
        return ""
    if not SERPER_API_KEY:
        return ""
    query = f"{company_name} {city}".strip() if city else company_name
    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": query, "num": 5, "gl": "us", "hl": "en"},
            timeout=15,
        )
        if response.status_code != 200:
            logger.debug(f"find_company_website non-200 for {query!r}: {response.status_code}")
            return ""
        data = response.json() or {}
        organic = data.get("organic") or []
        for item in organic:
            link = (item.get("link") or "").strip()
            if not link:
                continue
            # Cheap aggregator filter: substring match on host portion
            lower = link.lower()
            if any(agg in lower for agg in _AGGREGATOR_DOMAINS):
                continue
            return link
        return ""
    except Exception as exc:
        logger.debug(f"find_company_website failed for {company_name!r}: {exc}")
        return ""


def fetch_site_text(url: str) -> str:
    """
    Fetch readable text content from a website URL using requests + BeautifulSoup.

    Strips script and style tags. Collapses runs of whitespace. Returns plain
    text suitable as reference material for transcript-style-dna.extract.

    Best-effort. Never raises; logs and returns empty on any error including
    non-200, non-HTML content type, network failure, parse failure.

    Decision 2026-04-29: chose this over Firecrawl for the lift test. See
    memory/reference_firecrawl_pricing_2026.md.
    """
    if not url:
        return ""
    try:
        from bs4 import BeautifulSoup  # local import to keep startup cheap
    except ImportError:
        logger.error("fetch_site_text: beautifulsoup4 not installed")
        return ""
    try:
        response = requests.get(
            url,
            headers={
                # Some sites 403 the python-requests UA. A plain modern UA
                # is enough for most small-business marketing sites.
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=15,
            allow_redirects=True,
        )
    except Exception as exc:
        logger.debug(f"fetch_site_text request failed for {url}: {exc}")
        return ""
    if response.status_code != 200:
        logger.debug(f"fetch_site_text non-200 for {url}: {response.status_code}")
        return ""
    content_type = (response.headers.get("Content-Type") or "").lower()
    if "html" not in content_type:
        logger.debug(f"fetch_site_text non-HTML content_type={content_type} for {url}")
        return ""
    try:
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as exc:
        logger.debug(f"fetch_site_text parse failed for {url}: {exc}")
        return ""
    # Strip noise: scripts, styles, hidden elements, nav clutter
    for tag in soup(["script", "style", "noscript", "template", "iframe", "svg"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # Collapse runs of blank lines and trim per-line whitespace
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def scrape_google_maps_leads(
    niche: str,
    city: str,
    min_reviews: int = 20,
    max_reviews: int = 150,
    limit: int = 25,
    save_to_supabase: bool = True,
) -> list[dict]:
    """
    Scrape Google Maps for businesses in niche + city matching review criteria.
    Filters: min_reviews <= review_count <= max_reviews.
    Attempts to find email via Firecrawl for any lead that has a website_url.
    Tags each lead with niche + city + lead_type='website_prospect' for Signal Works.
    Returns list of enriched lead dicts.
    """
    raw = _fetch_maps_results(niche, city, limit=limit * 2)
    leads = []
    for biz in raw:
        rc = int(biz.get("review_count", 0))
        if rc < min_reviews or rc > max_reviews:
            continue
        website = biz.get("website", "") or ""
        email = find_email_from_website(website) if website else ""
        lead = {
            "name": biz["name"],
            "email": email,
            "phone": biz.get("phone", ""),
            "website_url": website,
            "has_website": biz.get("has_website", bool(website)),
            "review_count": rc,
            "google_rating": biz.get("rating", 0.0),
            "google_address": biz.get("address", ""),
            "google_maps_url": biz.get("maps_url", ""),
            "niche": niche,
            "city": city,
            "lead_type": "website_prospect",
            "ai_score": 0,
        }
        leads.append(lead)
        if save_to_supabase:
            try:
                upsert_signal_works_lead(lead)
            except Exception as exc:
                logger.warning(f"Could not save lead to Supabase (continuing): {exc}")
    logger.info(f"scrape_google_maps_leads: {len(leads)} qualifying leads for '{niche}' in {city}")
    return leads[:limit]


def load_leads_from_csv(csv_path: str, niche: str, city: str, save_to_supabase: bool = True) -> list[dict]:
    """
    Manual fallback: load leads from a CSV file.
    Expected columns: name, email, phone, website_url, review_count
    If email is blank and website_url is present, attempts Firecrawl email extraction.
    Saves all leads to Supabase regardless of whether email was found.
    """
    import csv
    leads = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            website = row.get("website_url", row.get("website", ""))
            email = row.get("email", "").strip()
            if email and not _is_valid_email(email):
                logger.warning(f"Rejected bad email from CSV: {email} for {row.get('name', '')}")
                email = ""
            if not email and website:
                logger.info(f"No email in CSV for {row.get('name', '')} -- trying Firecrawl...")
                email = find_email_from_website(website)
            lead = {
                "name": row.get("name", ""),
                "email": email,
                "phone": row.get("phone", ""),
                "website_url": website,
                "has_website": bool(website),
                "review_count": int(row.get("review_count", 0) or 0),
                "google_rating": float(row.get("google_rating", 0.0) or 0.0),
                "google_address": row.get("google_address", row.get("address", "")),
                "google_maps_url": row.get("google_maps_url", ""),
                "niche": niche,
                "city": city,
                "lead_type": "website_prospect",
                "ai_score": 0,
            }
            leads.append(lead)
            if save_to_supabase:
                try:
                    upsert_signal_works_lead(lead)
                except Exception as exc:
                    logger.warning(f"Could not save lead to Supabase (continuing): {exc}")
    logger.info(f"load_leads_from_csv: loaded {len(leads)} leads from {csv_path}")
    return leads
