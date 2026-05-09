# Session Handoff — Notion CRM Sync Deleted, Supabase = SOR — 2026-05-07

## TL;DR

Severed all Notion CRM Leads sync code from agentsHQ. Earlier session deactivated writes via bypass-logs; this session deleted the underlying functions outright (no flags, no compatibility shims, no commented blocks). Sankofa Council + Karpathy audit rejected the original 4-week phased plan as over-engineered and Boubacar approved the collapsed one-day cleanup. Parity audit ran inside `orc-crewai`; report shows 0 Notion-only orphans (no backfill needed). Atlas M19 queued as the replacement visual surface. Supabase is now the sole CRM system of record.

## What was built / changed

**Code deletions (lead-sync only — non-lead Notion features kept):**

- `skills/local_crm/crm_tool.py`
  - Removed `_sync_lead_to_notion`, `_sync_lead_status_to_notion`, `_notion_headers`, `_NOTION_DB_ID`, `_NOTION_API`, `_NOTION_VERSION`.
  - Removed top-level `import httpx` and `import os` (not used elsewhere in the file; `os` only inside `_get_conn`'s local import).
  - Removed bypass-log lines from `add_lead` (lines 211-213) and `mark_outreach_sent` (lines 397-401).
  - Updated module docstring (drop "Notion CRM Leads database synced automatically" bullet).
- `orchestrator/scheduler.py`
  - Removed `_run_notion_sync` (was line 334).
  - Removed `_listen_for_supabase_changes` (was line 799).
  - Removed listen_thread spawn block + bypass log in `_init_threads`.
  - Cleaned `_periodic_sync` — dropped `notion_sync_hours`, `last_notion_sync_date`, scheduled-fallback bypass-log block.
  - Removed commented `_run_notion_sync()` callsite from `_scheduler_loop`.
- `orchestrator/db.py`
  - Removed `sync_supabase_to_notion` (entire 184-line function plus inline helpers `_notion_status`, `_notion_priority`, `_notion_industry`, `_notion_source`).
- `orchestrator/tools.py`
  - Cleaned stale "auto-sync to Notion CRM Leads" docstring on `CRMAddLeadTool`.

**New files:**

- `scripts/reconcile_leads_one_shot.py` — paginated Notion DB pull, Supabase pull, email + name+company match, status-drift detection, markdown report writer.
- `docs/audits/notion_sever_parity_2026-05-07.md` — generated report (87 KB; full lists of status drift + Supabase-only).

**Roadmap updates:**

- `docs/roadmap/atlas.md` — added **M19: Atlas CRM Dashboard (`/crm`)** as trigger-gated milestone with proposed endpoints, predicate, success criteria.
- `docs/roadmap/harvest.md` — R-notion-sever block rewritten with sync-deleted status; new session-log entry added.

**Memory writes:**

- `project_supabase_sole_crm_sor_2026-05-07.md` (in MEMORY_ARCHIVE.md)
- `feedback_collapse_phased_plans_when_remaining_work_small.md` (in MEMORY.md under Workflow/SOP)

## Decisions made

1. **Delete, don't flag.** Original plan proposed `NOTION_SYNC_ENABLED = False` constant duplicated across 3 files. Sankofa + Karpathy both flagged this as theater for a final decision. Replaced with outright deletion.
2. **Audit script in repo, not scratch.** Original plan put `reconcile_leads.py` in Antigravity scratch dir. Moved to `scripts/reconcile_leads_one_shot.py` so script + report are git-tracked.
3. **Code deletion first, Notion archive second.** Reversed Step 3/4 sequencing from the original plan. Deleting code proves there are no callers; Notion archive happens after that proof.
4. **Atlas dashboard separated from sever.** Original plan bundled the Atlas `/crm` endpoint into the migration. Decoupled: sever ships today, dashboard becomes Atlas M19 with its own trigger gate.
5. **Run audit inside `orc-crewai` container.** Local Python had SSL cert verification failures hitting Notion API; container has clean trust store. SCP → docker cp → docker exec was the working path.

## What is NOT done (explicit)

- **Notion CRM Leads DB not archived.** Boubacar archives in Notion UI when ready. Code no longer references it; archive is purely a Notion-side cleanup.
- **Atlas M19 `/crm` dashboard not started.** Trigger-gated. Predicate `WHERE status='new' OR (status IN ('messaged','replied') AND last_contacted_at < NOW() - INTERVAL '7 days')` is proposed — needs Boubacar confirm before build.
- **Code not pushed to remote.** No `git push` issued this session (gate-mode rule). Files are committed-ready in working tree.
- **Container restart not performed.** Volume-mounted code is on disk locally only — needs `git pull` + `docker compose up -d orchestrator` on VPS to take effect on the running scheduler. Until then, container still runs old (bypass-log) code.

## Open questions

- Confirm "needs outreach today" SQL predicate before Atlas M19 build kicks off.
- 2,024 status-drift rows in audit: do we want a one-time backfill from Notion → Supabase (Notion holds older "contacted/replied" states from when sync was bidirectional)? Or trust Supabase status as authoritative going forward? Default: trust Supabase, no backfill.
- Notion CRM DB shows 10,000 pages vs 2,549 Supabase rows — duplication artifact from old sync runs creating multiple Notion pages per lead. No action needed, just noted.

## Next session must start here

1. Read `docs/handoff/2026-05-07-notion-crm-sync-deleted.md` (this file).
2. Confirm with Boubacar: `WHERE status='new' OR (status IN ('messaged','replied') AND last_contacted_at < NOW() - INTERVAL '7 days')` is correct predicate for "needs outreach today" on the Atlas M19 dashboard.
3. Decide on the 2,024 status-drift rows: backfill from Notion or accept Supabase as authoritative.
4. If pushing this session's deletions to VPS: commit changed files, push branch, gate handles deploy. Or if direct: `ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && docker compose up -d orchestrator"`.
5. If Atlas M19 unblocked, scope the `/atlas/crm/board` endpoint in `orchestrator/atlas_dashboard.py`. Follow success criteria in the M19 milestone block.

## Files changed this session

```
skills/local_crm/crm_tool.py            (deletions)
orchestrator/scheduler.py               (deletions)
orchestrator/db.py                      (deletion of sync_supabase_to_notion)
orchestrator/tools.py                   (docstring cleanup)
scripts/reconcile_leads_one_shot.py     (NEW)
docs/audits/notion_sever_parity_2026-05-07.md  (NEW, 87 KB)
docs/roadmap/atlas.md                   (added M19)
docs/roadmap/harvest.md                 (R-notion-sever rewrite + log entry)

Memory:
  ~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md
  ~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY_ARCHIVE.md
  ~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/project_supabase_sole_crm_sor_2026-05-07.md  (NEW)
  ~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_collapse_phased_plans_when_remaining_work_small.md  (NEW)
```
