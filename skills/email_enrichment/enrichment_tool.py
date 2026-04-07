"""
enrichment_tool.py — Deep Lead Enrichment Pipeline
===================================================
Runs after daily harvest, before the report email is sent.
For every lead missing an email or LinkedIn URL, attempts to find them
using Serper (search) and Firecrawl (scrape). Writes notes back to
Supabase in all cases -- found, not found, no website, ambiguous.

Pipeline per lead:
  1. Serper: "[Name]" "[Company]" contact email  -> find company website
  2. Firecrawl: scrape /contact, /about, homepage -> extract email
  3. Serper: "[Name]" "[Company]" site:linkedin.com/in -> find LinkedIn
  4. If no website found at all: flag as web prospect in notes

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


def _find_company_website(company: str) -> Optional[str]:
    """Search for the company's website. Returns domain or None."""
    results = _serper_search(f'"{company}" contact')
    for r in results:
        link = r.get("link", "")
        # Skip social, directories, review sites
        skip = ["linkedin.com", "facebook.com", "yelp.com", "bbb.org",
                "yellowpages.com", "google.com", "instagram.com", "twitter.com"]
        if any(s in link for s in skip):
            continue
        if link.startswith("http"):
            return link
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


def _httpx_scrape(url: str) -> Optional[str]:
    """
    Fetch a URL directly with httpx and extract visible text.
    Handles: static HTML, basic redirects, common encodings.
    Returns plain text (tags stripped) or None on failure.
    """
    try:
        with httpx.Client(timeout=15, follow_redirects=True, headers=_SCRAPE_HEADERS) as client:
            r = client.get(url)
            if r.status_code >= 400:
                return None
            html = r.text

        # Strip scripts and styles first
        html = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        # Replace common block tags with newlines to preserve structure
        html = re.sub(r"<(br|p|div|li|tr|h[1-6])[^>]*>", "\n", html, flags=re.IGNORECASE)
        # Strip remaining tags
        html = re.sub(r"<[^>]+>", " ", html)
        # Decode HTML entities
        html = html.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">") \
                   .replace("&#64;", "@").replace("&#46;", ".").replace("&nbsp;", " ")
        # Collapse whitespace
        html = re.sub(r"[ \t]+", " ", html)
        html = re.sub(r"\n{3,}", "\n\n", html)
        return html.strip()
    except Exception as e:
        logger.debug(f"Enrichment: httpx scrape failed for {url}: {e}")
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
    Unified scraper: httpx first (free), Firecrawl fallback if httpx
    returns no useful content (JS-heavy sites).
    """
    text = _httpx_scrape(url)
    # If httpx got content and it looks like real page text (>200 chars), use it
    if text and len(text) > 200:
        return text
    # Fallback to Firecrawl for JS-rendered pages
    fc_text = _firecrawl_scrape(url)
    if fc_text:
        return fc_text
    return text  # return whatever httpx got, even if thin


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


# ── Main entry point ─────────────────────────────────────────────

def enrich_missing_emails(limit: int = 999) -> dict:
    """
    Deep enrichment pass for leads missing email or LinkedIn.
    Uses Serper + Firecrawl. Writes notes back in all cases.
    Flags leads with no website as web prospects.

    Returns:
        dict with: processed, emails_found, linkedin_found,
                   no_website, still_missing, web_prospects (list), results (list)
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logger.info("Enrichment: starting deep enrichment pass...")

    try:
        conn = _get_crm_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, company, email, linkedin_url, industry
            FROM leads
            WHERE (email IS NULL OR email = '')
               OR (linkedin_url IS NULL OR linkedin_url = '')
            ORDER BY created_at ASC
            LIMIT %s
        """, (limit,))
        leads = [dict(r) for r in cur.fetchall()]
        cur.close()
    except Exception as e:
        logger.error(f"Enrichment: failed to query leads: {e}")
        return {"processed": 0, "emails_found": 0, "linkedin_found": 0,
                "no_website": 0, "still_missing": 0, "web_prospects": [], "results": []}

    processed = 0
    emails_found = 0
    linkedin_found = 0
    no_website_count = 0
    web_prospects = []
    results = []

    for lead in leads:
        lead_id = lead["id"]
        name = lead.get("name", "")
        company = lead.get("company", "")
        has_email = bool(lead.get("email"))
        has_linkedin = bool(lead.get("linkedin_url"))
        processed += 1
        found_email = None
        found_linkedin = None

        logger.info(f"Enrichment: processing {name} ({company})...")

        # ── Step 1: Find company website ────────────────────────
        website = _find_company_website(company)

        if not website:
            note = f"[{today}] Enriched — no website found. Flagged as web prospect."
            _write_note(conn, lead_id, note)
            no_website_count += 1
            web_prospects.append({"name": name, "company": company, "industry": lead.get("industry")})
            logger.info(f"Enrichment: {company} -- no website found, flagged as web prospect")
        else:
            # ── Step 2: Scrape for email ─────────────────────────
            if not has_email:
                found_email, scrape_note, _ = _scrape_for_email(website)
                if found_email:
                    _save_email(conn, lead_id, found_email)
                    emails_found += 1
                    has_email = True
                    _write_note(conn, lead_id, f"[{today}] Enriched — email found: {found_email}")
                else:
                    _write_note(conn, lead_id, f"[{today}] Enriched — no email found after scraping.")

        # ── Step 3: Find LinkedIn ────────────────────────────────
        if not has_linkedin:
            found_linkedin = _find_linkedin(name, company)
            if found_linkedin:
                _save_linkedin(conn, lead_id, found_linkedin)
                linkedin_found += 1
                _write_note(conn, lead_id, f"[{today}] Enriched — LinkedIn: {found_linkedin}")
            else:
                _write_note(conn, lead_id, f"[{today}] Enriched — LinkedIn not found.")

        results.append({
            "id": lead_id,
            "name": name,
            "company": company,
            "email_found": found_email,
            "linkedin_found": found_linkedin,
            "has_website": bool(website),
        })

    conn.close()
    still_missing = processed - emails_found - no_website_count

    logger.info(
        f"Enrichment: {processed} leads processed -- "
        f"{emails_found} emails found, {linkedin_found} LinkedIn found, "
        f"{no_website_count} no website (web prospects), {still_missing} still missing email."
    )

    return {
        "processed": processed,
        "emails_found": emails_found,
        "linkedin_found": linkedin_found,
        "no_website": no_website_count,
        "still_missing": still_missing,
        "web_prospects": web_prospects,
        "results": results,
    }
