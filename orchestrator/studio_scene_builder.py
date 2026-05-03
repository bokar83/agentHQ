"""
studio_scene_builder.py — Studio M3: Break script into timed scenes.

Takes script.full_text + voice timestamps → list of Scene objects,
each with narration text, image prompt, video prompt, and timing.

Visual prompts are enforced against brand.visual_style and
brand.regional_motif_tags to prevent cultural mismatch (Sankofa risk).

At ~200 words per scene for a 1500-word script = ~7-8 scenes.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("agentsHQ.studio_scene_builder")

_WORDS_PER_SCENE = 200
_SCENE_MARKER_RE = re.compile(r'\[SCENE:\s*([^\]]+)\]')


@dataclass
class Scene:
    index: int
    narration: str
    image_prompt: str
    video_prompt: str
    start_sec: float
    end_sec: float
    duration_sec: float = field(init=False)

    def __post_init__(self) -> None:
        self.duration_sec = max(0.0, self.end_sec - self.start_sec)

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "narration": self.narration,
            "image_prompt": self.image_prompt,
            "video_prompt": self.video_prompt,
            "start_sec": self.start_sec,
            "end_sec": self.end_sec,
            "duration_sec": self.duration_sec,
        }


def build_scenes(
    script: dict[str, Any],
    voice: dict[str, Any],
    brand: dict[str, Any],
    *,
    dry_run: bool = False,
) -> list[Scene]:
    """
    Segment script into scenes aligned to voice timestamps.

    Returns list of Scene objects ordered by start time.
    """
    full_text = script["full_text"]
    timestamps = voice.get("timestamps", [])
    total_duration = voice.get("duration_sec", 60.0)
    visual_style = brand.get("visual_style", "cinematic")
    motif_tags = brand.get("regional_motif_tags", [])
    channel_id = brand.get("channel_id", "unknown")

    # Extract LLM-provided scene hints from [SCENE: ...] markers
    scene_hints = _extract_scene_hints(full_text)

    # Split text into ~200-word blocks, aligned to sentence boundaries
    clean_text = _SCENE_MARKER_RE.sub("", full_text).strip()
    blocks = _split_into_blocks(clean_text, _WORDS_PER_SCENE)

    # Map word timestamps to blocks
    timed_blocks = _align_blocks_to_timestamps(blocks, timestamps, total_duration)

    scenes: list[Scene] = []
    for i, (block_text, start_sec, end_sec) in enumerate(timed_blocks):
        hint = scene_hints[i] if i < len(scene_hints) else _infer_hint(block_text)
        image_prompt = _build_image_prompt(hint, visual_style, motif_tags, channel_id)
        video_prompt = _build_video_prompt(hint, visual_style)

        scenes.append(Scene(
            index=i,
            narration=block_text,
            image_prompt=image_prompt,
            video_prompt=video_prompt,
            start_sec=start_sec,
            end_sec=end_sec,
        ))

    logger.info("scene_builder: %d scenes for '%s'", len(scenes), script.get("title", "?"))
    return scenes


# ─────────────────────────────────────────────────────────────────────────────
# Prompt builders
# ─────────────────────────────────────────────────────────────────────────────

def _build_image_prompt(
    hint: str,
    visual_style: str,
    motif_tags: list[str],
    channel_id: str,
) -> str:
    motif_clause = ""
    if motif_tags:
        motif_clause = f", {', '.join(motif_tags[:3])} cultural motifs"

    return (
        f"{hint}, {visual_style}{motif_clause}, "
        f"cinematic lighting, 4K, no text, no watermark, "
        f"photorealistic, warm color grade"
    )


def _build_video_prompt(hint: str, visual_style: str) -> str:
    return (
        f"Slow cinematic zoom on: {hint}. "
        f"Style: {visual_style}. "
        f"Gentle camera movement, smooth motion, no jump cuts, no text overlays."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Text segmentation
# ─────────────────────────────────────────────────────────────────────────────

def _split_into_blocks(text: str, words_per_block: int) -> list[str]:
    """Split text into ~words_per_block chunks at sentence boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    blocks: list[str] = []
    current: list[str] = []
    count = 0

    for sentence in sentences:
        words = sentence.split()
        if count + len(words) > words_per_block and current:
            blocks.append(" ".join(current))
            current = []
            count = 0
        current.append(sentence)
        count += len(words)

    if current:
        blocks.append(" ".join(current))

    return blocks or [text]


def _align_blocks_to_timestamps(
    blocks: list[str],
    timestamps: list[dict],
    total_duration: float,
) -> list[tuple[str, float, float]]:
    """Map each text block to (text, start_sec, end_sec) using word timestamps."""
    if not timestamps:
        # No timestamps (stub/dry_run): divide duration equally
        n = len(blocks)
        segment = total_duration / n if n else total_duration
        return [
            (block, i * segment, (i + 1) * segment)
            for i, block in enumerate(blocks)
        ]

    # Build flat word list from blocks to match against timestamp sequence
    word_boundaries: list[int] = []  # cumulative word count per block boundary
    cumulative = 0
    for block in blocks:
        cumulative += len(block.split())
        word_boundaries.append(cumulative)

    result: list[tuple[str, float, float]] = []
    prev_end = 0.0
    ts_idx = 0

    for b_idx, (block, boundary) in enumerate(zip(blocks, word_boundaries)):
        start = timestamps[ts_idx]["start"] if ts_idx < len(timestamps) else prev_end
        target_ts_idx = min(boundary - 1, len(timestamps) - 1)
        end = timestamps[target_ts_idx]["end"] if target_ts_idx < len(timestamps) else total_duration
        result.append((block, start, end))
        prev_end = end
        ts_idx = min(boundary, len(timestamps) - 1)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Hint extraction / inference
# ─────────────────────────────────────────────────────────────────────────────

def _extract_scene_hints(text: str) -> list[str]:
    return _SCENE_MARKER_RE.findall(text)


def _infer_hint(text: str) -> str:
    """Fallback: use first sentence of block as visual hint."""
    first_sentence = re.split(r'[.!?]', text)[0].strip()
    return first_sentence[:120] if first_sentence else "cinematic establishing shot"
