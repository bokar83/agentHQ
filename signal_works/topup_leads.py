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
from signal_works.email_gate import gate_email, EmailGateDrop
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
CIRCUIT_BREAKER_THRESHOLD = 50  # 50 consecutive double-fails -> disable Hunter
# Was 5. Raised 2026-05-05 because Apollo find_owner_by_company has ~0% hit rate
# on local trades-SMBs (663 misses, 1 hit in one Phoenix/Vegas pass). Old threshold
# tripped on lead 1-5 every run, killing Hunter.io fallback before it fired.


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


def _resolve_email(business: dict, hunter_disabled: bool) -> tuple[str, str, str]:
    """Walk the 4-layer resolution chain.

    Returns (email, source, owner_name). source in {"firecrawl", "apollo_strict",
    "hunter_domain", ""}. owner_name is the resolved person name from Apollo when
    available, otherwise empty string. Empty source means no email found.
    Raises HunterCapReached if Hunter cap hits during this call.
    """
    website = business.get("website_url") or ""
    if website and not business.get("no_website"):
        try:
            email = find_email_from_website(website)
            if email:
                try:
                    vetted = gate_email(email, source="sw_topup_firecrawl")
                    return vetted, "firecrawl", ""
                except EmailGateDrop as e:
                    logger.info(f"_resolve_email: firecrawl email {email} dropped ({e.reason})")
        except Exception as e:
            logger.warning(f"_resolve_email: Firecrawl error on {website}: {e}")

    apollo = find_owner_by_company(business["business_name"], business.get("city", ""))
    apollo_email = apollo.get("email") if apollo else None
    apollo_name = (apollo.get("name") if apollo else "") or ""
    apollo_domain = (apollo.get("domain") if apollo else "") or ""

    if apollo_email:
        try:
            vetted = gate_email(apollo_email, source="sw_topup_apollo")
            return vetted, "apollo_strict", apollo_name
        except EmailGateDrop as e:
            logger.info(f"_resolve_email: apollo email {apollo_email} dropped ({e.reason})")

    # Hunter.io fallback. Try Apollo's domain first (better-formatted), then
    # fall back to the website Serper already gave us. Apollo people DB has
    # near-zero coverage of local trades-SMBs, so most calls reach this point
    # with apollo=None. The website-domain path is the actual workhorse.
    if hunter_disabled:
        return "", "", ""

    candidate_domain = apollo_domain
    if not candidate_domain and website:
        from urllib.parse import urlparse
        try:
            parsed = urlparse(website if website.startswith("http") else f"https://{website}")
            candidate_domain = parsed.netloc.replace("www.", "")
        except Exception:
            candidate_domain = ""

    if not candidate_domain:
        return "", "", ""

    try:
        email = domain_search(candidate_domain)
        if email:
            # hunter_client.domain_search already runs gate_email internally on
            # each tier candidate. The defensive re-gate here covers manual
            # overrides and keeps a uniform drop-log source tag.
            try:
                vetted = gate_email(email, source="sw_topup_hunter")
                return vetted, "hunter_domain", apollo_name
            except EmailGateDrop as e:
                logger.info(f"_resolve_email: hunter email {email} dropped ({e.reason})")
    except HunterCapReached:
        logger.warning("_resolve_email: Hunter cap reached, skipping for rest of run")
        raise
    except Exception as e:
        logger.warning(f"_resolve_email: Hunter error on {candidate_domain}: {e}")
    return "", "", ""


def topup(minimum: int = DAILY_MINIMUM, dry_run: bool = False) -> int:
    """Harvest SW leads until `minimum` saved emails, walking the ladder.

    Returns count of leads saved this run.
    """
    reset_daily_counter()
    saved = 0
    consecutive_double_fails = 0
    hunter_disabled = False
    cap_alert_sent = False
    breaker_alert_sent = False

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
            biz["business_name"] = biz.get("business_name") or biz.get("name", "")

            try:
                email, source, owner_name = _resolve_email(biz, hunter_disabled)
            except HunterCapReached:
                hunter_disabled = True
                if not cap_alert_sent:
                    _telegram_alert(
                        "SW pipeline: Hunter daily cap hit. Falling back to skip for "
                        "remaining leads. Run continues."
                    )
                    cap_alert_sent = True
                email, source, owner_name = "", "", ""

            if not email:
                # Track consecutive double-failures (Firecrawl AND Apollo both failed)
                consecutive_double_fails += 1
                if consecutive_double_fails >= CIRCUIT_BREAKER_THRESHOLD and not breaker_alert_sent:
                    logger.warning(
                        "topup: circuit breaker tripped (5 consecutive Firecrawl+Apollo failures), "
                        "disabling Hunter to protect budget"
                    )
                    _telegram_alert(
                        "SW pipeline: 5 consecutive businesses failed BOTH Firecrawl and Apollo. "
                        "Disabling Hunter to protect budget. Investigate upstream APIs."
                    )
                    hunter_disabled = True
                    breaker_alert_sent = True

                # Locked 2026-05-07: phone-only/website-only leads still get saved
                # for the manual-review queue but DO NOT count toward email target.
                # email_source flagged so dashboard can filter.
                if biz.get("phone") or biz.get("website_url"):
                    biz["email"] = ""
                    biz["business_display_name"] = biz.get("name", "")
                    flag = "phone_only" if biz.get("phone") and not biz.get("website_url") else (
                        "website_only" if biz.get("website_url") and not biz.get("phone") else "phone_and_website"
                    )
                    biz["email_source"] = flag
                    _save_lead(biz, dry_run)
                    logger.info(f"topup: [skip-count] saved {flag} lead -> {biz.get('business_name', '?')}")
                continue

            consecutive_double_fails = 0
            biz["email"] = email
            biz["email_source"] = source
            # Owner name from Apollo overrides business-name-as-name placeholder so
            # the email greeting reads "Hi Amanda" not "Hi Utah Plumbing".
            biz["business_display_name"] = biz.get("name", "")
            if owner_name:
                biz["name"] = owner_name
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
