"""
enrichment_tool.py — Post-Harvest Email Enrichment
====================================================
Runs automatically after the daily lead harvest, before the report
email is sent. Finds all CRM leads missing an email address and
attempts to reveal them via Hunter.io then Apollo.

Pipeline per lead:
  1. Hunter.io email-finder (uses name + domain from LinkedIn URL)
  2. Apollo people/match (uses linkedin_url directly, costs 1 credit)

Results are saved back to Supabase leads table and logged in
lead_interactions. The daily report then shows full email coverage.

Called by: scheduler._run_daily_harvest() (after discover, before send)
Also callable standalone: enrich_missing_emails()
"""

import logging
import sys
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Industry bracket map -- matches cold outreach SKILL.md
INDUSTRY_BRACKET = {
    "Legal": "legal services",
    "Accounting": "accounting",
    "Marketing Agency": "agency",
    "HVAC": "trades",
    "Plumbing": "trades",
    "Roofing": "trades",
}


def _get_crm_conn():
    if "/app" not in sys.path:
        sys.path.insert(0, "/app")
    from db import get_crm_connection_with_fallback
    conn, is_fallback = get_crm_connection_with_fallback()
    if is_fallback:
        logger.warning("Enrichment: using local Postgres fallback.")
    return conn


def _reveal_via_hunter(name: str, linkedin_url: str = "", company: str = "") -> Optional[str]:
    """Hunter.io email-finder by domain + name. Free tier."""
    import httpx
    api_key = os.environ.get("HUNTER_API_KEY")
    if not api_key:
        return None

    # Extract domain from LinkedIn URL (won't work) or company website
    # For LinkedIn-only leads we skip Hunter and go straight to Apollo
    if not linkedin_url or "linkedin.com" in linkedin_url:
        return None

    try:
        from urllib.parse import urlparse
        domain = urlparse(linkedin_url if linkedin_url.startswith("http") else f"https://{linkedin_url}").netloc.replace("www.", "")
        if not domain or "linkedin.com" in domain:
            return None

        name_parts = name.strip().split()
        params = {
            "domain": domain,
            "api_key": api_key,
            "first_name": name_parts[0] if name_parts else "",
            "last_name": name_parts[-1] if len(name_parts) > 1 else "",
        }
        with httpx.Client(timeout=10) as client:
            r = client.get("https://api.hunter.io/v2/email-finder", params=params)
            r.raise_for_status()
        email = r.json().get("data", {}).get("email")
        if email:
            logger.info(f"Enrichment: Hunter found {email} for {name}")
        return email
    except Exception as e:
        logger.warning(f"Enrichment: Hunter failed for {name}: {e}")
        return None


def _reveal_via_apollo(name: str, linkedin_url: str = "") -> Optional[str]:
    """
    Apollo people/match by linkedin_url.
    NOTE: Requires Apollo paid plan (people/match endpoint).
    Returns None gracefully if 403 -- does not crash enrichment run.
    """
    import httpx
    api_key = os.environ.get("APOLLO_API_KEY")
    if not api_key or not linkedin_url:
        return None
    try:
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": api_key,
            "Cache-Control": "no-cache",
        }
        with httpx.Client(timeout=15) as client:
            r = client.post(
                "https://api.apollo.io/v1/people/match",
                json={"linkedin_url": linkedin_url},
                headers=headers,
            )
            if r.status_code == 403:
                # Paid endpoint -- skip silently
                return None
            r.raise_for_status()
        email = r.json().get("person", {}).get("email")
        if email:
            logger.info(f"Enrichment: Apollo found {email} for {name}")
        return email
    except Exception as e:
        logger.warning(f"Enrichment: Apollo failed for {name}: {e}")
        return None


def enrich_missing_emails(limit: int = 50) -> dict:
    """
    Find all CRM leads without an email, try Hunter.io then Apollo,
    save any found emails back to Supabase, log each reveal.

    Args:
        limit: max leads to process per run (default 50)

    Returns:
        dict with keys: processed, found, skipped, results (list of dicts)
    """
    logger.info("Enrichment: starting email enrichment pass...")

    try:
        conn = _get_crm_conn()
        cur = conn.cursor()

        # Get leads with no email
        cur.execute("""
            SELECT id, name, company, linkedin_url, industry
            FROM leads
            WHERE email IS NULL OR email = ''
            ORDER BY created_at ASC
            LIMIT %s
        """, (limit,))
        leads = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Enrichment: failed to query leads: {e}")
        return {"processed": 0, "found": 0, "skipped": 0, "results": []}

    processed = 0
    found = 0
    results = []

    for lead in leads:
        lead_id = lead["id"]
        name = lead.get("name", "")
        linkedin_url = lead.get("linkedin_url", "")
        company = lead.get("company", "")
        processed += 1

        # Try Hunter first, then Apollo
        email = _reveal_via_hunter(name, linkedin_url, company)
        if not email:
            email = _reveal_via_apollo(name, linkedin_url)

        if email:
            found += 1
            try:
                conn = _get_crm_conn()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE leads SET email = %s, updated_at = %s WHERE id = %s",
                    (email, datetime.utcnow(), lead_id)
                )
                cur.execute(
                    "INSERT INTO lead_interactions (lead_id, interaction_type, content) VALUES (%s, %s, %s)",
                    (lead_id, "email_revealed", f"Email enriched post-harvest: {email}")
                )
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                logger.error(f"Enrichment: failed to save email for lead {lead_id}: {e}")

            results.append({"id": lead_id, "name": name, "company": company, "email": email})
        else:
            results.append({"id": lead_id, "name": name, "company": company, "email": None})

    skipped = processed - found
    logger.info(f"Enrichment: {processed} leads processed, {found} emails found, {skipped} still missing.")
    return {"processed": processed, "found": found, "skipped": skipped, "results": results}
