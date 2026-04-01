"""
crm_tool.py — Catalyst Growth Engine CRM
=========================================
Direct database interface for lead tracking.
All data stored in Supabase (leads, lead_interactions).
Agents use these functions to move prospects through the pipeline.

Pipeline statuses: new → messaged → replied → booked → paid
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def _get_conn():
    """Return a Supabase CRM connection via the centralized db utility."""
    import sys
    import os
    # Ensure orchestrator/ is on path when running inside container
    app_dir = "/app"
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    from db import get_crm_connection
    return get_crm_connection()


def add_lead(lead_data: dict) -> int:
    """
    Add a new lead to the CRM.
    lead_data: {name, company, title, location, phone, linkedin_url, email, industry, source}
    Returns ID of new lead, or 0 on failure.
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
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
            lead_data.get('source', 'serper'),
        ))
        lead_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()

        log_interaction(lead_id, 'discovery', f"Lead found via {lead_data.get('source', 'serper')}")
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

        if itype == 'outreach':
            cur.execute(
                "UPDATE leads SET status = 'messaged', updated_at = %s WHERE id = %s",
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
