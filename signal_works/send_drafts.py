"""
signal_works/send_drafts.py
Daily runner: renders personalized HTML emails for un-drafted leads and
creates Gmail drafts in boubacar@catalystworks.consulting.

ARCHITECTURE NOTE:
  Gmail draft creation uses the Gmail MCP tool (mcp__claude_ai_Gmail__create_draft).
  This script generates the payloads; Claude Code session creates the drafts via MCP.

  Run this script to get the draft payloads:
    python -m signal_works.send_drafts --export

  Or run it in --dry-run mode to validate rendering without touching Gmail or DB.

Daily flow:
  1. Run harvester first to ensure >= 10 email-eligible leads exist:
       python -m signal_works.run_pipeline --niche "roofer" --city "Salt Lake City"
  2. Export payloads:
       python -m signal_works.send_drafts --export
  3. Claude session reads payloads and calls Gmail MCP to create drafts.
  4. Mark drafted: python -m signal_works.send_drafts --mark-drafted

Usage:
  python -m signal_works.send_drafts --dry-run       # validate rendering only
  python -m signal_works.send_drafts --export        # write draft_payloads.json
  python -m signal_works.send_drafts --mark-drafted  # mark all un-drafted as drafted
  python -m signal_works.send_drafts --count         # print how many ready to draft
"""
import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signal_works.email_builder import render_html, _subject
from orchestrator.db import get_leads_for_drafting, get_crm_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DAILY_MINIMUM = 10
EXPORT_PATH = Path(__file__).parent / "draft_payloads.json"


def count_ready() -> int:
    leads = get_leads_for_drafting(limit=100)
    return len(leads)


def export_payloads(limit: int = DAILY_MINIMUM) -> list[dict]:
    """Render HTML for each un-drafted lead. Returns list of draft payload dicts."""
    leads = get_leads_for_drafting(limit=limit)

    if not leads:
        logger.info("No un-drafted leads. Run the harvester first.")
        return []

    if len(leads) < DAILY_MINIMUM:
        logger.warning(
            f"Only {len(leads)} leads ready -- below the {DAILY_MINIMUM}/day minimum. "
            "Run the harvester: python -m signal_works.run_pipeline"
        )

    payloads = []
    for lead in leads:
        payloads.append({
            "lead_id": lead["id"],
            "name": lead["name"],
            "to": lead["email"],
            "subject": _subject(lead),
            "html": render_html(lead),
        })
        logger.info(f"Rendered: {lead['name']} <{lead['email']}>")

    with open(EXPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(payloads, f, ensure_ascii=False, indent=2)

    logger.info(f"Exported {len(payloads)} draft payloads -> {EXPORT_PATH}")
    return payloads


def mark_all_drafted(limit: int = DAILY_MINIMUM) -> int:
    """Mark up to `limit` un-drafted leads as drafted (call after Gmail MCP push)."""
    conn = get_crm_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE leads
            SET email_drafted = TRUE, email_drafted_at = NOW()
            WHERE id IN (
                SELECT id FROM leads
                WHERE lead_type = 'website_prospect'
                  AND email IS NOT NULL AND email != ''
                  AND (email_drafted IS NULL OR email_drafted = FALSE)
                ORDER BY ai_score ASC NULLS LAST
                LIMIT %s
            )
            """,
            (limit,),
        )
        count = cur.rowcount
        conn.commit()
        cur.close()
        logger.info(f"Marked {count} leads as email_drafted=TRUE")
        return count
    except Exception as e:
        logger.error(f"mark_all_drafted failed: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()


def dry_run(limit: int = DAILY_MINIMUM) -> int:
    leads = get_leads_for_drafting(limit=limit)
    if not leads:
        logger.info("No un-drafted leads found.")
        return 0
    if len(leads) < DAILY_MINIMUM:
        logger.warning(f"Only {len(leads)} leads ready -- need {DAILY_MINIMUM} minimum.")
    for lead in leads:
        subject = _subject(lead)
        html = render_html(lead)
        logger.info(f"[DRY RUN] {lead['name']} <{lead['email']}> | {subject} | {len(html)} chars")
    logger.info(f"Dry run complete. {len(leads)} emails would be drafted.")
    return len(leads)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Signal Works draft runner")
    parser.add_argument("--limit", type=int, default=DAILY_MINIMUM)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--export", action="store_true", help="Write draft_payloads.json")
    parser.add_argument("--mark-drafted", action="store_true", help="Mark un-drafted leads as drafted")
    parser.add_argument("--count", action="store_true", help="Print count of leads ready to draft")
    args = parser.parse_args()

    if args.count:
        n = count_ready()
        print(f"{n} leads ready to draft")
        sys.exit(0 if n >= DAILY_MINIMUM else 1)
    elif args.dry_run:
        dry_run(limit=args.limit)
    elif args.export:
        export_payloads(limit=args.limit)
    elif args.mark_drafted:
        mark_all_drafted(limit=args.limit)
    else:
        parser.print_help()
