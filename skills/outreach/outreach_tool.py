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

Worth a conversation?"""

OUTREACH_ACCOUNT = "catalystworks.ai@gmail.com"

# ── Email signature (Option 3: The Constraint Remover) ───────────
SIGNATURE_HTML = """
<br>
<table cellpadding="0" cellspacing="0" border="0" style="font-family: Arial, Helvetica, sans-serif; max-width: 520px;">
  <tr>
    <td style="padding-bottom: 12px;">
      <table cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="padding-right: 16px; padding-bottom: 4px;" valign="top">
            <span style="font-size: 17px; font-weight: 800; color: #071A2E; letter-spacing: -0.02em; display: block; line-height: 1.2;">Boubacar Barry</span>
            <span style="font-size: 11px; color: #718096; font-weight: 500; display: block; margin-top: 2px;">Founder, Catalyst Works</span>
          </td>
          <td valign="top" style="border-left: 1px solid #E2E8F0; padding-left: 16px;">
            <span style="font-size: 11px; color: #4A5568; display: block; line-height: 1.5; max-width: 220px;">
              I help growing companies remove the constraint blocking their next stage of growth.
            </span>
          </td>
        </tr>
      </table>
    </td>
  </tr>
  <tr>
    <td style="padding-bottom: 12px;">
      <table cellpadding="0" cellspacing="0" border="0" width="100%">
        <tr><td style="height: 1px; background-color: #E8ECF0; font-size: 0; line-height: 0;">&nbsp;</td></tr>
      </table>
    </td>
  </tr>
  <tr>
    <td style="padding-bottom: 12px;">
      <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #071A2E; border-radius: 4px;">
        <tr>
          <td style="padding: 14px 20px;">
            <table cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td valign="middle">
                  <span style="font-size: 12px; color: rgba(255,255,255,0.85); font-weight: 500; line-height: 1.4; display: block;">
                    I help growing companies remove the constraint blocking their next stage of growth.
                  </span>
                  <span style="font-size: 10px; color: #00B7C2; font-weight: 600; display: block; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.06em;">
                    One conversation. No pitch.
                  </span>
                </td>
                <td valign="middle" align="right" style="padding-left: 16px;" width="160">
                  <a href="https://catalystworks.consulting" target="_blank"
                     style="display: inline-block; background-color: #FF7A00; color: #ffffff; font-size: 11px; font-weight: 700; text-decoration: none; padding: 9px 16px; border-radius: 3px; white-space: nowrap; letter-spacing: 0.02em;">
                    catalystworks.consulting
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </td>
  </tr>
  <tr>
    <td>
      <table cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="padding-right: 12px;">
            <a href="https://catalystworks.consulting" target="_blank"
               style="font-size: 11px; color: #00B7C2; text-decoration: none; font-weight: 600;">catalystworks.consulting</a>
          </td>
          <td style="color: #CBD5E0; font-size: 11px; padding-right: 12px;">&middot;</td>
          <td style="padding-right: 12px;">
            <a href="https://boubacarbarry.com" target="_blank"
               style="font-size: 11px; color: #718096; text-decoration: none;">boubacarbarry.com</a>
          </td>
          <td style="color: #CBD5E0; font-size: 11px; padding-right: 12px;">&middot;</td>
          <td>
            <a href="mailto:catalystworks.ai@gmail.com"
               style="font-size: 11px; color: #718096; text-decoration: none;">catalystworks.ai@gmail.com</a>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
"""


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
    """Create a Gmail draft via API as pure HTML with signature. Returns draft ID or None on failure."""
    import httpx
    try:
        token = _get_access_token()

        # Convert plain text body to HTML paragraphs, then append signature
        paragraphs = body.strip().split("\n\n")
        html_body = "".join(
            f"<p style='margin: 0 0 16px 0;'>{p.replace(chr(10), '<br>')}</p>"
            for p in paragraphs
        )
        html = (
            "<html><body>"
            "<div style='font-family: Arial, Helvetica, sans-serif; font-size: 14px; "
            "color: #1a1a1a; line-height: 1.7; max-width: 600px;'>"
            f"{html_body}"
            "</div>"
            f"{SIGNATURE_HTML}"
            "</body></html>"
        )

        msg = MIMEText(html, "html")
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
