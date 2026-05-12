#!/usr/bin/env python3
"""check_concurrent_sessions.py: Telegram alert when 2+ active sessions
detected on this repo.

Reads `data/active_sessions.json` (written by the worktree-claim skill).
Entries older than 30 min are ignored (likely dead session). If 2+ live
entries remain, sends one Telegram message. Dedup via
/tmp/cw_concurrent_sessions_last_alert.json so we don't spam on every run.

Run via Windows Task Scheduler or cron every 2 min:
    */2 * * * * python3 scripts/check_concurrent_sessions.py

Why: 2026-05-12 incident — N>1 sessions ran concurrently without anyone
noticing until edits were destroyed. Surfacing the condition early lets
Boubacar pause one before damage compounds.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

LOOKBACK_MIN = 30
ALERT_STATE_PATH = Path("/tmp/cw_concurrent_sessions_last_alert.json")
MANIFEST_PATH = Path(__file__).resolve().parent.parent / "data" / "active_sessions.json"


def _load_manifest() -> list[dict]:
    if not MANIFEST_PATH.exists():
        return []
    try:
        return json.loads(MANIFEST_PATH.read_text())
    except json.JSONDecodeError:
        return []


def _live(entries: list[dict]) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MIN)
    out = []
    for e in entries:
        ts = e.get("started_at")
        if not ts:
            continue
        try:
            started = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        if started > cutoff:
            out.append(e)
    return out


def _last_alert_sig() -> str | None:
    if not ALERT_STATE_PATH.exists():
        return None
    try:
        return json.loads(ALERT_STATE_PATH.read_text()).get("sig")
    except (json.JSONDecodeError, OSError):
        return None


def _write_alert_sig(sig: str) -> None:
    try:
        ALERT_STATE_PATH.write_text(json.dumps({"sig": sig, "at": datetime.now(timezone.utc).isoformat()}))
    except OSError:
        pass


def _send_telegram(msg: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("TG_BOUBACAR_CHAT_ID")
    if not token or not chat_id:
        sys.stderr.write(
            "check_concurrent_sessions: TELEGRAM_BOT_TOKEN/CHAT_ID missing; "
            "printing to stderr instead\n"
        )
        sys.stderr.write(msg + "\n")
        return
    try:
        import urllib.request
        import urllib.parse

        data = urllib.parse.urlencode(
            {"chat_id": chat_id, "text": msg, "disable_notification": "false"}
        ).encode()
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data,
            timeout=8,
        )
    except Exception as exc:
        sys.stderr.write(f"check_concurrent_sessions: telegram send failed: {exc}\n")


def main() -> int:
    entries = _load_manifest()
    live = _live(entries)
    if len(live) < 2:
        return 0

    sig = "|".join(sorted(f"{e['session_id']}:{e['branch']}" for e in live))
    if sig == _last_alert_sig():
        return 0

    lines = ["agentsHQ: 2+ active sessions detected"]
    for e in live:
        lines.append(
            f"  - {e['session_id']} on {e['branch']} "
            f"(since {e['started_at']}, pid={e.get('pid')})"
        )
    lines.append("Verify both are intended. If not, pause one.")
    msg = "\n".join(lines)

    _send_telegram(msg)
    _write_alert_sig(sig)
    return 0


if __name__ == "__main__":
    sys.exit(main())
