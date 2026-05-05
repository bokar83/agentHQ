# Session Handoff - Scheduled Email Send - 2026-04-27

## TL;DR
Built and shipped a scheduled email send capability for agentsHQ from scratch. The system uses a Postgres `email_jobs` table, a new `GWSMailSendTool` CrewAI tool, and a per-minute scheduler hook. Emails send from `monkeybiz@catalystworks.consulting` to Boubacar's own inboxes on explicit schedule only. Tested live: two emails delivered at exactly 2:00 PM MT.

## What was built / changed

- `orchestrator/migrations/008_email_jobs.sql`: new table (LIVE on VPS postgres)
- `orchestrator/db.py`: 5 functions appended: `ensure_email_jobs_table`, `fetch_pending_email_jobs`, `mark_email_job_sent`, `mark_email_job_failed`, `insert_email_job`
- `orchestrator/scheduler.py`: `_run_pending_email_jobs()` added; called every minute in `_scheduler_loop`; `ensure_email_jobs_table()` in `start_scheduler()`
- `orchestrator/skills/doc_routing/gws_cli_tools.py`: `GWSMailSendTool` class appended; in `GWS_DOC_ROUTING_TOOLS` bundle
- Memory: `reference_vps_ssh.md`, `project_scheduled_email.md`, `feedback_vps_postgres_inject.md`, `feedback_never_ask_for_known_infra.md`

## Decisions made

- **Send-from:** `monkeybiz@catalystworks.consulting` (alias on `boubacar@catalystworks.consulting` GWS account): no re-auth needed, Google honors alias From header
- **Scope:** `email_jobs` is email-specific (not generalized to generic task queue) per Karpathy Principle 2
- **Design:** no draft-review path; plain send only; review path deferred
- **Self-to-self only:** this is a personal async channel, not an outbound email tool

## What is NOT done

- `gws_cli_tools.py` inside container is read-only mounted: the `From` header change for `GWSMailSendTool` (immediate sends) will only take effect on next full container rebuild (`docker compose up -d --build orchestrator`)
- Scheduler sends use the new `From` header immediately (hot-copied via `docker cp`)
- No HTML email support (plain text only)
- No CC/BCC support
- No retry logic beyond marking `failed`
- `monkeybiz@...` From header not verified end-to-end yet (only `bokar83@gmail.com` From was tested in the live run: the From header change was deployed after the test)

## Open questions

- Should the next full deploy include `docker compose up -d --build` to pick up the `gws_cli_tools.py` read-only mount fix?
- Any other recipients beyond `bokar83@gmail.com` and `boubacar@catalystworks.consulting`?

## Next session must start here

1. Verify `monkeybiz@catalystworks.consulting` From header works end-to-end by scheduling a test email and checking sender in inbox
2. On next planned VPS deploy, run `docker compose up -d --build orchestrator` to pick up the `gws_cli_tools.py` From header change for immediate sends
3. Commit the 4 changed files: `orchestrator/migrations/008_email_jobs.sql`, `orchestrator/db.py`, `orchestrator/scheduler.py`, `orchestrator/skills/doc_routing/gws_cli_tools.py`

## Files changed this session

- orchestrator/migrations/008_email_jobs.sql (new)
- orchestrator/db.py (modified)
- orchestrator/scheduler.py (modified)
- orchestrator/skills/doc_routing/gws_cli_tools.py (modified)
- ~/.claude/projects/d:Ai-Sandbox-agentsHQ/memory/reference_vps_ssh.md (new)
- ~/.claude/projects/d:Ai-Sandbox-agentsHQ/memory/project_scheduled_email.md (new)
- ~/.claude/projects/d:Ai-Sandbox-agentsHQ/memory/feedback_vps_postgres_inject.md (new)
- ~/.claude/projects/d:Ai-Sandbox-agentsHQ/memory/feedback_never_ask_for_known_infra.md (new)
- ~/.claude/projects/d:Ai-Sandbox-agentsHQ/memory/MEMORY.md (updated)
