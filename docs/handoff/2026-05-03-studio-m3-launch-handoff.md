# Studio M3 Launch Handoff  -  2026-05-03

## Context

Studio M3 production pipeline is **built and API-tested**. All 7 modules live in container. This chat's job:

1. **(You do)** Flip `studio.enabled=True`, trigger trend scout
2. **(You do)** Deliver candidate briefs to Boubacar's Telegram
3. **(Boubacar does)** Review Telegram briefs, approve 5 candidates
4. **(Regroup chat)** Run production on first approved candidate

**M4 is running in a parallel chat**  -  Blotato publisher built, heartbeat at 09:00 MT registered. Do not touch M4.

---

## Step 1  -  Flip studio crew on

```bash
ssh root@72.60.209.109
docker exec orc-crewai python3 -c "
import json
with open('/app/data/autonomy_state.json') as f: s=json.load(f)
s['crews']['studio']['enabled']=True
s['crews']['studio']['dry_run']=False
with open('/app/data/autonomy_state.json','w') as f: json.dump(s,f,indent=2)
print('studio enabled:', s['crews']['studio'])
"
```

## Step 2  -  Trigger trend scout now (don't wait for 06:00 MT)

```bash
docker exec orc-crewai python3 -c "
import sys; sys.path.insert(0,'/app')
from studio_trend_scout import studio_trend_scout_tick
studio_trend_scout_tick()
"
```

This scans all niches including `parenting-psychology`, sends Telegram brief with approve/reject buttons. Boubacar reviews and approves 5 candidates (sets Status=`qa-passed` in Pipeline DB or via Telegram buttons).

---

## Step 4  -  After Boubacar approves candidates

Run production on first approved candidate (get Notion ID from Pipeline DB):

```bash
docker exec orc-crewai python3 -c "
import sys; sys.path.insert(0,'/app')
from studio_production_crew import run_production
result = run_production('<NOTION_ID_OF_APPROVED_CANDIDATE>')
print(result)
"
```

Or let heartbeat handle it  -  `studio-production` fires every 30 min automatically.

---

## Key References

| Thing | Value |
|---|---|
| VPS | `ssh root@72.60.209.109` |
| Container | `orc-crewai` |
| Main orchestrator | `orchestrator/studio_production_crew.py` → `run_production(notion_id)` |
| Trend scout | `orchestrator/studio_trend_scout.py` → `studio_trend_scout_tick()` |
| Crew gate | `data/autonomy_state.json` → `crews.studio.enabled` |
| Pipeline DB | Notion ID `34ebcf1a-3029-8140-a565-f7c26fe9de86` |
| Brand Config DB | Notion ID `fc9abbd6-3388-4365-b285-81f508461d9a` |
| Brand configs | `/app/configs/brand_config.*.json` (all 5 baked into container) |
| Heartbeat | `studio-production` every 30m |

---

## What Was Built This Session (M3)

All files on VPS and in container. **Not yet committed to git**  -  do that on branch `feat/studio-m3-production`:

- `orchestrator/studio_script_generator.py`  -  Sonnet scriptwriter, [SCENE:]/[RETENTION:] markers, named sources
- `orchestrator/studio_qa_crew.py`  -  10-check QA (incl. retention loops, ai_origin_safe, word-count length)
- `orchestrator/studio_voice_generator.py`  -  ElevenLabs TTS, voice role resolution
- `orchestrator/studio_scene_builder.py`  -  segments script into timed scenes
- `orchestrator/studio_visual_generator.py`  -  kie_media wrapper, batch-3 parallel
- `orchestrator/studio_composer.py`  -  hyperframes project, GSAP word-level captions
- `orchestrator/studio_render_publisher.py`  -  3-format render + Drive + Notion PATCH + Telegram
- `orchestrator/studio_production_crew.py`  -  main orchestrator, `run_production(notion_id)`, heartbeat tick
- `orchestrator/scheduler.py`  -  studio-production heartbeat registered
- `configs/brand_config.under_the_baobab.json`  -  fully populated
- `configs/brand_config.ai_catalyst.json`  -  fully populated
- `configs/brand_config.first_generation_money.json`  -  fully populated
- `configs/voice_registry.json`  -  5 voice IDs
- `orchestrator/studio_trend_seeds.default.json`  -  parenting-psychology niche added
- `orchestrator/Dockerfile`  -  Node 22, hyperframes, ffmpeg, configs baked in

Container verified:
- `hyperframes --version` → 0.4.42 ✅
- `node --version` → v22.22.2 ✅
- `/app/configs/` → all 5 brand config files ✅

---

## Known Issues to Watch

- **`.env` CRLF**: If `orc_rebuild.sh` fails with `\r': command not found`, run `python3 /root/agentsHQ/scripts/fix_env.py` first then retry.
- **Kling image-to-video 422**: All Kling image-to-video slugs return 422 on Kai. Seedance-2 is working fallback (MODEL_REGISTRY already updated  -  rank-1 hailuo, rank-2 veo3_fast, rank-3 seedance-2).
- **hyperframes render**: dry_run tested only. First live render will be the real test. Watch logs closely.
- **Drive upload**: uses `GOOGLE_OAUTH_CREDENTIALS_JSON` env var → gws-oauth-credentials.json in container. Do not use gws_token.json (doesn't exist).

---

## Git Commit (pending)

```bash
cd /root/agentsHQ
git add orchestrator/studio_*.py orchestrator/scheduler.py orchestrator/kie_media.py orchestrator/Dockerfile configs/ docs/
git commit -m "feat(studio): M3 production pipeline  -  script, QA, voice, visuals, compose, render, publish

All 7 modules wired. hyperframes Node22+ffmpeg in container. Brand configs baked.
ElevenLabs + kie_media API-tested live. Awaiting first real MP4 render."
```
