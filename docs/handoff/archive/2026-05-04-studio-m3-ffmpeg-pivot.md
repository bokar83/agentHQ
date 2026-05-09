# Session Handoff - Studio M3 ffmpeg Pivot - 2026-05-04

## TL;DR

Long session that launched Studio M3 production pipeline, hit walls with hyperframes (blank renders, Chrome file:// path failure, audio bleed from video clips), and pivoted to a clean ffmpeg-based pipeline. GPT Image 2 for scene stills, ffmpeg Ken Burns motion + concat + audio mix + SRT captions. All 7 modules committed on feat/studio-m3-production. First auto-trigger fires Monday 06:00 MT.

## What was built / changed

- `orchestrator/studio_composer.py` - full rewrite: ffmpeg manifest + SRT writer (no hyperframes)
- `orchestrator/studio_render_publisher.py` - full rewrite: ffmpeg Ken Burns + concat + audio mix + caption burn; email via gws +send from channel alias
- `orchestrator/studio_visual_generator.py` - GPT Image 2 only (gpt_image_2_text), vault lookup before Kai
- `orchestrator/studio_production_crew.py` - status=Ready fix, QA retry, lint_passed removed
- `orchestrator/studio_qa_crew.py` - skip source_citation for storytelling niches
- `orchestrator/studio_brand_config.py` - slugify channel name for config lookup
- `orchestrator/studio_script_generator.py` - retention loop auto-inject, loop_interval passthrough
- `orchestrator/studio_voice_generator.py` - strip SCENE/RETENTION markers before TTS
- `orchestrator/studio_trend_scout.py` - niche-aware classifier (inspiration mode), dual YT key rotation
- `orchestrator/studio_trend_seeds.default.json` - broad keyword sets (8-20 terms/niche)
- `orchestrator/Dockerfile` - Chrome headless deps (future use)
- `docker-compose.yml` - YOUTUBE_API_KEY_2 + ELEVENLABS_API_KEY
- `configs/asset_vault.json` - 34 videos indexed (gitignored, lives in container)
- `docs/handoff/` - 8 handoff files from earlier sessions committed
- `skills/boubacar-skill-creator/references/` - gates-taxonomy, context-budget-discipline added

## Decisions made

1. **Drop hyperframes** - Chrome headless can't access container filesystem paths (blank purple render). ffmpeg is the renderer permanently.
2. **GPT Image 2 for stills** - not seedream (mediocre quality), not video (audio bleed, expensive). ~$0.04/image vs ~$7/video clip.
3. **SRT as separate track** - multilingual ready. English first, French translation later.
4. **Ken Burns motion** - 8 variants cycled per scene (zoom_in, pan_right, zoom_out, pan_left, zoom_in_tl, zoom_out_br, pan_up, zoom_in_tr)
5. **Asset vault** - search before generating (score >= 2 tag match = reuse, zero Kai spend)
6. **Email via gws** - `gws gmail +send --from UnderTheBaobab@catalystworks.consulting` (channel alias). 3 recipients: boubacar@catalystworks.consulting, bokar83@gmail.com, thatguy@boubacarbarry.com
7. **Music vault** - future: workspace/media/music/, Suno on Kie or Boubacar's own Suno account

## What is NOT done (explicit)

- Shorts (1080x1920) and square (1080x1080) reframe not yet implemented - all 3 formats currently render same 1920x1080 (need ffmpeg crop filter per format)
- Music vault builder not built - no music in pipeline yet
- VPS needs rebuild to bake Dockerfile changes (Chrome deps, etc.)
- feat/studio-m3-production not merged to main
- Monday scout still has Monday-gate for heartbeat - manual bypass tested, auto fires correctly

## Open questions

- Will ffmpeg Ken Burns + GPT Image 2 produce acceptable visual quality? First real run is Monday 06:00 MT.
- Shorts/square crop strategy: center crop? or smart-crop based on image focal point?
- How to add French SRT: translate EN SRT via Claude after ElevenLabs returns timestamps?

## Next session must start here

1. Check Monday 06:00 MT auto-trigger ran: `docker logs orc-crewai --tail 200` or check Telegram
2. If video produced, review quality and decide if Ken Burns + GPT Image 2 is acceptable
3. Fix shorts/square reframe in `studio_render_publisher.py` `_ffmpeg_render()` - use ffmpeg `crop` + `scale` per format
4. Build music vault: `workspace/media/music/` dir + extend `build_vault.py` to scan it
5. Merge feat/studio-m3-production to main when first successful video confirmed

## Files changed this session

```
orchestrator/
  studio_composer.py          (full rewrite)
  studio_render_publisher.py  (full rewrite)
  studio_visual_generator.py  (GPT Image 2, vault)
  studio_production_crew.py   (status fix, lint_passed removed)
  studio_qa_crew.py           (storytelling niche exception)
  studio_brand_config.py      (slugify fix)
  studio_script_generator.py  (retention auto-inject)
  studio_voice_generator.py   (strip markers)
  studio_trend_scout.py       (niche classifier, key rotation)
  studio_trend_seeds.default.json (broad keywords)
  Dockerfile                  (Chrome headless deps)
configs/
  asset_vault.json            (34 videos, gitignored)
docker-compose.yml            (new env vars)
docs/handoff/                 (8 new files)
skills/boubacar-skill-creator/references/ (2 new files)
```
