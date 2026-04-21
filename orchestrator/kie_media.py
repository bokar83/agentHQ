"""
kie_media.py — Kai (kie.ai) Media Generation Core
==================================================
Low-level client and business logic for image and video generation via kie.ai.

Flow:
  1. Pick top-ranked model for the requested task type from MODEL_REGISTRY.
  2. POST to the model's endpoint (unified /jobs/createTask or dedicated route).
  3. Poll /jobs/recordInfo every POLL_INTERVAL_SECS until state = success or fail.
  4. Download output URL to local workspace/media/ cache (URLs expire in 24h).
  5. Upload to the correct Google Drive folder (quarterly subfolder, auto-created).
  6. Write metadata row to Supabase media_generations.
  7. Return {drive_url, drive_file_id, local_path, model_used, cost_usd, attempts}.

Retry behavior (per Sankofa Council verdict):
  - On first model failure: retry same model once.
  - If still failing: escalate to rank-2, then rank-3.
  - Every attempt (pass or fail) logs to Supabase.
  - Rank-3 failure = total failure, report in chat.

Budget ceilings (auto-approve):
  - Image: <= $0.20 per call
  - Video: <= $2.00 per call

Models above ceiling require explicit user confirmation (Phase 2, not enforced yet).
"""

import os
import json
import time
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

KIE_BASE = "https://api.kie.ai"
POLL_INTERVAL_SECS = 5
MAX_POLL_ATTEMPTS = 120  # 10 minutes max for a single task

LOCAL_CACHE_DIR = Path(os.environ.get("MEDIA_LOCAL_CACHE", "workspace/media"))

ASSET_LIBRARY_ROOT = "1T3uF6jDOo_RBTXIb4qE60_ZxUeqJj6gL"  # pragma: allowlist secret
IMAGES_FOLDER = "1evq8JATALZhZXclxEIpdDEK4BJUJTQWZ"  # pragma: allowlist secret
VIDEOS_FOLDER = "1jvdSp0GggQi6-7o4WkS5Q-Jv3F1tjqE5"  # pragma: allowlist secret
SCRATCH_FOLDER = "1hsfYIHY9KbVn_GqpAzceO2tAWPsfOXKE"  # pragma: allowlist secret


MODEL_REGISTRY = {
    "text_to_image": [
        {
            "slug": "seedream/4.5-text-to-image",
            "endpoint": "unified",
            "input_key": "input",
            "default_input": {"aspect_ratio": "16:9", "quality": "high"},
        },
        {
            "slug": "google/imagen4",
            "endpoint": "unified",
            "input_key": "input",
            "default_input": {"aspect_ratio": "16:9"},
        },
        {
            "slug": "flux2/pro-text-to-image",
            "endpoint": "unified",
            "input_key": "input",
            "default_input": {"aspect_ratio": "16:9"},
        },
    ],
    "image_to_image": [
        {
            "slug": "google/nano-banana-pro-image-to-image",
            "endpoint": "unified",
            "input_key": "input",
            "default_input": {},
        },
        {
            "slug": "seedream/5-lite-text-to-image",
            "endpoint": "unified",
            "input_key": "input",
            "default_input": {},
        },
    ],
    "text_to_video": [
        {
            "slug": "veo3_fast",
            "endpoint": "/api/v1/veo/generate",
            "body_override": {"model": "veo3_fast", "aspect_ratio": "16:9", "resolution": "1080p"},
            "prompt_key": "prompt",
        },
        {
            "slug": "kling/v2-5-turbo-text-to-video-pro",
            "endpoint": "unified",
            "input_key": "input",
            "default_input": {},
        },
        {
            "slug": "bytedance/seedance-2",
            "endpoint": "unified",
            "input_key": "input",
            "default_input": {},
        },
    ],
    "image_to_video": [
        {
            "slug": "hailuo/2-3-image-to-video-pro",
            "endpoint": "unified",
            "input_key": "input",
            "default_input": {},
        },
        {
            "slug": "kling/v2-1-master-text-to-video",
            "endpoint": "unified",
            "input_key": "input",
            "default_input": {},
        },
    ],
}


class KieMediaError(Exception):
    """Raised when Kai generation fails after all retries."""


def _api_key() -> str:
    key = os.environ.get("KIE_AI_API_KEY", "").strip()
    if not key:
        raise KieMediaError("KIE_AI_API_KEY is not set in environment")
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }


def _create_task(model_config: dict, prompt: str, extra_input: dict | None = None) -> str:
    """POST to the right endpoint, return taskId."""
    endpoint = model_config["endpoint"]

    if endpoint == "unified":
        url = f"{KIE_BASE}/api/v1/jobs/createTask"
        input_obj = dict(model_config.get("default_input", {}))
        if extra_input:
            input_obj.update(extra_input)
        input_obj["prompt"] = prompt
        body = {"model": model_config["slug"], "input": input_obj}
    else:
        url = f"{KIE_BASE}{endpoint}"
        body = dict(model_config.get("body_override", {}))
        body[model_config.get("prompt_key", "prompt")] = prompt
        if extra_input:
            body.update(extra_input)

    logger.info(f"Kai createTask -> {model_config['slug']} at {url}")
    resp = httpx.post(url, headers=_headers(), json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 200:
        raise KieMediaError(f"Kai createTask failed: {data.get('msg')} (code={data.get('code')})")
    task_id = data.get("data", {}).get("taskId")
    if not task_id:
        raise KieMediaError(f"Kai createTask returned no taskId: {data}")
    return task_id


def _poll_task(task_id: str) -> dict:
    """Poll /jobs/recordInfo until state is terminal. Return parsed result."""
    url = f"{KIE_BASE}/api/v1/jobs/recordInfo"
    for attempt in range(MAX_POLL_ATTEMPTS):
        resp = httpx.get(url, headers=_headers(), params={"taskId": task_id}, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        state = data.get("state", "")
        if state == "success":
            result_raw = data.get("resultJson", "{}")
            result = json.loads(result_raw) if isinstance(result_raw, str) else result_raw
            urls = result.get("resultUrls", []) or []
            if not urls:
                raise KieMediaError(f"Task {task_id} succeeded but returned no resultUrls: {result}")
            return {
                "state": "success",
                "result_urls": urls,
                "cost_time_ms": data.get("costTime", 0),
            }
        if state == "fail":
            raise KieMediaError(
                f"Task {task_id} failed: {data.get('failMsg', 'unknown')} "
                f"(code={data.get('failCode')})"
            )
        time.sleep(POLL_INTERVAL_SECS)
    raise KieMediaError(f"Task {task_id} timed out after {MAX_POLL_ATTEMPTS * POLL_INTERVAL_SECS}s")


def _run_single_model(model_config: dict, prompt: str, extra_input: dict | None) -> dict:
    """Create + poll a single model. Raises on failure."""
    task_id = _create_task(model_config, prompt, extra_input)
    return _poll_task(task_id)


def _run_with_retries(task_type: str, prompt: str, extra_input: dict | None = None) -> dict:
    """
    Execute generation with retry/escalation policy.
    Returns: {result_urls, model_used, attempts, cost_time_ms_total}
    Raises KieMediaError on final failure.
    """
    if task_type not in MODEL_REGISTRY:
        raise KieMediaError(f"Unknown task_type '{task_type}'. Valid: {list(MODEL_REGISTRY.keys())}")

    models = MODEL_REGISTRY[task_type]
    attempts: list[dict] = []
    last_error = None

    for rank, model_config in enumerate(models, start=1):
        slug = model_config["slug"]
        same_model_tries = 2 if rank == 1 else 1
        for try_num in range(1, same_model_tries + 1):
            try:
                logger.info(f"Kai attempt rank={rank} try={try_num} model={slug}")
                result = _run_single_model(model_config, prompt, extra_input)
                attempts.append({"rank": rank, "try": try_num, "model": slug, "state": "success"})
                return {
                    "result_urls": result["result_urls"],
                    "model_used": slug,
                    "rank_used": rank,
                    "attempts": attempts,
                    "cost_time_ms_total": sum(
                        a.get("cost_time_ms", 0) for a in attempts
                    ) + result.get("cost_time_ms", 0),
                }
            except Exception as e:
                last_error = str(e)
                attempts.append({"rank": rank, "try": try_num, "model": slug, "state": "fail", "error": last_error[:300]})
                logger.warning(f"Kai {slug} attempt {try_num} failed: {last_error[:200]}")

    raise KieMediaError(
        f"All {len(models)} ranked models failed for {task_type}. Last error: {last_error}. Attempts: {attempts}"
    )


def _download_asset(url: str, local_path: Path) -> int:
    """Download URL to local_path. Returns byte count."""
    local_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "agentsHQ-kie-media/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    local_path.write_bytes(data)
    return len(data)


def _slugify(text: str, max_len: int = 40) -> str:
    slug = "".join(c.lower() if c.isalnum() else "-" for c in text.strip())
    slug = "-".join(s for s in slug.split("-") if s)
    return slug[:max_len] or "untitled"


def _current_quarter() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year}-Q{(now.month - 1) // 3 + 1}"


def _gws_request_passthrough(method: str, url: str, **kwargs) -> dict:
    """Thin wrapper importing the orchestrator's GWS helper at call time."""
    try:
        from orchestrator.tools import _gws_request as gws
    except ImportError:
        from tools import _gws_request as gws  # flat /app layout inside container
    return gws(method, url, **kwargs)


def _find_or_create_folder(name: str, parent_id: str) -> str:
    """Return folder ID; create it inside parent if missing."""
    query = (
        f"name='{name}' and '{parent_id}' in parents "
        f"and mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    result = _gws_request_passthrough(
        "get",
        "https://www.googleapis.com/drive/v3/files",
        params={"q": query, "fields": "files(id,name)", "pageSize": 10},
    )
    files = result.get("files", [])
    if files:
        return files[0]["id"]
    created = _gws_request_passthrough(
        "post",
        "https://www.googleapis.com/drive/v3/files?fields=id",
        json={
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        },
    )
    return created["id"]


def _upload_to_drive(local_path: Path, drive_folder_id: str, filename: str, mime_type: str) -> dict:
    """Upload a local file to Drive using multipart. Returns {id, webViewLink}."""
    try:
        import os as _os
        import json as _json
        creds_path = (
            _os.environ.get("GWS_CREDS_PATH")
            or _os.path.join(_os.path.dirname(__file__), "..", "secrets", "gws_token.json")
        )
        with open(creds_path) as f:
            creds = _json.load(f)
    except Exception as e:
        raise KieMediaError(f"Cannot load GWS credentials for Drive upload: {e}")

    token_resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"],
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    token_resp.raise_for_status()
    access_token = token_resp.json()["access_token"]

    metadata = {"name": filename, "parents": [drive_folder_id]}
    file_bytes = local_path.read_bytes()

    boundary = "kieMediaBoundary7d3f"
    body = (
        f"--{boundary}\r\n"
        f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--".encode("utf-8")

    resp = httpx.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,webViewLink,webContentLink",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
        content=body,
        timeout=300,
    )
    resp.raise_for_status()
    out = resp.json()
    return {
        "id": out.get("id"),
        "webViewLink": out.get("webViewLink", f"https://drive.google.com/file/d/{out.get('id')}/view"),
    }


def _log_to_notion_media_index(row: dict) -> None:
    """Insert a page into the Notion Media Index DB. Non-fatal on error."""
    db_id = os.environ.get("NOTION_MEDIA_INDEX_DB_ID", "").strip()
    token = (
        os.environ.get("NOTION_SECRET", "").strip()
        or os.environ.get("NOTION_TOKEN", "").strip()
        or os.environ.get("NOTION_API_KEY", "").strip()
    )
    if not db_id or not token:
        logger.info("Notion Media Index log skipped (missing NOTION_MEDIA_INDEX_DB_ID or NOTION_SECRET)")
        return
    try:
        media_kind = "Video" if row.get("task_type", "").endswith("_video") else "Image"
        state = row.get("state", "success")
        status_label = "Failed" if state == "fail" else "Success"
        props: dict[str, Any] = {
            "Title": {"title": [{"text": {"content": row.get("filename") or row.get("prompt", "")[:90]}}]},
            "Type": {"select": {"name": media_kind}},
            "Status": {"select": {"name": status_label}},
            "Task Type": {"select": {"name": row.get("task_type", "")}},
            "Prompt": {"rich_text": [{"text": {"content": (row.get("prompt") or "")[:1900]}}]},
            "Model Used": {"rich_text": [{"text": {"content": row.get("model_used") or ""}}]},
            "Rank Used": {"number": row.get("rank_used") or 0},
            "Quarter": {"rich_text": [{"text": {"content": row.get("quarter") or _current_quarter()}}]},
            "Attempts": {"rich_text": [{"text": {"content": json.dumps(row.get("attempts", []))[:1900]}}]},
        }
        if row.get("drive_url"):
            props["Drive URL"] = {"url": row["drive_url"]}
        if row.get("drive_file_id"):
            props["Drive File ID"] = {"rich_text": [{"text": {"content": row["drive_file_id"]}}]}
        if row.get("local_path"):
            props["Local Path"] = {"rich_text": [{"text": {"content": str(row["local_path"])[:1900]}}]}
        if row.get("linked_content_id"):
            props["Content Board"] = {"relation": [{"id": row["linked_content_id"]}]}

        resp = httpx.post(
            "https://api.notion.com/v1/pages",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            json={"parent": {"database_id": db_id}, "properties": props},
            timeout=30,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Notion Media Index log skipped (non-fatal): {type(e).__name__}: {e}")


def _log_to_supabase(row: dict) -> None:
    """Insert a row into media_generations. Non-fatal on error."""
    try:
        try:
            from orchestrator.db import get_crm_connection
        except ImportError:
            from db import get_crm_connection
        conn = get_crm_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO media_generations (
                        task_type, prompt, model_used, rank_used,
                        drive_file_id, drive_url, local_path,
                        state, attempts_json, quarter,
                        linked_content_id, notes, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        row.get("task_type"),
                        row.get("prompt", "")[:2000],
                        row.get("model_used"),
                        row.get("rank_used"),
                        row.get("drive_file_id"),
                        row.get("drive_url"),
                        row.get("local_path"),
                        row.get("state", "success"),
                        json.dumps(row.get("attempts", [])),
                        row.get("quarter", _current_quarter()),
                        row.get("linked_content_id"),
                        row.get("notes"),
                    ),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"media_generations log skipped (non-fatal): {type(e).__name__}: {e}")


def generate_image(
    prompt: str,
    aspect_ratio: str = "16:9",
    task_type: str = "text_to_image",
    linked_content_id: str | None = None,
) -> dict:
    """
    Generate an image via the top-ranked Kai model, store on Drive, log metadata.
    Returns: {drive_url, drive_file_id, local_path, model_used, attempts}
    """
    extra = {"aspect_ratio": aspect_ratio} if task_type == "text_to_image" else {}
    gen = _run_with_retries(task_type, prompt, extra)

    source_url = gen["result_urls"][0]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    slug = _slugify(prompt, max_len=40)
    model_slug = _slugify(gen["model_used"], max_len=30)
    filename = f"MEDIA_image_{timestamp}_{model_slug}_{slug}.png"

    local_path = LOCAL_CACHE_DIR / "images" / _current_quarter() / filename
    _download_asset(source_url, local_path)

    quarter_folder_id = _find_or_create_folder(_current_quarter(), IMAGES_FOLDER)
    drive_result = _upload_to_drive(local_path, quarter_folder_id, filename, "image/png")

    result = {
        "drive_url": drive_result["webViewLink"],
        "drive_file_id": drive_result["id"],
        "local_path": str(local_path),
        "model_used": gen["model_used"],
        "rank_used": gen["rank_used"],
        "attempts": gen["attempts"],
        "filename": filename,
    }
    log_row = {
        **result,
        "task_type": task_type,
        "prompt": prompt,
        "state": "success",
        "linked_content_id": linked_content_id,
        "quarter": _current_quarter(),
    }
    _log_to_supabase(log_row)
    _log_to_notion_media_index(log_row)
    return result


def generate_video(
    prompt: str,
    aspect_ratio: str = "16:9",
    task_type: str = "text_to_video",
    linked_content_id: str | None = None,
) -> dict:
    """
    Generate a video via the top-ranked Kai model, store on Drive, log metadata.
    Returns: {drive_url, drive_file_id, local_path, model_used, attempts}
    """
    extra = {"aspect_ratio": aspect_ratio} if task_type == "text_to_video" else {}
    gen = _run_with_retries(task_type, prompt, extra)

    source_url = gen["result_urls"][0]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    slug = _slugify(prompt, max_len=40)
    model_slug = _slugify(gen["model_used"], max_len=30)
    filename = f"MEDIA_video_{timestamp}_{model_slug}_{slug}.mp4"

    local_path = LOCAL_CACHE_DIR / "videos" / _current_quarter() / filename
    _download_asset(source_url, local_path)

    quarter_folder_id = _find_or_create_folder(_current_quarter(), VIDEOS_FOLDER)
    drive_result = _upload_to_drive(local_path, quarter_folder_id, filename, "video/mp4")

    result = {
        "drive_url": drive_result["webViewLink"],
        "drive_file_id": drive_result["id"],
        "local_path": str(local_path),
        "model_used": gen["model_used"],
        "rank_used": gen["rank_used"],
        "attempts": gen["attempts"],
        "filename": filename,
    }
    log_row = {
        **result,
        "task_type": task_type,
        "prompt": prompt,
        "state": "success",
        "linked_content_id": linked_content_id,
        "quarter": _current_quarter(),
    }
    _log_to_supabase(log_row)
    _log_to_notion_media_index(log_row)
    return result


def list_models(task_type: str | None = None) -> dict:
    """Return the current priority-ordered model registry."""
    if task_type:
        if task_type not in MODEL_REGISTRY:
            return {"error": f"unknown task_type '{task_type}'", "valid": list(MODEL_REGISTRY.keys())}
        return {task_type: [m["slug"] for m in MODEL_REGISTRY[task_type]]}
    return {k: [m["slug"] for m in v] for k, v in MODEL_REGISTRY.items()}


def check_credits() -> int:
    """Return current Kai credit balance."""
    resp = httpx.get(f"{KIE_BASE}/api/v1/chat/credit", headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json().get("data", 0)


__all__ = [
    "generate_image",
    "generate_video",
    "list_models",
    "check_credits",
    "MODEL_REGISTRY",
    "KieMediaError",
]
