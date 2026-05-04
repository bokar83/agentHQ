"""
signal_works/topup_studio_leads.py
Harvests Studio faceless-agency outreach leads via Apollo.io.

Targets: ecommerce, retail, restaurant, fitness, beauty, real estate
owners in Utah + adjacent markets who need video/content production.

Usage:
  python -m signal_works.topup_studio_leads
  python -m signal_works.topup_studio_leads --minimum 10
  python -m signal_works.topup_studio_leads --dry-run
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv(override=True)

from skills.apollo_skill.apollo_client import harvest_leads, STUDIO_ICP
from orchestrator.db import get_crm_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DAILY_MINIMUM = 25


def _count_ready_studio_leads(conn) -> int:
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as n FROM leads
        WHERE source LIKE 'apollo_studio%'
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


def _save_studio_lead(conn, lead: dict) -> bool:
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO leads
              (name, company, title, industry, email, linkedin_url, city,
               status, source, created_at, updated_at)
            VALUES
              (%s, %s, %s, %s, %s, %s, %s,
               'new', 'apollo_studio', NOW(), NOW())
            ON CONFLICT DO NOTHING
        """, (
            lead.get("name"),
            lead.get("company"),
            lead.get("title"),
            lead.get("industry"),
            lead.get("email"),
            lead.get("linkedin_url"),
            lead.get("city"),
        ))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        logger.warning(f"Failed to save Studio lead {lead.get('company')}: {e}")
        return False


def topup_studio_leads(minimum: int = DAILY_MINIMUM, dry_run: bool = False) -> int:
    conn = get_crm_connection()
    current = _count_ready_studio_leads(conn)
    logger.info(f"Studio topup: {current} ready leads (target: {minimum})")

    if current >= minimum:
        logger.info("Already at target. Nothing to do.")
        conn.close()
        return current

    needed = minimum - current
    logger.info(f"Need {needed} more leads. Harvesting via Apollo (STUDIO_ICP)...")

    if dry_run:
        logger.info("[DRY-RUN] Would call Apollo harvest. Skipping.")
        conn.close()
        return current

    new_leads = harvest_leads(STUDIO_ICP, target=needed + 10, max_pages=15)

    saved = 0
    for lead in new_leads:
        if not lead.get("email"):
            continue
        if _is_duplicate(conn, lead["email"]):
            logger.info(f"  Skip duplicate: {lead['email']}")
            continue
        ok = _save_studio_lead(conn, lead)
        if ok:
            saved += 1
            logger.info(f"  Saved: {lead['name']} <{lead['email']}> | {lead['company']}")
        if current + saved >= minimum:
            break

    total = current + saved
    if total < minimum:
        logger.warning(f"Studio topup finished with {total}/{minimum} leads.")
    else:
        logger.info(f"Studio topup complete: {total} leads ready.")

    conn.close()
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--minimum", type=int, default=DAILY_MINIMUM)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    total = topup_studio_leads(args.minimum, args.dry_run)
    print(f"Done. {total} Studio leads ready for outreach.")
