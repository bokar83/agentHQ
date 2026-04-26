"""
outreach_tool.py -- Direct Cold Outreach from Supabase
======================================================
Reads ONLY from the Supabase leads table. No agent, no guessing.

Rules:
  - Source: Supabase leads table only (via db.py)
  - Eligibility: email IS NOT NULL, status = 'new', last_contacted_at IS NULL
  - Default batch: 10 leads per run
  - "contact all": up to 50 leads per run
  - Gmail: catalystworks.ai@gmail.com via OAuth refresh token (same as GWS tools)
  - Template: loaded from templates/email/cold_outreach.py (single source of truth)
  - Logs every draft to lead_interactions (type: outreach_draft)
  - Updates email_drafted_at on each lead

Called by: engine.run_orchestrator when task_type == 'crm_outreach'
           Also importable standalone for testing.
"""

import os
import sys
import base64
import json
import logging
import importlib.util
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)

# -- Email template -- loaded by absolute path, no sys.path dependency ----
# To change the template, edit ONLY: templates/email/cold_outreach.py
_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'templates', 'email', 'cold_outreach.py')
_spec = importlib.util.spec_from_file_location('cold_outreach', os.path.abspath(_TEMPLATE_PATH))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
SUBJECT = _mod.SUBJECT
TEMPLATE = _mod.BODY

OUTREACH_ACCOUNT = "catalystworks.ai@gmail.com"


# -- Database helpers ---------------------------------------------

def _get_conn():
    if "/app" not in sys.path:
        sys.path.insert(0, "/app")
    from db import get_crm_connection_with_fallback
    conn, is_fallback = get_crm_connection_with_fallback()
    if is_fallback:
        logger.warning("Outreach: using local Postgres fallback.")
    return conn


_TITLE_PATTERNS = [
    "%owner%", "%founder%", "%ceo%", "%president%",
    "%managing%", "%principal%", "%coo%", "%partner%", "%attorney%",
]

_INDUSTRY_PATTERNS = [
    "%consult%", "%legal%", "%account%", "%engineer%", "%health%",
    "%market%", "%agenc%", "%logistic%", "%trade%", "%service%",
    "%hvac%", "%roofing%", "%plumbing%", "%electrical%", "%construction%",
]


def _get_eligible_leads(limit: int) -> list:
    conn = _get_conn()
    cur = conn.cursor()

    title_clause = " OR ".join(
        "LOWER(title) LIKE %s" for _ in _TITLE_PATTERNS
    )
    industry_clause = " OR ".join(
        "LOWER(industry) LIKE %s" for _ in _INDUSTRY_PATTERNS
    )

    query = f"""
        SELECT id, name, company, title, industry, email, linkedin_url
        FROM leads
        WHERE email IS NOT NULL
          AND email != ''
          AND status = 'new'
          AND email_drafted_at IS NULL
          AND last_contacted_at IS NULL
          AND ({title_clause})
          AND ({industry_clause})
        ORDER BY created_at ASC
        LIMIT %s
    """

    params = tuple(_TITLE_PATTERNS) + tuple(_INDUSTRY_PATTERNS) + (limit,)
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


# -- Gmail helpers ------------------------------------------------

def _get_access_token() -> str:
    import httpx
    creds_path = os.environ.get(
        "GOOGLE_OAUTH_CREDENTIALS_JSON_CW",
        "/app/secrets/gws-oauth-credentials-cw.json"
    )
    with open(creds_path) as f:
        creds = json.load(f)

    resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"],
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _create_draft(to_email: str, subject: str, body: str) -> Optional[str]:
    """Create a Gmail draft as plain text. Returns draft ID or None on failure."""
    import httpx
    try:
        token = _get_access_token()
        msg = MIMEText(body, "plain")
        msg["to"] = to_email
        msg["from"] = OUTREACH_ACCOUNT
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        resp = httpx.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/drafts",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": {"raw": raw}},
            timeout=20,
        )
        resp.raise_for_status()
        draft_id = resp.json().get("id")
        logger.info(f"Outreach: draft created for {to_email} (id: {draft_id})")
        return draft_id
    except Exception as e:
        logger.error(f"Outreach: Gmail draft failed for {to_email}: {e}")
        return None


def _sync_notion_contacted(notion_db_id: str, lead_name: str, contacted_date: str):
    """Update a lead's Notion page to contacted + set Last Contacted. Fails silently."""
    try:
        import httpx as _httpx
        import os as _os
        token = _os.environ.get("NOTION_SECRET", "")
        if not token:
            logger.warning("Outreach: NOTION_SECRET not set, skipping Notion sync.")
            return
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        r = _httpx.post(
            f"https://api.notion.com/v1/databases/{notion_db_id}/query",
            headers=headers,
            json={"filter": {"property": "Name", "title": {"equals": lead_name}}},
            timeout=15,
        )
        if r.status_code != 200 or not r.json().get("results"):
            logger.warning(f"Outreach Notion sync: '{lead_name}' not found ({r.status_code})")
            return
        page_id = r.json()["results"][0]["id"]
        u = _httpx.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=headers,
            json={"properties": {
                "Status": {"select": {"name": "contacted"}},
                "Last Contacted": {"date": {"start": contacted_date}},
            }},
            timeout=15,
        )
        if u.status_code == 200:
            logger.info(f"Outreach Notion sync: '{lead_name}' updated to contacted.")
        else:
            logger.warning(f"Outreach Notion sync: update failed for '{lead_name}' ({u.status_code})")
    except Exception as e:
        logger.warning(f"Outreach Notion sync error (non-blocking): {e}")


_NOTION_DB_ID = "619a842a-0e04-4cb3-8d17-19ec67c130f0"


def _log_and_update(lead_id: int, subject: str, lead_name: str = ""):
    """Log outreach_draft interaction and stamp email_drafted_at."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO lead_interactions (lead_id, interaction_type, content)
            VALUES (%s, 'outreach_draft', %s)
        """, (lead_id, subject))
        now = datetime.now(timezone.utc)
        cur.execute("""
            UPDATE leads
            SET email_drafted_at = %s,
                status = 'messaged',
                last_contacted_at = %s,
                updated_at = %s
            WHERE id = %s
        """, (now, now, now, lead_id))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Outreach: draft stamped for lead {lead_id} ({lead_name}).")
    except Exception as e:
        logger.error(f"Outreach: CRM update failed for lead {lead_id}: {e}")


# -- Main entry point ---------------------------------------------

def run_outreach(contact_all: bool = False) -> dict:
    """
    Create Gmail drafts for uncontacted leads with confirmed emails.

    Args:
        contact_all: if True, process up to 50 leads; default is 10

    Returns:
        dict with drafted, skipped, results list
    """
    limit = 50 if contact_all else 20
    logger.info(f"Outreach: fetching up to {limit} uncontacted leads from Supabase...")

    try:
        leads = _get_eligible_leads(limit)
    except Exception as e:
        logger.error(f"Outreach: failed to fetch leads: {e}")
        return {"drafted": 0, "skipped": 0, "results": [], "error": str(e)}

    if not leads:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as n FROM leads WHERE status = 'new' AND (email IS NULL OR email = '')")
        no_email_count = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) as n FROM leads WHERE email_drafted_at IS NOT NULL")
        drafted_count = cur.fetchone()["n"]
        cur.close()
        conn.close()
        msg = (
            f"No eligible leads to draft. "
            f"{drafted_count} already sent. "
            f"{no_email_count} leads in CRM have no email address (enrichment returned nothing). "
            f"Run 'find leads' to source fresh leads with emails."
        )
        logger.info(f"Outreach: {msg}")
        return {"drafted": 0, "skipped": 0, "results": [], "error": None, "message": msg}

    drafted = 0
    skipped = 0
    results = []

    for lead in leads:
        email = lead.get("email", "").strip()
        name = lead.get("name", "").strip()
        company = lead.get("company", "").strip()
        industry = lead.get("industry", "Other")
        first_name = name.split()[0] if name else "there"

        body = TEMPLATE.format(first_name=first_name)
        draft_id = _create_draft(email, SUBJECT, body)
        if draft_id:
            _log_and_update(lead["id"], SUBJECT, lead_name=name)
            drafted += 1
            results.append({
                "name": name,
                "company": company,
                "email": email,
                "industry": industry,
                "subject": SUBJECT,
                "draft_id": draft_id,
                "status": "drafted",
            })
        else:
            skipped += 1
            results.append({
                "name": name,
                "company": company,
                "email": email,
                "status": "failed",
            })

    logger.info(f"Outreach: {drafted} drafts created, {skipped} failed.")
    return {"drafted": drafted, "skipped": skipped, "results": results, "error": None}
