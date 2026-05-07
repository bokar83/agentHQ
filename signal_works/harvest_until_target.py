"""
signal_works/harvest_until_target.py
====================================
Daily harvest runner that does not stop until the email-verified lead target
is hit. Combines SW (35 with email) + CW (15 with email) = 50 total.

Hard rules (locked 2026-05-07):
- Target = 50 leads with VERIFIED EMAIL saved today.
- Email is REQUIRED for the 50-count. Phone-only / website-only leads
  are still saved (existing behavior in topup_leads.topup) but tracked
  with email_source="phone_only" or "website_only" and excluded from
  the 50-count metric.
- SW target = 35, CW target = 15. Combined floor = 50.
- Loop tries each pipeline until both ladders exhaust OR 50 hit.
- Hunter daily cap raised to 400 (default 200) for high-volume days.
- Telegram alert on completion (success OR ladder exhausted).
- Cron runs at 06:00 MT (existing). Re-runs every 4 hours until 22:00 MT
  if previous run did not hit 50.

Invocation:
  python -m signal_works.harvest_until_target
  python -m signal_works.harvest_until_target --target 50 --sw-target 35 --cw-target 15
  python -m signal_works.harvest_until_target --dry-run
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logger = logging.getLogger(__name__)

DAILY_TARGET_TOTAL = 50
DAILY_TARGET_SW = 35
DAILY_TARGET_CW = 15
HUNTER_CAP_DAILY = int(os.environ.get("HUNTER_MAX_SEARCHES_PER_DAY", "400"))


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


def _count_today_with_email() -> int:
    """Count leads created TODAY (UTC) with a verified email."""
    try:
        from orchestrator.db import get_crm_connection
    except ModuleNotFoundError:
        sys.path.insert(0, "/app")
        from db import get_crm_connection
    conn = get_crm_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) AS n FROM leads
            WHERE created_at::date = (NOW() AT TIME ZONE 'UTC')::date
              AND email IS NOT NULL AND email != ''
            """
        )
        row = cur.fetchone()
        return int(row["n"]) if row else 0
    finally:
        conn.close()


def _count_today_sw_with_email() -> int:
    """Count SW leads created today with email.

    SW saves with source='signal_works' OR source='serper_linkedin' for SMB
    google-maps harvests. CW saves with source='apollo_cw' OR source LIKE 'apollo_%'
    OR email_source IN ('apollo_fresh','cw_resend'). Anything not CW = SW.
    """
    try:
        from orchestrator.db import get_crm_connection
    except ModuleNotFoundError:
        sys.path.insert(0, "/app")
        from db import get_crm_connection
    conn = get_crm_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) AS n FROM leads
            WHERE created_at::date = (NOW() AT TIME ZONE 'UTC')::date
              AND email IS NOT NULL AND email != ''
              AND COALESCE(source, '') NOT LIKE 'apollo_%'
              AND COALESCE(source, '') NOT IN ('cw_resend')
              AND COALESCE(email_source, '') NOT IN ('apollo_fresh', 'cw_resend')
            """
        )
        row = cur.fetchone()
        return int(row["n"]) if row else 0
    finally:
        conn.close()


def _count_today_cw_with_email() -> int:
    """Count CW leads created today with email.

    CW saves with source='apollo_cw' OR email_source IN ('apollo_fresh','cw_resend').
    """
    try:
        from orchestrator.db import get_crm_connection
    except ModuleNotFoundError:
        sys.path.insert(0, "/app")
        from db import get_crm_connection
    conn = get_crm_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) AS n FROM leads
            WHERE created_at::date = (NOW() AT TIME ZONE 'UTC')::date
              AND email IS NOT NULL AND email != ''
              AND (
                COALESCE(source, '') LIKE 'apollo_%'
                OR COALESCE(source, '') = 'cw_resend'
                OR COALESCE(email_source, '') IN ('apollo_fresh', 'cw_resend')
              )
            """
        )
        row = cur.fetchone()
        return int(row["n"]) if row else 0
    finally:
        conn.close()


def _run_sw_until(target: int, dry_run: bool = False) -> int:
    """Run SW topup. Returns count of email-verified saves THIS RUN."""
    from signal_works.topup_leads import topup as sw_topup
    before = _count_today_sw_with_email()
    needed = max(0, target - before)
    if needed == 0:
        logger.info(f"SW already at {before}/{target} with email. Skipping.")
        return 0
    logger.info(f"SW: have {before}/{target} with email. Hunting {needed} more...")
    saved = sw_topup(minimum=needed, dry_run=dry_run)
    after = _count_today_sw_with_email()
    delta = max(0, after - before)
    logger.info(f"SW: ran for {needed}, saved {saved} total (incl phone/website-only), email-verified delta = {delta}")
    return delta


def _run_cw_until(target: int, dry_run: bool = False) -> int:
    """Run CW topup. Returns count of email-verified saves THIS RUN.

    CW topup_cw_leads.topup_cw() already requires email (line 108-109),
    so all saves count toward the email target.
    """
    from signal_works.topup_cw_leads import topup_cw_leads
    before = _count_today_cw_with_email()
    needed = max(0, target - before)
    if needed == 0:
        logger.info(f"CW already at {before}/{target} with email. Skipping.")
        return 0
    logger.info(f"CW: have {before}/{target} with email. Hunting {needed} more...")
    saved = topup_cw_leads(minimum=needed, dry_run=dry_run)
    after = _count_today_cw_with_email()
    delta = max(0, after - before)
    logger.info(f"CW: ran for {needed}, saved {saved} email-verified")
    return delta


def harvest_until_target(
    total_target: int = DAILY_TARGET_TOTAL,
    sw_target: int = DAILY_TARGET_SW,
    cw_target: int = DAILY_TARGET_CW,
    dry_run: bool = False,
    max_passes: int = 3,
) -> dict:
    """Run SW + CW topups in a loop until total_target hit OR ladders exhausted.

    Pass strategy:
      Pass 1: SW to sw_target, CW to cw_target.
      Pass 2: re-run whichever pipeline is short of its sub-target.
      Pass 3: if total still under target, top up SW with extra (CW credits expensive).

    Returns dict with: total_with_email, sw_with_email, cw_with_email,
    passes_run, status (complete | ladder_exhausted | partial).
    """
    # Raise Hunter cap for the day
    os.environ["HUNTER_MAX_SEARCHES_PER_DAY"] = str(HUNTER_CAP_DAILY)

    started_at = datetime.now(timezone.utc).isoformat()
    passes_run = 0
    last_total = -1

    for pass_num in range(1, max_passes + 1):
        passes_run = pass_num
        total_now = _count_today_with_email()
        sw_now = _count_today_sw_with_email()
        cw_now = _count_today_cw_with_email()

        logger.info(f"=== Pass {pass_num} START. SW={sw_now}/{sw_target}, CW={cw_now}/{cw_target}, TOTAL={total_now}/{total_target} ===")

        if total_now >= total_target:
            logger.info(f"Target hit: {total_now}/{total_target}. Stopping.")
            break

        # Detect stall (no progress between passes)
        if pass_num > 1 and total_now == last_total:
            logger.warning(f"Stall detected after pass {pass_num - 1} (no new email-verified leads). Both ladders likely exhausted.")
            break
        last_total = total_now

        # Run SW first (lower cost per lead via Hunter domain search)
        if sw_now < sw_target:
            try:
                _run_sw_until(sw_target, dry_run=dry_run)
            except Exception as e:
                logger.error(f"SW pass {pass_num} failed: {e}")

        # Then CW (Apollo credits more expensive, run after SW)
        cw_now = _count_today_cw_with_email()
        if cw_now < cw_target:
            try:
                _run_cw_until(cw_target, dry_run=dry_run)
            except Exception as e:
                logger.error(f"CW pass {pass_num} failed: {e}")

        # If both sub-targets hit but total still under (shouldn't happen but defensive)
        sw_now = _count_today_sw_with_email()
        cw_now = _count_today_cw_with_email()
        total_now = _count_today_with_email()
        if sw_now >= sw_target and cw_now >= cw_target and total_now < total_target:
            # Mathematically can't happen unless duplicates were excluded. Push SW further.
            extra_needed = total_target - total_now
            logger.info(f"Both sub-targets met but total {total_now} < {total_target}. Pushing SW for {extra_needed} more.")
            try:
                _run_sw_until(sw_target + extra_needed, dry_run=dry_run)
            except Exception as e:
                logger.error(f"SW extra pass failed: {e}")

    # Final tally
    final_total = _count_today_with_email()
    final_sw = _count_today_sw_with_email()
    final_cw = _count_today_cw_with_email()

    if final_total >= total_target:
        status = "complete"
        emoji = "✅"
        msg = f"{emoji} Daily harvest complete: {final_total}/{total_target} leads with email (SW={final_sw}, CW={final_cw}). Passes: {passes_run}."
    elif passes_run >= max_passes:
        status = "ladder_exhausted"
        emoji = "⚠️"
        msg = (
            f"{emoji} Harvest stopped at {final_total}/{total_target} after {passes_run} passes (SW={final_sw}/{sw_target}, CW={final_cw}/{cw_target}). "
            f"Reason: ladder exhausted or stall. Recommendation: widen niche/geography or check Apollo credit budget."
        )
    else:
        status = "partial"
        emoji = "⚠️"
        msg = f"{emoji} Harvest paused at {final_total}/{total_target} (SW={final_sw}, CW={final_cw}). Passes: {passes_run}."

    logger.info(msg)
    _telegram_alert(msg)

    return {
        "started_at": started_at,
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "total_with_email": final_total,
        "sw_with_email": final_sw,
        "cw_with_email": final_cw,
        "total_target": total_target,
        "sw_target": sw_target,
        "cw_target": cw_target,
        "passes_run": passes_run,
        "status": status,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Harvest leads until daily email target is hit")
    parser.add_argument("--target", type=int, default=DAILY_TARGET_TOTAL, help="Total email-verified leads target")
    parser.add_argument("--sw-target", type=int, default=DAILY_TARGET_SW, help="SW sub-target")
    parser.add_argument("--cw-target", type=int, default=DAILY_TARGET_CW, help="CW sub-target")
    parser.add_argument("--dry-run", action="store_true", help="Walk pipelines but do not save")
    parser.add_argument("--max-passes", type=int, default=3, help="Maximum loop passes before giving up")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = harvest_until_target(
        total_target=args.target,
        sw_target=args.sw_target,
        cw_target=args.cw_target,
        dry_run=args.dry_run,
        max_passes=args.max_passes,
    )
    sys.exit(0 if result["status"] == "complete" else 1)
