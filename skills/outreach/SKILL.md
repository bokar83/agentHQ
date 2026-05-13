---
name: outreach
description: Core outreach engine for SW + CW pipelines. Agent-internal only -- not Boubacar-invoked. sequence_engine.py runs 4/5-touch email sequences imported by morning_runner, engine.py, and send_scheduler. outreach_tool.py and email_templates.py are production code.
---

# Outreach (Agent-Internal)

Production code module. Not a Boubacar-invoked skill. Contains:

- `sequence_engine.py` -- 4/5-touch email sequence runner (SW + CW). Imported by `morning_runner.py`, `orchestrator/engine.py`, `send_scheduler.py`.
- `outreach_tool.py` -- outreach pipeline tool.
- `email_templates.py` -- email template library.

**DO NOT archive.** These files are active production imports.

## Key operational facts

**Auto-send is OFF by default.** `sequence_engine.py` checks env vars `AUTO_SEND_CW`, `AUTO_SEND_SW`, `AUTO_SEND_STUDIO`, `AUTO_SEND_CONSTRAINTS_AI` (all default `"false"`). When false, emails go to Gmail Drafts folder, NOT sent. Log says "drafted" not "sent". Boubacar reviews + sends manually. To flip: set env var to `"true"` in `.env` + `docker-compose.yml` orchestrator environment block.

**Constraints AI pipeline (added 2026-05-13):** 3-touch warm-inbound sequence at Day 0/2/4. Triggered when site visitor submits email on catalystworks.consulting Constraints AI demo. POST hits `/constraints-capture` → Supabase `leads` row with `sequence_pipeline='constraints_ai', sequence_touch=0`. Templates: `templates/email/constraints_ai_t{1,2,3}.py`. Known bugs 2026-05-13: `_get_due_leads` T1 picks unrelated SW leads (needs pipeline filter); `run_sequence` loop hardcoded 1-5 → KeyError on touch 4 for 3-touch pipelines; cosmetic row[0] post-INSERT log error. See `reference_constraints_ai_capture_route.md`.

**Morning runner fires via systemd**, not container heartbeat. Unit: `signal-works-morning.service`. Log: `/var/log/signal_works_morning.log` on VPS. Fires 07:00 MT daily. Check log there, not docker logs.

**Studio cohort is wired** (`sequence_engine.py` line 77). If studio leads are queued and `studio_t1` fails to import (e.g. SyntaxError), the entire Studio cohort silently skips. Always verify `python -c "import templates.email.studio_t1"` before morning run.

**Drive URLs in outreach emails must be public.** Use `orchestrator.drive_publish.audit_email_template_pdfs()` to verify. See `feedback_drive_pdfs_must_be_public.md`.

**SW leads live in Supabase, not orc-postgres.** `sequence_engine.py` calls `get_crm_connection_with_fallback()` → Supabase. The `leads` table in orc-postgres is unrelated. Never query orc-postgres to assess SW sequence volume.

**No per-send logging in Postgres (as of 2026-05-10).** `email_jobs` table only tracks system emails, not SW outreach. To assess T1-T5 volume: query Supabase `leads` table `sequence_touch` + `email_drafted_at` columns, or check Gmail Drafts/Sent. A `sw_email_log` table should be added to orc-postgres for real-time visibility.

**`AUTO_SEND_SW=false` = drafts, not silence.** T1s draft to Gmail Drafts for manual review + send. Not a bug — intentional gate. Flip to `true` in VPS `.env` + `docker compose up -d orchestrator` when ready for autonomous sends.
