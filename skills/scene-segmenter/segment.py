"""
skills/scene-segmenter/segment.py

Break a script into N scene beats at 200 wpm.
Emit one paired image-prompt + video-prompt per beat.

Usage:
    python skills/scene-segmenter/segment.py \
        --script path/to/script.txt \
        --style-profile path/to/style-dna.json \
        --niche-context "documentary-style historical events" \
        --out workspace/scenes/project.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.llm_helpers import call_llm

SEGMENTER_MODEL = "anthropic/claude-sonnet-4.6"

SYSTEM_PROMPT = """You are a script-to-scene segmenter. You break a script into N visual beats and emit one paired image-prompt and video-prompt per beat.

Rules:
- Output JSON only. No prose, no markdown fences.
- Each beat covers a contiguous span of the script (script_excerpt). The beats together must cover the full script in order, with no gaps and no overlaps.
- Beat granularity: ~12 words per beat (so a 2000-word script becomes ~167 beats). Honor the target_beats parameter as a soft target.
- image_prompt anchors the scene visually. It must reference the specific content of script_excerpt, not be generic.
- video_prompt describes camera motion or subject animation ONLY. It must not introduce new visual elements that would conflict with the image. Examples: "slow push-in on subject", "subject turns head left", "camera pans across the city skyline", "candle flame flickers as figure walks past".
- If a style_profile is provided, image_prompts should match its tone and visual language.
- ABSOLUTE BAN: no em-dashes (U+2014) and no en-dashes (U+2013). Use periods, commas, semicolons, parentheses, or two hyphens (--) instead.
"""


def _strip_dashes(s):
    if not isinstance(s, str):
        return s
    return s.replace("\u2014", ", ").replace("\u2013", ", ")


def _scrub(obj):
    if isinstance(obj, str):
        return _strip_dashes(obj)
    if isinstance(obj, list):
        return [_scrub(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _scrub(v) for k, v in obj.items()}
    return obj


def segment(script: str, style_profile: dict | None, niche_context: str, target_beats: int = 167, wpm: int = 200) -> dict:
    if not script.strip():
        raise ValueError("script is empty")

    word_count = len(script.split())
    estimated_duration = round(60.0 * word_count / wpm, 1)

    style_block = json.dumps(style_profile, indent=2) if style_profile else "(none)"

    user_msg = f"""SCRIPT ({word_count} words, {estimated_duration}s at {wpm} wpm)
{script}

NICHE CONTEXT
{niche_context}

STYLE PROFILE (optional, use to shape image_prompts)
{style_block}

TARGET BEATS
{target_beats} (soft target, balance to natural beat boundaries)

Return a JSON object with this shape:
{{
  "total_beats": int,
  "total_words": int,
  "estimated_duration_seconds": float,
  "wpm": int,
  "scenes": [
    {{
      "beat_number": 1,
      "script_excerpt": "...",
      "duration_seconds": float,
      "image_prompt": "...",
      "video_prompt": "..."
    }}
  ]
}}"""

    response = call_llm(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        model=SEGMENTER_MODEL,
        temperature=0.4,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

    result = json.loads(raw)
    result = _scrub(result)
    result["_niche_context"] = _strip_dashes(niche_context)
    result["_style_profile_id"] = style_profile.get("_target_context", None) if style_profile else None
    return result


def main():
    ap = argparse.ArgumentParser(description="Segment a script into scene beats with paired image+video prompts.")
    ap.add_argument("--script", required=True, help="path to script .txt file")
    ap.add_argument("--style-profile", help="path to transcript-style-dna JSON output")
    ap.add_argument("--niche-context", required=True, help="one-line niche description")
    ap.add_argument("--target-beats", type=int, default=167)
    ap.add_argument("--wpm", type=int, default=200)
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--no-style-profile", action="store_true")
    args = ap.parse_args()

    script_path = Path(args.script)
    if not script_path.exists():
        print(f"ERROR: {args.script} not found", file=sys.stderr)
        sys.exit(1)
    script = script_path.read_text(encoding="utf-8")

    style_profile = None
    if args.style_profile and not args.no_style_profile:
        sp_path = Path(args.style_profile)
        if not sp_path.exists():
            print(f"ERROR: style profile {args.style_profile} not found", file=sys.stderr)
            sys.exit(1)
        style_profile = json.loads(sp_path.read_text(encoding="utf-8"))

    result = segment(script, style_profile, args.niche_context, args.target_beats, args.wpm)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"OK: wrote {out_path}")
    print(f"Beats: {result.get('total_beats')} | Words: {result.get('total_words')} | Duration: {result.get('estimated_duration_seconds')}s")
    if result.get("scenes"):
        print(f"First beat preview: {result['scenes'][0].get('image_prompt', '')[:100]}...")


if __name__ == "__main__":
    main()
