# Session Handoff - Studio Blotato Silent-Failure Chain + AIC Re-Seed - 2026-05-11

## TL;DR
3 Blotato posts failed May 11 9:24 AM with opaque errors ("Failed to parse URL from undefined", "requires image or video"). Diagnosed 3 chained bugs in Studio pipeline: render-gate missing, weak media guard, module-level counter cross-contaminating records. All 3 fixed, deployed, Gate-merged. Recovered 2 stuck Notion records. Discovered + fixed docker-entrypoint.sh JSON sync bug (config edits had been silently no-op'd). Re-seeded AIC niche to primary-source queries; scout fired and unblocked AIC (3 picks landed after 6 weeks of starvation). Sankofa Council reviewed proposed QA gate changes — verdict: don't touch, source_citation already auto-skips for AIC via shorts path; 5-record sample = no calibration data.

## What was built / changed

### Code commits (all Gate-merged to main)
- `d4df7e8` — `orchestrator/studio_blotato_publisher.py`: per-record `rec_published`/`rec_failed` counters replace module-level. New `_MEDIA_REQUIRED_PLATFORMS = {"instagram","youtube","tiktok","pinterest"}` guard skips media-required platforms when `media_urls=[]`.
- `337ef42` — `orchestrator/studio_render_publisher.py`: `_update_notion` now sets `Status="render-failed"` when `asset_url` empty (was unconditionally `scheduled`). Writes diagnostic QA note.
- `dbaca0e` — `orchestrator/studio_trend_seeds.default.json`: AIC niche `ai-displacement-first-gen` re-seeded with 15 primary-source queries (Goldman Sachs, McKinsey, MIT, Stanford AI Index, Anthropic Economic Index, OECD, Brookings, WEF Future of Jobs, Pew Research, BLS, Oxford automation, Fed productivity).
- `978982e` — `scripts/docker-entrypoint.sh`: now syncs `orchestrator/*.json` alongside `*.py`. Prevents silent config-no-op via CWD fallback path.
- `f80f43f` (chore branch ready for Gate) — `.gitignore`: added `.tmp_screenshots/`.
- `093192b` (branch `docs/roadmap-studio-2026-05-11` ready for Gate) — `docs/roadmap/studio.md`: 2026-05-11 session log.

### Notion DB changes
- 2 Pipeline DB records recovered:
  - `35dbcf1a-3029-8177-ba24-d69f38426b9b` (Hannatu, UTB) → Status=render-failed, Sched=2026-05-15, Posted cleared
  - `35dbcf1a-3029-8162-9a4a-e951581cbdf7` (Parents', 1stGen) → Status=render-failed, Sched=2026-05-16, Posted cleared
- 11 new scout picks written (5 UTB, 3 AIC, 3 1stGen) — first AIC content in 6 weeks

### Memory files (4 new + MEMORY.md index updates)
- `feedback_studio_blotato_silent_failure_chain.md`
- `feedback_entrypoint_json_sync.md`
- `feedback_aic_seed_strategy.md`
- `feedback_qa_calibration_before_tuning.md`
- MEMORY.md: 4 entries archived to MEMORY_ARCHIVE.md (under 200-line cap; final = 199)

### Postgres memory
- 4 AgentLessons + 1 ProjectState + 1 SessionLog written via memory_store to VPS Postgres

## Decisions made

- **Don't build Layer 2 retry tick yet.** Sankofa Executor verdict: tactical fix today, wait 7-14 days for failure data, then decide between Studio-specific retry vs generic pipeline reconciler. Don't build for hypothetical failures.
- **Don't touch QA gate.** source_citation already auto-skipped for AIC via the shorts-first path (`target_duration_sec=55` → `length_target="short (<60s)"` → run_qa skip rule). 4 historical AIC qa-failed records were from pre-shorts-first era. Sample of 5 = no calibration data.
- **Manual recovery (not auto).** 2 stuck records reset by hand; rescheduled spread to avoid stacking (UTB Hannatu 5/15 vs Anansi 5/14, 1stGen Parents' 5/16 vs other Parents'-money 5/13).
- **AIC seeds shift.** Viral hot-takes ("AI taking my job") replaced with primary-source research queries. Faceless brands need citable source material; structural fix at scout layer, not QA layer.

## What is NOT done (explicit)

- **Branches pending Gate merge:**
  - `chore/gitignore-tmp-screenshots` (cosmetic gitignore add)
  - `docs/roadmap-studio-2026-05-11` (session log)
- **Layer 2 retry tick** — deferred per Sankofa, build only if failure pattern emerges in 7d
- **Layer 3 Blotato reconciler** — deferred until `/v2/posts?status=failed` API verified
- **QA calibration log** — postgres `qa_decisions` table for false-positive/negative measurement. Recommended but not built. Next session candidate.
- **AIC content quality verdict** — pending real production crew tick on 3 newly-scouted AIC picks
- **Render publisher Telegram alert on full-format-missing** — `_notify_telegram` already writes "MISSING" but signal got lost in noise May 11. Not adding more telemetry since render-gate now provides Status=render-failed signal in Pipeline DB. Re-evaluate if pattern recurs.

## Open questions

- Did AIC's 3 new scouted picks come from citation-friendly source channels? (Verify when production crew drafts them — likely tomorrow's 06:00 tick or next manual fire.)
- The original render-failure for Hannatu + Parents was never definitively isolated (manifest missing vs ffmpeg crash vs Drive quota). Pre-restart logs gone. Render-gate now catches the symptom regardless of which mode hits. Worth instrumenting render publisher with per-stage success/fail log if pattern recurs.
- Boubacar phone/CW email aliases/RTK/MemPalace memories moved to archive due to MEMORY.md cap — if accessed often, may need to be pulled back to always-loaded zone.

## Next session must start here

1. **Verify Gate has merged pending branches:** `gh pr list --state open` or check `cd /root/agentsHQ && git log --oneline origin/main -5` for `chore/gitignore-tmp-screenshots` + `docs/roadmap-studio-2026-05-11` commits in main.
2. **Check pipeline health:** Query Pipeline DB for new `Status=render-failed` records (signals real render crashes surfaced by Bug A fix). Query for `Status=publish-failed` (validates Bug B+C). Should be zero or minimal in first 24h.
3. **Inspect first AIC drafts:** When production crew processes the 3 newly-scouted AIC picks, read the actual draft text. Would Boubacar ship them under "AI Catalyst"? If yes → re-seed worked. If no → script generator needs work, not QA.
4. **AIC publish first piece:** If draft + render succeed for any AIC pick, that's first AIC content in 6 weeks. Big unblock.
5. **At day 7 (2026-05-18):** Review accumulated `publish-failed` + `render-failed` counts. Decide Layer 2 retry tick vs generic reconciler with real data, per Sankofa Executor.

## Files changed this session

- `orchestrator/studio_blotato_publisher.py`
- `orchestrator/studio_render_publisher.py`
- `orchestrator/studio_trend_seeds.default.json`
- `scripts/docker-entrypoint.sh`
- `.gitignore`
- `docs/roadmap/studio.md`
- Memory: `feedback_studio_blotato_silent_failure_chain.md`, `feedback_entrypoint_json_sync.md`, `feedback_aic_seed_strategy.md`, `feedback_qa_calibration_before_tuning.md`, `MEMORY.md`, `MEMORY_ARCHIVE.md`
- Postgres: 6 rows into memory table (4 lessons + 1 project_state + 1 session_log)
- 2 Notion Pipeline DB records recovered (Hannatu UTB, Parents' 1stGen)
- 11 Notion Pipeline DB records created (scout picks)
