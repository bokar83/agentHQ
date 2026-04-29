"""
signal_works/send_drafts.py
Daily runner: renders personalized HTML emails for un-drafted leads and
creates Gmail drafts in boubacar@catalystworks.consulting using the CW
OAuth credentials (secrets/gws-oauth-credentials-cw.json).

SAFETY RULE: Drafts with [TEST] in the subject are NEVER marked as drafted.
Only run --mark-drafted after reviewing real (non-test) drafts in Gmail.

Daily flow (automated at 07:00 MT):
  1. topup_leads.py runs first -- harvests until >= 10 email leads exist
  2. send_drafts.py --run creates drafts and marks them in DB (one shot)

Usage:
  python -m signal_works.send_drafts --run            # create drafts + mark drafted
  python -m signal_works.send_drafts --run --test     # create [TEST] drafts, do NOT mark
  python -m signal_works.send_drafts --dry-run        # validate rendering, no Gmail/DB
  python -m signal_works.send_drafts --mark-drafted   # mark un-drafted leads as drafted
  python -m signal_works.send_drafts --count          # print count of ready leads
"""
import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signal_works.email_builder import render_html, _subject
from signal_works.gmail_draft import create_draft

# Container vs dev import compatibility. orc-crewai flattens orchestrator/* to /app.
try:
    from orchestrator.db import get_leads_for_drafting, get_crm_connection
except ModuleNotFoundError:
    sys.path.insert(0, "/app")
    from db import get_leads_for_drafting, get_crm_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DAILY_MINIMUM = 10
EXPORT_PATH = Path(__file__).parent / "draft_payloads.json"


def count_ready() -> int:
    return len(get_leads_for_drafting(limit=100))


def run(limit: int = DAILY_MINIMUM, test_mode: bool = False) -> int:
    """Create Gmail drafts for un-drafted leads. Returns number of drafts created.

    test_mode=True: prepends [TEST] to subjects, does NOT mark leads as drafted.
    """
    leads = get_leads_for_drafting(limit=limit)

    if not leads:
        logger.info("No un-drafted leads. Run: python -m signal_works.topup_leads")
        return 0

    if len(leads) < DAILY_MINIMUM:
        logger.warning(
            f"Only {len(leads)} leads ready -- below the {DAILY_MINIMUM}/day minimum. "
            "Run: python -m signal_works.topup_leads"
        )

    drafted = 0
    failed = 0
    drafted_ids = []

    for lead in leads:
        subject = _subject(lead)
        if test_mode:
            subject = f"[TEST] {subject}"

        try:
            html = render_html(lead)
            create_draft(
                to_email=lead["email"],
                subject=subject,
                html_body=html,
            )
            drafted_ids.append(lead["id"])
            drafted += 1
            prefix = "[TEST] " if test_mode else ""
            logger.info(f"Drafted ({drafted}/{len(leads)}): {prefix}{lead['name']} <{lead['email']}>")
        except Exception as exc:
            failed += 1
            logger.error(f"Failed: {lead['name']} <{lead['email']}>: {exc}")

    if drafted_ids and not test_mode:
        _mark_drafted(drafted_ids)
        logger.info(f"Marked {len(drafted_ids)} leads as email_drafted=TRUE in Supabase.")
    elif test_mode and drafted > 0:
        logger.warning(
            f"TEST MODE: {drafted} drafts created with [TEST] subjects. "
            "Leads NOT marked as drafted -- they will be included in the next real run."
        )

    logger.info(f"Done. {drafted} drafted, {failed} failed.")
    return drafted


def _mark_drafted(lead_ids: list[int]) -> None:
    conn = get_crm_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE leads SET email_drafted=TRUE, email_drafted_at=NOW() WHERE id = ANY(%s)",
            (lead_ids,),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        logger.error(f"mark_drafted failed: {e}")
        conn.rollback()
    finally:
        conn.close()


def mark_all_drafted(limit: int = DAILY_MINIMUM) -> int:
    """Mark up to `limit` un-drafted leads as drafted. Only for manual recovery."""
    if EXPORT_PATH.exists():
        with open(EXPORT_PATH, encoding="utf-8") as f:
            try:
                payloads = json.load(f)
                test_subjects = [p["subject"] for p in payloads if "[TEST]" in p.get("subject", "")]
                if test_subjects:
                    logger.error(
                        f"BLOCKED: {len(test_subjects)} payload(s) have [TEST] in subject. "
                        "These should not be marked as drafted."
                    )
                    return 0
            except Exception:
                pass

    leads = get_leads_for_drafting(limit=limit)
    if not leads:
        logger.info("No un-drafted leads found.")
        return 0
    ids = [l["id"] for l in leads]
    _mark_drafted(ids)
    logger.info(f"Marked {len(ids)} leads as email_drafted=TRUE")
    return len(ids)


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
        logger.info("TEST MODE: No drafts created, no DB changes.")
    logger.info(f"Dry run complete. {len(leads)} emails ready.")
    return len(leads)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Signal Works Gmail draft runner")
    parser.add_argument("--limit", type=int, default=DAILY_MINIMUM)
    parser.add_argument("--run", action="store_true",
                        help="Create drafts in boubacar@catalystworks.consulting and mark drafted")
    parser.add_argument("--test", action="store_true",
                        help="Add [TEST] to subjects. Leads NOT marked drafted.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Render HTML and log, no Gmail or DB changes")
    parser.add_argument("--mark-drafted", action="store_true",
                        help="Mark un-drafted leads as drafted (manual recovery only)")
    parser.add_argument("--count", action="store_true",
                        help="Print count of leads ready to draft")
    args = parser.parse_args()

    if args.count:
        n = count_ready()
        print(f"{n} leads ready to draft")
        sys.exit(0 if n >= DAILY_MINIMUM else 1)
    elif args.dry_run:
        dry_run(limit=args.limit, test_mode=args.test)
    elif args.run:
        if args.mark_drafted:
            logger.error("Cannot combine --run with --mark-drafted.")
            sys.exit(1)
        count = run(limit=args.limit, test_mode=args.test)
        sys.exit(0 if count > 0 else 1)
    elif args.mark_drafted:
        if args.test:
            logger.error("Cannot combine --mark-drafted with --test.")
            sys.exit(1)
        mark_all_drafted(limit=args.limit)
    else:
        parser.print_help()
