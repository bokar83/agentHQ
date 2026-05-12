"""
signal_works/topup_leads.py
===========================
SW lead harvest. Walks the geo expansion ladder, resolves emails
through 5 layers (Firecrawl, Apollo, Hunter domain-search,
Prospeo person-enrich, skip), and stops when the daily target is hit.

Per-process behavior (locked 2026-05-12 after harvest stalled on 200-cap):
- Raises Hunter per-process cap to 400 internally. Callers that already
  set HUNTER_MAX_SEARCHES_PER_DAY are honored; bare callers
  (morning_runner.topup(minimum=35)) get the 400 cap automatically.
- 45-minute wall-clock cap. Exits gracefully if the loop runs over,
  even if `minimum` is not hit. Telegram alert on wall-clock exit.
- Apollo owner-less -> Hunter domain-search -> Prospeo person-enrich
  fallback chain. Apollo find_owner_by_company has ~0% hit rate on
  trades-SMBs; without the fallback, leads save phone-only and never
  count toward the email-target, so topup loops forever.
"""
import argparse
import logging
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signal_works.lead_scraper import scrape_google_maps_leads, find_email_from_website
from signal_works.expansion_ladder import PAIRS
from signal_works.hunter_client import domain_search, HunterCapReached, reset_daily_counter
from signal_works.email_gate import gate_email, EmailGateDrop
from signal_works.prospeo_client import prospeo_enrich_company
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
HUNTER_CAP_DAILY = 400  # see hunter_client._max_calls(); env override honored
WALL_CLOCK_SECONDS = 45 * 60  # 45-minute wall-clock cap per topup() invocation


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


def _candidate_domain(apollo_domain: str, website: str) -> str:
    """Pick best domain for Hunter/Prospeo lookup. Apollo's first, then website."""
    if apollo_domain:
        return apollo_domain
    if not website:
        return ""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(website if website.startswith("http") else f"https://{website}")
        return parsed.netloc.replace("www.", "")
    except Exception:
        return ""


def _resolve_email(business: dict, hunter_disabled: bool) -> tuple[str, str, str]:
    """Walk the 5-layer resolution chain.

    Order: Firecrawl scrape -> Apollo find_owner_by_company -> Hunter
    domain-search -> Prospeo company-enrich -> give up.

    Returns (email, source, owner_name). source in {"firecrawl",
    "apollo_strict", "hunter_domain", "prospeo", ""}. owner_name is the
    resolved person name from Apollo or Prospeo when available, otherwise
    empty string. Empty source means no email found.

    Raises HunterCapReached if Hunter cap hits during this call. Prospeo
    failures degrade silently (no cap exception today; we just log).
    """
    website = business.get("website_url") or ""
    business_name = business.get("business_name", "")
    city = business.get("city", "")

    # Layer 1: Firecrawl scrape of the lead's own website
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

    # Layer 2: Apollo find_owner_by_company (org search + people reveal)
    apollo = find_owner_by_company(business_name, city)
    apollo_email = apollo.get("email") if apollo else None
    apollo_name = (apollo.get("name") if apollo else "") or ""
    apollo_domain = (apollo.get("domain") if apollo else "") or ""

    if apollo_email:
        try:
            vetted = gate_email(apollo_email, source="sw_topup_apollo")
            return vetted, "apollo_strict", apollo_name
        except EmailGateDrop as e:
            logger.info(f"_resolve_email: apollo email {apollo_email} dropped ({e.reason})")

    # Apollo people DB has ~0% hit rate on trades-SMBs. Most calls land
    # here with apollo=None or owner-less. Fall through to Hunter domain
    # search on whatever domain we have (Apollo's if any, else website).
    candidate_domain = _candidate_domain(apollo_domain, website)

    # Layer 3: Hunter domain-search
    if candidate_domain and not hunter_disabled:
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

    # Layer 4: Prospeo person-enrich. Paid (1 cr/email, 10 cr/phone) but
    # higher hit rate on small-business decision-makers than Hunter when
    # the company has any web presence at all. Skipped if no candidate
    # domain (Prospeo needs at least a company hint).
    #
    # owner_name passthrough (2026-05-12 schema fix): Prospeo /enrich-person
    # REQUIRES a person identifier (first/last + company, OR full_name +
    # company, OR linkedin_url, OR person_id). When Apollo found the
    # person but the email reveal missed, apollo_name is populated --
    # forward it so Prospeo can target the same decision-maker directly
    # (1 credit, no /search-person hop). When apollo_name is empty,
    # prospeo_client falls back to /search-person internally to locate a
    # decision-maker by company website. See prospeo_client docstring
    # for the full schema rationale.
    if candidate_domain:
        try:
            prospeo_result = prospeo_enrich_company(
                business_name=business_name,
                domain=candidate_domain,
                city=city,
                owner_name=apollo_name,
                want_phone=False,  # phone-enrich is 10 credits; keep cheap here
            )
        except Exception as e:
            logger.warning(f"_resolve_email: Prospeo error on {candidate_domain}: {e}")
            prospeo_result = None

        if prospeo_result and prospeo_result.get("email"):
            try:
                vetted = gate_email(prospeo_result["email"], source="sw_topup_prospeo")
                prospeo_name = (prospeo_result.get("name") or apollo_name or "").strip()
                return vetted, "prospeo", prospeo_name
            except EmailGateDrop as e:
                logger.info(
                    f"_resolve_email: prospeo email {prospeo_result['email']} dropped ({e.reason})"
                )

    return "", "", ""


def topup(minimum: int = DAILY_MINIMUM, dry_run: bool = False) -> int:
    """Harvest SW leads until `minimum` saved emails, walking the ladder.

    Per-process protections (locked 2026-05-12):
    - Hunter per-process cap raised to 400 internally via env (override
      with HUNTER_MAX_SEARCHES_PER_DAY before call to keep a lower ceiling).
    - 45-minute wall-clock cap. Exits gracefully and fires Telegram alert
      if the loop runs past the deadline regardless of `minimum`.
    - Resolution chain: Firecrawl -> Apollo -> Hunter domain-search ->
      Prospeo company-enrich -> phone/website-only save (does not count
      toward email target).

    Returns count of email-verified leads saved this run.
    """
    # Raise Hunter per-process cap to 400 unless caller pinned a lower value.
    # Honors any explicit lower override (e.g. tests set "9").
    # Bad config (non-integer string) must NOT crash the harvest step — log a
    # warning and treat as unset. Codex review P1 2026-05-12.
    env_cap_raw = os.environ.get("HUNTER_MAX_SEARCHES_PER_DAY")
    env_cap_int: int | None = None
    if env_cap_raw:
        try:
            env_cap_int = int(env_cap_raw)
        except ValueError:
            logger.warning(
                "topup: HUNTER_MAX_SEARCHES_PER_DAY=%r is not an integer; "
                "falling back to HUNTER_CAP_DAILY=%d",
                env_cap_raw, HUNTER_CAP_DAILY,
            )
            env_cap_int = None
    if env_cap_int is None or env_cap_int < HUNTER_CAP_DAILY:
        # Only raise; never lower a stricter caller-set value (tests rely on this).
        if env_cap_int is None:
            os.environ["HUNTER_MAX_SEARCHES_PER_DAY"] = str(HUNTER_CAP_DAILY)

    reset_daily_counter()
    saved = 0
    consecutive_double_fails = 0
    hunter_disabled = False
    cap_alert_sent = False
    breaker_alert_sent = False
    wall_clock_alert_sent = False
    started_at = time.monotonic()

    for niche, city, tier, default_target in PAIRS:
        if saved >= minimum:
            break
        if time.monotonic() - started_at > WALL_CLOCK_SECONDS:
            if not wall_clock_alert_sent:
                _telegram_alert(
                    f"SW pipeline: 45min wall-clock cap hit at {saved}/{minimum} leads. "
                    "Exiting topup() gracefully. Re-run will pick up next ladder pair."
                )
                wall_clock_alert_sent = True
            logger.warning(
                f"topup: wall-clock cap ({WALL_CLOCK_SECONDS}s) reached at {saved}/{minimum}, exiting"
            )
            break

        try:
            scraped = scrape_google_maps_leads(niche=niche, city=city, limit=20)
        except Exception as e:
            logger.warning(f"topup: Serper failed for {niche}/{city}: {e}")
            continue

        for biz in scraped:
            if saved >= minimum:
                break
            if time.monotonic() - started_at > WALL_CLOCK_SECONDS:
                # Inner-loop wall-clock guard. Same alert as outer; broken out
                # so we exit mid-scrape-batch instead of mid-niche.
                if not wall_clock_alert_sent:
                    _telegram_alert(
                        f"SW pipeline: 45min wall-clock cap hit at {saved}/{minimum} leads. "
                        "Exiting topup() gracefully. Re-run will pick up next ladder pair."
                    )
                    wall_clock_alert_sent = True
                logger.warning(
                    f"topup: wall-clock cap reached mid-niche at {saved}/{minimum}, exiting"
                )
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
                        "SW pipeline: Hunter daily cap hit. Falling back to Prospeo "
                        "(then skip) for remaining leads. Run continues."
                    )
                    cap_alert_sent = True
                # Hunter cap doesn't kill Prospeo; re-resolve with hunter disabled
                # so Prospeo still runs as the layer-4 fallback for THIS lead.
                try:
                    email, source, owner_name = _resolve_email(biz, hunter_disabled=True)
                except Exception:
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
