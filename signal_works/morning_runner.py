"""
signal_works/morning_runner.py
Unified daily runner -- Signal Works + Catalyst Works outreach.
Runs at 07:00 MT via Windows Task Scheduler (see register_task_admin.ps1).

Sequence:
  1. Bounce scan (2-day lookback on boubacar@catalystworks.consulting)
  2. Signal Works topup -- harvest until 10 email leads exist (Serper/Firecrawl)
  3. Signal Works drafts -- 10 emails to boubacar@catalystworks.consulting Drafts
  4. Catalyst Works topup -- harvest via Apollo.io (credit-efficient ICP scoring)
  5. Catalyst Works outreach -- 10 CRM lead drafts to same Drafts folder

Total: up to 20 drafts per day in boubacar@catalystworks.consulting.
You review, personalise if needed, hit Send. That's it.

Logs to: logs/signal_works_morning.log
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

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

    # ── Step 3: Signal Works -- create drafts ─────────────────────
    logger.info("STEP 3: Signal Works drafts (10 emails)...")
    try:
        from signal_works.send_drafts import run as sw_send
        sw_drafted = sw_send(limit=10, test_mode=False)
        logger.info(f"  Done. {sw_drafted} Signal Works drafts created.")
    except Exception as e:
        logger.error(f"  Signal Works drafts failed: {e}")

    # ── Step 4: Catalyst Works -- Apollo lead topup ───────────────
    logger.info("STEP 4: Catalyst Works lead topup via Apollo (target: 10 leads)...")
    try:
        from signal_works.topup_cw_leads import topup_cw_leads
        cw_leads = topup_cw_leads(minimum=10)
        logger.info(f"  Done. {cw_leads} CW email leads ready.")
    except Exception as e:
        logger.error(f"  CW Apollo topup failed: {e}")

    # ── Step 5: Catalyst Works -- cold outreach drafts ────────────
    logger.info("STEP 5: Catalyst Works cold outreach drafts (10 leads)...")
    try:
        from signal_works.outreach_runner import run as cw_send
        cw_drafted = cw_send()
        logger.info(f"  Done. {cw_drafted} CW outreach drafts created.")
    except Exception as e:
        logger.error(f"  CW outreach failed: {e}")

    # ── Summary ───────────────────────────────────────────────────
    total = sw_drafted + cw_drafted
    logger.info("=" * 60)
    logger.info(f"Run complete:")
    logger.info(f"  Bounces cleared:        {bounce_nulled}")
    logger.info(f"  SW leads harvested:     {sw_leads}")
    logger.info(f"  SW drafts created:      {sw_drafted}")
    logger.info(f"  CW outreach drafts:     {cw_drafted}")
    logger.info(f"  TOTAL drafts in inbox:  {total}")
    if total > 0:
        logger.info("  Check boubacar@catalystworks.consulting Drafts -- ready to send.")
    logger.info("=" * 60)
    return 0 if total > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
