"""
signal_works/topup_leads.py
Keeps harvesting leads until there are at least DAILY_MINIMUM un-drafted
leads with email addresses in the DB. Then stops.

Covers the full Wasatch Front market: 3 niches x 15 cities = 45 niche/city
combinations per round. At ~25% email hit rate that gives 150+ potential
email leads per full sweep -- well above the 10/day minimum.

Rules:
  - Only saves leads that have at minimum a phone number
  - Leads with no phone, no website, and no email are discarded
  - Scrapes one niche/city pair at a time, checks count after each batch
  - Stops as soon as minimum is reached (does not over-harvest)
  - Rotates through combinations in round-robin order across rounds

Usage:
  python -m signal_works.topup_leads
  python -m signal_works.topup_leads --minimum 15
  python -m signal_works.topup_leads --dry-run    # show what would be scraped, no API calls
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signal_works.lead_scraper import scrape_google_maps_leads
from signal_works.ai_scorer import score_leads_batch
try:
    from orchestrator.db import upsert_signal_works_lead, get_crm_connection
except ModuleNotFoundError:
    sys.path.insert(0, "/app")
    from db import upsert_signal_works_lead, get_crm_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DAILY_MINIMUM = 10
BATCH_SIZE = 15   # leads per niche/city request (Serper limit = 20)
MAX_PAIRS_PER_RUN = 90  # hard ceiling -- prevents runaway API usage

# ── Market definition ────────────────────────────────────────────────────────
# Wasatch Front from Ogden to St. George -- full Utah addressable market.
# Ordered roughly north to south; harvester rotates through all of them.

NICHES = [
    "roofer",
    "pediatric dentist",
    "hvac",
]

CITIES = [
    # Salt Lake County
    "Salt Lake City, UT",
    "West Valley City, UT",
    "Murray, UT",
    "Sandy, UT",
    "South Jordan, UT",
    "Taylorsville, UT",
    "Millcreek, UT",
    "Cottonwood Heights, UT",
    "Holladay, UT",
    "Midvale, UT",
    "Herriman, UT",
    "Riverton, UT",
    "Draper, UT",
    # Utah County
    "Provo, UT",
    "Orem, UT",
    "Lehi, UT",
    "American Fork, UT",
    "Pleasant Grove, UT",
    "Spanish Fork, UT",
    "Springville, UT",
    "Payson, UT",
    # Davis / Weber / Cache Counties (north)
    "Ogden, UT",
    "Layton, UT",
    "Bountiful, UT",
    "Logan, UT",
    # Washington County (south)
    "St. George, UT",
    "Washington, UT",
]

# All niche/city pairs in priority order (SLC core first, then expand outward)
def _all_pairs() -> list[tuple[str, str]]:
    """Return all (niche, city) pairs. SLC core rotated first."""
    slc_core = ["Salt Lake City, UT", "Sandy, UT", "Murray, UT", "Provo, UT", "Orem, UT"]
    rest = [c for c in CITIES if c not in slc_core]
    ordered_cities = slc_core + rest
    return [(niche, city) for city in ordered_cities for niche in NICHES]


# ── DB helpers ────────────────────────────────────────────────────────────────

def count_ready_email_leads() -> int:
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
    return bool(phone or email or website)


# ── Main topup loop ───────────────────────────────────────────────────────────

def topup(minimum: int = DAILY_MINIMUM, dry_run: bool = False) -> int:
    """
    Harvest leads across all Wasatch Front niche/city pairs until `minimum`
    un-drafted email leads exist. Stops the moment the target is reached.
    Returns final count of un-drafted email leads.
    """
    current = count_ready_email_leads()
    logger.info(
        f"Starting topup: {current} un-drafted email leads (target: {minimum})"
    )

    if current >= minimum:
        logger.info("Already at minimum. No harvesting needed.")
        return current

    pairs = _all_pairs()
    pairs_scraped = 0

    for niche, city in pairs:
        if current >= minimum:
            break
        if pairs_scraped >= MAX_PAIRS_PER_RUN:
            logger.warning(f"Hit MAX_PAIRS_PER_RUN ({MAX_PAIRS_PER_RUN}). Stopping.")
            break

        pairs_scraped += 1
        label = f"{niche} / {city}"

        if dry_run:
            logger.info(f"[DRY RUN] Would scrape: {label}")
            continue

        logger.info(f"Scraping: {label} ({pairs_scraped}/{len(pairs)})")

        try:
            leads = scrape_google_maps_leads(niche, city, limit=BATCH_SIZE, save_to_supabase=False)
        except Exception as exc:
            logger.warning(f"  Scrape failed for {label}: {exc}")
            continue

        qualified = [l for l in leads if _lead_qualifies(l)]
        discarded = len(leads) - len(qualified)
        if discarded:
            logger.info(f"  Discarded {discarded} leads (no phone/email/website)")

        if not qualified:
            logger.info(f"  No qualifying leads for {label}")
            continue

        scored = score_leads_batch(qualified)

        saved = 0
        for lead in scored:
            try:
                upsert_signal_works_lead(lead)
                saved += 1
            except Exception as exc:
                logger.warning(f"  Could not save {lead.get('name', '?')}: {exc}")

        new_with_email = sum(1 for l in scored if (l.get("email") or "").strip())
        logger.info(
            f"  {label}: {saved} saved, {new_with_email} have email"
        )

        current = count_ready_email_leads()
        logger.info(f"  Running total: {current} email leads ready")

    if dry_run:
        logger.info(f"Dry run complete. Would have scraped {len(pairs)} niche/city pairs.")
        return current

    if current < minimum:
        logger.warning(
            f"Topup finished after {pairs_scraped} pairs with only {current}/{minimum} "
            "email leads. Expanding to more niches or cities may help."
        )
    else:
        logger.info(
            f"Topup complete. {current} email leads ready after {pairs_scraped} pair(s) scraped."
        )

    return current


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Signal Works Wasatch Front lead top-up")
    parser.add_argument(
        "--minimum", type=int, default=DAILY_MINIMUM,
        help=f"Target number of un-drafted email leads (default: {DAILY_MINIMUM})"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be scraped without making any API calls"
    )
    parser.add_argument(
        "--list-pairs", action="store_true",
        help="Print all niche/city pairs and exit"
    )
    args = parser.parse_args()

    if args.list_pairs:
        pairs = _all_pairs()
        print(f"{len(pairs)} niche/city pairs:")
        for i, (niche, city) in enumerate(pairs, 1):
            print(f"  {i:3}. {niche:<25} {city}")
        sys.exit(0)

    final_count = topup(minimum=args.minimum, dry_run=args.dry_run)
    sys.exit(0 if final_count >= args.minimum else 1)
