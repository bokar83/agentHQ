---
name: scene-segmenter
description: Breaks a script into N scene beats at 200 words/minute and emits one paired image-prompt and video-prompt per beat. Front-half of the Studio M3.5 channel cloner pipeline. Trigger on "segment script", "scene split", "beat segmentation", "script to scenes", "image and video prompts from script".
---

# scene-segmenter

Studio M3.5 sub-skill. Built 2026-04-29 as the next missing primitive in the channel cloner pipeline.

## What it does

Input: a script (string or file) plus an optional style profile (from `transcript-style-dna`).
Output: a JSON file with one scene per beat, where each scene contains:

- `beat_number` (1-indexed)
- `script_excerpt` (the words the voiceover says during this scene)
- `duration_seconds` (computed from word count at 200 wpm)
- `image_prompt` (single still that anchors this scene)
- `video_prompt` (animation/motion prompt to turn the still into a video clip)

**Granularity:** roughly one beat per ~12 words, which gives ~167 beats for a 2000-word (10-minute) script. Matches the segmentation pattern from the YouTube video that motivated this build.

## Why it exists

The cloner pipeline needs script -> visual prompts at the right granularity for kie_media to generate. Without this primitive, the operator has to manually chop a 2000-word script into ~167 paired prompts. With it, one CLI call produces the full prompt list ready to feed into kie_media.

## How to invoke

```bash
python skills/scene-segmenter/segment.py \
  --script path/to/script.txt \
  --style-profile path/to/style-dna.json \
  --niche-context "documentary-style historical events" \
  --out workspace/scenes/<project>.json
```

Optional flags:

- `--wpm 200` (default): words-per-minute for duration calc
- `--target-beats 167` (default): approximate beat count; segmenter will balance to hit this
- `--no-style-profile`: skip style profile if not available

## Output schema

```json
{
  "total_beats": 167,
  "total_words": 2000,
  "estimated_duration_seconds": 600,
  "wpm": 200,
  "scenes": [
    {
      "beat_number": 1,
      "script_excerpt": "...",
      "duration_seconds": 4.2,
      "image_prompt": "...",
      "video_prompt": "..."
    }
  ],
  "_style_profile_id": "...",
  "_niche_context": "..."
}
```

## Hard rules

- No em-dashes or en-dashes in any output field. Enforced in prompt + post-process scrub (same pattern as transcript-style-dna).
- Image prompts are anchored to the script_excerpt content, not generic.
- Video prompts describe motion only, not new visual elements (the still anchors the scene).
- **Non-generic enforcement gate:** If an `image_prompt` or `video_prompt` repeats the prior scene's prompt without new evidence from `script_excerpt`, mark that scene `FAIL` and regenerate before returning output. A scene is FAIL if the prompt could apply to any scene in the script without reading its `script_excerpt`.

## Files

```
skills/scene-segmenter/
├── SKILL.md
├── segment.py
└── samples/
    └── sample_script.txt
```

## Status

- 2026-04-29: scaffolded; needs smoke test against a 500-word sample script before being declared working
- Studio M3.5 dependency. Full cloner pipeline awaits Studio M3 ship.

## Source

Strategy session 2026-04-29. Studio M3.5 milestone in `docs/roadmap/studio.md`.
