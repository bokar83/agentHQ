"""
enrichment_tool.py — Deep Lead Enrichment Pipeline
===================================================
Runs after daily harvest, before the report email is sent.
For every lead missing an email, phone, or LinkedIn URL, attempts to find them
using Serper + web scraping first (free), then Prospeo API (paid, fallback).

Pipeline per lead:
  1. Serper: "[Name]" "[Company]" contact email  -> find company website
  2. Scrape /contact, /about, homepage -> extract email (httpx > curl_cffi > Firecrawl)
  3. Prospeo /enrich-person -> email + mobile fallback (1 credit email, 10 credits mobile)
  4. Serper: "[Name]" "[Company]" site:linkedin.com/in -> find LinkedIn
  5. If no website found at all: flag as web prospect in notes

Notes are written to:
  - leads.notes column (persistent summary)
  - lead_interactions (audit trail, type: enrichment_attempt)

Called by: scheduler._run_daily_harvest() after discover, before send
Also callable standalone: enrich_missing_emails()
"""

import logging
import sys
import os
import re
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def _get_crm_conn():
    if "/app" not in sys.path:
        sys.path.insert(0, "/app")
    from db import get_crm_connection_with_fallback
    conn, is_fallback = get_crm_connection_with_fallback()
    if is_fallback:
        logger.warning("Enrichment: using local Postgres fallback.")
    return conn


# ── Serper helpers ───────────────────────────────────────────────

def _serper_search(query: str) -> list:
    """Run a Serper Google search. Returns list of result dicts."""
    import httpx
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        logger.warning("Enrichment: SERPER_API_KEY not set.")
        return []
    try:
        with httpx.Client(timeout=15) as client:
            r = client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query, "num": 5},
            )
            r.raise_for_status()
        return r.json().get("organic", [])
    except Exception as e:
        logger.warning(f"Enrichment: Serper search failed for '{query}': {e}")
        return []


_DIRECTORY_DOMAINS = [
    "linkedin.com", "facebook.com", "yelp.com", "bbb.org",
    "yellowpages.com", "google.com", "instagram.com", "twitter.com",
    "rocketreach.co", "zoominfo.com", "apollo.io", "crunchbase.com",
    "bloomberg.com", "bizbuysell.com", "manta.com", "chamberofcommerce.com",
    "angieslist.com", "houzz.com", "thumbtack.com", "bark.com",
    "clutch.co", "upcity.com", "expertise.com", "goodfirms.io",
    "indeed.com", "glassdoor.com", "mapquest.com", "whitepages.com",
]


def _find_company_website(company: str) -> Optional[str]:
    """
    Search for the company's own website domain via Serper.
    Returns the base homepage URL (not a sub-page) or None.
    Aggressively filters out directories, aggregators, and data brokers.
    """
    from urllib.parse import urlparse

    for query in [f'"{company}" official site', f'"{company}" contact email']:
        results = _serper_search(query)
        for r in results:
            link = r.get("link", "")
            if not link.startswith("http"):
                continue
            if any(d in link for d in _DIRECTORY_DOMAINS):
                continue
            # Strip to base homepage so we control which pages we scrape
            parsed = urlparse(link)
            base = f"{parsed.scheme}://{parsed.netloc}"
            return base
    return None


def _find_linkedin(name: str, company: str) -> Optional[str]:
    """Search for the person's LinkedIn profile URL."""
    results = _serper_search(f'"{name}" "{company}" site:linkedin.com/in')
    for r in results:
        link = r.get("link", "")
        if "linkedin.com/in/" in link:
            return link
    return None


# ── Scraping helpers ─────────────────────────────────────────────
# Primary: httpx direct fetch (free, no credits)
# Fallback: Firecrawl (only if key present and credits available)

_SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _html_to_text(html: str) -> str:
    """Strip HTML tags and normalize whitespace to plain text."""
    html = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<(br|p|div|li|tr|h[1-6])[^>]*>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<[^>]+>", " ", html)
    html = html.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">") \
               .replace("&#64;", "@").replace("&#46;", ".").replace("&nbsp;", " ")
    html = re.sub(r"[ \t]+", " ", html)
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()


def _httpx_scrape(url: str) -> Optional[str]:
    """Tier 1: fetch with httpx (static sites, fast, zero cost)."""
    try:
        with httpx.Client(timeout=15, follow_redirects=True, headers=_SCRAPE_HEADERS) as client:
            r = client.get(url)
            if r.status_code >= 400:
                return None
            return _html_to_text(r.text)
    except Exception as e:
        logger.debug(f"Enrichment: httpx scrape failed for {url}: {e}")
        return None


def _curl_cffi_scrape(url: str) -> Optional[str]:
    """
    Tier 2: fetch with curl_cffi, impersonating Chrome browser fingerprint.
    Bypasses Cloudflare and basic bot-detection that blocks httpx.
    Zero cost, no browser process.
    """
    try:
        from curl_cffi import requests as curl_requests
        r = curl_requests.get(
            url,
            impersonate="chrome",
            timeout=15,
            allow_redirects=True,
        )
        if r.status_code >= 400:
            return None
        return _html_to_text(r.text)
    except ImportError:
        logger.debug("Enrichment: curl_cffi not installed, skipping tier 2.")
        return None
    except Exception as e:
        logger.debug(f"Enrichment: curl_cffi scrape failed for {url}: {e}")
        return None


_firecrawl_exhausted = False  # set to True on first 402, skips all further calls


def _firecrawl_scrape(url: str) -> Optional[str]:
    """
    Firecrawl scrape -- only called if FIRECRAWL_API_KEY is set and credits available.
    Used as upgrade for JS-heavy sites when httpx returns no useful content.
    Returns markdown text or None.
    """
    global _firecrawl_exhausted
    if _firecrawl_exhausted:
        return None
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        return None
    try:
        with httpx.Client(timeout=20) as client:
            r = client.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"url": url, "formats": ["markdown"]},
            )
            if r.status_code == 402:
                _firecrawl_exhausted = True
                logger.warning("Enrichment: Firecrawl credits exhausted -- switching to httpx-only mode.")
                return None
            r.raise_for_status()
        return r.json().get("data", {}).get("markdown", "")
    except Exception as e:
        logger.debug(f"Enrichment: Firecrawl scrape failed for {url}: {e}")
        return None


def _scrape_page(url: str) -> Optional[str]:
    """
    Three-tier scraper (all free):
      Tier 1 — httpx: fast, works on static sites (WordPress, Squarespace, Wix)
      Tier 2 — curl_cffi: Chrome fingerprint spoofing, bypasses Cloudflare/bot detection
      Tier 3 — Firecrawl: JS rendering, only if key present and credits available
    Each tier is tried only if the previous returned thin/no content.
    """
    # Tier 1: httpx
    text = _httpx_scrape(url)
    if text and len(text) > 300:
        return text

    # Tier 2: curl_cffi (browser fingerprint spoofing)
    curl_text = _curl_cffi_scrape(url)
    if curl_text and len(curl_text) > 300:
        return curl_text

    # Tier 3: Firecrawl (JS rendering, optional)
    fc_text = _firecrawl_scrape(url)
    if fc_text:
        return fc_text

    # Return best effort from what we got
    return curl_text or text


def _extract_emails_from_text(text: str, exclude_domains: list = None) -> list:
    """Extract all emails from text, filtering out common noise."""
    exclude_domains = exclude_domains or [
        "example.com", "domain.com", "email.com", "your@", "info@info",
        "sentry.io", "wix.com", "squarespace.com", "wordpress.com"
    ]
    found = EMAIL_REGEX.findall(text or "")
    cleaned = []
    for e in found:
        e = e.lower().strip(".")
        if any(d in e for d in exclude_domains):
            continue
        if e not in cleaned:
            cleaned.append(e)
    return cleaned


def _scrape_for_email(website_url: str) -> tuple:
    """
    Try to find an email by scraping the website.
    Returns (email_or_None, note_string, has_contact_form_only)
    """
    from urllib.parse import urlparse, urljoin

    parsed = urlparse(website_url if website_url.startswith("http") else f"https://{website_url}")
    base = f"{parsed.scheme}://{parsed.netloc}"
    domain = parsed.netloc.replace("www.", "")

    # Pages to try in order
    pages_to_try = [
        website_url,
        urljoin(base, "/contact"),
        urljoin(base, "/contact-us"),
        urljoin(base, "/about"),
        urljoin(base, "/about-us"),
    ]

    all_emails = []
    contact_form_only = False

    for page_url in pages_to_try:
        text = _scrape_page(page_url)
        if not text:
            continue
        emails = _extract_emails_from_text(text, exclude_domains=[domain])
        if emails:
            all_emails.extend(e for e in emails if e not in all_emails)
        # Detect contact-form-only pages
        if "contact form" in text.lower() or "fill out" in text.lower() or "submit" in text.lower():
            contact_form_only = True
        if all_emails:
            break  # Found something -- stop scraping

    if len(all_emails) == 1:
        return all_emails[0], f"Email found via Firecrawl on {domain}", False
    elif len(all_emails) > 1:
        return None, f"Multiple emails found -- review needed: {', '.join(all_emails[:3])}", False
    elif contact_form_only:
        return None, f"Contact form only on {domain} -- no email visible", False
    else:
        return None, f"No email found after scraping {domain}", False


# ── Database write helpers ───────────────────────────────────────

def _write_note(conn, lead_id: int, note: str):
    """Append note to leads.notes and insert lead_interactions row."""
    try:
        cur = conn.cursor()
        # Append to notes (don't overwrite existing notes)
        cur.execute("""
            UPDATE leads
            SET notes = CASE
                WHEN notes IS NULL OR notes = '' THEN %s
                ELSE notes || E'\n' || %s
            END,
            updated_at = %s
            WHERE id = %s
        """, (note, note, datetime.now(timezone.utc), lead_id))
        cur.execute("""
            INSERT INTO lead_interactions (lead_id, interaction_type, content)
            VALUES (%s, 'enrichment_attempt', %s)
        """, (lead_id, note))
        conn.commit()
        cur.close()
    except Exception as e:
        logger.error(f"Enrichment: failed to write note for lead {lead_id}: {e}")


def _save_email(conn, lead_id: int, email: str):
    """Save found email to leads table."""
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE leads SET email = %s, updated_at = %s WHERE id = %s",
            (email, datetime.now(timezone.utc), lead_id)
        )
        conn.commit()
        cur.close()
    except Exception as e:
        logger.error(f"Enrichment: failed to save email for lead {lead_id}: {e}")


def _save_linkedin(conn, lead_id: int, linkedin_url: str):
    """Save found LinkedIn URL to leads table."""
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE leads SET linkedin_url = %s, updated_at = %s WHERE id = %s",
            (linkedin_url, datetime.now(timezone.utc), lead_id)
        )
        conn.commit()
        cur.close()
    except Exception as e:
        logger.error(f"Enrichment: failed to save LinkedIn for lead {lead_id}: {e}")


def _save_phone(conn, lead_id: int, phone: str):
    """Save found phone number to leads table."""
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE leads SET phone = %s, updated_at = %s WHERE id = %s",
            (phone, datetime.now(timezone.utc), lead_id)
        )
        conn.commit()
        cur.close()
    except Exception as e:
        logger.error(f"Enrichment: failed to save phone for lead {lead_id}: {e}")


def _prospeo_enrich(name: str, company: str, linkedin_url: str = None,
                    want_phone: bool = True) -> dict:
    """
    Call Prospeo /enrich-person to find email and/or mobile number.

    Credit cost:
      - Email only: 1 credit
      - Phone (with or without email): 10 credits
      - No match: 0 credits charged

    Returns dict with keys: email, phone, source ('prospeo'), error
    """
    api_key = os.environ.get("PROSPEO_KEY")
    if not api_key:
        logger.warning("Enrichment: PROSPEO_KEY not set -- skipping Prospeo.")
        return {"email": None, "phone": None, "error": "no_key"}

    # Build data payload -- prefer LinkedIn URL for highest match rate
    data = {}
    if linkedin_url:
        data["linkedin_url"] = linkedin_url
    else:
        # Split name into first/last
        parts = name.strip().split()
        if len(parts) >= 2:
            data["first_name"] = parts[0]
            data["last_name"] = " ".join(parts[1:])
        else:
            data["full_name"] = name
        if company:
            data["company_name"] = company

    if not data:
        return {"email": None, "phone": None, "error": "insufficient_data"}

    payload = {"data": data}
    if want_phone:
        payload["enrich_mobile"] = True

    try:
        with httpx.Client(timeout=20) as client:
            r = client.post(
                "https://api.prospeo.io/enrich-person",
                headers={"X-KEY": api_key, "Content-Type": "application/json"},
                json=payload,
            )
        resp = r.json()
    except Exception as e:
        logger.warning(f"Enrichment: Prospeo request failed for {name}: {e}")
        return {"email": None, "phone": None, "error": str(e)}

    if resp.get("error"):
        code = resp.get("error_code", "unknown")
        logger.info(f"Enrichment: Prospeo no match for {name} ({company}): {code}")
        return {"email": None, "phone": None, "error": code}

    person = resp.get("person", {})

    # Extract email
    found_email = None
    email_data = person.get("email", {})
    if email_data.get("revealed") and email_data.get("email"):
        found_email = email_data["email"].lower().strip()

    # Extract mobile
    found_phone = None
    mobile_data = person.get("mobile", {})
    if mobile_data.get("revealed") and mobile_data.get("mobile"):
        found_phone = mobile_data.get("mobile_international") or mobile_data.get("mobile")

    return {"email": found_email, "phone": found_phone, "error": None}


# ── Main entry point ─────────────────────────────────────────────

def enrich_missing_emails(limit: int = 999) -> dict:
    """
    Deep enrichment pass for leads missing email, phone, or LinkedIn.

    Pipeline per lead:
      1. Serper -- find company website
      2. Web scrape -- extract email from /contact, /about, homepage (free)
      3. Prospeo /enrich-person -- email + mobile fallback (paid, only if still missing)
      4. Serper -- find LinkedIn profile URL

    Returns:
        dict with: processed, emails_found, phones_found, linkedin_found,
                   no_website, still_missing, web_prospects (list), results (list)
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logger.info("Enrichment: starting deep enrichment pass...")

    try:
        conn = _get_crm_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, company, email, phone, linkedin_url, industry, priority
            FROM leads
            WHERE (email IS NULL OR email = '')
               OR (linkedin_url IS NULL OR linkedin_url = '')
               OR (phone IS NULL AND email IS NOT NULL)
            ORDER BY created_at ASC
            LIMIT %s
        """, (limit,))
        leads = [dict(r) for r in cur.fetchall()]
        cur.close()
    except Exception as e:
        logger.error(f"Enrichment: failed to query leads: {e}")
        return {"processed": 0, "emails_found": 0, "phones_found": 0,
                "linkedin_found": 0, "no_website": 0, "still_missing": 0,
                "web_prospects": [], "results": []}

    processed = 0
    emails_found = 0
    phones_found = 0
    linkedin_found = 0
    no_website_count = 0
    web_prospects = []
    results = []

    def _enrich_one(lead: dict) -> dict:
        """Enrich a single lead. Runs in a thread pool — no shared mutable state."""
        lead_id = lead["id"]
        name = lead.get("name", "")
        company = lead.get("company", "")
        linkedin_url = lead.get("linkedin_url", "")
        has_email = bool(lead.get("email"))
        has_phone = bool(lead.get("phone"))
        has_linkedin = bool(linkedin_url)
        found_email = None
        found_phone = None
        found_linkedin = None
        is_web_prospect = False

        logger.info(f"Enrichment: processing {name} ({company})...")

        # ── Step 1: Find company website ────────────────────────
        website = _find_company_website(company)

        if not website and not has_email:
            note = f"[{today}] Enriched — no website found. Flagged as web prospect."
            _write_note(conn, lead_id, note)
            is_web_prospect = True
            logger.info(f"Enrichment: {company} -- no website found, flagged as web prospect")
        elif website and not has_email:
            # ── Step 2: Scrape website for email ─────────────────
            found_email, _scrape_note, _ = _scrape_for_email(website)
            if found_email:
                _save_email(conn, lead_id, found_email)
                has_email = True
                _write_note(conn, lead_id, f"[{today}] Enriched — email found via scrape: {found_email}")
            else:
                _write_note(conn, lead_id, f"[{today}] Enriched — no email found after scraping.")

        # ── Step 3: Prospeo fallback ─────────────────────────────
        is_priority = bool(lead.get("priority"))
        if not has_email:
            prospeo = _prospeo_enrich(
                name=name,
                company=company,
                linkedin_url=linkedin_url or None,
                want_phone=False,
            )
            if not prospeo.get("email") and is_priority and not has_phone:
                prospeo = _prospeo_enrich(
                    name=name,
                    company=company,
                    linkedin_url=linkedin_url or None,
                    want_phone=True,
                )
            if prospeo.get("email"):
                _save_email(conn, lead_id, prospeo["email"])
                has_email = True
                found_email = prospeo["email"]
                _write_note(conn, lead_id, f"[{today}] Enriched — email found via Prospeo: {prospeo['email']}")
            if prospeo.get("phone") and not has_phone:
                _save_phone(conn, lead_id, prospeo["phone"])
                has_phone = True
                found_phone = prospeo["phone"]
                _write_note(conn, lead_id, f"[{today}] Enriched — mobile found via Prospeo: {prospeo['phone']}")
            if not prospeo.get("email") and not prospeo.get("phone") and prospeo.get("error") not in ("no_key",):
                _write_note(conn, lead_id, f"[{today}] Enriched — Prospeo: no match ({prospeo.get('error', 'no_match')})")

        # ── Step 4: Find LinkedIn ────────────────────────────────
        if not has_linkedin:
            found_linkedin = _find_linkedin(name, company)
            if found_linkedin:
                _save_linkedin(conn, lead_id, found_linkedin)
                _write_note(conn, lead_id, f"[{today}] Enriched — LinkedIn: {found_linkedin}")

        return {
            "id": lead_id,
            "name": name,
            "company": company,
            "industry": lead.get("industry"),
            "email_found": found_email,
            "phone_found": found_phone,
            "linkedin_found": found_linkedin,
            "has_website": bool(website),
            "is_web_prospect": is_web_prospect,
        }

    # Run enrichment in parallel — 5 threads keeps Prospeo within rate limits
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(_enrich_one, lead): lead for lead in leads}
        for future in as_completed(futures):
            try:
                r = future.result()
            except Exception as e:
                lead = futures[future]
                logger.error(f"Enrichment: unhandled error for {lead.get('name')}: {e}")
                continue
            processed += 1
            if r["email_found"]:
                emails_found += 1
            if r["phone_found"]:
                phones_found += 1
            if r["linkedin_found"]:
                linkedin_found += 1
            if r["is_web_prospect"]:
                no_website_count += 1
                web_prospects.append({"name": r["name"], "company": r["company"], "industry": r["industry"]})
            results.append(r)

    conn.close()
    still_missing = sum(1 for r in results if not r["email_found"] and not r["phone_found"])

    logger.info(
        f"Enrichment: {processed} leads processed -- "
        f"{emails_found} emails found, {phones_found} phones found, "
        f"{linkedin_found} LinkedIn found, {no_website_count} no website, "
        f"{still_missing} still missing both."
    )

    return {
        "processed": processed,
        "emails_found": emails_found,
        "phones_found": phones_found,
        "linkedin_found": linkedin_found,
        "no_website": no_website_count,
        "still_missing": still_missing,
        "web_prospects": web_prospects,
        "results": results,
    }
