"""
signal_works/run_pipeline.py
Master pipeline: scrape leads -> find emails -> score -> save to Supabase -> build email queue.

Usage:
  python -m signal_works.run_pipeline --niche "pediatric dentist" --city "Salt Lake City"
  python -m signal_works.run_pipeline --niche "roofer" --city "Salt Lake City" --csv signal_works/seed_leads.csv --loom https://loom.com/share/abc
"""
import argparse
import logging
import os
from signal_works.lead_scraper import scrape_google_maps_leads, load_leads_from_csv
from signal_works.ai_scorer import score_leads_batch
from signal_works.email_builder import build_email_queue
from orchestrator.db import upsert_signal_works_lead

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run(niche: str, city: str, csv_path: str = "", loom_url: str = "", limit: int = 10) -> str:
    """Run the full Signal Works pipeline. Returns path to email queue CSV."""
    logger.info(f"Signal Works pipeline starting: {niche} / {city}")

    if csv_path:
        # load_leads_from_csv now attempts Firecrawl email extraction + saves to Supabase
        leads = load_leads_from_csv(csv_path, niche, city, save_to_supabase=True)
        logger.info(f"Loaded {len(leads)} leads from CSV")
    else:
        # scrape_google_maps_leads attempts Firecrawl email extraction + saves to Supabase
        leads = scrape_google_maps_leads(niche, city, limit=limit, save_to_supabase=True)
        logger.info(f"Scraped {len(leads)} leads from Google Maps")

    if not leads:
        logger.error("No leads found. Use --csv to provide manual leads.")
        return ""

    logger.info("Scoring leads for AI visibility...")
    leads = score_leads_batch(leads)

    # Persist scored leads back to Supabase (updates ai_score + ai_breakdown)
    saved = 0
    for lead in leads:
        try:
            upsert_signal_works_lead(lead)
            saved += 1
        except Exception as exc:
            logger.warning(f"Could not update scored lead in Supabase: {exc}")
    logger.info(f"Saved {saved}/{len(leads)} scored leads to Supabase")

    leads.sort(key=lambda x: x.get("ai_score", 0))

    if loom_url:
        for lead in leads:
            lead["loom_url"] = loom_url
    else:
        loom_env_key = f"SIGNAL_WORKS_LOOM_{niche.upper().replace(' ', '_')}"
        loom_from_env = os.environ.get(loom_env_key, "")
        if loom_from_env:
            for lead in leads:
                lead["loom_url"] = loom_from_env

    safe_niche = niche.replace(" ", "_")
    safe_city = city.replace(" ", "_")
    queue_path = f"signal_works/email_queue_{safe_niche}_{safe_city}.csv"
    out = build_email_queue(leads, output_csv=queue_path)
    logger.info(f"Pipeline complete. Email queue: {out}")

    top = leads[:3]
    logger.info("Top leads by AI score (lowest = most urgent pitch):")
    for lead in top:
        logger.info(f"  {lead['name']}: {lead.get('ai_score', 0)}/100 | email: {lead.get('email', '(none)')}")

    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Signal Works lead pipeline")
    parser.add_argument("--niche", required=True, help="Business niche e.g. 'pediatric dentist'")
    parser.add_argument("--city", required=True, help="City e.g. 'Salt Lake City'")
    parser.add_argument("--csv", default="", help="Path to manual leads CSV (optional)")
    parser.add_argument("--loom", default="", help="Loom URL to embed in emails")
    parser.add_argument("--limit", type=int, default=10, help="Max leads to process")
    args = parser.parse_args()
    run(args.niche, args.city, csv_path=args.csv, loom_url=args.loom, limit=args.limit)
