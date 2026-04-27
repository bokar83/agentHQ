"""
signal_works/gmail_draft.py
Creates Gmail drafts from boubacar@catalystworks.consulting using the same
OAuth credentials pattern as orchestrator/tools.py _gws_request().

Reads secrets/gws-oauth-credentials-cw.json directly -- no gws CLI, no
subprocess quoting issues, no command-line length limits.
"""
import base64
import json
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

SENDER = "boubacar@catalystworks.consulting"

# Resolve credentials path: env var → local secrets/ → Docker /app/secrets/
def _creds_path() -> str:
    env = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON_CW", "")
    if env and os.path.exists(env):
        return env
    local = Path(__file__).resolve().parents[1] / "secrets" / "gws-oauth-credentials-cw.json"
    if local.exists():
        return str(local)
    docker = "/app/secrets/gws-oauth-credentials-cw.json"
    if os.path.exists(docker):
        return docker
    raise FileNotFoundError(
        "Cannot find gws-oauth-credentials-cw.json. "
        "Set GOOGLE_OAUTH_CREDENTIALS_JSON_CW or place file in secrets/."
    )


def _get_access_token() -> str:
    with open(_creds_path()) as f:
        creds = json.load(f)
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


def create_draft(to_email: str, subject: str, html_body: str) -> str:
    """Create a Gmail draft from boubacar@catalystworks.consulting. Returns draft ID."""
    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8").rstrip("=")
    token = _get_access_token()

    resp = httpx.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/drafts",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": {"raw": raw}},
        timeout=30,
    )
    resp.raise_for_status()
    draft_id = resp.json().get("id", "")
    logger.info(f"Draft created from {SENDER}: {to_email} | {subject[:60]} | id={draft_id}")
    return draft_id
