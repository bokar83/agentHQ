"""
crm_tool.py — Catalyst Growth Engine CRM Logic
==============================================
This skill provides the direct database interface for lead tracking.
Agents should use these functions to move prospects through the pipeline.
"""

import os
import logging
import psycopg2
from datetime import datetime

logger = logging.getLogger(__name__)

def _get_pg_conn():
    """Return a psycopg2 connection using env vars."""
    # Try POSTGRES_HOST first (container name in docker), 
    # then VPS_IP if running externally, then localhost.
    host = os.environ.get("POSTGRES_HOST") or os.environ.get("VPS_IP") or "localhost"
    
    return psycopg2.connect(
        host=host,
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "agentsHQ10kday"),
        port=5432
    )

def add_lead(lead_data: dict) -> int:
    """
    Add a new lead to the CRM.
    lead_data: {name, company, title, location, linkedin_url, email, source}
    Returns ID of new lead.
    """
    try:
        conn = _get_pg_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO leads (name, company, title, location, linkedin_url, email, source, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'new')
            RETURNING id
        """, (
            lead_data.get('name'),
            lead_data.get('company'),
            lead_data.get('title'),
            lead_data.get('location'),
            lead_data.get('linkedin_url'),
            lead_data.get('email', ''),
            lead_data.get('source', 'apollo')
        ))
        lead_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        # Log discovery interaction
        log_interaction(lead_id, 'discovery', f"Lead found via {lead_data.get('source', 'apollo')}")
        
        return lead_id
    except Exception as e:
        logger.error(f"CRM add_lead failed: {e}")
        return 0

def log_interaction(lead_id: int, itype: str, content: str) -> bool:
    """
    Log an interaction with a lead.
    itype: outreach, reply, note, discovery
    """
    try:
        conn = _get_pg_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO lead_interactions (lead_id, interaction_type, content)
            VALUES (%s, %s, %s)
        """, (lead_id, itype, content))
        
        # If it was outreach, update lead status to 'messaged'
        if itype == 'outreach':
            cur.execute("UPDATE leads SET status = 'messaged', updated_at = %s WHERE id = %s", (datetime.utcnow(), lead_id))
        
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
        conn = _get_pg_conn()
        cur = conn.cursor()
        cur.execute("UPDATE leads SET status = %s, updated_at = %s WHERE id = %s", (new_status, datetime.utcnow(), lead_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"CRM update_lead_status failed: {e}")
        return False

def get_daily_scoreboard() -> dict:
    """
    Get today's sales velocity stats.
    """
    try:
        conn = _get_pg_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE date(created_at) = CURRENT_DATE) as leads_found,
                COUNT(*) FILTER (WHERE status = 'messaged' AND date(updated_at) = CURRENT_DATE) as messages_sent,
                COUNT(*) FILTER (WHERE status = 'replied' AND date(updated_at) = CURRENT_DATE) as replies,
                COUNT(*) FILTER (WHERE status = 'booked' AND date(updated_at) = CURRENT_DATE) as booked
            FROM leads
        """)
        row = cur.fetchone()
        cur.close()
        conn.close()
        return {
            "leads_found": row[0],
            "messages_sent": row[1],
            "replies": row[2],
            "booked": row[3],
            "revenue": 0 # Placeholder if revenue isn't tracked in postgres
        }
    except Exception as e:
        logger.error(f"CRM get_daily_scoreboard failed: {e}")
        return {}
