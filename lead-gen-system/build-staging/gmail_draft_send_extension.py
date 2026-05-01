"""DRAFT extension to signal_works/gmail_draft.py.

Pre-staged 2026-04-30. NOT a new file. The function below gets APPENDED to
signal_works/gmail_draft.py. It mirrors create_draft() but actually sends
instead of drafting. Same auth (gws CLI on Windows, gws Python on VPS),
same SENDER constant, same MIMEMultipart structure.

Used by skills/score_request/runner.py when SCORE_AUTO_SEND=true.
"""

# === BEGIN PASTE-IN APPEND TO signal_works/gmail_draft.py ===============

def send_message(to_email: str, subject: str, html_body: str) -> str:
    """Send an HTML email immediately (not a draft).

    Mirrors create_draft() but uses gws gmail users messages send instead
    of drafts create. Returns the Gmail message ID.

    Used by inbound automations where waiting for a human to click Send is
    not viable. Cold outreach should still use create_draft() so Boubacar
    can review before sending.

    Auth: same gws CLI / Python pattern as create_draft. Sender is the
    SENDER constant (boubacar@catalystworks.consulting).
    """
    import platform
    import tempfile
    import json
    import base64
    import subprocess
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8").rstrip("=\n")
    send_payload = json.dumps({"raw": raw})

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    tmp.write(send_payload)
    tmp.close()
    tmp_path = tmp.name

    try:
        if platform.system() == "Windows":
            safe_path = tmp_path.replace("\\", "/")
            ps_script = (
                f"Get-Content -Raw -Encoding UTF8 '{safe_path}'"
                " | gws gmail users messages send"
                " --params '{\"userId\":\"me\"}'"
                " --json -"
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True, text=True,
                env=_gws_env(), timeout=30,
            )
        else:
            with open(tmp_path, "r", encoding="utf-8") as f:
                json_content = f.read()
            result = subprocess.run(
                [
                    "gws", "gmail", "users", "messages", "send",
                    "--params", json.dumps({"userId": "me"}),
                    "--json", json_content,
                ],
                capture_output=True, text=True,
                env=_gws_env(), timeout=30,
            )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "unknown error")[:300]
        raise RuntimeError(f"Gmail send failed: {err}")

    try:
        data = json.loads(result.stdout)
        message_id = data.get("id", "")
        logger.info(f"Sent from {SENDER} to {to_email} | {subject[:60]} | id={message_id}")
        return message_id
    except json.JSONDecodeError:
        raise RuntimeError(f"Unexpected gws response: {result.stdout[:200]}")

# === END PASTE-IN APPEND ===============================================
