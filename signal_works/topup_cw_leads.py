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

from skills.apollo_skill.apollo_client import harvest_leads, CW_ICP
try:
    from orchestrator.db import get_crm_connection
except ModuleNotFoundError:
    sys.path.insert(0, "/app")
    from db import get_crm_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DAILY_MINIMUM = 10


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
               status, source, created_at, updated_at)
            VALUES
              (%s, %s, %s, %s, %s, %s, %s,
               'new', %s, NOW(), NOW())
            ON CONFLICT DO NOTHING
        """, (
            lead.get("name"),
            lead.get("company"),
            lead.get("title"),
            lead.get("industry"),
            lead.get("email"),
            lead.get("linkedin_url"),
            lead.get("city"),
            lead.get("source", "apollo_cw"),
        ))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        logger.warning(f"Failed to save lead {lead.get('company')}: {e}")
        return False


def topup_cw_leads(minimum: int = DAILY_MINIMUM, dry_run: bool = False) -> int:
    conn = get_crm_connection()
    current = _count_ready_cw_leads(conn)
    logger.info(f"CW topup: {current} ready leads (target: {minimum})")

    if current >= minimum:
        logger.info("Already at target. Nothing to do.")
        conn.close()
        return current

    needed = minimum - current
    logger.info(f"Need {needed} more leads. Harvesting via Apollo...")

    if dry_run:
        logger.info("[DRY-RUN] Would call Apollo harvest. Skipping.")
        conn.close()
        return current

    # Harvest from Apollo -- only spends credits on ICP matches with emails
    new_leads = harvest_leads(CW_ICP, target=needed + 5, max_pages=5)

    saved = 0
    for lead in new_leads:
        if not lead.get("email"):
            continue
        if _is_duplicate(conn, lead["email"]):
            logger.info(f"  Skip duplicate: {lead['email']}")
            continue
        ok = _save_cw_lead(conn, lead)
        if ok:
            saved += 1
            logger.info(f"  Saved: {lead['name']} <{lead['email']}> | {lead['company']}")
        if current + saved >= minimum:
            break

    total = current + saved
    if total < minimum:
        logger.warning(f"Topup finished with only {total}/{minimum} leads. Apollo returned fewer than expected.")
    else:
        logger.info(f"Topup complete: {total} CW leads ready.")

    conn.close()
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--minimum", type=int, default=DAILY_MINIMUM)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    total = topup_cw_leads(args.minimum, args.dry_run)
    print(f"Done. {total} CW leads ready for outreach.")
