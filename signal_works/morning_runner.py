"""
signal_works/morning_runner.py
Unified daily runner -- Signal Works + Catalyst Works outreach.
Runs at 07:00 MT via VPS systemd timer (see scripts/systemd/signal-works-morning.*).

Sequence:
  1. Bounce scan (2-day lookback on boubacar@catalystworks.consulting)
  2. Signal Works topup -- harvest until 10 email leads exist (Serper/Firecrawl)
  3. Signal Works sequence -- T1-T4 drafts (manual review, SW pipeline)
  4. Catalyst Works topup -- harvest via Apollo.io (credit-efficient ICP scoring)
  5. Catalyst Works sequence -- T1-T4 auto-send (CW pipeline)

Total: up to 20 touches per day across both pipelines.
CW emails auto-send. SW emails land in Drafts for review.

Logs to: logs/signal_works_morning.log
On any unhandled exception or zero-draft run, fires a Telegram alert.
"""
import logging
import os
import socket
import sys
import traceback
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _telegram_alert(msg: str) -> None:
    """Best-effort Telegram alert. Never raises -- failure here must not crash the runner."""
    token = os.getenv("ORCHESTRATOR_TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("OWNER_TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    try:
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": msg[:4000]}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data,
            method="POST",
        )
        urllib.request.urlopen(req, timeout=15).read()
    except Exception:
        pass

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "signal_works_morning.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "orchestrator"))


def main():
    from skills.coordination import claim, complete

    holder = f"{socket.gethostname()}/pid={os.getpid()}"
    task = claim(resource="task:morning-runner", holder=holder, ttl_seconds=1800)
    if task is None:
        logger.warning(
            "Another morning_runner is already running. Exiting cleanly. "
            "Resource 'task:morning-runner' is held; check skills.coordination.list_running()."
        )
        return 0

    try:
        return _main_body()
    finally:
        complete(task["id"])


def _main_body():
    logger.info("=" * 60)
    logger.info(f"Daily outreach run: {datetime.now().strftime('%Y-%m-%d %H:%M MT')}")
    logger.info("=" * 60)

    bounce_nulled = 0
    sw_leads = 0
    sw_drafted = 0
    cw_drafted = 0
    studio_drafted = 0

    # Weekday gate: harvest every day, but only send Mon-Fri.
    # Saturday=5, Sunday=6. Uses local time of the runner (orc-crewai container).
    is_weekend = datetime.now().weekday() >= 5
    if is_weekend:
        day_name = datetime.now().strftime("%A")
        logger.info("Weekend detected (" + day_name + "). Will harvest leads but SKIP email send steps.")

    # ── Step 1: Bounce scan ───────────────────────────────────────
    logger.info("STEP 1: Bounce scan (boubacar@catalystworks.consulting, last 2 days)...")
    try:
        from signal_works.bounce_scanner import run as bounce_scan
        bounce_nulled = bounce_scan(days=2)
        logger.info(f"  Done. {bounce_nulled} bounced emails nulled in DB.")
    except Exception as e:
        logger.error(f"  Bounce scan failed: {e}")

    # ── Step 2: Signal Works -- harvest leads ─────────────────────
    logger.info("STEP 2: Signal Works lead harvest (target: 10 email leads)...")
    try:
        from signal_works.topup_leads import topup
        sw_leads = topup(minimum=35)
        logger.info(f"  Done. {sw_leads} Signal Works email leads ready.")
    except Exception as e:
        logger.error(f"  Signal Works topup failed: {e}")

    # ── Step 3: Signal Works -- 4-touch sequence (draft, manual review) ──
    if is_weekend:
        logger.info("STEP 3: SKIPPED on weekend (no SW sends Sat/Sun).")
    else:
        logger.info("STEP 3: Signal Works sequence T1-T4 (drafts, manual review)...")
        try:
            from skills.outreach.sequence_engine import run_sequence
            sw_result = run_sequence("sw", dry_run=False, daily_limit=35)
            sw_drafted = sw_result.get("drafted", 0) + sw_result.get("sent", 0)
            logger.info(f"  Done. {sw_drafted} SW sequence drafts created.")
        except Exception as e:
            logger.error(f"  Signal Works sequence failed: {e}")

    # ── Step 4: Catalyst Works -- Apollo lead topup ───────────────
    logger.info("STEP 4: Catalyst Works lead topup via Apollo (target: 20 leads, full US)...")
    try:
        from signal_works.topup_cw_leads import topup_cw_leads
        cw_leads = topup_cw_leads(minimum=20)
        logger.info(f"  Done. {cw_leads} CW email leads ready.")
    except Exception as e:
        logger.error(f"  CW Apollo topup failed: {e}")

    # ── Step 4b: Studio -- Apollo lead topup (full US) ────────────
    studio_leads = 0
    logger.info("STEP 4b: Studio lead topup via Apollo (target: 25 leads, full US)...")
    try:
        from signal_works.topup_studio_leads import topup_studio_leads
        studio_leads = topup_studio_leads(minimum=25)
        logger.info(f"  Done. {studio_leads} Studio email leads ready.")
    except Exception as e:
        logger.error(f"  Studio Apollo topup failed: {e}")

    # ── Step 4.5: CW voice personalization (transcript-style-dna) ─
    voice_personalized = 0
    logger.info("STEP 4.5: Voice-personalize today's CW leads (transcript-style-dna)...")
    try:
        from signal_works.voice_personalizer import personalize_pending_leads
        # Match daily_limit of CW sequence so we never over-personalize
        voice_personalized = personalize_pending_leads(limit=15)
        logger.info(f"  Done. {voice_personalized} leads personalized.")
    except Exception as e:
        # Best-effort: a failure here must not block CW sequence from running
        # with template-only opens.
        logger.error(f"  Voice personalization failed (non-fatal): {e}")

    # ── Step 5: Catalyst Works -- 4-touch sequence (auto-send) ───
    if is_weekend:
        logger.info("STEP 5: SKIPPED on weekend (no CW sends Sat/Sun).")
    else:
        logger.info("STEP 5: Catalyst Works sequence T1-T5 (auto-send)...")
        try:
            from skills.outreach.sequence_engine import run_sequence
            cw_result = run_sequence("cw", dry_run=False, daily_limit=15)
            cw_drafted = cw_result.get("drafted", 0)
            logger.info(f"  Done. {cw_drafted} CW emails drafted.")
        except Exception as e:
            logger.error(f"  CW sequence failed: {e}")


    # Step 5b: SW gap fill -- CW shortfall covered by extra SW to hit 50 total
    if not is_weekend:
        _gap = 50 - sw_drafted - cw_drafted
        if _gap > 0:
            logger.info(f"STEP 5b: SW gap fill -- need {_gap} more to hit 50 total...")
            try:
                from skills.outreach.sequence_engine import run_sequence
                _gap_result = run_sequence("sw", dry_run=False, daily_limit=_gap)
                _extra = _gap_result.get("drafted", 0)
                sw_drafted += _extra
                logger.info(f"  Done. {_extra} extra SW drafts. Total SW today: {sw_drafted}")
            except Exception as e:
                logger.error(f"  SW gap fill failed: {e}")

    # ── Step 6: Studio -- web presence 4-touch sequence (auto-send) ──
    if is_weekend:
        logger.info("STEP 6: SKIPPED on weekend (no Studio sends Sat/Sun).")
    else:
        logger.info("STEP 6: Studio web presence sequence T1-T4 (auto-send)...")
        try:
            from skills.outreach.sequence_engine import run_sequence
            studio_seq = run_sequence("studio", dry_run=False, daily_limit=15)
            studio_drafted = studio_seq.get("drafted", 0) or studio_seq.get("sent", 0)
            logger.info(f"  Done. {studio_drafted} Studio emails drafted.")
        except Exception as e:
            logger.error(f"  Studio sequence failed: {e}")

    # ── Summary ───────────────────────────────────────────────────
    total = sw_drafted + cw_drafted + studio_drafted
    logger.info("=" * 60)
    logger.info(f"Run complete:")
    logger.info(f"  Bounces cleared:        {bounce_nulled}")
    logger.info(f"  SW leads harvested:     {sw_leads}")
    logger.info(f"  SW drafts created:      {sw_drafted}")
    logger.info(f"  CW leads personalized:  {voice_personalized}")
    logger.info(f"  CW outreach drafts:     {cw_drafted}")
    logger.info(f"  Studio leads harvested: {studio_leads}")
    logger.info(f"  Studio outreach drafts: {studio_drafted}")
    logger.info(f"  TOTAL drafts in inbox:  {total}")
    if total > 0:
        logger.info("  Check boubacar@catalystworks.consulting Drafts -- ready to send.")
    logger.info("=" * 60)

    # ── Harvest Health Check ─────────────────────────────────────
    # Alert when below threshold even if total > 0. Prevents silent
    # under-performance going unnoticed until the daily report email.
    # Thresholds aligned with daily targets: SW=35, CW=15.
    SW_THRESHOLD = 30
    CW_THRESHOLD = 10
    health_warnings = []
    if not is_weekend:
        if sw_drafted < SW_THRESHOLD:
            health_warnings.append(f"SW drafts low: {sw_drafted}/{SW_THRESHOLD}")
        if cw_drafted < CW_THRESHOLD:
            health_warnings.append(f"CW drafts low: {cw_drafted}/{CW_THRESHOLD}")
    if health_warnings:
        msg = "agentsHQ morning runner: harvest below threshold.\n" + "\n".join(health_warnings)
        msg += f"\nTotal drafts: {total}. Check /var/log/signal_works_morning.log."
        _telegram_alert(msg)
        logger.warning(f"Harvest health check: {'; '.join(health_warnings)}")

    return 0 if total > 0 else 1


if __name__ == "__main__":
    try:
        rc = main()
        if rc != 0:
            _telegram_alert(
                "agentsHQ morning runner: 0 drafts created today. "
                "Check /var/log/signal_works_morning.log."
            )
        sys.exit(rc)
    except Exception as e:
        _telegram_alert(
            f"agentsHQ morning runner CRASHED: {type(e).__name__}: {e}\n"
            f"Check /var/log/signal_works_morning.log."
        )
        logger.error("Unhandled exception:\n%s", traceback.format_exc())
        raise
