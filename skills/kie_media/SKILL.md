---
name: kie_media
description: >
  Generates images and videos via the Kai (kie.ai) API. Routes each request to
  the top-ranked model for the task (text-to-image, image-to-image, text-to-video,
  image-to-video), retries once on the top model, escalates to ranks 2 and 3 on
  failure, downloads the output to local cache, uploads to Google Drive under
  05_Asset_Library/, and logs metadata to Supabase media_generations with a link
  back to the Content Board. Trigger on any "create image", "create video",
  "generate image", "generate video", or "make me an image/video" request.
---

# Kai Media Skill

Unified image and video generation using the Kai (kie.ai) model marketplace.

**Kai is to media what OpenRouter is to LLMs:** one API key, dozens of models,
ranked by current quality for each task. The skill picks the best model, runs
retries and fallbacks, and returns a Drive URL.

---

## When to Use

Trigger phrases:
- "create image", "create an image", "generate image", "make an image"
- "create video", "create a video", "generate video", "make a video"
- "picture of", "video of", "image of" (imperative)
- "animate this", "render this as video"

Do NOT trigger for:
- Prompt-only requests ("give me a prompt for Midjourney"). Route those to the
  `image-generator` skill.
- Video editing or compositing. Route those to the `hyperframes` skill.
- Upscaling existing assets (future: add Topaz route).

---

## What the Skill Does

1. Classify the task into one of four types:
   - `text_to_image`
   - `image_to_image`
   - `text_to_video`
   - `image_to_video`
2. Pull the top-ranked model for that task from `MODEL_REGISTRY` in
   `orchestrator/kie_media.py`.
3. POST to the correct endpoint (unified `/jobs/createTask` or dedicated
   `/veo/generate` / `/runway/generate` / `/gpt4o-image/generate`).
4. Poll `/jobs/recordInfo` every 5 seconds (max 10 min per task).
5. On success: download output, upload to Drive, log to Supabase, return URL.
6. On failure: retry rank-1 once, then escalate to rank-2, then rank-3.
7. On all failures: raise with full attempt trace so the user sees what failed.

---

## Retry and Fallback

```
rank-1 model
  try 1 -> fail
  try 2 -> fail
rank-2 model
  try 1 -> fail
rank-3 model
  try 1 -> fail
=> total failure, report in chat with attempt trace
```

Every attempt logs to Supabase `media_generations` with `state='fail'` so the
biweekly audit sees silent failures, not just successful generations.

---

## Budget Ceilings

Auto-approve without asking:
- Image: `<= $0.20` per call
- Video: `<= $2.00` per call

The registry is ordered with these ceilings in mind. If you add a model above
ceiling, mark it `requires_confirmation: true` in `MODEL_REGISTRY` and wire a
confirmation step before `_run_with_retries`.

---

## Storage

- **Google Drive (primary):**
  `NotebookLM_Library/05_Asset_Library/01_Images/<YEAR>-Q<N>/`
  `NotebookLM_Library/05_Asset_Library/02_Videos/<YEAR>-Q<N>/`
  Quarterly subfolders auto-create on first save of the quarter.
- **Local cache:** `workspace/media/images/<quarter>/` and
  `workspace/media/videos/<quarter>/` (working copy; gitignored).
- **Supabase `media_generations` (metadata only):** prompt, model, drive_url,
  cost, attempts, quarter, linked_content_id (FK to Content Board).
- **Notion Content Board:** every generation inserts a row into the linked
  `Media_Index` DB if `linked_content_id` is passed.

**File naming:**
`MEDIA_<image|video>_YYYYMMDD_HHMM_<model-slug>_<prompt-slug>.<ext>`

Example: `MEDIA_video_20260421_1830_veo3-fast_constraint-diagnostic.mp4`

---

## Function Signatures

From `orchestrator/kie_media.py`:

```python
generate_image(prompt: str, aspect_ratio: str = "16:9",
               task_type: str = "text_to_image",
               linked_content_id: str | None = None) -> dict

generate_video(prompt: str, aspect_ratio: str = "16:9",
               task_type: str = "text_to_video",
               linked_content_id: str | None = None) -> dict

list_models(task_type: str | None = None) -> dict

check_credits() -> int
```

Each `generate_*` returns:
```python
{
  "drive_url": "https://drive.google.com/file/d/.../view",
  "drive_file_id": "1abc...",
  "local_path": "workspace/media/videos/2026-Q2/MEDIA_video_...mp4",
  "model_used": "veo3_fast",
  "rank_used": 1,
  "attempts": [...],
  "filename": "MEDIA_video_20260421_1830_veo3-fast_...mp4"
}
```

---

## Model Registry Update Cadence

Every other Sunday the `media_quality_audit` routine regenerates a fixed
5-prompt battery across the top 3 image and top 3 video models, saves outputs
to `05_Asset_Library/99_Generation_Scratch/audits/YYYY-MM-DD/`, and posts a
side-by-side comparison to the `Kai Model Leaderboard` Notion DB for manual
scoring. Update `MODEL_REGISTRY` ranks based on scores.

Registry file: `docs/kai_model_registry.md` (human-readable source of truth).
Runtime registry: `orchestrator/kie_media.py` `MODEL_REGISTRY` dict. Keep them
in sync. The doc is what you edit, the dict is what the skill reads. A future
PR can auto-generate the dict from the doc.

---

## Env Vars

- `KIE_AI_API_KEY`: required. Set locally and on VPS.
- `MEDIA_LOCAL_CACHE`: optional, defaults to `workspace/media`.

---

## Tools Exposed to Agents

Wired in `orchestrator/tools.py` and bundled as `MEDIA_TOOLS`:

- `kie_generate_image`
- `kie_generate_video`
- `kie_list_models`
- `kie_check_credits`

Any agent needing media generation should include `MEDIA_TOOLS` in its tool
list. The `media_crew` in `orchestrator/crews.py` is the default entry point.
