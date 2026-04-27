"""
signal_works/topup_leads.py
Keeps harvesting leads until there are at least DAILY_MINIMUM un-drafted
leads with email addresses in the DB. Then stops.

Rules:
  - Only saves leads that have at minimum a phone number
  - Leads with no phone, no website, and no email are discarded
  - Runs up to MAX_ROUNDS scraping rounds before giving up
  - Each round scrapes BATCH_SIZE leads per niche/city pair

Usage:
  python -m signal_works.topup_leads
  python -m signal_works.topup_leads --minimum 15
  python -m signal_works.topup_leads --niches "roofer,pediatric dentist" --city "Salt Lake City"
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signal_works.lead_scraper import scrape_google_maps_leads
from signal_works.ai_scorer import score_leads_batch
from orchestrator.db import upsert_signal_works_lead, get_crm_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DAILY_MINIMUM = 10
BATCH_SIZE = 15
MAX_ROUNDS = 5

DEFAULT_NICHES = ["roofer", "pediatric dentist"]
DEFAULT_CITY = "Salt Lake City"


def count_ready_email_leads() -> int:
    """Count un-drafted leads with an email address."""
    conn = get_crm_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) as n FROM leads
            WHERE lead_type = 'website_prospect'
              AND email IS NOT NULL AND email != ''
              AND (email_drafted IS NULL OR email_drafted = FALSE)
            """
        )
        row = cur.fetchone()
        return int(row["n"]) if row else 0
    except Exception as e:
        logger.warning(f"count_ready_email_leads failed: {e}")
        return 0
    finally:
        conn.close()


def _lead_qualifies(lead: dict) -> bool:
    """Lead must have at least a phone number to enter the DB."""
    phone = (lead.get("phone") or "").strip()
    email = (lead.get("email") or "").strip()
    website = (lead.get("website_url") or "").strip()
    if not phone and not email and not website:
        return False
    return True


def topup(minimum: int = DAILY_MINIMUM, niches: list[str] = None, city: str = DEFAULT_CITY) -> int:
    """
    Harvest leads until `minimum` un-drafted email leads exist.
    Returns final count of un-drafted email leads.
    """
    if niches is None:
        niches = DEFAULT_NICHES

    current = count_ready_email_leads()
    logger.info(f"Starting topup: {current} un-drafted email leads (need {minimum})")

    if current >= minimum:
        logger.info("Already at minimum. No harvesting needed.")
        return current

    rounds = 0
    while current < minimum and rounds < MAX_ROUNDS:
        rounds += 1
        needed = minimum - current
        logger.info(f"Round {rounds}: need {needed} more email leads. Scraping {BATCH_SIZE} per niche...")

        for niche in niches:
            leads = scrape_google_maps_leads(niche, city, limit=BATCH_SIZE, save_to_supabase=False)

            # Filter: must have at least a phone number
            qualified = [l for l in leads if _lead_qualifies(l)]
            discarded = len(leads) - len(qualified)
            if discarded:
                logger.info(f"  Discarded {discarded} leads with no phone/email/website")

            if not qualified:
                logger.warning(f"  No qualifying leads found for {niche} in {city}")
                continue

            # Score
            scored = score_leads_batch(qualified)

            # Save to Supabase
            saved = 0
            for lead in scored:
                try:
                    upsert_signal_works_lead(lead)
                    saved += 1
                except Exception as exc:
                    logger.warning(f"  Could not save {lead.get('name', '?')}: {exc}")
            logger.info(f"  {niche}: {saved}/{len(scored)} leads saved to DB")

        current = count_ready_email_leads()
        logger.info(f"After round {rounds}: {current} un-drafted email leads")

        if current >= minimum:
            break

    if current < minimum:
        logger.warning(
            f"Topup finished after {rounds} rounds with only {current}/{minimum} email leads. "
            "Some businesses in this niche may not have findable email addresses. "
            "Leads with phone numbers only are still in the DB for manual outreach."
        )
    else:
        logger.info(f"Topup complete. {current} email leads ready to draft.")

    return current


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Signal Works lead top-up")
    parser.add_argument("--minimum", type=int, default=DAILY_MINIMUM,
                        help=f"Target number of un-drafted email leads (default: {DAILY_MINIMUM})")
    parser.add_argument("--niches", default=",".join(DEFAULT_NICHES),
                        help="Comma-separated list of niches to harvest")
    parser.add_argument("--city", default=DEFAULT_CITY,
                        help="City to harvest leads for")
    args = parser.parse_args()

    niches = [n.strip() for n in args.niches.split(",") if n.strip()]
    final_count = topup(minimum=args.minimum, niches=niches, city=args.city)
    sys.exit(0 if final_count >= args.minimum else 1)
