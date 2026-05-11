"""
signal_works/send_scheduler.py
================================
Batched email sender. Reads Gmail Drafts created by sequence_engine,
sends them in staggered batches throughout the business day.

Architecture:
  morning_runner -> sequence_engine -> Gmail Drafts (harvest + create)
  send_scheduler -> Gmail Drafts    -> Gmail Sent   (send in batches)

Why separate from sequence_engine:
  sequence_engine creates ALL drafts at 07:00 when the runner fires.
  send_scheduler is called on a separate cron (every 90 min, 09:00-17:00 MT)
  and sends a small batch each time. Mimics human sending behavior, keeps
  hourly send rate low (< 20/hr per inbox), avoids spam spike from 50+
  emails going out simultaneously at 07:00.

Send limits (per Gmail deliverability best practice):
  SW:     10 per batch, up to 50/day
  CW:     5  per batch, up to 25/day
  Studio: 5  per batch, up to 25/day
  Combined cap: 100/day across all pipelines

Delay: 3-8 minutes randomized between individual emails within a batch.
Cron:  */90 09-17 * * 1-5  (every 90 min, 09:00-17:00 MT, weekdays)

Usage:
  python -m signal_works.send_scheduler
  python -m signal_works.send_scheduler --dry-run
  python -m signal_works.send_scheduler --pipeline sw --batch-size 5
"""

import os
import sys
import json
import logging
import argparse
import random
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv(override=True)

logger = logging.getLogger(__name__)

# Per-pipeline daily send caps
# 35 SW + 15 CW + 15 Studio = 65/day total
# Hormozi ramp: prove reply rate at this volume before increasing
DAILY_CAPS = {
    "sw":     35,
    "cw":     15,
    "studio": 15,
}

# Per-batch size: 6 batches/day (every 90 min, 09:00-16:30 MT)
# SW: 6 per batch = 36 max (cap kicks in at 35)
# CW: 3 per batch = 18 max (cap kicks in at 15)
BATCH_SIZES = {
    "sw":     6,
    "cw":     3,
    "studio": 3,
}

# Delay range between individual emails within a batch (seconds)
MIN_DELAY = 180   # 3 min
MAX_DELAY = 480   # 8 min

# Subject keywords to identify which pipeline a draft belongs to
PIPE_KEYWORDS = {
    "sw":     ["invisible on ChatGPT", "ChatGPT", "customers find", "SaaS audit upsell"],
    "cw":     ["margin", "closing the loop on", "constraint", "Something I thought"],
    "studio": ["searching AI", "website is missing", "1,500 website"],
}
# Evaluation order: sw checked before cw so "SaaS audit" (sw-specific) never matches cw "SaaS"
PIPE_ORDER = ["sw", "studio", "cw"]


def _get_access_token() -> str:
    import httpx
    env_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON_CW", "")
    local_path = Path(__file__).resolve().parents[1] / "secrets" / "gws-oauth-credentials-cw.json"
    docker_path = "/app/secrets/gws-oauth-credentials-cw.json"
    creds_path = (
        env_path if (env_path and Path(env_path).exists())
        else str(local_path) if local_path.exists()
        else docker_path
    )
    with open(creds_path) as f:
        creds = json.load(f)
    resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id":     creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"],
            "grant_type":    "refresh_token",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _list_drafts(token: str, max_results: int = 200) -> list[dict]:
    """List Gmail drafts with subject + to headers."""
    import httpx
    resp = httpx.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/drafts",
        headers={"Authorization": f"Bearer {token}"},
        params={"maxResults": max_results},
        timeout=20,
    )
    resp.raise_for_status()
    drafts_raw = resp.json().get("drafts", [])
    drafts = []
    for d in drafts_raw:
        try:
            detail = httpx.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/drafts/{d['id']}",
                headers={"Authorization": f"Bearer {token}"},
                params={"format": "metadata", "metadataHeaders": ["Subject", "To"]},
                timeout=15,
            )
            detail.raise_for_status()
            msg = detail.json().get("message", {})
            headers = {
                h["name"].lower(): h["value"]
                for h in msg.get("payload", {}).get("headers", [])
            }
            drafts.append({
                "draft_id":   d["id"],
                "message_id": msg.get("id", ""),
                "subject":    headers.get("subject", ""),
                "to":         headers.get("to", ""),
            })
        except Exception as e:
            logger.warning(f"  Could not fetch draft {d['id']}: {e}")
    return drafts


def _send_draft(token: str, draft_id: str, dry_run: bool = False) -> bool:
    """Send a Gmail draft by ID. Returns True on success."""
    import httpx
    if dry_run:
        logger.info(f"  [DRY-RUN] Would send draft {draft_id}")
        return True
    try:
        resp = httpx.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/drafts/send",
            headers={"Authorization": f"Bearer {token}"},
            json={"id": draft_id},
            timeout=20,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"  Failed to send draft {draft_id}: {e}")
        return False


def _count_sent_today(pipeline: str) -> int:
    """Count emails already sent today for this pipeline via leads DB."""
    try:
        try:
            from orchestrator.db import get_crm_connection
        except ModuleNotFoundError:
            sys.path.insert(0, "/app")
            from db import get_crm_connection  # type: ignore
        conn = get_crm_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) as n FROM leads
            WHERE sequence_pipeline = %s
              AND DATE(last_contacted_at) = %s
        """, (pipeline, date.today()))
        row = cur.fetchone()
        conn.close()
        return row["n"] if row else 0
    except Exception as e:
        logger.warning(f"Could not count sent today for {pipeline}: {e}")
        return 0


def _telegram_alert(msg: str) -> None:
    """Best-effort Telegram alert. Uses orchestrator bot token. Never raises."""
    import urllib.parse, urllib.request
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


def _bounce_rate_kill_switch() -> bool:
    """Pre-send reputation guard. Returns True if sending should HALT.

    Checks 7-day rolling bounce rate from sw_email_log. Thresholds (Ship 2c):
      > 2%  -> pause sends, Telegram alert
      > 3%  -> pause + auto-drop pending sequences 48h (mark in alert; manual
               drop still required until a queue table exists)

    Fail-open: any DB error returns False so the gate itself cannot kill
    legitimate sending.
    """
    try:
        try:
            from orchestrator.db import get_crm_connection
        except ModuleNotFoundError:
            sys.path.insert(0, "/app")
            from db import get_crm_connection  # type: ignore
        conn = get_crm_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
              SUM(CASE WHEN status IN ('bounced','failed') THEN 1 ELSE 0 END)::float
                / NULLIF(COUNT(*), 0) AS bounce_rate,
              COUNT(*) AS total
            FROM sw_email_log
            WHERE created_at > NOW() - INTERVAL '7 days'
        """)
        row = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.warning(f"bounce kill-switch: query failed (fail-open): {e}")
        return False

    if not row:
        return False
    bounce_rate = row["bounce_rate"]
    total = row["total"] or 0
    # Need >=50 sends in the window before the rate is meaningful. Below
    # that, 1 bounce trips the gate spuriously.
    if total < 50:
        return False
    if bounce_rate is None:
        return False

    if bounce_rate > 0.03:
        _telegram_alert(
            f"REPUTATION CRITICAL: 7-day bounce rate {bounce_rate:.1%} > 3% "
            f"(n={total}). Sending paused. Auto-drop pending sequences 48h required."
        )
        logger.error(
            f"bounce kill-switch: rate {bounce_rate:.1%} > 3% threshold (n={total})"
        )
        return True
    if bounce_rate > 0.02:
        _telegram_alert(
            f"REPUTATION ALERT: 7-day bounce rate {bounce_rate:.1%} > 2% "
            f"(n={total}). Sending paused."
        )
        logger.error(
            f"bounce kill-switch: rate {bounce_rate:.1%} > 2% threshold (n={total})"
        )
        return True
    return False


def run_batch(pipeline: str = "all", batch_size: int = None,
              dry_run: bool = False) -> dict:
    """
    Fetch Gmail drafts and send up to batch_size per pipeline,
    with randomized delays between individual sends.

    Reputation guard (Ship 2c): if the 7-day rolling bounce rate from
    sw_email_log exceeds 2%, this run is aborted and a Telegram alert
    fires. Skipped when dry_run=True so test runs are never gated.
    """
    if not dry_run and _bounce_rate_kill_switch():
        logger.error("run_batch: bounce-rate kill switch tripped, aborting batch")
        return {"total_sent": 0, "by_pipeline": {}, "halted": "bounce_rate"}

    pipelines = PIPE_ORDER if pipeline == "all" else [pipeline]

    token = _get_access_token()
    all_drafts = _list_drafts(token)
    logger.info(f"Found {len(all_drafts)} total drafts in Gmail")

    results = {}
    total_sent = 0

    for pipe in pipelines:
        cap = DAILY_CAPS[pipe]
        already_sent = _count_sent_today(pipe)
        remaining_cap = cap - already_sent

        if remaining_cap <= 0:
            logger.info(f"[{pipe.upper()}] Daily cap {cap} reached. Skipping.")
            results[pipe] = {"sent": 0, "capped": True, "drafts_found": 0}
            continue

        size = batch_size or BATCH_SIZES[pipe]
        to_send = min(size, remaining_cap)

        keywords = PIPE_KEYWORDS.get(pipe, [])
        pipe_drafts = [
            d for d in all_drafts
            if any(kw.lower() in d["subject"].lower() for kw in keywords)
        ]

        logger.info(
            f"[{pipe.upper()}] {len(pipe_drafts)} matching drafts found. "
            f"Sending {to_send} (cap={cap}, sent today={already_sent})"
        )

        sent = 0
        for draft in pipe_drafts[:to_send]:
            ok = _send_draft(token, draft["draft_id"], dry_run=dry_run)
            if ok:
                sent += 1
                total_sent += 1
                logger.info(
                    f"  [{pipe.upper()}] Sent -> {draft['to']} | {draft['subject'][:55]}"
                )
                if sent < to_send:
                    delay = random.randint(MIN_DELAY, MAX_DELAY)
                    logger.info(f"  Sleeping {delay}s before next send...")
                    if not dry_run:
                        time.sleep(delay)

        results[pipe] = {
            "sent": sent,
            "capped": False,
            "drafts_found": len(pipe_drafts),
        }

    logger.info(f"Batch complete. Total sent this run: {total_sent}")
    return {"total_sent": total_sent, "by_pipeline": results}


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    parser = argparse.ArgumentParser(description="Send queued email drafts in batches")
    parser.add_argument("--pipeline", choices=["sw", "cw", "studio", "all"], default="all")
    parser.add_argument("--batch-size", type=int, default=None,
                        help="Emails per batch per pipeline (overrides default)")
    parser.add_argument("--dry-run", action="store_true",
                        help="List drafts but do not actually send")
    args = parser.parse_args()

    summary = run_batch(
        pipeline=args.pipeline,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )
    print(f"\nDone. {summary['total_sent']} emails sent this batch.")
    for pipe, r in summary["by_pipeline"].items():
        status = "CAPPED" if r.get("capped") else f"{r['sent']} sent"
        print(f"  {pipe.upper()}: {status} ({r.get('drafts_found', 0)} drafts found)")
