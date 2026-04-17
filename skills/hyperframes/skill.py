"""
hyperframes_skill.py
Hyperframes video production skill for agentsHQ.
Generates validated briefs for Hyperframes CLI HTML composition rendering.

IMPORTANT: This is NOT the website_build skill. Both write HTML. Outputs differ:
- website_build: live HTML served in a browser
- hyperframes: HTML video source file rendered headless to MP4 via FFmpeg

Phase gate: Phase 0 = knowledge only. Phase 1 = active builds.
To activate: update PHASE_GATE to "phase_1" after first revenue is confirmed.
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Literal
import logging

logger = logging.getLogger(__name__)


PHASE_GATE = "phase_1"  # Activated 2026-04-17 — leGriot video layer for content-driven lead gen

BRIEF_REQUIRED_FIELDS = [
    "purpose",
    "duration",
    "aspect_ratio",
    "mood_style",
    "brand_palette",
    "typography",
    "scenes",
    "audio",
    "caption_tone",
    "transitions",
    "asset_paths",
]

EASING_MAP = {
    "smooth": "power2.out",
    "snappy": "power4.out",
    "bouncy": "back.out",
    "springy": "elastic.out",
    "dramatic": "expo.out",
    "dreamy": "sine.inOut",
}


class HyperframesBrief(BaseModel):
    purpose: str = Field(..., description="What this video is for and where it will be published")
    duration: str = Field(..., description="e.g. 15s, 30s, 45s")
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = Field(..., description="Video aspect ratio")
    mood_style: str = Field(..., description="e.g. minimal Swiss grid, warm analog, high-energy social")
    brand_palette: str = Field(..., description="Hex values with usage caps")
    typography: str = Field(..., description="body font, heading font")
    scenes: str = Field(..., description="Key scenes and elements")
    audio: str = Field(..., description="none | music at path | TTS with voice preference")
    caption_tone: Literal["Hype", "Corporate", "Tutorial", "Storytelling", "Social"]
    transitions: str = Field(..., description="energy level or mood description")
    asset_paths: str = Field(..., description="Exact file paths for all media -- never invent")


class HyperframesCompositionTool(BaseTool):
    name: str = "hyperframes_composition"
    description: str = (
        "Generates and validates a HeyGen Hyperframes video composition brief. "
        "This skill produces video files (MP4/WebM), NOT live websites. "
        "Use website_build skill for live browser HTML. Use this skill only when "
        "the output is a rendered video file. Phase-gated: inactive during Phase 0."
    )

    def _run(self, brief: dict) -> str:
        if PHASE_GATE == "phase_0":
            return (
                "[HYPERFRAMES SKILL] Phase gate active: Phase 0. "
                "No video builds during Phase 0. Capability is documented and "
                "ready for Phase 1. Update PHASE_GATE to 'phase_1' in skill.py "
                "after first revenue is confirmed by Boubacar."
            )

        missing = [f for f in BRIEF_REQUIRED_FIELDS if f not in brief or not brief[f]]
        if missing:
            return (
                f"[HYPERFRAMES SKILL] Brief incomplete. Missing required fields: "
                f"{', '.join(missing)}. "
                f"Do not proceed. Request the missing fields from the user before continuing."
            )

        logger.info(f"Hyperframes brief validated. Purpose: {brief.get('purpose')}")

        render_cmd = self._build_render_command(brief)

        return (
            f"[HYPERFRAMES SKILL] Brief validated. Pass this to Claude Code with "
            f"/hyperframes skill loaded for composition authoring.\n\n"
            f"BRIEF SUMMARY:\n"
            f"- Purpose: {brief['purpose']}\n"
            f"- Duration: {brief['duration']}\n"
            f"- Aspect ratio: {brief['aspect_ratio']}\n"
            f"- Mood/style: {brief['mood_style']}\n"
            f"- Caption tone: {brief['caption_tone']}\n"
            f"- Transitions: {brief['transitions']}\n"
            f"- Audio: {brief['audio']}\n\n"
            f"RENDER COMMAND (after composition is authored):\n"
            f"{render_cmd}\n\n"
            f"REMINDER: Human approval via Telegram required before any video "
            f"is posted or sent. Never auto-publish."
        )

    def _build_render_command(self, brief: dict) -> str:
        quality = "draft"
        try:
            seconds = int(brief.get("duration", "30s").replace("s", "").strip())
            if seconds > 30:
                quality = "standard"
        except ValueError:
            pass
        return f"npx hyperframes render --output output.mp4 --quality {quality}"


def get_hyperframes_tool() -> HyperframesCompositionTool:
    """Return the Hyperframes tool instance for registration in tools.py."""
    return HyperframesCompositionTool()
