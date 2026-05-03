"""
studio_brand_config.py — Dynamic brand config loader for Studio M3.

Resolution order:
  1. Notion Studio Brand Config DB (live, M2 fills this)
  2. configs/brand_config.<channel_id>.json  (per-channel file, M2 fills placeholders)
  3. configs/brand_config.placeholder.json   (dev fallback, always works)

When M2 ships: Boubacar fills the Notion Brand Config DB or updates the
per-channel JSON files. Pipeline picks up new values on next tick — zero code changes.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("agentsHQ.studio_brand_config")

# Resolve configs/ directory: works for both local dev (orchestrator/../configs)
# and container flat layout (/app/configs).
_CONFIGS_DIR = Path(__file__).parent.parent / "configs"
if not _CONFIGS_DIR.exists():
    _CONFIGS_DIR = Path(__file__).parent / "configs"
if not _CONFIGS_DIR.exists():
    _CONFIGS_DIR = Path("/app/configs")
_PLACEHOLDER_PATH = _CONFIGS_DIR / "brand_config.placeholder.json"
_NOTION_BRAND_DB_ID = os.environ.get("NOTION_STUDIO_BRAND_CONFIG_DB_ID", "")


def load_brand_config(channel_id: str) -> dict[str, Any]:
    """Return brand config for channel_id. Never raises — falls back to placeholder."""
    if _NOTION_BRAND_DB_ID:
        cfg = _load_from_notion(channel_id)
        if cfg:
            logger.info("brand_config loaded from Notion for %s", channel_id)
            return cfg

    per_channel_path = _CONFIGS_DIR / f"brand_config.{channel_id}.json"
    if per_channel_path.exists():
        cfg = _load_json(per_channel_path)
        if cfg:
            logger.info("brand_config loaded from %s", per_channel_path.name)
            return _fill_placeholders_with_defaults(cfg)

    logger.warning(
        "brand_config: no config for '%s', using placeholder. "
        "Run M2 to fill brand values.",
        channel_id,
    )
    return _load_json(_PLACEHOLDER_PATH) or {}


def is_brand_ready(channel_id: str) -> bool:
    """True when M2 has filled all __M2_PENDING__ slots."""
    cfg = load_brand_config(channel_id)
    return not any(
        isinstance(v, str) and "__M2_PENDING__" in v
        for v in _flatten_values(cfg)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("brand_config: failed to load %s: %s", path, exc)
        return None


def _load_from_notion(channel_id: str) -> dict | None:
    try:
        import httpx
        token = os.environ["NOTION_TOKEN"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
        }
        resp = httpx.post(
            f"https://api.notion.com/v1/databases/{_NOTION_BRAND_DB_ID}/query",
            headers=headers,
            json={"filter": {"property": "channel_id", "rich_text": {"equals": channel_id}}},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return None
        return _notion_page_to_config(results[0])
    except Exception as exc:
        logger.warning("brand_config: Notion lookup failed for '%s': %s", channel_id, exc)
        return None


def _notion_page_to_config(page: dict) -> dict:
    """Flatten Notion page properties into brand config dict."""
    props = page.get("properties", {})

    def _text(key: str) -> str:
        val = props.get(key, {})
        rich = val.get("rich_text", []) or val.get("title", [])
        return rich[0]["plain_text"] if rich else ""

    def _select(key: str) -> str:
        sel = props.get(key, {}).get("select")
        return sel["name"] if sel else ""

    cfg_json = _text("config_json")
    if cfg_json:
        try:
            return json.loads(cfg_json)
        except json.JSONDecodeError:
            pass

    return {
        "channel_id": _text("channel_id"),
        "display_name": _text("display_name"),
        "voice_id": _text("voice_id"),
        "primary_color": _text("primary_color"),
        "accent_color": _text("accent_color"),
        "background_color": _text("background_color"),
        "font_family": _text("font_family"),
        "visual_style": _text("visual_style"),
        "script_tone": _text("script_tone"),
    }


def _fill_placeholders_with_defaults(cfg: dict) -> dict:
    """Replace __M2_PENDING__* values with placeholder equivalents so pipeline never crashes."""
    placeholder = _load_json(_PLACEHOLDER_PATH) or {}
    result = dict(cfg)
    for key, val in result.items():
        if isinstance(val, str) and "__M2_PENDING__" in val:
            result[key] = placeholder.get(key, val)
        elif isinstance(val, dict):
            result[key] = val  # nested dicts (platform_specs) kept as-is
    return result


def _flatten_values(d: dict) -> list:
    out = []
    for v in d.values():
        if isinstance(v, dict):
            out.extend(_flatten_values(v))
        else:
            out.append(v)
    return out
