# HyperFrame Boost — Design Spec

## Goal

Automatically convert top-scoring personal LinkedIn/X Notion drafts into HyperFrame videos (9:16 + 1:1), queue them to post 24hr after the text post, and route to LinkedIn, X, and YouTube Shorts. Telegram gate lets Boubacar multi-select which posts get boosted each cycle.

## Scope

**Phase 1 (this spec):** Personal brand only — LinkedIn, X, YouTube Shorts.
**Phase 2 (future):** AIC channel with brand-voice rewrite layer. Not in scope here.

---

## Architecture

### Flow

```
[Cron: every 2 days, 16:00 UTC / 9am MT]
       ↓
hyperframe_boost_cron.py
  → calls HyperframeBoostAgent.run()
       ↓
Query Griot content board (Notion)
  filter: personal posts (LinkedIn + X), Status=Draft or Queued
          hyperframe_twin_id IS EMPTY (no existing twin)
  rank: total_score desc
  take: top 3
       ↓
Send Telegram message:
  "HyperFrame candidates ready:
   1. [score: 87] The biggest mistake I made...
   2. [score: 82] Most automation fails not...
   3. [score: 79] If I had to start over...
   Reply: 1, 2, 3, 1,3, all, or skip"
       ↓
Poll Telegram for reply (timeout: 24hr → auto-skip)
       ↓
For each approved post ID:
  1. LLM: post text → HyperFrames scene brief (JSON)
  2. hyperframes render → 9:16 MP4 + 1:1 MP4 (two subprocess calls)
  3. Drive upload both files
  4. Notion: create TWO companion records in Studio Pipeline DB
       record A: aspect_ratio=9:16, platform=[x, youtube_shorts]
       record B: aspect_ratio=1:1, platform=[linkedin]
       both: Status=Scheduled, scheduled_date=source_post_date+24hr,
             linked_text_post_id=source_notion_page_id,
             channel=personal, format=hyperframe-boost
  5. Write hyperframe_twin_id back to source Griot record (dedup guard)
       ↓
Telegram confirmation: "Boosted: [post preview]. Videos queued for [date]."
       ↓
auto_publisher.py picks up on next tick (existing machinery)
  routes 9:16 → X + YouTube Shorts
  routes 1:1 → LinkedIn
```

### Phase 0 — Manual Stack Validation (before cron goes live)

Run once manually before activating cron:

1. Pick 1 Notion draft with known total_score
2. Hand-craft a HyperFrames brief JSON
3. Run: `npx hyperframes render --brief brief.json --aspect 9x16 --output /tmp/test_9x16.mp4`
4. Run: `npx hyperframes render --brief brief.json --aspect 1x1 --output /tmp/test_1x1.mp4`
5. Upload both to Drive via `_upload_to_drive`
6. Create Blotato post manually, route to X + LinkedIn
7. Confirm both appear scheduled in Blotato dashboard

All 7 steps green = cron safe to activate.

---

## Components

### New Files

**`orchestrator/hyperframe_boost_agent.py`**
- `HyperframeBoostAgent` class
- `run()` — main orchestration: query → telegram → parse reply → render loop
- `_query_candidates()` — Notion query, returns top 3 dicts with id, total_score, text preview
- `_send_telegram_menu(candidates)` — formats and sends candidate message
- `_poll_telegram_reply(timeout_hours=24)` → list of approved indices or None (skip)
- `_render_and_queue(candidate)` — brief gen + render + upload + Notion record creation
- Each step fails independently; failure sends one Telegram line, skips that post only

**`orchestrator/hyperframe_brief_generator.py`**
- `HyperframeBriefGenerator` class
- `generate(post_text: str) -> dict` — LLM call: post text → HyperFrames brief JSON
- Brief structure matches `HyperframesBrief` pydantic model in `skills/hyperframes/skill.py`:
  `purpose, duration, aspect_ratio, mood_style, brand_palette, typography, scenes, audio, caption_tone, transitions, asset_paths`
- Uses claude-sonnet-4-6, prompt cached
- Scene breakdown: hook scene (0-3s), 2-3 content scenes, CTA scene

**`orchestrator/hyperframe_boost_cron.py`**
- Entry point: `if __name__ == "__main__": HyperframeBoostAgent().run()`
- Logs result to `/var/log/hf_boost.log`

### Modified Files

**`orchestrator/auto_publisher.py`**
- `_account_id_for_platform()` — already handles x, linkedin
- Add: if record has `format=hyperframe-boost` and `aspect_ratio=9:16`, also route to `youtube_shorts` account ID
- Minimal change: one elif branch in existing routing function

### Notion Changes (manual, one-time)

**Griot content board:**
- Add field: `hyperframe_twin_id` (relation → Studio Pipeline DB) — dedup guard

**Studio Pipeline DB:**
- Add fields: `linked_text_post_id` (text), `channel` (select), `format` (select), `aspect_ratio` (select)

---

## Data Flow

### Candidate dict structure (internal)
```python
{
    "notion_id": str,          # Griot page ID
    "total_score": float,
    "text_preview": str,       # first 150 chars of Draft field
    "full_text": str,          # full Draft field
    "scheduled_date": str,     # ISO date string
    "platform": list[str],     # ["linkedin", "x"]
}
```

### Companion Notion record (Studio Pipeline DB)
```python
{
    "Name": f"HF Boost — {text_preview[:60]}",
    "Status": "Scheduled",
    "Scheduled Date": scheduled_date + 1 day,
    "Platform": ["x", "youtube_shorts"],   # or ["linkedin"]
    "Asset URL": drive_url,
    "linked_text_post_id": griot_notion_id,
    "channel": "personal",
    "format": "hyperframe-boost",
    "aspect_ratio": "9:16",                # or "1:1"
}
```

---

## Error Handling

| Step | Failure | Action |
|---|---|---|
| Notion query | 0 candidates | Telegram: "No new HF candidates. Skip." Stop. |
| Notion query | API error | Telegram alert. Stop. |
| Telegram timeout | No reply in 24hr | Auto-skip all. Log. |
| LLM brief gen | API error | Telegram: "Brief gen failed for post 1. Skipping." Continue others. |
| FFmpeg render | Non-zero exit | Telegram: "Render failed: [stderr first 200 chars]." Mark retry_next_cycle=true on Griot record. |
| Drive upload | Fail after 3 retries | Telegram alert. Skip that post. |
| Notion record create | Fail | Telegram alert. Do NOT write hyperframe_twin_id (ensures retry next cycle). |
| Blotato queue | Fail | Existing auto_publisher retry handles it. |

No silent failures. One Telegram line per failure max. One post failure never blocks others.

---

## Cadence

- Cron: every 2 days at 16:00 UTC (9am MT)
- VPS crontab entry: `0 16 */2 * * cd /root/agentsHQ && python orchestrator/hyperframe_boost_cron.py >> /var/log/hf_boost.log 2>&1`
- Max 1 video per platform per day (guard: check Notion for existing scheduled HF records on same date)
- Text post posts same day as normal (Griot/auto_publisher unchanged)
- Video companion posts text_post_scheduled_date + 1 day = natural A/B gap

---

## A/B Tracking

- `linked_text_post_id` on companion record pairs text + video
- Phase 2: query both records, compare `engagement_score` / `impressions` fields populated post-publish
- No Phase 2 work in this spec

---

## Out of Scope (Phase 2)

- AIC channel with brand-voice rewrite
- Real engagement scraping from LinkedIn/X API
- Auto-threshold scoring (replacing Telegram gate)
- Studio channel HyperFrame boosts
