"""
signal_works/topup_cw_leads.py
Harvests fresh Catalyst Works CRM leads via Apollo.io.

Apollo search is free; email reveal costs 1 credit per person.
Only reveals email for leads that pass CW ICP scoring (score >= 2).

Usage:
  python -m signal_works.topup_cw_leads
  python -m signal_works.topup_cw_leads --minimum 15
  python -m signal_works.topup_cw_leads --dry-run
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv(override=True)

from skills.apollo_skill.apollo_client import harvest_leads, CW_ICP_WIDENED
try:
    from orchestrator.db import get_crm_connection, ensure_leads_columns, get_resend_queue
except ModuleNotFoundError:
    sys.path.insert(0, "/app")
    from db import get_crm_connection, ensure_leads_columns, get_resend_queue

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DAILY_MINIMUM = 20


def _count_ready_cw_leads(conn) -> int:
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as n FROM leads
        WHERE source IS DISTINCT FROM 'signal_works'
          AND email IS NOT NULL AND email != ''
          AND LOWER(status) = 'new'
          AND last_contacted_at IS NULL
          AND email_drafted_at IS NULL
    """)
    return cur.fetchone()["n"]


def _is_duplicate(conn, email: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM leads WHERE email ILIKE %s LIMIT 1", (email,))
    return cur.fetchone() is not None


def _save_cw_lead(conn, lead: dict) -> bool:
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO leads
              (name, company, title, industry, email, linkedin_url, city,
               website_url, status, source, created_at, updated_at)
            VALUES
              (%s, %s, %s, %s, %s, %s, %s,
               %s, 'new', %s, NOW(), NOW())
            ON CONFLICT DO NOTHING
        """, (
            lead.get("name"),
            lead.get("company"),
            lead.get("title"),
            lead.get("industry"),
            lead.get("email"),
            lead.get("linkedin_url"),
            lead.get("city"),
            lead.get("website_url"),
            lead.get("source", "apollo_cw"),
        ))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        logger.warning(f"Failed to save lead {lead.get('company')}: {e}")
        return False


def topup_cw_leads(minimum: int = DAILY_MINIMUM, dry_run: bool = False) -> int:
    """Hybrid CW lead topup: 5 fresh from Apollo (widened ICP) + 5 resends.

    If resend queue returns fewer than 5, top up the gap from Apollo so we
    always hit `minimum`.
    """
    conn = get_crm_connection()
    try:
        ensure_leads_columns(conn)
    except Exception as e:
        logger.warning(f"topup_cw_leads: ensure_leads_columns failed: {e}")
    ready = _count_ready_cw_leads(conn)
    logger.info(f"CW topup: {ready} ready leads (target: {minimum})")
    if ready >= minimum:
        return ready

    target_fresh = 5
    target_resend = 5
    saved = 0

    # Slot 1-5: fresh Apollo
    fresh = harvest_leads(CW_ICP_WIDENED, target=target_fresh, max_pages=12)
    for lead in fresh:
        if not lead.get("email"):
            continue
        if _is_duplicate(conn, lead["email"]):
            continue
        lead["email_source"] = "apollo_fresh"
        if dry_run or _save_cw_lead(conn, lead):
            saved += 1

    # Slot 6-10: resend queue
    resends = get_resend_queue(limit=target_resend, days_back=60)
    for r in resends:
        if _is_duplicate(conn, r["email"]):
            continue
        lead = {
            "apollo_id": r["apollo_id"], "email": r["email"], "name": r["name"],
            "email_source": "cw_resend",
        }
        if dry_run or _save_cw_lead(conn, lead):
            saved += 1

    # Top up the gap: if saved < minimum, pull more fresh
    gap = minimum - saved
    if gap > 0:
        topup_extra = harvest_leads(CW_ICP_WIDENED, target=gap, max_pages=12)
        for lead in topup_extra:
            if not lead.get("email"):
                continue
            if _is_duplicate(conn, lead["email"]):
                continue
            lead["email_source"] = "apollo_fresh"
            if dry_run or _save_cw_lead(conn, lead):
                saved += 1

    conn.close()
    logger.info(f"CW topup complete: {saved} new leads ready.")
    return saved


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--minimum", type=int, default=DAILY_MINIMUM)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    total = topup_cw_leads(args.minimum, args.dry_run)
    print(f"Done. {total} CW leads ready for outreach.")
