"""
crm_tool.py — Catalyst Growth Engine CRM
=========================================
Direct database interface for lead tracking.
All data stored in Supabase (leads, lead_interactions).
Agents use these functions to move prospects through the pipeline.

Pipeline statuses: new → messaged → replied → booked → paid

On every add_lead() call:
  1. Lead saved to Supabase leads table
  2. Discovery interaction logged to lead_interactions
  3. Notion CRM Leads database synced automatically (REST API)
"""

import os
import logging
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

# Notion CRM Leads database (agentsHQ > CRM Leads)
_NOTION_DB_ID = "619a842a-0e04-4cb3-8d17-19ec67c130f0"
_NOTION_API = "https://api.notion.com/v1"
_NOTION_VERSION = "2022-06-28"


def _notion_headers() -> dict:
    token = os.environ.get("NOTION_SECRET", "")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": _NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _sync_lead_to_notion(lead_data: dict, lead_id: int) -> bool:
    """
    Create a page in the Notion CRM Leads database for a new lead.
    Fires after Supabase insert. Fails silently so CRM write is never blocked.
    """
    try:
        industry_options = {
            "Legal", "Accounting", "Marketing Agency", "HVAC", "Plumbing", "Roofing"
        }
        industry = lead_data.get("industry", "Other")
        if industry not in industry_options:
            industry = "Other"

        source_options = {"Hunter", "Apollo", "Manual"}
        source = lead_data.get("source", "Hunter")
        if source not in source_options:
            source = "Manual"

        props = {
            "Name": {"title": [{"text": {"content": lead_data.get("name", "")}}]},
            "Company": {"rich_text": [{"text": {"content": lead_data.get("company", "")}}]},
            "Title": {"rich_text": [{"text": {"content": lead_data.get("title", "")}}]},
            "Location": {"rich_text": [{"text": {"content": lead_data.get("location", "")}}]},
            "Industry": {"select": {"name": industry}},
            "Source": {"select": {"name": source}},
            "Status": {"select": {"name": "new"}},
            "Lead Date": {"date": {"start": datetime.utcnow().strftime("%Y-%m-%d")}},
        }
        if lead_data.get("email"):
            props["Email"] = {"email": lead_data["email"]}
        if lead_data.get("phone"):
            props["Phone"] = {"phone_number": lead_data["phone"]}
        if lead_data.get("linkedin_url"):
            props["LinkedIn"] = {"url": lead_data["linkedin_url"]}

        payload = {
            "parent": {"database_id": _NOTION_DB_ID},
            "properties": props,
        }
        resp = httpx.post(
            f"{_NOTION_API}/pages",
            headers=_notion_headers(),
            json=payload,
            timeout=10,
        )
        if resp.status_code in (200, 201):
            logger.info(f"Notion sync: lead '{lead_data.get('name')}' added (Supabase ID {lead_id}).")
            return True
        else:
            logger.warning(f"Notion sync failed ({resp.status_code}): {resp.text[:200]}")
            return False
    except Exception as e:
        logger.warning(f"Notion sync error (non-blocking): {e}")
        return False


def _get_conn():
    """
    Return a CRM connection -- Supabase primary, local Postgres fallback.
    Logs a warning if falling back so we know a sync will be needed.
    """
    import sys
    import os
    app_dir = "/app"
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    from db import get_crm_connection_with_fallback
    conn, is_fallback = get_crm_connection_with_fallback()
    if is_fallback:
        logger.warning("CRM: writing to local Postgres fallback -- Supabase unreachable.")
    return conn


def add_lead(lead_data: dict) -> int:
    """
    Add a new lead to the CRM. Deduplicates by linkedin_url (if present)
    or by (lower(name), lower(company)). Returns existing ID if duplicate found.
    lead_data: {name, company, title, location, phone, linkedin_url, email, industry, source}
    Returns ID of new or existing lead, or 0 on failure.
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()

        # Check for existing lead before inserting
        linkedin_url = lead_data.get('linkedin_url', '').strip() if lead_data.get('linkedin_url') else ''
        name = lead_data.get('name', '').strip()
        company = lead_data.get('company', '').strip()

        if linkedin_url:
            cur.execute(
                "SELECT id FROM leads WHERE linkedin_url = %s LIMIT 1",
                (linkedin_url,)
            )
        else:
            cur.execute(
                "SELECT id FROM leads WHERE lower(name) = lower(%s) AND lower(company) = lower(%s) LIMIT 1",
                (name, company)
            )
        existing = cur.fetchone()
        if existing:
            logger.info(f"CRM add_lead: duplicate skipped for {name} / {company} (id={existing['id']})")
            cur.close()
            conn.close()
            return existing['id']

        cur.execute("""
            INSERT INTO leads (name, company, title, location, phone, linkedin_url, email, industry, source, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'new')
            RETURNING id
        """, (
            lead_data.get('name'),
            lead_data.get('company', 'Unknown'),
            lead_data.get('title'),
            lead_data.get('location'),
            lead_data.get('phone'),
            lead_data.get('linkedin_url'),
            lead_data.get('email'),
            lead_data.get('industry'),
            lead_data.get('source', 'Hunter'),
        ))
        lead_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()

        log_interaction(lead_id, 'discovery', f"Lead found via {lead_data.get('source', 'Hunter')}")
        _sync_lead_to_notion(lead_data, lead_id)
        return lead_id

    except Exception as e:
        logger.error(f"CRM add_lead failed: {e}")
        return 0


def log_interaction(lead_id: int, itype: str, content: str) -> bool:
    """
    Log an interaction with a lead.
    itype: discovery, outreach, outreach_draft, reply, note, email_revealed
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO lead_interactions (lead_id, interaction_type, content)
            VALUES (%s, %s, %s)
        """, (lead_id, itype, content))

        # outreach and outreach_draft both count as a contact touch
        if itype in ('outreach', 'outreach_draft'):
            cur.execute(
                "UPDATE leads SET status = 'messaged', last_contacted_at = %s, updated_at = %s WHERE id = %s",
                (datetime.utcnow(), datetime.utcnow(), lead_id)
            )
        elif itype in ('reply', 'note', 'email_revealed'):
            cur.execute(
                "UPDATE leads SET updated_at = %s WHERE id = %s",
                (datetime.utcnow(), lead_id)
            )

        conn.commit()
        cur.close()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"CRM log_interaction failed: {e}")
        return False


def update_lead_status(lead_id: int, new_status: str) -> bool:
    """
    Update a lead's pipeline status.
    new_status: new, messaged, replied, booked, paid
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE leads SET status = %s, updated_at = %s WHERE id = %s",
            (new_status, datetime.utcnow(), lead_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"CRM update_lead_status failed: {e}")
        return False


def update_lead_email(lead_id: int, email: str) -> bool:
    """
    Store a revealed email address for a lead.
    Called after Hunter.io or Apollo email reveal.
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE leads SET email = %s, updated_at = %s WHERE id = %s",
            (email, datetime.utcnow(), lead_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        log_interaction(lead_id, 'email_revealed', f"Email updated: {email}")
        return True

    except Exception as e:
        logger.error(f"CRM update_lead_email failed: {e}")
        return False


def get_lead_by_name(name: str, company: str = "") -> dict:
    """
    Find a lead by name (and optionally company) for targeted email reveals.
    Returns lead dict or empty dict if not found.
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
        if company:
            cur.execute(
                "SELECT * FROM leads WHERE LOWER(name) LIKE %s AND LOWER(company) LIKE %s LIMIT 1",
                (f"%{name.lower()}%", f"%{company.lower()}%")
            )
        else:
            cur.execute(
                "SELECT * FROM leads WHERE LOWER(name) LIKE %s LIMIT 1",
                (f"%{name.lower()}%",)
            )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row) if row else {}

    except Exception as e:
        logger.error(f"CRM get_lead_by_name failed: {e}")
        return {}


def get_uncontacted_leads(limit: int = 50) -> list:
    """
    Return leads who have never been contacted.
    Criteria: status = 'new' AND last_contacted_at IS NULL.
    Returns list of lead dicts ordered by created_at ASC (oldest first).
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, company, title, location, email, phone,
                   linkedin_url, industry, source, status, created_at
            FROM leads
            WHERE status = 'new' AND last_contacted_at IS NULL
            ORDER BY priority ASC NULLS LAST, created_at ASC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"CRM get_uncontacted_leads failed: {e}")
        return []


def mark_outreach_sent() -> dict:
    """
    Mark leads as messaged after you manually send their Gmail drafts.

    Finds leads that:
      - have an outreach_draft interaction logged today or yesterday
      - still have status = 'new' (not yet marked)
      - last_contacted_at IS NULL

    Sets status = 'messaged' and last_contacted_at = now for each.
    Returns: { "marked": int, "leads": [{"id", "name", "email"}] }
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT l.id, l.name, l.email
            FROM leads l
            JOIN lead_interactions li ON li.lead_id = l.id
            WHERE li.interaction_type = 'outreach_draft'
              AND li.created_at >= NOW() - INTERVAL '48 hours'
              AND l.status = 'new'
              AND l.last_contacted_at IS NULL
            ORDER BY l.id
        """)
        rows = [dict(r) for r in cur.fetchall()]
        if not rows:
            cur.close()
            conn.close()
            return {"marked": 0, "leads": []}

        now = datetime.utcnow()
        ids = [r["id"] for r in rows]
        cur.execute("""
            UPDATE leads
            SET status = 'messaged',
                last_contacted_at = %s,
                updated_at = %s
            WHERE id = ANY(%s)
        """, (now, now, ids))
        conn.commit()
        cur.close()
        conn.close()
        return {"marked": len(rows), "leads": rows}
    except Exception as e:
        logger.error(f"CRM mark_outreach_sent failed: {e}")
        return {"marked": 0, "leads": [], "error": str(e)}


def get_daily_scoreboard() -> dict:
    """
    Get today's sales velocity stats.
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE date(created_at) = CURRENT_DATE) as leads_found,
                COUNT(*) FILTER (WHERE status = 'messaged' AND date(updated_at) = CURRENT_DATE) as messages_sent,
                COUNT(*) FILTER (WHERE status = 'replied' AND date(updated_at) = CURRENT_DATE) as replies,
                COUNT(*) FILTER (WHERE status = 'booked' AND date(updated_at) = CURRENT_DATE) as booked,
                COUNT(*) FILTER (WHERE email IS NOT NULL) as with_email,
                COUNT(*) as total_leads
            FROM leads
        """)
        row = cur.fetchone()
        cur.close()
        conn.close()
        return {
            "leads_found": row['leads_found'],
            "messages_sent": row['messages_sent'],
            "replies": row['replies'],
            "booked": row['booked'],
            "with_email": row['with_email'],
            "total_leads": row['total_leads'],
            "revenue": 0,
        }

    except Exception as e:
        logger.error(f"CRM get_daily_scoreboard failed: {e}")
        return {}
