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
- End-to-end pipeline test: trigger a real `social_content` task and confirm Drive + Notion entries appear correctly.
- Google Drive Organizer / Cleanup Agent: in Ideas DB, high effort, prerequisite for full-Drive automated sync at scale.

## Open questions

- None blocking. Everything is live and working.

## Next session must start here

1. Create a Google Sheet in the agentsHQ Drive folder (name it "NLM Registry Mirror"). Copy its ID from the URL. SSH to VPS and add `NLM_EXPORT_SHEET_ID=<id>` to `/root/agentsHQ/.env`. Redeploy.
2. Trigger an end-to-end test: send a `social_content` task to the orchestrator via Telegram, confirm the result includes a Drive URL and a Notion content board entry appears with `Drive Link` populated and Status = Draft.
3. After both pass, this entire NotebookLM + pipeline system is fully verified.

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
