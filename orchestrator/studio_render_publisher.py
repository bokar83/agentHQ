"""
studio_render_publisher.py — Studio M3: Render + Drive upload + Notion update.

Renders 3 formats from one hyperframes project:
  long_form  1920x1080 → 05_Asset_Library/<channel>/<YYYY-MM-DD>/long_form/
  shorts     1080x1920 → .../shorts/
  square     1080x1080 → .../square/

After render:
  - Upload each MP4 to Drive
  - Update Notion Pipeline DB record: Asset_URL + Status=scheduled
  - Send Telegram notification
"""
from __future__ import annotations

import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("agentsHQ.studio_render_publisher")

_HF_CMD = os.environ.get("HYPERFRAMES_CMD", "npx hyperframes")
_RENDERS_DIR = Path(os.environ.get("STUDIO_RENDERS_DIR", "workspace/renders"))

_NOTION_TOKEN = (
    os.environ.get("NOTION_SECRET")
    or os.environ.get("NOTION_API_KEY")
    or ""
)
_PIPELINE_DB_ID = os.environ.get("NOTION_STUDIO_PIPELINE_DB_ID", "")

# Drive folder IDs — per-format subfolders created automatically under channel folder
_DRIVE_ASSET_LIBRARY_ROOT = os.environ.get(
    "DRIVE_ASSET_LIBRARY_ROOT",
    "1T3uF6jDOo_RBTXIb4qE60_ZxUeqJj6gL",  # pragma: allowlist secret
)

_PLATFORM_SPECS = {
    "long_form": {"width": 1920, "height": 1080, "fps": 30},
    "shorts":    {"width": 1080, "height": 1920, "fps": 30},
    "square":    {"width": 1080, "height": 1080, "fps": 30},
}


def render_and_publish(
    composition: dict[str, Any],
    brand: dict[str, Any],
    notion_id: str,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Render all platform formats, upload to Drive, update Notion, notify Telegram.

    Returns:
      {
        "renders": {
          "long_form": {"local_path": str, "drive_url": str, "drive_file_id": str},
          "shorts": {...},
          "square": {...},
        },
        "notion_updated": bool,
        "primary_asset_url": str,   # long_form Drive URL
      }
    """
    project_dir = Path(composition["project_dir"])
    channel_id = brand.get("channel_id", "unknown")
    title = composition.get("composition_html", "")[:60]  # for logging only
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    renders: dict[str, Any] = {}

    for fmt, specs in _PLATFORM_SPECS.items():
        output_path = _render_format(project_dir, fmt, specs, channel_id, today, dry_run)
        if output_path and output_path.exists():
            drive_result = _upload_render(output_path, channel_id, fmt, today, dry_run)
            renders[fmt] = {
                "local_path": str(output_path),
                "drive_url": drive_result.get("webViewLink", ""),
                "drive_file_id": drive_result.get("id", ""),
            }
        else:
            renders[fmt] = {"local_path": "", "drive_url": "", "drive_file_id": ""}
            logger.warning("render_publisher: %s render missing for %s", fmt, channel_id)

    primary_url = renders.get("long_form", {}).get("drive_url", "")
    notion_updated = _update_notion(notion_id, primary_url, dry_run)
    _notify_telegram(channel_id, notion_id, renders, dry_run)

    return {
        "renders": renders,
        "notion_updated": notion_updated,
        "primary_asset_url": primary_url,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Render
# ─────────────────────────────────────────────────────────────────────────────

def _render_format(
    project_dir: Path,
    fmt: str,
    specs: dict,
    channel_id: str,
    today: str,
    dry_run: bool,
) -> Path | None:
    out_dir = _RENDERS_DIR / channel_id / today / fmt
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%H%M%S")
    output_path = out_dir / f"{channel_id}_{fmt}_{today}_{ts}.mp4"

    if dry_run:
        output_path.write_bytes(b"")  # empty file, smoke test only
        logger.info("[dry_run] render_publisher: stub render %s", output_path)
        return output_path

    w, h, fps = specs["width"], specs["height"], specs["fps"]
    cmd = (
        _HF_CMD.split()
        + ["render",
           "--output", str(output_path),
           "--quality", "high",
           "--fps", str(fps),
           # hyperframes reads composition dimensions from index.html data-composition-id
           # Width/height override passed via env for platform format switching
           ]
    )

    env = os.environ.copy()
    env["HF_RENDER_WIDTH"] = str(w)
    env["HF_RENDER_HEIGHT"] = str(h)

    logger.info("render_publisher: rendering %s (%dx%d@%d)", fmt, w, h, fps)
    result = subprocess.run(
        cmd,
        cwd=str(project_dir),
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        logger.error(
            "render_publisher: %s render failed (rc=%d):\n%s",
            fmt, result.returncode, result.stderr[-2000:],
        )
        return None

    logger.info("render_publisher: %s complete → %s", fmt, output_path)
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# Drive upload
# ─────────────────────────────────────────────────────────────────────────────

def _upload_render(
    local_path: Path,
    channel_id: str,
    fmt: str,
    today: str,
    dry_run: bool,
) -> dict:
    if dry_run:
        return {"webViewLink": f"https://drive.google.com/stub_{fmt}", "id": f"stub_{fmt}"}
    try:
        from kie_media import _upload_to_drive, _find_or_create_folder
        channel_folder = _find_or_create_folder(channel_id, _DRIVE_ASSET_LIBRARY_ROOT)
        date_folder = _find_or_create_folder(today, channel_folder)
        fmt_folder = _find_or_create_folder(fmt, date_folder)
        return _upload_to_drive(local_path, fmt_folder)
    except Exception as exc:
        logger.error("render_publisher: Drive upload failed for %s/%s: %s", fmt, local_path.name, exc)
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# Notion update
# ─────────────────────────────────────────────────────────────────────────────

def _update_notion(notion_id: str, asset_url: str, dry_run: bool) -> bool:
    if dry_run:
        logger.info("[dry_run] render_publisher: Notion update skipped for %s", notion_id)
        return True
    if not _NOTION_TOKEN or not notion_id:
        logger.warning("render_publisher: Notion update skipped (missing token or id)")
        return False
    try:
        resp = httpx.patch(
            f"https://api.notion.com/v1/pages/{notion_id}",
            headers={
                "Authorization": f"Bearer {_NOTION_TOKEN}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            json={
                "properties": {
                    "Status": {"select": {"name": "scheduled"}},
                    "Asset URL": {"url": asset_url or None},
                }
            },
            timeout=15,
        )
        resp.raise_for_status()
        logger.info("render_publisher: Notion %s → scheduled", notion_id)
        return True
    except Exception as exc:
        logger.error("render_publisher: Notion update failed for %s: %s", notion_id, exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Telegram notification
# ─────────────────────────────────────────────────────────────────────────────

def _notify_telegram(
    channel_id: str,
    notion_id: str,
    renders: dict,
    dry_run: bool,
) -> None:
    if dry_run:
        logger.info("[dry_run] render_publisher: Telegram notification skipped")
        return
    try:
        from notifier import send_message
        lf = renders.get("long_form", {})
        sh = renders.get("shorts", {})
        sq = renders.get("square", {})
        lines = [
            f"Studio M3 render complete",
            f"Channel: {channel_id}",
            f"Notion: {notion_id}",
            f"Long form: {lf.get('drive_url') or 'MISSING'}",
            f"Shorts: {sh.get('drive_url') or 'MISSING'}",
            f"Square: {sq.get('drive_url') or 'MISSING'}",
            f"Status: scheduled",
        ]
        send_message("\n".join(lines))
    except Exception as exc:
        logger.warning("render_publisher: Telegram notification failed: %s", exc)
