"""
outreach_tool.py — Direct Cold Outreach from Supabase
======================================================
Reads ONLY from the Supabase leads table. No agent, no guessing.

Rules:
  - Source: Supabase leads table only (via db.py)
  - Eligibility: email IS NOT NULL, status = 'new', last_contacted_at IS NULL
  - Default batch: 5 leads per run
  - "contact all": up to 50 leads per run
  - Gmail: catalystworks.ai@gmail.com via OAuth refresh token (same as GWS tools)
  - Template: cold outreach skill, Template A (sector bracket by industry)
  - Logs every draft to lead_interactions (type: outreach_draft)
  - Updates last_contacted_at and status = 'messaged' on each lead

Called by: orchestrator.py when task_type == 'crm_outreach'
           Also importable standalone for testing.
"""

import os
import sys
import base64
import json
import logging
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)

# ── Email template ──────────────────────────────────────────────
SUBJECT = "Where is your margin actually going?"

TEMPLATE = """Hi {first_name},

I'll keep this simple.

Most businesses aren't losing margin to bad strategy. They're losing it to one bottleneck that often goes unnamed: a handoff, an approval loop, a pricing gap quietly taxing everything downstream.

I'm Boubacar Barry, founder of Catalyst Works. I work with the people running the business day to day to find that bottleneck and build a clear path to removing it. Over 15 years working with leadership teams across three continents, the constraint is almost always findable, and almost always fixable faster than people expect.

I'd love a quick 20-minute conversation to hear what's going on in your business and see if there's something worth exploring together. No pitch, no prep required on your end.

Worth a conversation?

Boubacar
catalystworks.consulting"""

OUTREACH_ACCOUNT = "catalystworks.ai@gmail.com"


# ── Database helpers ─────────────────────────────────────────────

def _get_conn():
    if "/app" not in sys.path:
        sys.path.insert(0, "/app")
    from db import get_crm_connection_with_fallback
    conn, is_fallback = get_crm_connection_with_fallback()
    if is_fallback:
        logger.warning("Outreach: using local Postgres fallback.")
    return conn


def _get_eligible_leads(limit: int) -> list:
    """
    Pull leads from Supabase who:
      - have a confirmed email address
      - have never been contacted (last_contacted_at IS NULL)
      - status = 'new'
    Ordered oldest first.
    """
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, company, title, industry, email, linkedin_url
        FROM leads
        WHERE email IS NOT NULL
          AND email != ''
          AND status = 'new'
          AND last_contacted_at IS NULL
        ORDER BY created_at ASC
        LIMIT %s
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


# ── Gmail helpers ────────────────────────────────────────────────

def _get_access_token() -> str:
    """Refresh OAuth token for catalystworks.ai@gmail.com."""
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
    """Create a Gmail draft via API. Returns draft ID or None on failure."""
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


def _log_and_update(lead_id: int, subject: str):
    """Log outreach_draft interaction and update lead status + last_contacted_at."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO lead_interactions (lead_id, interaction_type, content)
            VALUES (%s, 'outreach_draft', %s)
        """, (lead_id, subject))
        cur.execute("""
            UPDATE leads
            SET status = 'messaged',
                last_contacted_at = %s,
                updated_at = %s
            WHERE id = %s
        """, (datetime.now(timezone.utc), datetime.now(timezone.utc), lead_id))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Outreach: CRM update failed for lead {lead_id}: {e}")


# ── Main entry point ─────────────────────────────────────────────

def run_outreach(contact_all: bool = False) -> dict:
    """
    Create Gmail drafts for uncontacted leads with confirmed emails.

    Args:
        contact_all: if True, process up to 50 leads; default is 5

    Returns:
        dict with drafted, skipped, results list
    """
    limit = 50 if contact_all else 5
    logger.info(f"Outreach: fetching up to {limit} uncontacted leads from Supabase...")

    try:
        leads = _get_eligible_leads(limit)
    except Exception as e:
        logger.error(f"Outreach: failed to fetch leads: {e}")
        return {"drafted": 0, "skipped": 0, "results": [], "error": str(e)}

    if not leads:
        logger.info("Outreach: no eligible leads found.")
        return {"drafted": 0, "skipped": 0, "results": [], "error": None}

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
            _log_and_update(lead["id"], SUBJECT)
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
