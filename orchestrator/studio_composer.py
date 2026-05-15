"""
studio_composer.py - Studio M3: Compose video from scenes + audio using ffmpeg.

Replaces hyperframes entirely. Pipeline:
  1. Each scene image gets a Ken Burns motion effect (zoom/pan, varied per scene)
  2. Scenes are concatenated with crossfade transitions
  3. Narration audio overlaid
  4. Word-level SRT subtitle file generated for multilingual captioning
  5. Output: project dict with paths for render_publisher

No Chrome, no headless browser, no video audio bleed.

Pattern 3 — explicit no-agent flag: this module is fully deterministic
(ffmpeg + subprocess + filesystem). It MUST NOT make LLM calls. The
NO_AGENT constant below is a tripwire — if a future refactor adds an
anthropic/openai import here, that's a regression. Verified
2026-05-14: zero Anthropic / openai / chat-completion calls.
"""
from __future__ import annotations

# Pattern 3: deterministic-stage marker. Do not wake an LLM from this module.
NO_AGENT = True

import json
import logging
import os
import pathlib
import re
import subprocess
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("agentsHQ.studio_composer")

WORKSPACE = pathlib.Path("/app/workspace")
COMPOSITIONS_DIR = WORKSPACE / "compositions"

# Ken Burns motion variants — cycled per scene for variety
_MOTION_EFFECTS = [
    "zoom_in",       # slow zoom toward center
    "pan_right",     # pan left to right
    "zoom_out",      # slow zoom out from center
    "pan_left",      # pan right to left
    "zoom_in_tl",    # zoom in from top-left
    "zoom_out_br",   # zoom out toward bottom-right
    "pan_up",        # pan bottom to top
    "zoom_in_tr",    # zoom in from top-right
]

# Transition between scenes
_TRANSITIONS = [
    "fade",
    "fadeblack",
    "slideleft",
    "slideright",
    "dissolve",
    "pixelize",
    "fadewhite",
    "smoothleft",
]

_TRANSITION_DURATION = 0.5  # seconds


def compose(
    scenes: list[Any],
    scene_assets: list[dict],
    voice: dict,
    script: dict,
    brand: dict,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Build ffmpeg composition project. Returns project dict for render_publisher."""
    title = script.get("title", "untitled")
    channel_id = brand.get("channel_id", "unknown")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = _slugify(title)
    project_dir = COMPOSITIONS_DIR / f"{channel_id}_{slug}_{ts}"
    project_dir.mkdir(parents=True, exist_ok=True)

    audio_path = voice.get("audio_path", "")
    audio_dur = voice.get("duration_sec", 60.0)
    timestamps = voice.get("timestamps", [])

    # Build scene plan: image path + timing + motion effect
    scene_plan = []
    for i, scene in enumerate(scenes):
        assets = scene_assets[i] if i < len(scene_assets) else {}
        img = assets.get("image_local_path", "") or assets.get("video_local_path", "")
        motion = _MOTION_EFFECTS[i % len(_MOTION_EFFECTS)]
        transition = _TRANSITIONS[i % len(_TRANSITIONS)]
        scene_plan.append({
            "index": i,
            "image_path": img,
            "start_sec": getattr(scene, "start_sec", 0.0),
            "end_sec": getattr(scene, "end_sec", 10.0),
            "duration_sec": getattr(scene, "duration_sec", 10.0),
            "motion": motion,
            "transition": transition,
            "narration": getattr(scene, "narration", ""),
        })

    # Generate SRT from word timestamps
    srt_path = project_dir / "captions_en.srt"
    _write_srt(timestamps, srt_path, intro_offset=3.0)

    # Write project manifest for render_publisher
    manifest = {
        "title": title,
        "channel_id": channel_id,
        "project_dir": str(project_dir),
        "audio_path": audio_path,
        "audio_dur_sec": audio_dur,
        "srt_path": str(srt_path),
        "scenes": scene_plan,
        "brand": {
            "primary_color": brand.get("primary_color", "#E8A020"),
            "background_color": brand.get("background_color", "#1E1433"),
            "font_family": brand.get("font_family", "Playfair Display"),
            "display_name": brand.get("display_name", channel_id),
        },
        "intro_duration_sec": brand.get("intro_duration_sec", 3),
        "outro_duration_sec": brand.get("outro_duration_sec", 4),
        "lint": True,
        "dry_run": dry_run,
    }

    manifest_path = project_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info("composer: project written to %s (%d scenes)", project_dir, len(scene_plan))

    return manifest


def _write_srt(timestamps: list[dict], path: pathlib.Path, intro_offset: float = 3.0) -> None:
    """Write word-level SRT. Groups words into ~8-word caption chunks."""
    if not timestamps:
        path.write_text("")
        return

    chunks = []
    chunk: list[dict] = []
    for word in timestamps:
        chunk.append(word)
        w_text = word.get("word") or word.get("w", "")
        if len(chunk) >= 8 or w_text.endswith((".", "!", "?")):
            chunks.append(chunk)
            chunk = []
    if chunk:
        chunks.append(chunk)

    lines = []
    for i, ch in enumerate(chunks, 1):
        start = (ch[0].get("start") or ch[0].get("s", 0.0)) + intro_offset
        end = (ch[-1].get("end") or ch[-1].get("e", 0.0)) + intro_offset
        text = " ".join(w.get("word") or w.get("w", "") for w in ch)
        lines.append(f"{i}")
        lines.append(f"{_srt_ts(start)} --> {_srt_ts(end)}")
        lines.append(text)
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("composer: SRT written (%d chunks) → %s", len(chunks), path)


def _srt_ts(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower().strip())
    return slug.strip('-')[:max_len]
