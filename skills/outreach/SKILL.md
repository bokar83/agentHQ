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

**Auto-send is OFF by default.** `sequence_engine.py` checks env vars `AUTO_SEND_CW`, `AUTO_SEND_SW`, `AUTO_SEND_STUDIO` (all default `"false"`). When false, emails go to Gmail Drafts folder, NOT sent. Log says "drafted" not "sent". Boubacar reviews + sends manually. To flip: set env var to `"true"` in `.env` + `docker-compose.yml` orchestrator environment block.

**Morning runner fires via systemd**, not container heartbeat. Unit: `signal-works-morning.service`. Log: `/var/log/signal_works_morning.log` on VPS. Fires 07:00 MT daily. Check log there, not docker logs.

**Studio cohort is wired** (`sequence_engine.py` line 77). If studio leads are queued and `studio_t1` fails to import (e.g. SyntaxError), the entire Studio cohort silently skips. Always verify `python -c "import templates.email.studio_t1"` before morning run.

**Drive URLs in outreach emails must be public.** Use `orchestrator.drive_publish.audit_email_template_pdfs()` to verify. See `feedback_drive_pdfs_must_be_public.md`.
