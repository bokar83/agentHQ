"""
drive_publish.py — Publish PDFs (and other files) to Google Drive with public-link permission.

Use for any file that ships in an outgoing email or external-facing message.
Upload + permission grant happen in one call so we never email a Drive URL
that recipients cannot open.

Public API:
  publish_public_file(local_path, drive_folder_id, filename, mime_type) -> {id, url}
      Uploads a new file to the given folder, then grants anyone-with-link reader.

  update_public_file(file_id, local_path, mime_type) -> {id, url}
      Replaces content of an existing Drive file (preserves URL), then ensures
      anyone-with-link reader is set.

  ensure_public(file_id) -> bool
      Idempotent: adds anyone-with-link reader if missing. Returns True if a
      permission was created, False if it was already public.

Auth: reuses GOOGLE_OAUTH_CREDENTIALS_JSON / GWS_CREDS_PATH like kie_media.py.

Lint helper:
  audit_email_template_pdfs() -> list[dict]
      Scans templates/email/ for drive.google.com URLs and reports any file
      that does not have anyone-with-link reader. Use in CI / pre-send checks.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import httpx


DRIVE_FILE_RE = re.compile(r"drive\.google\.com/file/d/([A-Za-z0-9_-]+)")
EMAIL_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"

# Local Windows dev: set DRIVE_PUBLISH_VERIFY_SSL=0 if Python cannot verify Google certs.
# Container (Linux) keeps verification on by default.
_VERIFY_SSL = os.environ.get("DRIVE_PUBLISH_VERIFY_SSL", "1") != "0"


class DrivePublishError(RuntimeError):
    pass


def _access_token() -> str:
    candidates = [
        os.environ.get("GWS_CREDS_PATH"),
        os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON"),
        os.path.join(os.path.dirname(__file__), "..", "secrets", "gws-oauth-credentials.json"),
        os.path.join(os.path.dirname(__file__), "..", "secrets", "gws_token.json"),
    ]
    creds = None
    last_err: Exception | None = None
    for path in candidates:
        if not path:
            continue
        try:
            with open(path) as f:
                creds = json.load(f)
            break
        except Exception as e:
            last_err = e
            continue
    if creds is None:
        raise DrivePublishError(f"Cannot load GWS credentials: {last_err}")

    resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"],
            "grant_type": "refresh_token",
        },
        timeout=15,
        verify=_VERIFY_SSL,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _drive_url(file_id: str) -> str:
    return f"https://drive.google.com/file/d/{file_id}/view"


def ensure_public(file_id: str, token: str | None = None) -> bool:
    """Grant anyone-with-link reader if not already present.

    Returns True if a new permission was created, False if already public.
    """
    tok = token or _access_token()
    headers = {"Authorization": f"Bearer {tok}"}

    list_resp = httpx.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions",
        headers=headers,
        params={"fields": "permissions(id,type,role,allowFileDiscovery)"},
        timeout=15,
        verify=_VERIFY_SSL,
    )
    list_resp.raise_for_status()
    perms = list_resp.json().get("permissions", [])
    for p in perms:
        if p.get("type") == "anyone" and p.get("role") in ("reader", "writer", "commenter"):
            return False

    create_resp = httpx.post(
        f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions",
        headers={**headers, "Content-Type": "application/json"},
        params={"fields": "id,type,role"},
        content=json.dumps({"role": "reader", "type": "anyone", "allowFileDiscovery": False}),
        timeout=15,
        verify=_VERIFY_SSL,
    )
    create_resp.raise_for_status()
    return True


def publish_public_file(
    local_path: Path | str,
    drive_folder_id: str,
    filename: str,
    mime_type: str,
) -> dict:
    """Upload local file to Drive folder, set anyone-with-link reader. Returns {id, url}."""
    local_path = Path(local_path)
    if not local_path.exists():
        raise DrivePublishError(f"local file not found: {local_path}")

    token = _access_token()
    headers = {"Authorization": f"Bearer {token}"}

    metadata = {"name": filename, "parents": [drive_folder_id]}
    file_bytes = local_path.read_bytes()

    boundary = "drivePublishBoundary7d3f"
    body = (
        f"--{boundary}\r\n"
        f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--".encode("utf-8")

    upload_resp = httpx.post(
        "https://www.googleapis.com/upload/drive/v3/files",
        headers={**headers, "Content-Type": f"multipart/related; boundary={boundary}"},
        params={"uploadType": "multipart", "fields": "id,webViewLink"},
        content=body,
        timeout=300,
        verify=_VERIFY_SSL,
    )
    upload_resp.raise_for_status()
    out = upload_resp.json()
    file_id = out["id"]

    ensure_public(file_id, token=token)
    return {"id": file_id, "url": out.get("webViewLink") or _drive_url(file_id)}


def update_public_file(file_id: str, local_path: Path | str, mime_type: str) -> dict:
    """Replace content of existing Drive file (preserves URL), ensure public."""
    local_path = Path(local_path)
    if not local_path.exists():
        raise DrivePublishError(f"local file not found: {local_path}")

    token = _access_token()
    headers = {"Authorization": f"Bearer {token}"}
    file_bytes = local_path.read_bytes()

    upload_resp = httpx.patch(
        f"https://www.googleapis.com/upload/drive/v3/files/{file_id}",
        headers={**headers, "Content-Type": mime_type},
        params={"uploadType": "media", "fields": "id,webViewLink"},
        content=file_bytes,
        timeout=300,
        verify=_VERIFY_SSL,
    )
    upload_resp.raise_for_status()
    out = upload_resp.json()

    ensure_public(file_id, token=token)
    return {"id": file_id, "url": out.get("webViewLink") or _drive_url(file_id)}


def audit_email_template_pdfs() -> list[dict]:
    """Scan templates/email/ for Drive URLs and report public-permission status.

    Returns list of {file, file_id, public, source} dicts. Use in pre-send checks.
    """
    findings: list[dict] = []
    if not EMAIL_TEMPLATE_DIR.exists():
        return findings

    seen: set[tuple[str, str]] = set()
    token = _access_token()

    for path in sorted(EMAIL_TEMPLATE_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for match in DRIVE_FILE_RE.finditer(text):
            file_id = match.group(1)
            key = (path.name, file_id)
            if key in seen:
                continue
            seen.add(key)
            try:
                resp = httpx.get(
                    f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"fields": "permissions(type,role)"},
                    timeout=15,
                    verify=_VERIFY_SSL,
                )
                resp.raise_for_status()
                perms = resp.json().get("permissions", [])
                public = any(
                    p.get("type") == "anyone" and p.get("role") in ("reader", "writer", "commenter")
                    for p in perms
                )
            except Exception as e:
                findings.append(
                    {"file": path.name, "file_id": file_id, "public": None, "error": str(e)}
                )
                continue
            findings.append(
                {"file": path.name, "file_id": file_id, "public": public, "source": str(path)}
            )
    return findings


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "audit":
        results = audit_email_template_pdfs()
        any_private = False
        for r in results:
            status = "PUBLIC" if r.get("public") else ("ERROR" if r.get("public") is None else "PRIVATE")
            print(f"{status:7s} {r['file']:20s} {r['file_id']}")
            if r.get("public") is False:
                any_private = True
        sys.exit(2 if any_private else 0)
    else:
        print("usage: python -m orchestrator.drive_publish audit")
        sys.exit(1)
