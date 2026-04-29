"""
signal_works/topup_leads.py
===========================
SW lead harvest. Walks the geo expansion ladder, resolves emails
through 4 layers (Firecrawl, Apollo strict, Hunter, skip), and stops
when the daily target is hit.
"""
import argparse
import logging
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signal_works.lead_scraper import scrape_google_maps_leads, find_email_from_website
from signal_works.expansion_ladder import PAIRS
from signal_works.hunter_client import domain_search, HunterCapReached, reset_daily_counter
from skills.apollo_skill.apollo_client import find_owner_by_company

try:
    from orchestrator.db import (
        upsert_signal_works_lead,
        get_crm_connection,
    )
except ModuleNotFoundError:
    sys.path.insert(0, "/app")
    from db import upsert_signal_works_lead, get_crm_connection

logger = logging.getLogger(__name__)
DAILY_MINIMUM = 10  # Tier 1-2 default
CIRCUIT_BREAKER_THRESHOLD = 5  # 5 consecutive double-fails -> disable Hunter


def _telegram_alert(msg: str) -> None:
    token = os.getenv("ORCHESTRATOR_TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    try:
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": msg[:4000]}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST",
        )
        urllib.request.urlopen(req, timeout=15).read()
    except Exception:
        pass


def _save_lead(lead: dict, dry_run: bool) -> bool:
    """Insert lead into Supabase. Return True on success."""
    if dry_run:
        return True
    try:
        upsert_signal_works_lead(lead)
        return True
    except Exception as e:
        logger.warning(f"_save_lead: insert failed for {lead.get('business_name', '?')}: {e}")
        return False


def _resolve_email(business: dict, hunter_disabled: bool) -> tuple[str, str]:
    """Walk the 4-layer resolution chain.

    Returns (email, source). source in {"firecrawl", "apollo_strict", "hunter_domain", ""}.
    Empty source means no email found.
    Raises HunterCapReached if Hunter cap hits during this call.
    """
    website = business.get("website_url") or ""
    if website and not business.get("no_website"):
        try:
            email = find_email_from_website(website)
            if email:
                return email, "firecrawl"
        except Exception as e:
            logger.warning(f"_resolve_email: Firecrawl error on {website}: {e}")

    apollo = find_owner_by_company(business["business_name"], business.get("city", ""))
    if not apollo:
        return "", ""
    if apollo.get("email"):
        return apollo["email"], "apollo_strict"

    if hunter_disabled or not apollo.get("domain"):
        return "", ""

    try:
        email = domain_search(apollo["domain"])
        if email:
            return email, "hunter_domain"
    except HunterCapReached:
        logger.warning("_resolve_email: Hunter cap reached, skipping for rest of run")
        raise
    except Exception as e:
        logger.warning(f"_resolve_email: Hunter error on {apollo['domain']}: {e}")
    return "", ""


def topup(minimum: int = DAILY_MINIMUM, dry_run: bool = False) -> int:
    """Harvest SW leads until `minimum` saved emails, walking the ladder.

    Returns count of leads saved this run.
    """
    reset_daily_counter()
    saved = 0
    consecutive_double_fails = 0
    hunter_disabled = False
    cap_alert_sent = False

    for niche, city, tier, default_target in PAIRS:
        if saved >= minimum:
            break

        try:
            scraped = scrape_google_maps_leads(niche=niche, city=city, limit=20)
        except Exception as e:
            logger.warning(f"topup: Serper failed for {niche}/{city}: {e}")
            continue

        for biz in scraped:
            if saved >= minimum:
                break
            biz["niche"] = niche
            biz["city"] = city
            biz["tier"] = tier

            try:
                email, source = _resolve_email(biz, hunter_disabled)
            except HunterCapReached:
                hunter_disabled = True
                if not cap_alert_sent:
                    _telegram_alert(
                        "SW pipeline: Hunter daily cap hit. Falling back to skip for "
                        "remaining leads. Run continues."
                    )
                    cap_alert_sent = True
                email, source = "", ""

            if not email:
                # Track consecutive double-failures (Firecrawl AND Apollo both failed)
                consecutive_double_fails += 1
                if consecutive_double_fails >= CIRCUIT_BREAKER_THRESHOLD and not hunter_disabled:
                    logger.warning(
                        "topup: circuit breaker tripped (5 consecutive Firecrawl+Apollo failures), "
                        "disabling Hunter to protect budget"
                    )
                    _telegram_alert(
                        "SW pipeline: 5 consecutive businesses failed BOTH Firecrawl and Apollo. "
                        "Disabling Hunter to protect budget. Investigate upstream APIs."
                    )
                    hunter_disabled = True
                continue

            consecutive_double_fails = 0
            biz["email"] = email
            biz["email_source"] = source
            if _save_lead(biz, dry_run):
                saved += 1
                logger.info(f"topup: [{saved}/{minimum}] {source} -> {biz['business_name']} ({email})")

    if saved < minimum:
        _telegram_alert(
            f"SW pipeline finished tier-walk with {saved}/{minimum} leads. Ladder exhausted."
        )

    logger.info(f"topup complete: {saved} leads saved (target was {minimum})")
    return saved


def count_ready_email_leads() -> int:
    """Count un-drafted email leads ready for outreach. Used by monitoring/reporting."""
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
    """Lead must have at least a phone number, email, or website to enter the DB."""
    phone = (lead.get("phone") or "").strip()
    email = (lead.get("email") or "").strip()
    website = (lead.get("website_url") or "").strip()
    return bool(phone or email or website)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Signal Works lead top-up (ladder walk)")
    parser.add_argument(
        "--minimum", type=int, default=DAILY_MINIMUM,
        help=f"Target number of leads to save this run (default: {DAILY_MINIMUM})"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Walk the ladder but do not write to DB"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    final = topup(minimum=args.minimum, dry_run=args.dry_run)
    sys.exit(0 if final >= args.minimum else 1)
