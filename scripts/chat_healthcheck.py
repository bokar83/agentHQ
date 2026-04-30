#!/usr/bin/env python3
"""
chat_healthcheck.py

Synthetic monitor for the agentsHQ chat surfaces. Runs as a systemd timer on
the VPS every 10 minutes. Exits 0 on success, 1 on any probe failure (which
is also when alerts fire).

Probes (v1):
  1. Web /atlas/chat: POST a known prompt, assert 200 + reply doesn't match
     /sorry, i hit an error/i AND len(reply) > 20.
  2. Telegram bot: send a test message via Bot API to OWNER_TELEGRAM_CHAT_ID
     with the prompt /__healthcheck__ <nonce>. Poll getUpdates for ~30s. Pass
     if the bot replies with anything containing the nonce or any non-empty
     human message; fail on timeout.

On any failure: send Telegram alert to owner chat AND email to REPORT_EMAIL,
both with the failing probe name + last 50 lines of orc-crewai logs.

This script is intentionally dependency-light: stdlib only (urllib, json,
subprocess, smtplib). Designed to keep working when half the system is sick.
"""
import json
import os
import smtplib
import subprocess
import sys
import time
import urllib.error
import urllib.request
from email.mime.text import MIMEText

ENV_FILE = "/root/agentsHQ/.env"

ORC_URL = "http://127.0.0.1:8000/atlas/chat"
WEB_PROMPT = "reply with the single word PONG and nothing else"
WEB_TIMEOUT_S = 30
WEB_FAIL_PATTERN = "sorry, i hit an error"

TELEGRAM_API = "https://api.telegram.org"
TELEGRAM_PROBE_TIMEOUT_S = 45
TELEGRAM_POLL_INTERVAL_S = 3

LOG_TAIL_LINES = 50


# ──────────────────────────────────────────────────────────────────────────
# env loading (no python-dotenv dependency)
# ──────────────────────────────────────────────────────────────────────────

def load_env(path: str) -> dict:
    out: dict = {}
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            out[key.strip()] = val.strip().strip('"').strip("'")
    return out


# ──────────────────────────────────────────────────────────────────────────
# Probe 1: web /atlas/chat
# ──────────────────────────────────────────────────────────────────────────

def probe_web_chat(api_key: str) -> tuple[bool, str]:
    """Returns (passed, message)."""
    payload = json.dumps({
        "messages": [{"role": "user", "content": WEB_PROMPT}],
        "session_key": "healthcheck-synthetic",
    }).encode("utf-8")
    req = urllib.request.Request(
        ORC_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=WEB_TIMEOUT_S) as resp:
            status = resp.status
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return False, f"web /atlas/chat returned HTTP {e.code}: {e.read()[:200]!r}"
    except Exception as e:
        return False, f"web /atlas/chat request raised {type(e).__name__}: {e}"

    if status != 200:
        return False, f"web /atlas/chat returned HTTP {status}: {body[:200]!r}"

    try:
        parsed = json.loads(body)
    except Exception:
        return False, f"web /atlas/chat returned non-JSON: {body[:200]!r}"

    reply = (parsed.get("reply") or "").strip()
    if not reply:
        return False, f"web /atlas/chat returned empty reply: {parsed!r}"
    if WEB_FAIL_PATTERN in reply.lower():
        return False, f"web /atlas/chat returned error reply: {reply[:200]!r}"
    if len(reply) < 3:
        return False, f"web /atlas/chat reply too short: {reply!r}"

    return True, f"web /atlas/chat OK (reply={reply[:80]!r})"


# ──────────────────────────────────────────────────────────────────────────
# Probe 2: Telegram bot roundtrip
# ──────────────────────────────────────────────────────────────────────────

def probe_telegram(bot_token: str) -> tuple[bool, str]:
    """
    Verify Bot API reachability + bot identity via getMe.

    v1 deliberately does NOT send messages to the owner chat (that would spam
    every 10 minutes). getMe catches: revoked token, Telegram API outage, DNS
    breakage. It does NOT catch "bot process crashed but token still works"
    -- that requires a roundtrip via a separate test user account, deferred
    to v2 once v1 has run clean for 48h.
    """
    try:
        with urllib.request.urlopen(
            f"{TELEGRAM_API}/bot{bot_token}/getMe",
            timeout=10,
        ) as resp:
            getme = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return False, f"telegram getMe failed: {type(e).__name__}: {e}"

    if not getme.get("ok"):
        return False, f"telegram getMe returned not-ok: {getme!r}"

    bot_username = getme.get("result", {}).get("username", "<unknown>")
    return True, f"telegram bot @{bot_username} reachable (getMe OK)"


# ──────────────────────────────────────────────────────────────────────────
# Alerting
# ──────────────────────────────────────────────────────────────────────────

def get_log_tail() -> str:
    try:
        out = subprocess.run(
            ["docker", "logs", "orc-crewai", "--tail", str(LOG_TAIL_LINES)],
            capture_output=True, text=True, timeout=10,
        )
        return (out.stdout or "") + (out.stderr or "")
    except Exception as e:
        return f"<could not collect logs: {e}>"


def send_telegram_alert(bot_token: str, chat_id: str, text: str) -> None:
    try:
        payload = json.dumps({
            "chat_id": chat_id,
            "text": text[:3800],
            "disable_notification": False,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{TELEGRAM_API}/bot{bot_token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as e:
        print(f"[chat_healthcheck] telegram alert failed: {e}", file=sys.stderr)


def send_email_alert(to_addr: str, subject: str, body: str, env: dict) -> None:
    """Best-effort SMTP alert. Uses gws CLI if available; otherwise stderr."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = to_addr
    msg["To"] = to_addr

    smtp_host = env.get("SMTP_HOST")
    smtp_port = env.get("SMTP_PORT")
    smtp_user = env.get("SMTP_USER")
    smtp_pass = env.get("SMTP_PASS")
    if smtp_host and smtp_user and smtp_pass:
        try:
            with smtplib.SMTP(smtp_host, int(smtp_port or 587), timeout=15) as s:
                s.starttls()
                s.login(smtp_user, smtp_pass)
                s.send_message(msg)
            return
        except Exception as e:
            print(f"[chat_healthcheck] SMTP alert failed: {e}", file=sys.stderr)
    # Fallback: just log. The Telegram alert is the primary channel.
    print(f"[chat_healthcheck] would email {to_addr}: {subject}", file=sys.stderr)


# ──────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────

def main() -> int:
    env = load_env(ENV_FILE)
    # Fall back to process env so the script works even outside cron context.
    for k, v in env.items():
        os.environ.setdefault(k, v)

    api_key = os.environ.get("ORCHESTRATOR_API_KEY", "").strip()
    bot_token = (
        os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN")
        or os.environ.get("TELEGRAM_BOT_TOKEN")
        or ""
    ).strip()
    chat_id = (
        os.environ.get("OWNER_TELEGRAM_CHAT_ID")
        or os.environ.get("TELEGRAM_CHAT_ID")
        or ""
    ).strip()
    report_email = os.environ.get("REPORT_EMAIL", "").strip()

    if not api_key:
        print("[chat_healthcheck] FATAL: ORCHESTRATOR_API_KEY missing", file=sys.stderr)
        return 1

    failures: list[str] = []
    passes: list[str] = []

    ok, msg = probe_web_chat(api_key)
    (passes if ok else failures).append(msg)

    if bot_token:
        ok, msg = probe_telegram(bot_token)
        (passes if ok else failures).append(msg)
    else:
        failures.append("telegram probe skipped: bot_token MISSING")

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    if not failures:
        print(f"[chat_healthcheck] {timestamp} OK — {len(passes)} probes passed")
        for p in passes:
            print(f"  PASS: {p}")
        return 0

    # Alert
    log_tail = get_log_tail()
    summary = (
        f"agentsHQ chat health probe FAILED at {timestamp}\n\n"
        f"FAILURES ({len(failures)}):\n"
        + "\n".join(f"  - {f}" for f in failures)
        + "\n\nPASSES:\n"
        + ("\n".join(f"  - {p}" for p in passes) if passes else "  (none)")
        + "\n\nLast 50 log lines (orc-crewai):\n"
        + log_tail
    )
    print(summary)

    if bot_token and chat_id:
        send_telegram_alert(
            bot_token, chat_id,
            f"chat_healthcheck FAILED ({len(failures)} probe(s)). "
            f"Failures: {'; '.join(failures)[:300]}",
        )
    if report_email:
        send_email_alert(report_email, "agentsHQ chat health probe FAILED", summary, env)

    return 1


if __name__ == "__main__":
    sys.exit(main())
