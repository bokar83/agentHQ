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
  5b. CW recycle -- re-touch yesterday's CW queue if Step 5 below CW_THRESHOLD

Total: up to 20 touches per day across both pipelines.
CW emails auto-send. SW emails land in Drafts for review.

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

    # ── Step 4: Catalyst Works -- Apollo lead topup ───────────────
    _RUN_STATE["step"] = "cw_harvest"
    logger.info("STEP 4: Catalyst Works lead topup via Apollo (target: 20 leads, full US)...")
    cw_leads = 0
    try:
        from signal_works.topup_cw_leads import topup_cw_leads
        from signal_works.harvest_until_target import _count_today_cw_with_email
        # force_fresh=True bypasses the _count_ready_cw_leads short-circuit so
        # Apollo harvest runs every morning regardless of stale ready-pool count.
        # Previously this caused CW T1 to go dead from 2026-05-08 onward.
        topup_cw_leads(minimum=20, force_fresh=True)
        # DB truth for the metric, not topup_cw_leads() return value.
        cw_leads = _count_today_cw_with_email()
        logger.info(f"  Done. {cw_leads} CW email leads created today (DB truth).")
        log_step("cw_harvest", attempted=20, succeeded=cw_leads)
    except Exception as e:
        logger.error(f"  CW Apollo topup failed: {e}")
        log_step("cw_harvest", attempted=20, reason=f"error: {type(e).__name__}")
    _RUN_STATE["cw_leads"] = cw_leads

    # ── Step 4.5: CW voice personalization (transcript-style-dna) ─
    _RUN_STATE["step"] = "cw_voice_personalize"
    voice_personalized = 0
    logger.info("STEP 4.5: Voice-personalize today's CW leads (transcript-style-dna)...")
    try:
        from signal_works.voice_personalizer import personalize_pending_leads
        # Match daily_limit of CW sequence so we never over-personalize
        voice_personalized = personalize_pending_leads(limit=15)
        logger.info(f"  Done. {voice_personalized} leads personalized.")
        log_step("cw_voice_personalize", attempted=15, succeeded=voice_personalized,
                 skipped=max(0, 15 - voice_personalized))
    except Exception as e:
        # Best-effort: a failure here must not block CW sequence from running
        # with template-only opens.
        logger.error(f"  Voice personalization failed (non-fatal): {e}")
        log_step("cw_voice_personalize", attempted=15, reason=f"error: {type(e).__name__}")
    _RUN_STATE["voice_personalized"] = voice_personalized

    # ── Step 5: Catalyst Works -- 4-touch sequence (auto-send) ───
    _RUN_STATE["step"] = "cw_sequence"
    if is_weekend:
        logger.info("STEP 5: SKIPPED on weekend (no CW sends Sat/Sun).")
        log_step("cw_sequence", reason="weekend_skip")
    else:
        logger.info("STEP 5: Catalyst Works sequence T1-T5 (auto-send)...")
        try:
            from skills.outreach.sequence_engine import run_sequence
            cw_result = run_sequence("cw", dry_run=False, t1_cap=15, followup_cap=150)
            cw_drafted = cw_result.get("drafted", 0) + cw_result.get("sent", 0)
            cw_per_touch = cw_result.get("per_touch", {})
            logger.info(f"  Done. {cw_drafted} CW emails drafted. per_touch={cw_per_touch}")
            log_step("cw_sequence", attempted=15, succeeded=cw_drafted)
        except Exception as e:
            logger.error(f"  CW sequence failed: {e}")
            log_step("cw_sequence", attempted=15, reason=f"error: {type(e).__name__}")

        # ── Step 5b: T-advance recycle when below floor ──
        # If today's CW T1 pool was thin and Step 5 produced fewer than
        # CW_THRESHOLD drafts/sends, age-back the last_contacted_at on a cohort
        # of leads we contacted in the past 7 days (T1..T4) so their *next*
        # touch becomes due. Then re-run run_sequence("cw") with t1_cap=0 so
        # only follow-ups fire. Finally mark those new sw_email_log rows as
        # recycle=TRUE so analytics can separate primary volume from recycle.
        #
        # All existing template/personalisation/auto-send logic is reused. No
        # duplicate touch-progression code in recycle_cw. Honors AUTO_SEND_CW.
        if cw_drafted < CW_THRESHOLD:
            _RUN_STATE["step"] = "cw_recycle"
            shortfall = CW_THRESHOLD - cw_drafted
            logger.info(
                f"STEP 5b: CW drafted {cw_drafted}/{CW_THRESHOLD}. "
                f"T-advancing recyclable leads to top up shortfall of {shortfall}..."
            )
            try:
                from signal_works.recycle_cw import (
                    recycle_yesterdays_cw,
                    mark_today_recycled,
                )
                advanced_emails = recycle_yesterdays_cw(min_floor=shortfall)
                logger.info(
                    f"  Advanced {len(advanced_emails)} CW leads "
                    f"({', '.join(advanced_emails[:3])}"
                    f"{'...' if len(advanced_emails) > 3 else ''})."
                )
                if advanced_emails:
                    # Re-run CW sequence: T1 disabled, followups capped at the
                    # advanced cohort size. _get_due_leads now finds these leads
                    # because we just aged their last_contacted_at past the gap.
                    recycle_result = run_sequence(
                        "cw", dry_run=False,
                        t1_cap=0, followup_cap=len(advanced_emails),
                    )
                    cw_recycled = (
                        recycle_result.get("drafted", 0)
                        + recycle_result.get("sent", 0)
                    )
                    # Mark the rows we just wrote as recycle=TRUE (recycle BOOL
                    # column on sw_email_log, added by migration 008).
                    mark_today_recycled(advanced_emails)
                    logger.info(
                        f"  Recycle pass: {cw_recycled} touches sent/drafted. "
                        f"per_touch={recycle_result.get('per_touch', {})}"
                    )
                    log_step(
                        "cw_recycle",
                        attempted=len(advanced_emails),
                        succeeded=cw_recycled,
                    )
                else:
                    log_step("cw_recycle", attempted=shortfall, succeeded=0,
                             reason="no_eligible_leads")
            except Exception as e:
                logger.error(f"  CW recycle failed (non-fatal): {e}")
                log_step("cw_recycle", attempted=shortfall,
                         reason=f"error: {type(e).__name__}")
    _RUN_STATE["cw_drafted"] = cw_drafted
    _RUN_STATE["cw_recycled"] = cw_recycled

    # ── Summary ───────────────────────────────────────────────────
    total = sw_drafted + cw_drafted + cw_recycled
    logger.info("=" * 60)
    logger.info(f"Run complete:")
    logger.info(f"  Bounces cleared:        {bounce_nulled}")
    logger.info(f"  SW leads harvested:     {sw_leads}")
    logger.info(f"  SW drafts created:      {sw_drafted}")
    logger.info(f"  CW leads personalized:  {voice_personalized}")
    logger.info(f"  CW outreach drafts:     {cw_drafted}")
    logger.info(f"  CW recycled (5b):       {cw_recycled}")
    logger.info(f"  TOTAL drafts in inbox:  {total}")
    if total > 0:
        logger.info("  Check boubacar@catalystworks.consulting Drafts -- ready to send.")
    try:
        from signal_works.pipeline_metrics import apollo_credits_used_today
        logger.info(f"  Apollo credits used today: {apollo_credits_used_today()}")
    except Exception:
        pass
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
    # Thresholds aligned with daily targets: SW=35, CW=15.
    # Constants live at module level (also drives Step 5b recycle floor).
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
