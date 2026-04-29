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
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
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
    logger.info("=" * 60)
    logger.info(f"Daily outreach run: {datetime.now().strftime('%Y-%m-%d %H:%M MT')}")
    logger.info("=" * 60)

    bounce_nulled = 0
    sw_leads = 0
    sw_drafted = 0
    cw_drafted = 0

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
        sw_leads = topup(minimum=10)
        logger.info(f"  Done. {sw_leads} Signal Works email leads ready.")
    except Exception as e:
        logger.error(f"  Signal Works topup failed: {e}")

    # ── Step 3: Signal Works -- 4-touch sequence (draft, manual review) ──
    logger.info("STEP 3: Signal Works sequence T1-T4 (drafts, manual review)...")
    try:
        from skills.outreach.sequence_engine import run_sequence
        sw_result = run_sequence("sw", dry_run=False, daily_limit=10)
        sw_drafted = sw_result.get("drafted", 0)
        logger.info(f"  Done. {sw_drafted} SW sequence drafts created.")
    except Exception as e:
        logger.error(f"  Signal Works sequence failed: {e}")

    # ── Step 4: Catalyst Works -- Apollo lead topup ───────────────
    logger.info("STEP 4: Catalyst Works lead topup via Apollo (target: 10 leads)...")
    try:
        from signal_works.topup_cw_leads import topup_cw_leads
        cw_leads = topup_cw_leads(minimum=10)
        logger.info(f"  Done. {cw_leads} CW email leads ready.")
    except Exception as e:
        logger.error(f"  CW Apollo topup failed: {e}")

    # ── Step 4.5: CW voice personalization (transcript-style-dna) ─
    voice_personalized = 0
    logger.info("STEP 4.5: Voice-personalize today's CW leads (transcript-style-dna)...")
    try:
        from signal_works.voice_personalizer import personalize_pending_leads
        # Match daily_limit of CW sequence so we never over-personalize
        voice_personalized = personalize_pending_leads(limit=10)
        logger.info(f"  Done. {voice_personalized} leads personalized.")
    except Exception as e:
        # Best-effort: a failure here must not block CW sequence from running
        # with template-only opens.
        logger.error(f"  Voice personalization failed (non-fatal): {e}")

    # ── Step 5: Catalyst Works -- 4-touch sequence (auto-send) ───
    logger.info("STEP 5: Catalyst Works sequence T1-T4 (auto-send)...")
    try:
        from skills.outreach.sequence_engine import run_sequence
        cw_result = run_sequence("cw", dry_run=False, daily_limit=10)
        cw_drafted = cw_result.get("sent", 0)
        logger.info(f"  Done. {cw_drafted} CW emails sent.")
    except Exception as e:
        logger.error(f"  CW sequence failed: {e}")

    # ── Summary ───────────────────────────────────────────────────
    total = sw_drafted + cw_drafted
    logger.info("=" * 60)
    logger.info(f"Run complete:")
    logger.info(f"  Bounces cleared:        {bounce_nulled}")
    logger.info(f"  SW leads harvested:     {sw_leads}")
    logger.info(f"  SW drafts created:      {sw_drafted}")
    logger.info(f"  CW leads personalized:  {voice_personalized}")
    logger.info(f"  CW outreach drafts:     {cw_drafted}")
    logger.info(f"  TOTAL drafts in inbox:  {total}")
    if total > 0:
        logger.info("  Check boubacar@catalystworks.consulting Drafts -- ready to send.")
    logger.info("=" * 60)
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
