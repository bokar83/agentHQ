#!/usr/bin/env python3
"""
lighthouse_digest_send.py — L-R9 Sunday digest auto-send.

CARVE-OUT: This script is the ONLY auto-send path Boubacar has approved
without per-batch explicit "send it" authorization, locked Sat 2026-05-16 PM.
Scope is intentionally narrow:

  - To = bokar83@gmail.com + boubacar@catalystworks.consulting (self only)
  - From = boubacar@catalystworks.consulting (cw OAuth identity)
  - Schedule = fixed cron, Sun 00:00 UTC (= 18:00 MDT Sun)
  - Kill-switch flag = data/lighthouse-digest-skip.flag (commit to halt)
  - Idempotency flag = data/lighthouse-digest-sent-<YYYY-WW>.flag (one fire/week)
  - Verify-after-send is MANDATORY (CLAUDE.md HARD RULE: EMAIL SENDING)

Any outbound to prospects / third parties is STILL gated by explicit
"send it" per session per batch. This carve-out does NOT extend beyond
self-digests.

Invoked by /etc/cron.d/lighthouse-rituals:

    0 0 * * 1 root docker exec orc-crewai \\
        python /app/orchestrator/scripts/lighthouse_digest_send.py \\
        >> /var/log/lighthouse-rituals.log 2>&1

Dry-run (no send, just print plan):

    python /app/orchestrator/scripts/lighthouse_digest_send.py --dry-run
"""
from __future__ import annotations

import argparse
import base64
import datetime as _dt
import json
import logging
import os
import re
import sys
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional, Tuple

LOG_FORMAT = "%(asctime)s [lighthouse_digest_send] %(levelname)s %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Paths + constants (override-friendly for tests)
# --------------------------------------------------------------------------

DEFAULT_OUTPUT_DIR = Path(
    os.environ.get("LIGHTHOUSE_OUTPUT_DIR", "/app/data/lighthouse-digests")
)
DEFAULT_DATA_DIR = Path(os.environ.get("LIGHTHOUSE_DATA_DIR", "/app/data"))
DEFAULT_SECRETS_PATH = Path(
    os.environ.get(
        "GOOGLE_OAUTH_CREDENTIALS_JSON_CW",
        "/app/secrets/gws-oauth-credentials-cw.json",
    )
)
DEFAULT_LOG_PATH = Path(
    os.environ.get("LIGHTHOUSE_RITUAL_LOG", "/var/log/lighthouse-rituals.log")
)

KILL_SWITCH_NAME = "lighthouse-digest-skip.flag"
SENT_FLAG_PREFIX = "lighthouse-digest-sent-"
FROM_ADDR = "boubacar@catalystworks.consulting"
TO_ADDRS = ["bokar83@gmail.com", "boubacar@catalystworks.consulting"]

DIGEST_NAME_RE = re.compile(r"^w(\d+)-close-(\d{4}-\d{2}-\d{2})\.html$")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _telegram_alert(text: str) -> None:
    """Best-effort Telegram alert to OWNER_TELEGRAM_CHAT_ID. Never raises."""
    try:
        import httpx  # type: ignore
    except Exception:
        logger.warning("httpx unavailable — cannot send Telegram alert")
        return
    chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID")
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get(
        "ORCHESTRATOR_TELEGRAM_BOT_TOKEN"
    )
    if not (chat_id and token):
        logger.warning(
            "OWNER_TELEGRAM_CHAT_ID or TELEGRAM_BOT_TOKEN not set — skipping alert"
        )
        return
    try:
        httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("Telegram alert failed (non-fatal): %s", e)


def _append_log(line: str, log_path: Path = DEFAULT_LOG_PATH) -> None:
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line.rstrip("\n") + "\n")
    except Exception as e:  # noqa: BLE001
        logger.warning("log append failed (non-fatal): %s", e)


def find_latest_digest(output_dir: Path) -> Tuple[Path, int, str]:
    """Return (path, week_number, date_str) for the latest digest.

    Selection rule:
      1. Filter to files matching w<N>-close-<YYYY-MM-DD>.html
      2. Prefer the file with the highest <N>; tiebreak by date string
         (lexical order works because format is ISO-fixed).

    Raises FileNotFoundError if no digest is present.
    """
    if not output_dir.exists():
        raise FileNotFoundError(f"output dir does not exist: {output_dir}")
    candidates = []
    for p in output_dir.iterdir():
        if not p.is_file():
            continue
        m = DIGEST_NAME_RE.match(p.name)
        if not m:
            continue
        n = int(m.group(1))
        date_str = m.group(2)
        candidates.append((n, date_str, p))
    if not candidates:
        raise FileNotFoundError(
            f"no digest files matching w<N>-close-<YYYY-MM-DD>.html in {output_dir}"
        )
    candidates.sort(key=lambda t: (t[0], t[1]))
    n, date_str, path = candidates[-1]
    return path, n, date_str


def kill_switch_active(data_dir: Path) -> bool:
    return (data_dir / KILL_SWITCH_NAME).exists()


def idempotency_flag_path(data_dir: Path, now: Optional[_dt.datetime] = None) -> Path:
    now = now or _dt.datetime.now(_dt.timezone.utc)
    iso_year, iso_week, _ = now.isocalendar()
    return data_dir / f"{SENT_FLAG_PREFIX}{iso_year:04d}-{iso_week:02d}.flag"


def idempotency_flag_active(data_dir: Path, now: Optional[_dt.datetime] = None) -> bool:
    return idempotency_flag_path(data_dir, now=now).exists()


def write_idempotency_flag(
    data_dir: Path, message_id: str, now: Optional[_dt.datetime] = None
) -> Path:
    path = idempotency_flag_path(data_dir, now=now)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "message_id": message_id,
        "sent_at": (now or _dt.datetime.now(_dt.timezone.utc)).isoformat(),
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def derive_subject(week_n: int) -> str:
    return f"Lighthouse W{week_n} close + W{week_n + 1} launch read"


# --------------------------------------------------------------------------
# Send pipeline (canonical cw OAuth path, per CLAUDE.md HARD RULE)
# --------------------------------------------------------------------------


def _load_oauth_creds(creds_path: Path) -> dict:
    with creds_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _get_access_token(creds: dict) -> str:
    import httpx  # type: ignore

    resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"],
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _build_mime(html_body: str, subject: str, to_addrs: list[str]) -> str:
    msg = MIMEText(html_body, "html", "utf-8")
    msg["From"] = FROM_ADDR
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = subject
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii").rstrip("=")


def _send_via_gmail(raw_b64: str, token: str) -> str:
    import httpx  # type: ignore

    resp = httpx.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"raw": raw_b64},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def _verify_from_header(message_id: str, token: str) -> str:
    """MANDATORY verify-after-send. Returns From header, raises on mismatch."""
    import httpx  # type: ignore

    resp = httpx.get(
        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"format": "metadata"},
        timeout=20,
    )
    resp.raise_for_status()
    payload = resp.json()
    headers = payload.get("payload", {}).get("headers", [])
    from_hdr = ""
    for h in headers:
        if h.get("name", "").lower() == "from":
            from_hdr = h.get("value", "")
            break
    if not from_hdr.endswith(FROM_ADDR):
        raise RuntimeError(
            f"From-header verification failed: got {from_hdr!r}, expected suffix {FROM_ADDR!r}"
        )
    return from_hdr


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def run(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    data_dir: Path = DEFAULT_DATA_DIR,
    secrets_path: Path = DEFAULT_SECRETS_PATH,
    log_path: Path = DEFAULT_LOG_PATH,
    dry_run: bool = False,
    now: Optional[_dt.datetime] = None,
) -> int:
    now = now or _dt.datetime.now(_dt.timezone.utc)

    # 1. Kill-switch check
    if kill_switch_active(data_dir):
        msg = "L-R9 send skipped per kill-switch flag"
        logger.info(msg)
        _append_log(f"{now.isoformat()} SKIP_KILL_SWITCH {data_dir / KILL_SWITCH_NAME}", log_path)
        _telegram_alert(f"<b>L-R9 Sunday digest</b>\n{msg}")
        return 0

    # 2. Idempotency check
    if idempotency_flag_active(data_dir, now=now):
        flag = idempotency_flag_path(data_dir, now=now)
        msg = f"L-R9 already sent this week (flag: {flag.name})"
        logger.info(msg)
        _append_log(f"{now.isoformat()} SKIP_IDEMPOTENT {flag}", log_path)
        return 0

    # 3. Discover digest file
    try:
        digest_path, week_n, date_str = find_latest_digest(output_dir)
    except FileNotFoundError as e:
        err = f"L-R9 send failed: {e}"
        logger.error(err)
        _append_log(f"{now.isoformat()} ERROR {err}", log_path)
        _telegram_alert(f"<b>L-R9 Sunday digest FAILED</b>\n{err}")
        return 4

    subject = derive_subject(week_n)
    html_body = digest_path.read_text(encoding="utf-8")

    if dry_run:
        logger.info("DRY-RUN: would send")
        logger.info("  digest: %s", digest_path)
        logger.info("  subject: %s", subject)
        logger.info("  from: %s", FROM_ADDR)
        logger.info("  to: %s", TO_ADDRS)
        logger.info("  body bytes: %d", len(html_body.encode("utf-8")))
        _append_log(
            f"{now.isoformat()} DRY_RUN digest={digest_path.name} subject={subject!r}",
            log_path,
        )
        return 0

    # 4. Send via canonical cw OAuth path
    try:
        creds = _load_oauth_creds(secrets_path)
        token = _get_access_token(creds)
        raw_b64 = _build_mime(html_body, subject, TO_ADDRS)
        message_id = _send_via_gmail(raw_b64, token)
    except Exception as e:  # noqa: BLE001
        err = f"L-R9 send failed during send: {type(e).__name__}: {e}"
        logger.exception("send pipeline failed")
        _append_log(f"{now.isoformat()} ERROR {err}", log_path)
        _telegram_alert(f"<b>L-R9 Sunday digest FAILED</b>\n{err}")
        return 5

    # 5. MANDATORY verify-after-send
    try:
        from_hdr = _verify_from_header(message_id, token)
    except Exception as e:  # noqa: BLE001
        err = (
            f"L-R9 sent (id={message_id}) but From-verification FAILED: "
            f"{type(e).__name__}: {e}. Sent flag NOT written; next run will resend "
            "after manual review."
        )
        logger.exception("verify-after-send failed")
        _append_log(f"{now.isoformat()} ERROR_VERIFY {err}", log_path)
        _telegram_alert(f"<b>L-R9 Sunday digest verify FAILED</b>\n{err}")
        return 6

    # 6. Idempotency flag + success log
    flag_path = write_idempotency_flag(data_dir, message_id, now=now)
    success_line = (
        f"{now.isoformat()} OK message_id={message_id} from={from_hdr} "
        f"digest={digest_path.name} flag={flag_path.name}"
    )
    logger.info(success_line)
    _append_log(success_line, log_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Find digest + build MIME but do NOT send. Prints plan, exits 0.",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Override digest output dir (default: /app/data/lighthouse-digests)",
    )
    p.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Override flag dir (default: /app/data)",
    )
    p.add_argument(
        "--secrets-path",
        type=Path,
        default=DEFAULT_SECRETS_PATH,
        help="Override OAuth creds path",
    )
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return run(
        output_dir=args.output_dir,
        data_dir=args.data_dir,
        secrets_path=args.secrets_path,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
