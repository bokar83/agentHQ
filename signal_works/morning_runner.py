"""
signal_works/morning_runner.py
Unified daily runner -- Signal Works + Catalyst Works outreach.
Runs at 07:00 MT via VPS systemd timer (see scripts/systemd/signal-works-morning.*).

Sequence:
  1. Bounce scan (2-day lookback on boubacar@catalystworks.consulting)
  2. Signal Works topup -- harvest until 10 email leads exist (Serper/Firecrawl)
  3. Signal Works sequence -- T1-T4 drafts (manual review, SW pipeline)

CW automation removed 2026-05-12. Steps 4 / 4.5 / 5 / 5b stripped per Sankofa
Council premortem verdict: CW = 0 replies on 127 sends + 142 messaged all-time;
Apollo cold scrape is not the right channel for consulting. CW pipeline now
operates manually only -- new CW prospects added by hand to cw_target_list.csv
(permission filter: must already know who Boubacar is). Existing CW leads
already in the DB continue to advance through T2-T5 via sequence_engine cron
elsewhere; this runner no longer harvests, personalizes, sends T1, or recycles
for CW. See docs/handoff/2026-05-12-cw-strip-rationale.md (TBD) and roadmap
docs/roadmap/harvest.md.

Total: SW touches only via this runner.
SW emails land in Drafts for review.

Logs to: logs/signal_works_morning.log
On any unhandled exception or zero-draft run, fires a Telegram alert.
On early exit (systemd timeout, crash before main_body completes), atexit fires
a partial-state Telegram alert so we never silently die mid-pipeline.
"""
import atexit
import logging
import os
import socket
import sys
import threading
import traceback
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# ── Run state (module-level for atexit visibility) ────────────────
# Updated as the runner progresses. atexit reads this to fire a partial-state
# Telegram alert if the process exits before _main_body returns cleanly.
_RUN_STATE = {
    "started": False,
    "completed": False,
    "step": "init",
    "bounce_nulled": 0,
    "sw_leads": 0,
    "sw_drafted": 0,
    "cw_leads": 0,
    "cw_drafted": 0,
    "voice_personalized": 0,
    "cw_recycled": 0,
}

# Step 2 internal wall-clock cap. Default 60min; override via env.
_SW_TOPUP_TIMEOUT_SEC = int(os.environ.get("SW_TOPUP_TIMEOUT_SEC", "3600"))

# Health-check thresholds. Also drive the Step 5b CW recycle floor.
SW_THRESHOLD = 30
CW_THRESHOLD = 10


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


def _partial_state_atexit() -> None:
    """
    Fire Telegram alert with partial state if process exits before _main_body
    completes. Covers systemd SIGTERM/timeout kills + crashes that escape the
    exception handler. Never raises.

    Skips if:
      - runner never started (init failure or another runner already holds claim)
      - runner completed cleanly (regular health-check + 0-draft alerts handle it)
    """
    try:
        if not _RUN_STATE.get("started"):
            return
        if _RUN_STATE.get("completed"):
            return
        msg = (
            "agentsHQ morning runner EXITED EARLY at step="
            f"{_RUN_STATE.get('step')}.\n"
            f"  bounce_nulled:        {_RUN_STATE.get('bounce_nulled')}\n"
            f"  sw_leads:             {_RUN_STATE.get('sw_leads')}\n"
            f"  sw_drafted:           {_RUN_STATE.get('sw_drafted')}\n"
            f"  cw_leads:             {_RUN_STATE.get('cw_leads')}\n"
            f"  voice_personalized:   {_RUN_STATE.get('voice_personalized')}\n"
            f"  cw_drafted:           {_RUN_STATE.get('cw_drafted')}\n"
            f"  cw_recycled:          {_RUN_STATE.get('cw_recycled')}\n"
            "Check /var/log/signal_works_morning.log."
        )
        _telegram_alert(msg)
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

    # Register partial-state atexit BEFORE claim so a claim-side crash still alerts.
    # Idempotent: never fires unless _RUN_STATE["started"] flips True.
    atexit.register(_partial_state_atexit)

    holder = f"{socket.gethostname()}/pid={os.getpid()}"
    task = claim(resource="task:morning-runner", holder=holder, ttl_seconds=1800)
    if task is None:
        logger.warning(
            "Another morning_runner is already running. Exiting cleanly. "
            "Resource 'task:morning-runner' is held; check skills.coordination.list_running()."
        )
        return 0

    try:
        _RUN_STATE["started"] = True
        return _main_body()
    finally:
        complete(task["id"])


def _main_body():
    logger.info("=" * 60)
    logger.info(f"Daily outreach run: {datetime.now().strftime('%Y-%m-%d %H:%M MT')}")
    logger.info("=" * 60)

    # Best-effort metrics logger. Never raises if DB is unavailable.
    try:
        from signal_works.pipeline_metrics import log_step
    except Exception:
        def log_step(*a, **kw):
            pass

    bounce_nulled = 0
    sw_leads = 0
    sw_drafted = 0
    cw_drafted = 0
    cw_recycled = 0

    # Weekday gate: harvest every day, but only send Mon-Fri.
    # Saturday=5, Sunday=6. Uses local time of the runner (orc-crewai container).
    is_weekend = datetime.now().weekday() >= 5
    if is_weekend:
        day_name = datetime.now().strftime("%A")
        logger.info("Weekend detected (" + day_name + "). Will harvest leads but SKIP email send steps.")

    # ── Step 1: Bounce scan ───────────────────────────────────────
    _RUN_STATE["step"] = "bounce_scan"
    logger.info("STEP 1: Bounce scan (boubacar@catalystworks.consulting, last 2 days)...")
    try:
        from signal_works.bounce_scanner import run as bounce_scan
        bounce_nulled = bounce_scan(days=2)
        logger.info(f"  Done. {bounce_nulled} bounced emails nulled in DB.")
        log_step("bounce_scan", succeeded=bounce_nulled)
    except Exception as e:
        logger.error(f"  Bounce scan failed: {e}")
        log_step("bounce_scan", reason=f"error: {type(e).__name__}")
    _RUN_STATE["bounce_nulled"] = bounce_nulled

    # ── Step 2: Signal Works -- harvest leads ─────────────────────
    # Wall-clock cap: topup() is opaque and historically has hung (Serper rate
    # limits, Firecrawl backoff). Run it in a daemon thread and join with a
    # bounded wait so Step 3-5 always get a chance to execute. If we time out,
    # log_step records skipped+reason and we read DB truth for whatever leads
    # the thread already saved.
    _RUN_STATE["step"] = "sw_harvest"
    logger.info(
        f"STEP 2: Signal Works lead harvest (target: 35 email leads, "
        f"wall-clock cap: {_SW_TOPUP_TIMEOUT_SEC}s)..."
    )
    _topup_error = {"err": None}

    def _run_topup():
        try:
            from signal_works.topup_leads import topup
            topup(minimum=35)
        except Exception as e:  # captured -- thread cannot raise into caller
            _topup_error["err"] = e

    topup_thread = threading.Thread(target=_run_topup, name="sw-topup", daemon=True)
    topup_thread.start()
    topup_thread.join(timeout=_SW_TOPUP_TIMEOUT_SEC)
    try:
        from signal_works.harvest_until_target import _count_today_sw_with_email
        sw_leads = _count_today_sw_with_email()
    except Exception as e:
        logger.error(f"  Could not read SW lead count: {e}")
        sw_leads = 0

    if topup_thread.is_alive():
        logger.warning(
            f"  Step 2 wall-clock cap hit at {_SW_TOPUP_TIMEOUT_SEC}s. "
            f"topup() still running in background daemon thread; will be killed on process exit. "
            f"DB shows {sw_leads} SW email leads so far. Continuing to Step 3."
        )
        log_step(
            "sw_harvest", attempted=35, succeeded=sw_leads,
            skipped=max(0, 35 - sw_leads),
            reason=f"wall_clock_timeout_{_SW_TOPUP_TIMEOUT_SEC}s",
        )
    elif _topup_error["err"] is not None:
        e = _topup_error["err"]
        logger.error(f"  Signal Works topup failed: {e}")
        log_step("sw_harvest", attempted=35, succeeded=sw_leads,
                 reason=f"error: {type(e).__name__}")
    else:
        # DB truth, not topup() return value. The return value counts
        # UPDATE-on-match as a fresh save, masking re-discovery of the same
        # 250 Provo/Vegas leads day after day. Read fresh-inserted-with-email
        # straight from the leads table for an honest metric.
        logger.info(f"  Done. {sw_leads} SW email leads created today (DB truth).")
        log_step("sw_harvest", attempted=35, succeeded=sw_leads)
    _RUN_STATE["sw_leads"] = sw_leads

    # ── Step 3: Signal Works -- 4-touch sequence (draft, manual review) ──
    _RUN_STATE["step"] = "sw_sequence"
    if is_weekend:
        logger.info("STEP 3: SKIPPED on weekend (no SW sends Sat/Sun).")
        log_step("sw_sequence", reason="weekend_skip")
    else:
        logger.info("STEP 3: Signal Works sequence T1-T4 (drafts, manual review)...")
        try:
            from skills.outreach.sequence_engine import run_sequence
            sw_result = run_sequence("sw", dry_run=False, t1_cap=35, followup_cap=150)
            sw_drafted = sw_result.get("drafted", 0) + sw_result.get("sent", 0)
            sw_per_touch = sw_result.get("per_touch", {})
            logger.info(f"  Done. {sw_drafted} SW sequence drafts created. per_touch={sw_per_touch}")
            log_step("sw_sequence", attempted=35, succeeded=sw_drafted)
        except Exception as e:
            logger.error(f"  Signal Works sequence failed: {e}")
            log_step("sw_sequence", attempted=35, reason=f"error: {type(e).__name__}")
    _RUN_STATE["sw_drafted"] = sw_drafted

    # ── Steps 4 / 4.5 / 5 / 5b: CW automation REMOVED 2026-05-12 ─────
    # CW auto-harvest (Apollo), voice-personalize, T1 auto-send, and recycle
    # were all removed after Sankofa Council premortem verdict:
    #   - 0 replies on 127 CW sends + 142 messaged all-time
    #   - Apollo widened-ICP yielded 97.6% email coverage -> sourcing was fine,
    #     conversion was the actual failure
    #   - Cold scrape is the wrong channel for consulting; CW needs recognition
    #     + warm referrals + content engagement, not more volume
    # CW pipeline now operates manually: new leads added by hand to
    # data/cw_target_list.csv (permission filter: prospect must already know
    # who Boubacar is -- warm referrals, completed SW audits, content-engagement
    # DMs only). Existing CW leads already in the DB continue to advance
    # through T2-T5 via the regular sequence_engine cron elsewhere; nothing
    # in this runner kills those follow-ups.

    # ── Summary ───────────────────────────────────────────────────
    # CW counters retained at 0 for downstream payload symmetry only.
    total = sw_drafted + cw_drafted + cw_recycled
    logger.info("=" * 60)
    logger.info(f"Run complete:")
    logger.info(f"  Bounces cleared:        {bounce_nulled}")
    logger.info(f"  SW leads harvested:     {sw_leads}")
    logger.info(f"  SW drafts created:      {sw_drafted}")
    logger.info(f"  TOTAL drafts in inbox:  {total}")
    if total > 0:
        logger.info("  Check boubacar@catalystworks.consulting Drafts -- ready to send.")
    logger.info("=" * 60)

    # ── Delegation: enqueue run summary for downstream consumers ──────
    # Design ref: skills/coordination/references/agent-delegation-pattern.md
    # Kind: sw:run-complete — downstream agents can claim_next("sw:run-complete")
    # to trigger follow-up work (digest posting, anomaly review, etc.)
    # Pure addition: never blocks, never raises.
    try:
        from skills.coordination import enqueue
        enqueue(
            kind="sw:run-complete",
            payload={
                "date": datetime.now().strftime("%Y-%m-%d"),
                "sw_drafted": sw_drafted,
                "cw_drafted": cw_drafted,
                "cw_recycled": cw_recycled,
                "total": total,
                "sw_leads": sw_leads,
                "bounce_nulled": bounce_nulled,
                "is_weekend": is_weekend,
            },
        )
        logger.info("DELEGATION: sw:run-complete enqueued for downstream consumers.")
    except Exception as _e:
        logger.warning(f"DELEGATION: enqueue failed (non-fatal): {_e}")

    # ── Step 7: Reserve Works daily paper trade nudge (weekdays only) ─
    if not is_weekend:
        rw_msg = (
            "RW paper trade check-in\n\n"
            "Log today's wheel candidate (or 'skipped -- reason').\n"
            "Ticker / action / score / why. 60 seconds.\n\n"
            "Gate 4: 30 closed trades with journal. You need this to clear Tier 0."
        )
        try:
            from orchestrator.notifier import send_message, send_email
            chat_id = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("OWNER_TELEGRAM_CHAT_ID", "")
            if chat_id:
                send_message(chat_id, rw_msg)
            send_email(
                subject=f"RW paper trade nudge -- {datetime.now().strftime('%Y-%m-%d')}",
                body=rw_msg,
                to_addresses=["bokar83@gmail.com"],
            )
            logger.info("  RW nudge sent (Telegram + email).")
        except Exception as e:
            logger.warning(f"  RW nudge failed (non-fatal): {e}")

    # ── Harvest Health Check ─────────────────────────────────────
    # Alert when below threshold even if total > 0. Prevents silent
    # under-performance going unnoticed until the daily report email.
    # SW-only after 2026-05-12 CW strip. CW threshold check removed -- CW
    # automation no longer runs from this runner, so cw_drafted=0 is expected.
    health_warnings = []
    if not is_weekend:
        if sw_drafted < SW_THRESHOLD:
            health_warnings.append(f"SW drafts low: {sw_drafted}/{SW_THRESHOLD}")
    if health_warnings:
        msg = "agentsHQ morning runner: harvest below threshold.\n" + "\n".join(health_warnings)
        msg += f"\nTotal drafts: {total}. Check /var/log/signal_works_morning.log."
        _telegram_alert(msg)
        logger.warning(f"Harvest health check: {'; '.join(health_warnings)}")

    # Mark clean completion. atexit handler reads this and skips the partial-state
    # alert when set.
    _RUN_STATE["step"] = "complete"
    _RUN_STATE["completed"] = True
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
