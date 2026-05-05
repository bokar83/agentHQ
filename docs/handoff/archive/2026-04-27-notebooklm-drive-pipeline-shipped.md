# Session Handoff - NotebookLM + Drive Watch + Deliverable Pipeline - 2026-04-27

## TL;DR

Long session that fully wired agentsHQ's knowledge management layer. Installed the NotebookLM CLI skill locally and on VPS, built and fixed the document routing matrix (19/19 tests), enabled Drive Watch, backfilled 11 high-signal docs into the correct CW_* notebooks, audited Drive vs NotebookLM (one gap found and filled), wired the deliverable pipeline so agent outputs auto-save to Drive and content types create Notion content board entries, and built the daily Postgres-to-Sheets audit mirror. Everything is live on VPS.

## What was built / changed

**New files:**
- `agentsHQ/skills/notebooklm/`: full skill (SKILL.md + scripts/nlm.py + scripts/refresh_auth.py)
- `~/.claude/skills/notebooklm/`: local copy
- `scripts/notebooklm_auth_refresh.py`: headless auth refresh + Telegram alert on failure
- `scripts/nlm_registry_export.py`: daily Postgres-to-Sheets export (cron 06:00 UTC)

**Modified files:**
- `orchestrator/constants.py`: added `CONTENT_TASK_TYPES` set + `nlm_artifact` to `SAVE_REQUIRED_TASK_TYPES`
- `orchestrator/saver.py`: added `save_to_notion_content_board()`; field name fixed to `Drive Link` (NOT `Drive URL`)
- `orchestrator/app.py`: `CONTENT_TASK_TYPES` import + Notion board wiring after Drive save
- `orchestrator/skills/doc_routing/taxonomy_agent.py`: routing matrix rewritten: 13 rules, P0 skool guard, 3 exclusion categories, full keyword set
- `orchestrator/scheduler.py`: exclusion check injected before Drive Watch routing (~line 719)
- `docker-compose.yml`: `DRIVE_WATCH_ENABLED`, `NLM_BIN`, `AUDIENCE_ENGINE_NOTEBOOK_ID` added to allowlist
- `docs/roadmap/atlas.md`: session log appended
- `docs/superpowers/plans/2026-04-12-notebooklm-ingestion-system.md`: SHIPPED header added

**VPS env vars added to `.env`:**
- `DRIVE_WATCH_ENABLED=true`
- `NOTEBOOKLM_LIBRARY_ROOT_ID=1S0t78tojgA6VugqMtE3soZYFSEAcSvvH`
- `NOTEBOOKLM_REVIEW_QUEUE_FOLDER_ID=1UJ81j0O_AewmmkqrocQ4g5tCVMOEE3x5`
- `NLM_BIN=/root/.claude/skills/notebooklm/scripts/nlm.py`
- `AUDIENCE_ENGINE_NOTEBOOK_ID=e246e525-8618-47ef-afd6-e279eed17d37`

**VPS crons added:**
- `30 5 */3 * *`: NotebookLM auth refresh (`scripts/notebooklm_auth_refresh.py`)
- `0 6 * * *`: Postgres-to-Sheets export (`scripts/nlm_registry_export.py`)

## Decisions made

1. **CLI-primary, MCP-backup** for all NotebookLM operations. `mcp__notebooklm-mcp__*` tools are fallback only.
2. **Postgres is the live registry**, Google Sheets is the daily audit mirror (not primary).
3. **Drive Watch scans root only**: does NOT recurse subfolders. Files organized in subfolders are already correct; Drive Watch catches new intake.
4. **Scripts, raw HTML site builds, and `.py/.js/.sh` files are permanently excluded** from routing: code is not knowledge.
5. **Notion content board field is `Drive Link`** (url type): NOT `Drive URL`. This was caught and fixed before any real deliverable hit it.
6. **Routing matrix P0 priority for skool content**: beats bare `harvest` keyword at P2 to prevent collision.

## What is NOT done (explicit)

- `NLM_EXPORT_SHEET_ID` not yet set in VPS `.env`: need to create a Google Sheet in the agentsHQ Drive folder, copy its ID, add to VPS `.env`. Script prints a clear reminder when it runs without it.
- Google Drive Organizer / Cleanup Agent: in Ideas DB, high effort, prerequisite for full-Drive automated sync at scale.

## Open questions

- None blocking. Everything is live, synced, and verified.

## Next session must start here

1. Create a Google Sheet in the agentsHQ Drive folder (name it "NLM Registry Mirror"). Copy its ID from the URL. SSH to VPS and add `NLM_EXPORT_SHEET_ID=<id>` to `/root/agentsHQ/.env`. Redeploy.
2. Check `/var/log/nlm_registry_export.log` (the 06:00 UTC cron may have already run). If `NLM_EXPORT_SHEET_ID` is missing, the log will say so clearly.
3. Pick next Atlas milestone from `docs/roadmap/atlas.md`.

## Follow-on session (same day): bug fixes + nsync (2026-04-27)

The original handoff was written before the deliverable pipeline e2e test completed. A second session fixed the remaining bugs and fully synced all three locations.

**Bugs fixed:**

1. `social_content` re-classified as `app_build` by LLM every run. Root cause: `classify_task()` in `router.py` had no way to skip LLM classification. Fix: added `explicit_task_type` param that short-circuits the entire classifier when a valid task type is passed. Threaded through `engine.py` run_orchestrator() -> `router.py` classify_task(). `app.py` and `worker.py` pass `request.task_type` when not empty/unknown.

2. Notion content board step not firing for async (Telegram) jobs. Root cause: the Notion step was added to `app.py` sync path only; async jobs go through `worker.py` `_run_background_job()`. Fix: added the `CONTENT_TASK_TYPES` check + `save_to_notion_content_board()` call to `worker.py`.

3. `TaskRequest` missing `task_type` field on VPS. Root cause: VPS `schemas.py` was behind local. Fix: added `task_type: str = "unknown"` to `TaskRequest`.

4. All five patches were applied directly to VPS working directory (Pyright LSP race condition blocks local Edit -> SCP flow). Nsync at session close pulled VPS files back to local, committed as `9a080ee`, pushed to origin, VPS pulled clean. All three locations confirmed at `9a080ee`.

**E2e test result (job d5042bc6):**

- Classified as `social_content` via explicit_task_type bypass
- Drive saved: `https://drive.google.com/file/d/1zb5nIwvBXtKcudxnOGUq2AEkHDtGGY3V/view`
- Notion content board Draft created with Drive Link populated

**Files added to commit `9a080ee`:**

- `orchestrator/router.py`: `explicit_task_type` param in `classify_task()`
- `orchestrator/engine.py`: `explicit_task_type` threaded through `run_orchestrator()`
- `orchestrator/app.py`: `task_type` passed from `TaskRequest` on both sync + async paths
- `orchestrator/worker.py`: Notion content board step added to async job path
- `orchestrator/schemas.py`: `task_type: str = "unknown"` on `TaskRequest`

## Files changed this session

```
agentsHQ/
  orchestrator/
    constants.py                         : CONTENT_TASK_TYPES, nlm_artifact
    saver.py                             : save_to_notion_content_board(), Drive Link fix
    app.py                               : CONTENT_TASK_TYPES wiring
    skills/doc_routing/taxonomy_agent.py : full routing matrix rewrite
    scheduler.py                         : exclusion check
  scripts/
    notebooklm_auth_refresh.py           : NEW: headless auth refresh + Telegram alert
    nlm_registry_export.py               : NEW: daily Sheets export
  skills/notebooklm/                     : NEW: full skill
  docker-compose.yml                     : env var allowlist additions
  docs/roadmap/atlas.md                  : session log
  docs/superpowers/plans/2026-04-12-notebooklm-ingestion-system.md: SHIPPED header

~/.claude/skills/notebooklm/            : local copy of skill
```
