# Kai (kie.ai) Model Registry

**Last audit**: 2026-04-21
**API base**: `https://api.kie.ai`
**Auth**: `Authorization: Bearer <KIE_AI_API_KEY>`
**Rate limit**: 20 new generations per 10 seconds per account
**Output URL expiry**: 24 hours after success (download immediately)

## API Patterns

Two patterns exist. The skill handles both.

### Pattern A: Unified jobs endpoint (most models)

```
POST https://api.kie.ai/api/v1/jobs/createTask
body: { "model": "<slug>", "input": { ... }, "callBackUrl": "<optional>" }
returns: { code:200, data: { taskId } }
```

Poll with:
```
GET https://api.kie.ai/api/v1/jobs/recordInfo?taskId=<id>
response state: waiting | queuing | generating | success | fail
result URLs in: data.resultJson -> JSON-encoded -> {"resultUrls": ["https://..."]}
```

### Pattern B: Dedicated endpoints (top-tier models)

- Veo 3.1: `POST /api/v1/veo/generate` (same polling shape)
- Runway: `POST /api/v1/runway/generate`
- 4o Image: `POST /api/v1/gpt4o-image/generate`

All return a `taskId` and share the same polling flow on `/api/v1/jobs/recordInfo`.

## Priority Image Models (ranked)

Quality first, cost second. Budgets: auto-approve ≤ $0.20 per image.

| Rank | Model Slug | Endpoint | Modality | Notes |
|---|---|---|---|---|
| 1 | `seedream/4.5-text-to-image` | jobs | text-to-image | Photorealistic 4K; current SOTA for product shots |
| 2 | `google/nano-banana-pro-image-to-image` | jobs | image-to-image | Best edit/transform model |
| 3 | `google/imagen4` | jobs | text-to-image | Multi-variant (fast/ultra); strong for hero shots |
| 4 | `flux2/pro-text-to-image` | jobs | text-to-image | Photorealistic |
| 5 | `4o-image` | `/gpt4o-image/generate` | text-to-image | GPT-native; good for text-in-image; cheap |
| 6 | `seedream/5-lite-text-to-image` | jobs | text+image-to-image | Budget tier |
| 7 | `ideogram/v3-text-to-image` | jobs | text-to-image | Best for typography/text inside images |
| 8 | `topaz/image-upscale` | jobs | upscale | Post-processing only |

## Priority Video Models (ranked)

Budgets: auto-approve ≤ $2.00 per video.

| Rank | Model Slug | Endpoint | Modality | Notes |
|---|---|---|---|---|
| 1 | `veo3` | `/veo/generate` | text-to-video, image-to-video | 1080p/4K; 25% of Google's price; current SOTA |
| 2 | `kling/v2-5-turbo-text-to-video-pro` | jobs | text-to-video | Pro tier; strong narrative motion |
| 3 | `runway` | `/runway/generate` | text-to-video | 5s or 10s at 720p/1080p (10s caps at 720p) |
| 4 | `bytedance/seedance-2` | jobs | text-to-video | Strong quality/cost ratio |
| 5 | `kling/v2-1-master-text-to-video` | jobs | text-to-video | Reliable fallback |
| 6 | `hailuo/2-3-image-to-video-pro` | jobs | image-to-video | Best for animating a still |
| 7 | `veo3_fast` | `/veo/generate` (model param) | text-to-video | Faster + cheaper Veo variant |
| 8 | `sora2/sora-2-text-to-video` | jobs | text-to-video | Per-character / non-commercial notes; use with caution |

## Retry & Fallback Behavior

On failure (API error, empty response, content-policy block):

1. Retry rank-1 model once (same prompt).
2. If fail, escalate to rank-2.
3. If fail, escalate to rank-3.
4. If rank-3 fails, report total failure in chat with full trace.

Every attempt writes a row to Supabase `media_generations` with `state = 'fail'` so the biweekly audit sees silent failures.

## Biweekly Quality Audit

Every other Sunday evening:
1. Run a fixed 5-prompt battery against top 3 image + top 3 video models.
2. Save outputs to Drive `05_Asset_Library/99_Generation_Scratch/audits/YYYY-MM-DD/`.
3. Post side-by-side comparison to Notion DB `Kai Model Leaderboard` for manual scoring.
4. Update this file's rankings based on scores.

## Account Status (last check)

- Credits remaining: 9734 (2026-04-21)
- Check via: `GET /api/v1/chat/credit` returns `{"data": <credits>}`
