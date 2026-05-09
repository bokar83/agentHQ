# Session Handoff - Studio Activation Day 1 - 2026-05-06

## TL;DR

Full Studio pipeline activation from scratch. Started with 13 scraped foreign content records blocking production, zero posts, and a cascade of bugs. By end of session: all 3 channels (Under the Baobab, 1stGen Money, AI Catalyst) posted to X + Instagram + TikTok + YouTube. 12 pipeline bugs fixed. Warm-up Day 1 started.

## What was built / changed

- `orchestrator/studio_production_crew.py` — OR filter for Status=qa-passed + Ready (production_tick was returning 0)
- `orchestrator/studio_blotato_publisher.py` — multi_select Platform support, per-platform publish loop, case-insensitive platform lookup, X 280-char truncation, idempotency guard fix
- `orchestrator/blotato_publisher.py` — TikTok required target fields (privacyLevel etc), YouTube required target fields (title/privacyStatus/shouldNotifySubscribers), X truncation, case-insensitive normalize
- `orchestrator/studio_render_publisher.py` — channel_id passed to _ffmpeg_render (intro/outro fix), apad whole_dur (no timeout), auto-set Platform=[x,Instagram,tiktok,YouTube] on render complete
- `docker-compose.yml` — 9 per-channel Blotato account ID env vars, PYTHONDONTWRITEBYTECODE=1, workspace/renders volume mount
- `configs/brand_config.ai_catalyst.json` — voice_id_male + voice_id_female = KuCymRJ2M5Gs5LQIAbwJ (Boubacar clone)
- VPS `.env` — BLOTATO_1STGEN_INSTAGRAM_ACCOUNT_ID=45755, BLOTATO_CATALYST_X_ACCOUNT_ID=17065
- Notion Pipeline DB — 13 scraped foreign records archived, 1 AIC record created, Platform field set

## Decisions made

- **1stGen abbreviation only** — never FGM (female genital mutilation)
- **AIC X = @boubacarbarry** — account 17065 = Boubacar's personal X, intentional, keep it
- **Static intro/outro from /app/workspace/assets/** — NOT programmatic title cards. Files: `{channel_id}_intro.mp4` / `{channel_id}_outro.mp4`
- **Renders volume-mounted** — workspace/renders/ persists across restarts now
- **Auto-Platform on render** — render_publisher sets all 4 platforms automatically; no manual field needed
- **Warm-up Day 1 = 2026-05-06** — Day 30 target = 2026-06-05

## What is NOT done (explicit)

- UTB + 1stGen Day 1 videos have no intro/outro (rendered before fix) — already posted, not replacing
- AIC Day 1 video used African voice (rendered before AIC voice fix) — already posted, not replacing
- 1stGen Instagram account (@1stgenmoneyz, ID 45755) pending Blotato confirmation email — Boubacar will confirm when Blotato sends it
- **Critical infrastructure bug not fully fixed:** Dockerfile `COPY orchestrator/*.py .` bakes files into `/app/` root, which Python imports before `/app/orchestrator/` (volume-mounted). Every container restart wipes docker cp fixes. Permanent fix = rebuild container or modify Dockerfile. See `feedback_baked_image_import_precedence.md`.

## Open questions

1. Should UTB + 1stGen Day 1 videos be replaced with re-renders that have intro/outro? (Boubacar said keep them — but worth revisiting after quality review)
2. Does 1stGen YT account ID (35698) map to correct channel? YouTube posts were triggered via direct Blotato call — verify at youtube.com
3. When should AIC get its own X account separate from @boubacarbarry?

## Next session must start here

1. Check `docker exec orc-crewai env | grep BLOTATO` — verify all 9 channel IDs still loaded (restart wipes docker cp, not env vars from .env)
2. Verify today's posts look correct on each platform — check profile URLs not reel URLs (reel URLs can lag)
3. Run `docker cp orchestrator/blotato_publisher.py orc-crewai:/app/blotato_publisher.py && docker cp orchestrator/studio_render_publisher.py orc-crewai:/app/studio_render_publisher.py` to ensure fixed files are in `/app/` root (container restart wipes docker cp)
4. Monitor first autonomous production tick — heartbeat fires every 30 min at `studio-production`; verify it picks up remaining Ready records and renders with intro/outro
5. Confirm 1stGen IG if Boubacar has confirmed in Blotato dashboard

## Files changed this session

```
orchestrator/studio_production_crew.py
orchestrator/studio_blotato_publisher.py
orchestrator/blotato_publisher.py
orchestrator/studio_render_publisher.py
docker-compose.yml
configs/brand_config.ai_catalyst.json
docs/roadmap/atlas.md (auto-updated by heartbeat)
docs/handoff/2026-05-06-studio-activation-day1.md (this file)
```

VPS only (not in git):
```
.env  (BLOTATO_1STGEN_INSTAGRAM_ACCOUNT_ID=45755, BLOTATO_CATALYST_X_ACCOUNT_ID=17065)
/app/blotato_publisher.py (docker cp — wiped on restart)
/app/studio_render_publisher.py (docker cp — wiped on restart)
```
