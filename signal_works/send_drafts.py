"""
signal_works/send_drafts.py
Daily runner: renders personalized HTML emails for un-drafted leads and
creates Gmail drafts in boubacar@catalystworks.consulting.

SAFETY RULE: Drafts with [TEST] in the subject are NEVER marked as drafted.
Only run --mark-drafted after you have reviewed real (non-test) drafts in Gmail.

ARCHITECTURE:
  Gmail draft creation uses the Gmail MCP tool (mcp__claude_ai_Gmail__create_draft).
  This script generates the payloads; a Claude Code session creates the drafts via MCP.

Daily flow (automated at 07:00 MT):
  1. topup_leads.py runs first -- harvests until >= 10 email leads exist
  2. send_drafts.py --export writes draft_payloads.json
  3. Claude session reads payloads and calls Gmail MCP to create drafts
  4. send_drafts.py --mark-drafted marks them drafted in DB

Usage:
  python -m signal_works.send_drafts --dry-run          # validate rendering only
  python -m signal_works.send_drafts --dry-run --test   # dry run with [TEST] subjects
  python -m signal_works.send_drafts --export           # write draft_payloads.json (real)
  python -m signal_works.send_drafts --export --test    # write payloads with [TEST] subjects
  python -m signal_works.send_drafts --mark-drafted     # mark drafted (NEVER after --test)
  python -m signal_works.send_drafts --count            # print count of ready leads
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


def export_payloads(limit: int = DAILY_MINIMUM, test_mode: bool = False) -> list[dict]:
    """Render HTML for each un-drafted lead. Returns list of draft payload dicts.

    test_mode=True: prepends [TEST] to every subject.
    IMPORTANT: Leads are NOT marked as drafted after a test run.
    Only call --mark-drafted for real (non-test) exports.
    """
    leads = get_leads_for_drafting(limit=limit)

    if not leads:
        logger.info("No un-drafted leads. Run: python -m signal_works.topup_leads")
        return []

    if len(leads) < DAILY_MINIMUM:
        logger.warning(
            f"Only {len(leads)} leads ready -- below the {DAILY_MINIMUM}/day minimum. "
            "Run: python -m signal_works.topup_leads"
        )

    payloads = []
    for lead in leads:
        subject = _subject(lead)
        if test_mode:
            subject = f"[TEST] {subject}"
        payloads.append({
            "lead_id": lead["id"],
            "name": lead["name"],
            "to": lead["email"],
            "subject": subject,
            "html": render_html(lead),
            "is_test": test_mode,
        })
        prefix = "[TEST] " if test_mode else ""
        logger.info(f"Rendered: {prefix}{lead['name']} <{lead['email']}>")

    with open(EXPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(payloads, f, ensure_ascii=False, indent=2)

    logger.info(f"Exported {len(payloads)} payloads -> {EXPORT_PATH}")
    if test_mode:
        logger.warning(
            "TEST MODE: Do NOT run --mark-drafted after reviewing these drafts. "
            "Leads remain un-drafted so real emails can be sent later."
        )
    return payloads


def mark_all_drafted(limit: int = DAILY_MINIMUM) -> int:
    """Mark up to `limit` un-drafted leads as drafted.

    SAFETY: Refuses to run if draft_payloads.json contains any [TEST] subjects.
    """
    if EXPORT_PATH.exists():
        with open(EXPORT_PATH, encoding="utf-8") as f:
            payloads = json.load(f)
        test_subjects = [p["subject"] for p in payloads if "[TEST]" in p.get("subject", "")]
        if test_subjects:
            logger.error(
                f"BLOCKED: {len(test_subjects)} payload(s) have [TEST] in subject. "
                "Re-run --export without --test before marking as drafted."
            )
            return 0

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


def dry_run(limit: int = DAILY_MINIMUM, test_mode: bool = False) -> int:
    leads = get_leads_for_drafting(limit=limit)
    if not leads:
        logger.info("No un-drafted leads found.")
        return 0
    if len(leads) < DAILY_MINIMUM:
        logger.warning(f"Only {len(leads)} leads ready -- need {DAILY_MINIMUM} minimum.")
    for lead in leads:
        subject = _subject(lead)
        if test_mode:
            subject = f"[TEST] {subject}"
        html = render_html(lead)
        logger.info(f"[DRY RUN] {lead['name']} <{lead['email']}> | {subject} | {len(html)} chars")
    if test_mode:
        logger.info("TEST MODE: No DB changes. Leads remain un-drafted.")
    logger.info(f"Dry run complete. {len(leads)} emails would be drafted.")
    return len(leads)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Signal Works draft runner")
    parser.add_argument("--limit", type=int, default=DAILY_MINIMUM)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--test", action="store_true",
                        help="Add [TEST] to subjects. Leads are NOT marked drafted.")
    parser.add_argument("--export", action="store_true",
                        help="Write draft_payloads.json for Gmail MCP")
    parser.add_argument("--mark-drafted", action="store_true",
                        help="Mark un-drafted leads as drafted (real emails only)")
    parser.add_argument("--count", action="store_true",
                        help="Print count of leads ready to draft")
    args = parser.parse_args()

    if args.count:
        n = count_ready()
        print(f"{n} leads ready to draft")
        sys.exit(0 if n >= DAILY_MINIMUM else 1)
    elif args.dry_run:
        dry_run(limit=args.limit, test_mode=args.test)
    elif args.export:
        export_payloads(limit=args.limit, test_mode=args.test)
    elif args.mark_drafted:
        if args.test:
            logger.error("Cannot combine --mark-drafted with --test. That would defeat the safety check.")
            sys.exit(1)
        mark_all_drafted(limit=args.limit)
    else:
        parser.print_help()
