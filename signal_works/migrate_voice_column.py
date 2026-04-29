"""
signal_works/migrate_voice_column.py
Adds voice_personalization_line column to leads table.
Run once: python -m signal_works.migrate_voice_column

Idempotent (uses ADD COLUMN IF NOT EXISTS).
"""
import logging
from orchestrator.db import get_crm_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MIGRATION = """
ALTER TABLE leads
  ADD COLUMN IF NOT EXISTS voice_personalization_line TEXT;

COMMENT ON COLUMN leads.voice_personalization_line IS 'One-line personalized opener in lead voice, from transcript-style-dna. Null = use template fallback.';
"""

if __name__ == "__main__":
    conn = get_crm_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(MIGRATION)
        conn.commit()
        logger.info("Migration complete: voice_personalization_line column added.")
    except Exception as exc:
        logger.error(f"Migration failed: {exc}")
        conn.rollback()
    finally:
        conn.close()
