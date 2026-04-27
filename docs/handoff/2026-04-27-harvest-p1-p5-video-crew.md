# Session Handoff - RoboNuggets Harvest P1-P5 + Video Crew - 2026-04-27

## TL;DR

Full RoboNuggets Bonus Lessons harvest pipeline ran (64 lessons, n0-n49 + b1-b14). Sankofa Council reviewed 5 priority builds. All 5 were built (P1 async polling, P1b QMD memory, P1c Sora watermark, P1d Suno remix, P2 ValidateOutputTool, P3 Blotato platform extension, P4 fal.ai upscale webhook, P5 unified VideoJobDispatcher). P5 is staged in dry-run mode; activation scheduled for May 8 via remote routine. Codex was used for all implementation: this is now the standing SOP (Codex-First Rule added to docs/AGENT_SOP.md). Ideas DB was fully reviewed and updated with activation gates for n22 and N8N Workflow Adapter.

## What was built / changed

- `orchestrator/async_poll.py`: NEW: shared Kie AI polling (poll_until_done, backoff 1.3x/cap 30s, PollFailed/PollTimeout)
- `orchestrator/memory_qmd.py`: NEW: QMD local semantic search wrapper (qmd_available, qmd_search, index_document, qmd_search_with_fallback)
- `orchestrator/kie_media.py`: MODIFIED: sora_watermark_remover(), audio_remix(), _poll_task() now delegates to async_poll
- `orchestrator/tools.py`: MODIFIED: KieSoraWatermarkRemoveTool, KieAudioRemixTool, KieEnqueueVideoJobTool, ValidateOutputTool added; VALIDATION_TOOLS bundle updated
- `orchestrator/webhooks.py`: NEW: FastAPI router POST /webhooks/fal-upscale, writes to upscale_jobs via _pg_conn()
- `orchestrator/upscale.py`: NEW: submit_upscale_job() via queue.fal.run, FAL_API_KEY required
- `orchestrator/video_crew.py`: NEW: VideoJobDispatcher, 6 job types, MAX_JOBS_PER_TICK=3, run_video_tick()
- `orchestrator/video_crew_agents.py`: NEW: build_video_director_agent()
- `orchestrator/contracts/video_crew.md`: NEW: autonomy contract, C2/C10/C11/C15 PENDING, UNSIGNED (NOT in commit 9107b28: must be staged separately)
- `orchestrator/migrations/0001_create_video_jobs.sql`: NEW: video_jobs DDL
- `orchestrator/db.py`: MODIFIED: ensure_video_jobs_table()
- `orchestrator/app.py`: MODIFIED: startup table creation + feature-flagged video-crew-tick wake
- `orchestrator/autonomy_guard.py`: MODIFIED: "video_crew" added to KNOWN_CREWS
- `orchestrator/crews.py`: MODIFIED: build_video_crew() added
- `orchestrator/router.py`: MODIFIED: "video_job" task type with keywords
- `orchestrator/auto_publisher.py`: MODIFIED: _account_id_for_platform() extended for YouTube/IG/TikTok/Threads
- `data/autonomy_state.json`: MODIFIED: video_crew entry (enabled=false, dry_run=true, cost_ceiling_usd=2.00)
- `docker-compose.yml`: MODIFIED: VIDEO_CREW_ENABLED=${VIDEO_CREW_ENABLED:-} in orchestrator env block
- `docs/AGENT_SOP.md`: MODIFIED: Codex-First Rule section added
- `skills/memory/qmd_semantic_retrieval/SKILL.md`: NEW: QMD skill documentation
- `workspace/memory-index/.gitkeep`: NEW: QMD index dir sentinel
- `scripts/skool-harvester/skool_harvest.py`: MODIFIED: emoji encoding fix on line 87
- `n8n/imported/`: NEW DIR: 18 RoboNuggets workflow JSONs archived as reference
- Notion Ideas DB: 25 rows updated (P1-P5 Done, archive Queued, n22 + N8N Adapter gate notes)
- Notion Harvested Recommendations DB: 4 rows added (b6/QMD, b1/Sora watermark, b3/Suno, n44/Reddit)

## Decisions made

1. **Codex-First Rule** (permanent SOP): Claude Code handles planning/Council/Notion; Codex handles all code. Added to docs/AGENT_SOP.md. Boubacar confirmed strongly.
2. **Unified VideoJobDispatcher instead of 5 separate crews**: n25/n19/n16/n15/n21 all fold into one crew with job_type routing. Saved ~50h of redundant builds.
3. **video_jobs in local Postgres, not Supabase**: Operational data rule. video_jobs is agentsHQ-internal; promote to Supabase only if external reader appears.
4. **P5 dry-run first**: Video crew stays enabled=false, dry_run=true until 3 cycles complete. Remote routine fires 2026-05-08 09:00 MT (trig_01LWzVfXvcxWMFZwYrv8ondt).
5. **n22 gates on P5 live**: Wan2.5+Seedream folds into VideoJobDispatcher MODEL_REGISTRY, ~45min Codex task, queue until May 8.
6. **N8N Workflow Adapter gates on P5 dry runs**: Uses n8n MCP + new n8n_triage_crew.py; queue until May 8.
7. **QMD package is @tobilu/qmd** (not @tobi/qmd: different package entirely).

## What is NOT done (explicit)

- **orchestrator/contracts/video_crew.md is NOT committed**: untracked on feat/m11d-model-review. Must be staged before merging to main.
- **feat/m11d-model-review not merged to main**: All P1-P5 work is on this branch. Merge + VPS deploy not done.
- **VPS deploy of P1-P5**: Container has not been rebuilt with P1-P5 code. Needs git pull + docker compose up -d --build orchestrator on VPS.
- **P5 dry-run cycles**: C2, C10, C11, C15 all PENDING. Scheduled for May 8 via remote routine.
- **1-3 new Ideas DB items** may have been added by Boubacar tonight: review them with the same harvest treatment (Council pass, activation gate, Notion update).
- **16 archive workflow templates** from RoboNuggets: deferred until P5 is live.

## Open questions

- Should feat/m11d-model-review be merged to main now, or after P5 dry runs? (Probably now: the code is complete and clean.)
- VPS deploy: should it happen in next session or wait for May 8 dry-run session?

## Next session must start here

1. Check Ideas DB for any new items Boubacar added tonight: apply full harvest review treatment if found.
2. Commit the untracked contract file on feat/m11d-model-review: `git checkout feat/m11d-model-review && git add orchestrator/contracts/video_crew.md && git commit -m "docs(video-crew): add autonomy contract (C2/C10/C11/C15 pending dry-run)"`.
3. Ask Boubacar: merge feat/m11d-model-review to main + deploy to VPS now, or wait for May 8?
4. If deploy: run `ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && docker compose up -d --build orchestrator"`.
5. May 8 (routine auto-fires): Walk through 3 P5 dry-run cycles, sign contract, enable crew.

## Files changed this session

```
orchestrator/
  async_poll.py               NEW
  memory_qmd.py               NEW
  webhooks.py                 NEW
  upscale.py                  NEW
  video_crew.py               NEW
  video_crew_agents.py        NEW
  contracts/video_crew.md     NEW (untracked: commit separately)
  migrations/0001_create_video_jobs.sql  NEW
  kie_media.py                MODIFIED
  tools.py                    MODIFIED
  db.py                       MODIFIED
  app.py                      MODIFIED
  autonomy_guard.py           MODIFIED
  crews.py                    MODIFIED
  router.py                   MODIFIED
  auto_publisher.py           MODIFIED
data/autonomy_state.json      MODIFIED
docker-compose.yml            MODIFIED
docs/AGENT_SOP.md             MODIFIED
skills/memory/qmd_semantic_retrieval/SKILL.md  NEW
workspace/memory-index/.gitkeep  NEW
scripts/skool-harvester/skool_harvest.py  MODIFIED (emoji fix line 87)
n8n/imported/                 NEW DIR (18 workflow JSONs)
```

All of the above (except contracts/video_crew.md) are in commit 9107b28 on feat/m11d-model-review.
