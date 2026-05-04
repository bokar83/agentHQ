"""
studio_voice_generator.py — Studio M3: TTS voice generation.

Primary:  ElevenLabs v1/text-to-speech/{voice_id}/with-timestamps
Fallback: Kai TTS via kie_media (future: add kie_tts task_type when wired)

Returns:
  {
    "audio_path": str,            # local path to MP3
    "drive_url": str,             # Drive URL after upload
    "drive_file_id": str,
    "duration_sec": float,
    "timestamps": list[WordTimestamp],  # word-level for caption sync
    "provider": str,              # "elevenlabs" | "kie_tts"
  }
"""
from __future__ import annotations

import json
import logging
import os
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("agentsHQ.studio_voice_generator")

ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"
LOCAL_CACHE_DIR = Path(os.environ.get("MEDIA_LOCAL_CACHE", "workspace/media")) / "audio"
_DRIVE_AUDIO_FOLDER = os.environ.get(
    "DRIVE_STUDIO_AUDIO_FOLDER",
    "1evq8JATALZhZXclxEIpdDEK4BJUJTQWZ",  # fallback: kie_media IMAGES_FOLDER
)


@dataclass
class WordTimestamp:
    word: str
    start_sec: float
    end_sec: float


def generate_voice(
    script: dict[str, Any],
    brand: dict[str, Any],
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Generate TTS audio from script.full_text using brand voice_id.
    Tries ElevenLabs first; falls back to Kai TTS on failure.

    Voice resolution order:
      1. script["voice_role"] → look up in brand["voice_roles"] map
      2. brand["voice_id"]    → explicit default for this channel
      3. voice_registry.json defaults.studio_generic
      4. Hunter fallback (X4Lh5Ftnso6JSt25plzX)
    """
    text = script["full_text"]
    voice_role = script.get("voice_role")  # e.g. "elder", "female", "male", "boubacar"
    voice_id = _resolve_voice_id(voice_role, brand)
    title_slug = _slugify(script.get("title", "untitled"))
    channel_id = brand.get("channel_id", "unknown")
    logger.info("voice_generator: role=%s → voice_id=%s", voice_role or "default", voice_id)

    # Strip SSML tags for Kai fallback; ElevenLabs accepts them natively
    clean_text = _strip_scene_markers(text)

    if dry_run:
        logger.info("[dry_run] voice_generator skipping API call")
        return _stub_result(title_slug, channel_id)

    try:
        result = _elevenlabs_tts(clean_text, voice_id, title_slug, channel_id)
        result["provider"] = "elevenlabs"
        return result
    except Exception as exc:
        logger.warning("ElevenLabs TTS failed (%s), trying Kai fallback", exc)

    try:
        result = _kai_tts_fallback(clean_text, title_slug, channel_id)
        result["provider"] = "kie_tts"
        return result
    except Exception as exc:
        raise RuntimeError(f"Both TTS providers failed. Last error: {exc}") from exc


# ─────────────────────────────────────────────────────────────────────────────
# ElevenLabs
# ─────────────────────────────────────────────────────────────────────────────

def _elevenlabs_tts(
    text: str,
    voice_id: str,
    title_slug: str,
    channel_id: str,
) -> dict[str, Any]:
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY not set")

    # Strip SSML phoneme tags for the plain text path; ElevenLabs SSML requires
    # the text endpoint, not the timestamps endpoint. Send clean text + rely on
    # the pronunciation dict applied upstream in script_generator.
    plain_text = _strip_ssml(text)

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = {
        "text": plain_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }

    url = f"{ELEVENLABS_API_BASE}/text-to-speech/{voice_id}/with-timestamps"
    resp = httpx.post(url, headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    # Decode base64 audio
    import base64
    audio_b64 = data.get("audio_base64", "")
    if not audio_b64:
        raise RuntimeError("ElevenLabs returned no audio_base64")
    audio_bytes = base64.b64decode(audio_b64)

    local_path = _save_audio(audio_bytes, title_slug, channel_id)

    # Parse word-level alignment
    alignment = data.get("alignment", {})
    timestamps = _parse_elevenlabs_timestamps(alignment)

    duration_sec = timestamps[-1].end_sec if timestamps else len(plain_text.split()) / 2.5

    drive_result = _upload_audio_to_drive(local_path, channel_id)

    return {
        "audio_path": str(local_path),
        "drive_url": drive_result.get("webViewLink", ""),
        "drive_file_id": drive_result.get("id", ""),
        "duration_sec": duration_sec,
        "timestamps": [{"word": t.word, "start": t.start_sec, "end": t.end_sec} for t in timestamps],
    }


def _parse_elevenlabs_timestamps(alignment: dict) -> list[WordTimestamp]:
    """Parse ElevenLabs character-level alignment into word-level timestamps."""
    chars = alignment.get("characters", [])
    char_starts = alignment.get("character_start_times_seconds", [])
    char_ends = alignment.get("character_end_times_seconds", [])

    if not chars or not char_starts:
        return []

    timestamps: list[WordTimestamp] = []
    current_word = ""
    word_start = 0.0
    word_end = 0.0

    for char, start, end in zip(chars, char_starts, char_ends):
        if char == " " or char == "\n":
            if current_word.strip():
                timestamps.append(WordTimestamp(current_word.strip(), word_start, word_end))
            current_word = ""
        else:
            if not current_word:
                word_start = start
            current_word += char
            word_end = end

    if current_word.strip():
        timestamps.append(WordTimestamp(current_word.strip(), word_start, word_end))

    return timestamps


# ─────────────────────────────────────────────────────────────────────────────
# Kai TTS fallback
# ─────────────────────────────────────────────────────────────────────────────

def _kai_tts_fallback(text: str, title_slug: str, channel_id: str) -> dict[str, Any]:
    # Kai TTS via kie_media text_to_video path is not yet wired for audio-only.
    # This stub logs the gap and raises so the caller knows to investigate.
    # When kie.ai exposes a dedicated TTS endpoint, wire it here.
    raise NotImplementedError(
        "Kai TTS fallback not yet wired. "
        "Add kie.ai TTS task_type to kie_media.MODEL_REGISTRY when available. "
        "Interim: set a valid ELEVENLABS_API_KEY and voice_id in brand_config."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Drive upload
# ─────────────────────────────────────────────────────────────────────────────

def _upload_audio_to_drive(local_path: Path, channel_id: str) -> dict:
    try:
        from kie_media import _upload_to_drive, IMAGES_FOLDER
        folder_id = os.environ.get("DRIVE_STUDIO_AUDIO_FOLDER", IMAGES_FOLDER)
        return _upload_to_drive(local_path, folder_id, local_path.name, "audio/mpeg")
    except Exception as exc:
        logger.warning("Drive upload failed for audio (%s), continuing without Drive URL", exc)
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_VOICE_REGISTRY_PATH = Path(__file__).parent.parent / "configs" / "voice_registry.json"
_HUNTER_FALLBACK = "X4Lh5Ftnso6JSt25plzX"


def _resolve_voice_id(voice_role: str | None, brand: dict[str, Any]) -> str:
    """
    Resolve ElevenLabs voice_id from role → brand config → registry → Hunter fallback.

    voice_role values (set by script_generator based on content):
      "male"    → brand voice_id_male  (African stories male)
      "female"  → brand voice_id_female (African stories female)
      "elder"   → registry elder_male  (Elhadja — wisdom/gravitas)
      "boubacar"→ registry boubacar
      "hunter"  → registry hunter_vo
      None      → brand voice_id default
    """
    # Step 1: role-based lookup in brand config
    if voice_role:
        role_map = {
            "male":     brand.get("voice_id_male"),
            "female":   brand.get("voice_id_female"),
            "default":  brand.get("voice_id"),
        }
        if voice_role in role_map and role_map[voice_role]:
            return role_map[voice_role]

        # Step 2: role-based lookup in voice_registry.json
        registry_map = {
            "elder":    "elder_male",
            "boubacar": "boubacar",
            "hunter":   "hunter_vo",
            "male":     "african_stories_male",
            "female":   "african_stories_female",
        }
        registry_key = registry_map.get(voice_role)
        if registry_key:
            reg_id = _registry_voice(registry_key)
            if reg_id:
                return reg_id

    # Step 3: brand default
    brand_default = brand.get("voice_id", "")
    if brand_default and "__M2_PENDING__" not in brand_default:
        return brand_default

    # Step 4: registry studio_generic default
    reg_default = _registry_voice_default("studio_generic")
    if reg_default:
        return reg_default

    # Step 5: Hunter hardcoded fallback
    return _HUNTER_FALLBACK


def _registry_voice(key: str) -> str | None:
    try:
        import json
        data = json.loads(_VOICE_REGISTRY_PATH.read_text(encoding="utf-8"))
        return data.get("voices", {}).get(key, {}).get("id")
    except Exception:
        return None


def _registry_voice_default(key: str) -> str | None:
    try:
        import json
        data = json.loads(_VOICE_REGISTRY_PATH.read_text(encoding="utf-8"))
        return data.get("defaults", {}).get(key)
    except Exception:
        return None


def _save_audio(audio_bytes: bytes, title_slug: str, channel_id: str) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{channel_id}_{title_slug}_{ts}.mp3"
    local_path = LOCAL_CACHE_DIR / channel_id / filename
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(audio_bytes)
    logger.info("audio saved: %s (%d bytes)", local_path, len(audio_bytes))
    return local_path


def _strip_scene_markers(text: str) -> str:
    return re.sub(r'\[SCENE:[^\]]*\]\s*', '', text).strip()


def _strip_ssml(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text)


def _slugify(text: str, max_len: int = 40) -> str:
    slug = "".join(c.lower() if c.isalnum() else "-" for c in text.strip())
    slug = "-".join(s for s in slug.split("-") if s)
    return slug[:max_len] or "untitled"


def _stub_result(title_slug: str, channel_id: str) -> dict[str, Any]:
    stub_path = LOCAL_CACHE_DIR / channel_id / f"{title_slug}_stub.mp3"
    stub_path.parent.mkdir(parents=True, exist_ok=True)
    stub_path.write_bytes(b"")  # empty file, smoke test only
    return {
        "audio_path": str(stub_path),
        "drive_url": "https://drive.google.com/stub",
        "drive_file_id": "stub_file_id",
        "duration_sec": 60.0,
        "timestamps": [
            {"word": "stub", "start": 0.0, "end": 1.0},
            {"word": "audio", "start": 1.0, "end": 2.0},
        ],
        "provider": "stub",
    }
