"""
signal_works/migrate_leads_table.py
Adds Signal Works columns to the existing Supabase leads table.
Run once: python -m signal_works.migrate_leads_table

Columns added (all safe to re-run -- uses ADD COLUMN IF NOT EXISTS):
  website_url     TEXT
  review_count    INTEGER
  ai_score        INTEGER
  google_maps_url TEXT
  niche           TEXT
  city            TEXT
  lead_type       TEXT   -- e.g. 'website_prospect', 'consulting', 'inbound'
  ai_breakdown    JSONB  -- per-dimension score details
  ai_quick_wins   TEXT   -- comma-separated quick win suggestions
"""
import logging
from orchestrator.db import get_crm_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MIGRATION = """
ALTER TABLE leads
  ADD COLUMN IF NOT EXISTS website_url     TEXT,
  ADD COLUMN IF NOT EXISTS review_count    INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS ai_score        INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS google_maps_url TEXT,
  ADD COLUMN IF NOT EXISTS niche           TEXT,
  ADD COLUMN IF NOT EXISTS city            TEXT,
  ADD COLUMN IF NOT EXISTS lead_type       TEXT,
  ADD COLUMN IF NOT EXISTS ai_breakdown    JSONB,
  ADD COLUMN IF NOT EXISTS ai_quick_wins   TEXT,
  ADD COLUMN IF NOT EXISTS google_rating   NUMERIC(3,1),
  ADD COLUMN IF NOT EXISTS has_website     BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS google_address  TEXT,
  ADD COLUMN IF NOT EXISTS baseline_reviews INTEGER,
  ADD COLUMN IF NOT EXISTS baseline_rating  NUMERIC(3,1),
  ADD COLUMN IF NOT EXISTS baseline_date    DATE;

COMMENT ON COLUMN leads.lead_type       IS 'website_prospect | consulting | inbound | cold_outreach';
COMMENT ON COLUMN leads.ai_score        IS '0-100 AI visibility score (Signal Works scoring system)';
COMMENT ON COLUMN leads.google_rating   IS 'Google Maps star rating at time of scrape (1.0-5.0)';
COMMENT ON COLUMN leads.has_website     IS 'True if business has a website in Google listing';
COMMENT ON COLUMN leads.google_address  IS 'Full address from Google Maps listing';
COMMENT ON COLUMN leads.baseline_reviews IS 'review_count snapshot when first added -- track growth over time';
COMMENT ON COLUMN leads.baseline_rating  IS 'google_rating snapshot when first added';
COMMENT ON COLUMN leads.baseline_date    IS 'Date baseline was captured';
"""

if __name__ == "__main__":
    conn = get_crm_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(MIGRATION)
        conn.commit()
        logger.info("Migration complete -- Signal Works columns added to leads table.")
    except Exception as exc:
        logger.error(f"Migration failed: {exc}")
        conn.rollback()
    finally:
        conn.close()
