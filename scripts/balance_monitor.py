#!/usr/bin/env python3
"""
balance_monitor.py — OpenRouter Balance Monitor
================================================
Runs as a cron job on the VPS. Checks OpenRouter credit balance
and sends a Telegram alert if below threshold.

Thresholds:
  WARNING:  $5.00 — gives ~3-5 days notice at normal usage
  CRITICAL: $3.00 — top up now

Cron schedule (set in /etc/cron.d/balance-monitor):
  0 */6 * * *  root  python3 /root/agentsHQ/scripts/balance_monitor.py

Required env vars (read from /root/agentsHQ/.env):
  OPENROUTER_API_KEY
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# ── Config ────────────────────────────────────────────────────
WARN_THRESHOLD    = 5.00   # dollars — first warning
CRITICAL_THRESHOLD = 3.00  # dollars — urgent alert

ENV_FILE = Path("/root/agentsHQ/.env")

# ── Load .env ─────────────────────────────────────────────────
def load_env(path: Path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())

load_env(ENV_FILE)

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
BOT_TOKEN      = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID        = os.environ.get("TELEGRAM_CHAT_ID", "")

# ── Helpers ───────────────────────────────────────────────────
def get_balance() -> float:
    """Query OpenRouter /api/v1/credits and return remaining USD balance."""
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/credits",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    # Response: {"data": {"total_credits": X, "usage": Y}}
    # Remaining = total_credits - usage (both in USD)
    d = data.get("data", data)
    total = float(d.get("total_credits", d.get("credits", 0)))
    usage = float(d.get("usage", 0))
    return round(total - usage, 4)


def send_telegram(message: str):
    """Send a message via Telegram Bot API."""
    if not BOT_TOKEN or not CHAT_ID:
        print("ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env", file=sys.stderr)
        return
    payload = json.dumps({
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()


def state_file_path() -> Path:
    return Path("/tmp/openrouter_balance_state.json")


def load_state() -> dict:
    p = state_file_path()
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {"last_warned": None}


def save_state(state: dict):
    state_file_path().write_text(json.dumps(state))


# ── Main ──────────────────────────────────────────────────────
def main():
    if not OPENROUTER_KEY:
        print("ERROR: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    try:
        balance = get_balance()
    except Exception as e:
        print(f"ERROR checking balance: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"OpenRouter balance: ${balance:.2f}")

    state = load_state()

    if balance <= CRITICAL_THRESHOLD:
        if state.get("last_warned") != "critical":
            send_telegram(
                f"<b>CRITICAL: OpenRouter balance low</b>\n\n"
                f"Balance: <b>${balance:.2f}</b>\n"
                f"Top up now — you have very little runway left.\n\n"
                f"<a href='https://openrouter.ai/credits'>Add credits</a>"
            )
            state["last_warned"] = "critical"
            save_state(state)
            print(f"Sent CRITICAL alert (${balance:.2f})")

    elif balance <= WARN_THRESHOLD:
        if state.get("last_warned") not in ("warning", "critical"):
            send_telegram(
                f"<b>Warning: OpenRouter balance below $5</b>\n\n"
                f"Balance: <b>${balance:.2f}</b>\n"
                f"Consider topping up soon.\n\n"
                f"<a href='https://openrouter.ai/credits'>Add credits</a>"
            )
            state["last_warned"] = "warning"
            save_state(state)
            print(f"Sent WARNING alert (${balance:.2f})")

    else:
        # Balance is healthy — reset state so next drop triggers again
        if state.get("last_warned"):
            state["last_warned"] = None
            save_state(state)
        print(f"Balance healthy (${balance:.2f}) — no alert needed")


if __name__ == "__main__":
    main()
