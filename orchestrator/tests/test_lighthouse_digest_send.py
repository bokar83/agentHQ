"""Tests for orchestrator/scripts/lighthouse_digest_send.py (L-R9 auto-send).

NO REAL EMAILS sent. All httpx calls are mocked.
"""
from __future__ import annotations

import base64
import datetime as _dt
import importlib.util
import json
import sys
from email import message_from_bytes
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Load the dispatch script as a module without needing it on PYTHONPATH.
_HERE = Path(__file__).resolve().parent
_SCRIPT = _HERE.parent / "scripts" / "lighthouse_digest_send.py"
_spec = importlib.util.spec_from_file_location("lighthouse_digest_send", _SCRIPT)
assert _spec is not None and _spec.loader is not None
lds = importlib.util.module_from_spec(_spec)
sys.modules["lighthouse_digest_send"] = lds
_spec.loader.exec_module(lds)  # type: ignore[union-attr]


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture
def tmp_dirs(tmp_path: Path):
    """Build (output_dir, data_dir, secrets_path, log_path) in a tmp tree."""
    output_dir = tmp_path / "output" / "lighthouse"
    data_dir = tmp_path / "data"
    secrets_path = tmp_path / "secrets" / "cw.json"
    log_path = tmp_path / "logs" / "lighthouse-rituals.log"
    for d in (output_dir, data_dir, secrets_path.parent, log_path.parent):
        d.mkdir(parents=True, exist_ok=True)
    secrets_path.write_text(
        json.dumps(
            {
                "client_id": "fake-client",
                "client_secret": "fake-secret",
                "refresh_token": "fake-refresh",
            }
        ),
        encoding="utf-8",
    )
    return output_dir, data_dir, secrets_path, log_path


def _write_digest(output_dir: Path, week: int, date_str: str, body: str = "<html>body</html>") -> Path:
    p = output_dir / f"w{week}-close-{date_str}.html"
    p.write_text(body, encoding="utf-8")
    return p


def _fake_httpx_module(
    *,
    send_message_id: str = "msg-abc-123",
    verify_from: str = lds.FROM_ADDR,
):
    """Build a MagicMock that stands in for the httpx module."""
    mod = MagicMock(name="httpx")

    # Capture call args for assertions
    calls: dict[str, list] = {"post": [], "get": []}

    def post(url, *args, **kwargs):
        calls["post"].append((url, args, kwargs))
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        if "oauth2.googleapis.com/token" in url:
            resp.json.return_value = {"access_token": "fake-access-token"}
        elif "gmail.googleapis.com" in url and "messages/send" in url:
            resp.json.return_value = {"id": send_message_id}
        elif "api.telegram.org" in url:
            resp.json.return_value = {"ok": True}
        else:
            resp.json.return_value = {}
        return resp

    def get(url, *args, **kwargs):
        calls["get"].append((url, args, kwargs))
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        if "gmail.googleapis.com" in url and "/messages/" in url:
            resp.json.return_value = {
                "payload": {
                    "headers": [
                        {"name": "From", "value": verify_from},
                        {"name": "To", "value": ", ".join(lds.TO_ADDRS)},
                        {"name": "Subject", "value": "anything"},
                    ]
                }
            }
        else:
            resp.json.return_value = {}
        return resp

    mod.post.side_effect = post
    mod.get.side_effect = get
    mod._calls = calls  # for assertions
    return mod


# --------------------------------------------------------------------------
# Pure-function tests (no IO)
# --------------------------------------------------------------------------


def test_derive_subject_from_week_n():
    assert lds.derive_subject(1) == "Lighthouse W1 close + W2 launch read"
    assert lds.derive_subject(12) == "Lighthouse W12 close + W13 launch read"


def test_find_latest_digest_picks_highest_week(tmp_dirs):
    output_dir, *_ = tmp_dirs
    _write_digest(output_dir, 1, "2026-05-16")
    _write_digest(output_dir, 3, "2026-05-30")
    _write_digest(output_dir, 2, "2026-05-23")
    # Non-matching files are ignored
    (output_dir / "notes.md").write_text("ignore me")
    (output_dir / "w99-close-bad.html").write_text("bad date")
    path, n, date_str = lds.find_latest_digest(output_dir)
    assert n == 3
    assert date_str == "2026-05-30"
    assert path.name == "w3-close-2026-05-30.html"


def test_find_latest_digest_raises_when_empty(tmp_dirs):
    output_dir, *_ = tmp_dirs
    with pytest.raises(FileNotFoundError):
        lds.find_latest_digest(output_dir)


def test_build_mime_has_both_recipients_and_html_content_type():
    raw_b64 = lds._build_mime("<p>hi</p>", "Subj", lds.TO_ADDRS)
    # base64url unpacking
    padded = raw_b64 + "=" * (-len(raw_b64) % 4)
    raw_bytes = base64.urlsafe_b64decode(padded.encode("ascii"))
    msg = message_from_bytes(raw_bytes)
    assert msg["From"] == lds.FROM_ADDR
    assert "bokar83@gmail.com" in msg["To"]
    assert "boubacar@catalystworks.consulting" in msg["To"]
    assert msg["Subject"] == "Subj"
    assert msg.get_content_type() == "text/html"


def test_idempotency_flag_path_matches_iso_week():
    now = _dt.datetime(2026, 5, 17, 12, 0, tzinfo=_dt.timezone.utc)
    p = lds.idempotency_flag_path(Path("/tmp/data"), now=now)
    iso_year, iso_week, _ = now.isocalendar()
    assert p.name == f"lighthouse-digest-sent-{iso_year:04d}-{iso_week:02d}.flag"


# --------------------------------------------------------------------------
# run() end-to-end tests with mocked httpx
# --------------------------------------------------------------------------


def test_kill_switch_blocks_send(tmp_dirs):
    output_dir, data_dir, secrets_path, log_path = tmp_dirs
    _write_digest(output_dir, 1, "2026-05-16")
    (data_dir / lds.KILL_SWITCH_NAME).write_text("halt")

    fake_httpx = _fake_httpx_module()
    with patch.dict(sys.modules, {"httpx": fake_httpx}):
        rc = lds.run(
            output_dir=output_dir,
            data_dir=data_dir,
            secrets_path=secrets_path,
            log_path=log_path,
        )
    assert rc == 0
    # No Gmail POSTs happened — only the optional Telegram alert
    gmail_posts = [c for c in fake_httpx._calls["post"] if "gmail.googleapis.com" in c[0]]
    assert gmail_posts == []
    # No idempotency flag written
    assert not any(p.name.startswith(lds.SENT_FLAG_PREFIX) for p in data_dir.iterdir())


def test_idempotency_flag_blocks_resend(tmp_dirs):
    output_dir, data_dir, secrets_path, log_path = tmp_dirs
    _write_digest(output_dir, 2, "2026-05-23")
    now = _dt.datetime(2026, 5, 17, 0, 0, tzinfo=_dt.timezone.utc)
    # Pre-write the idempotency flag for the same ISO week as `now`
    pre_flag = lds.idempotency_flag_path(data_dir, now=now)
    pre_flag.write_text(json.dumps({"message_id": "earlier-fire"}))

    fake_httpx = _fake_httpx_module()
    with patch.dict(sys.modules, {"httpx": fake_httpx}):
        rc = lds.run(
            output_dir=output_dir,
            data_dir=data_dir,
            secrets_path=secrets_path,
            log_path=log_path,
            now=now,
        )
    assert rc == 0
    gmail_posts = [c for c in fake_httpx._calls["post"] if "gmail.googleapis.com" in c[0]]
    assert gmail_posts == []


def test_from_header_verification_failure_raises_non_zero(tmp_dirs):
    output_dir, data_dir, secrets_path, log_path = tmp_dirs
    _write_digest(output_dir, 1, "2026-05-16")

    # Simulate Gmail returning a rewritten From-line — verification must fail.
    fake_httpx = _fake_httpx_module(verify_from="bokar83@gmail.com")
    with patch.dict(sys.modules, {"httpx": fake_httpx}):
        rc = lds.run(
            output_dir=output_dir,
            data_dir=data_dir,
            secrets_path=secrets_path,
            log_path=log_path,
        )
    assert rc == 6  # verify failure exit code
    # Idempotency flag NOT written so the next run can re-investigate
    assert not any(p.name.startswith(lds.SENT_FLAG_PREFIX) for p in data_dir.iterdir())


def test_happy_path_sends_verifies_and_writes_flag(tmp_dirs):
    output_dir, data_dir, secrets_path, log_path = tmp_dirs
    _write_digest(output_dir, 7, "2026-07-04", body="<html><body>W7</body></html>")
    now = _dt.datetime(2026, 7, 5, 0, 0, tzinfo=_dt.timezone.utc)

    fake_httpx = _fake_httpx_module(send_message_id="msg-w7-id")
    with patch.dict(sys.modules, {"httpx": fake_httpx}):
        rc = lds.run(
            output_dir=output_dir,
            data_dir=data_dir,
            secrets_path=secrets_path,
            log_path=log_path,
            now=now,
        )
    assert rc == 0

    # Exactly one Gmail send POST + one OAuth token POST
    send_posts = [c for c in fake_httpx._calls["post"] if "messages/send" in c[0]]
    token_posts = [c for c in fake_httpx._calls["post"] if "oauth2.googleapis.com/token" in c[0]]
    assert len(send_posts) == 1
    assert len(token_posts) == 1

    # Send POST carries our raw MIME
    raw_b64 = send_posts[0][2]["json"]["raw"]
    padded = raw_b64 + "=" * (-len(raw_b64) % 4)
    msg = message_from_bytes(base64.urlsafe_b64decode(padded.encode("ascii")))
    assert msg["From"] == lds.FROM_ADDR
    assert "bokar83@gmail.com" in msg["To"]
    assert "boubacar@catalystworks.consulting" in msg["To"]
    assert msg["Subject"] == "Lighthouse W7 close + W8 launch read"

    # Verify-after-send GET happened
    verify_gets = [c for c in fake_httpx._calls["get"] if "gmail.googleapis.com" in c[0]]
    assert len(verify_gets) == 1
    assert "msg-w7-id" in verify_gets[0][0]

    # Idempotency flag written for current ISO week
    flag = lds.idempotency_flag_path(data_dir, now=now)
    assert flag.exists()
    payload = json.loads(flag.read_text())
    assert payload["message_id"] == "msg-w7-id"

    # Log line written
    log_text = log_path.read_text(encoding="utf-8")
    assert "OK" in log_text and "msg-w7-id" in log_text


def test_dry_run_does_not_send(tmp_dirs):
    output_dir, data_dir, secrets_path, log_path = tmp_dirs
    _write_digest(output_dir, 4, "2026-06-13")

    fake_httpx = _fake_httpx_module()
    with patch.dict(sys.modules, {"httpx": fake_httpx}):
        rc = lds.run(
            output_dir=output_dir,
            data_dir=data_dir,
            secrets_path=secrets_path,
            log_path=log_path,
            dry_run=True,
        )
    assert rc == 0
    assert fake_httpx._calls["post"] == []
    assert fake_httpx._calls["get"] == []
    assert not any(p.name.startswith(lds.SENT_FLAG_PREFIX) for p in data_dir.iterdir())


def test_missing_digest_returns_error_and_alerts(tmp_dirs):
    output_dir, data_dir, secrets_path, log_path = tmp_dirs
    # No digest files — directory is empty

    fake_httpx = _fake_httpx_module()
    # Make Telegram credentials available so the alert path exercises
    with patch.dict(sys.modules, {"httpx": fake_httpx}), patch.dict(
        "os.environ",
        {"OWNER_TELEGRAM_CHAT_ID": "123", "TELEGRAM_BOT_TOKEN": "tok"},
    ):
        rc = lds.run(
            output_dir=output_dir,
            data_dir=data_dir,
            secrets_path=secrets_path,
            log_path=log_path,
        )
    assert rc == 4
    telegram_posts = [c for c in fake_httpx._calls["post"] if "api.telegram.org" in c[0]]
    assert len(telegram_posts) == 1
