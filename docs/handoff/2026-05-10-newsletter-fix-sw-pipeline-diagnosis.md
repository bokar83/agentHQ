# Session Handoff - Newsletter Fix + SW Pipeline Diagnosis - 2026-05-10

## TL;DR

Sunday session. Fixed `newsletter_editorial_input` missing table. Diagnosed SW pipeline — found a critical blind spot: no per-email send tracking exists in Postgres. T1 drafts fire correctly (Boubacar confirmed) but we have zero visibility into which touch fired when, to whom, at what stage. Next session must add SW email send logging to Postgres.

## What was built / changed

- `orchestrator/newsletter_editorial_input.py` — `get_reply_for_week()` wrapped in try/except; returns None on any DB error
- `migrations/006_newsletter_editorial_input.sql` — run on VPS `orc-postgres`; table exists
- `docs/roadmap/atlas.md` — session log + cheat block updated; item 4 DONE
- `skills/outreach/SKILL.md` — zero-volume diagnosis rule added
- Memory files updated: orc-postgres container name, SW pipeline state

## Key correction: SW leads are in Supabase, not orc-postgres

`sequence_engine.py` calls `get_crm_connection_with_fallback()` → Supabase.
The `leads` table in orc-postgres (0 rows) is unrelated. Querying it was wrong.
T1 drafts have been generating correctly all week per Boubacar.
`AUTO_SEND_SW=false` means drafts go to Gmail Drafts — not a bug, intentional.

## Critical gap found: no SW email send tracking

`email_jobs` table in orc-postgres only has 2 rows (April 27 skill catalog emails).
SW outreach sends/drafts are NOT logged to any Postgres table.
We have zero visibility into: which touch fired, to whom, at what time, success/failure.
This is a blind spot — can't answer "how many T1s went out this week?" without reading Gmail.

## Decisions made

- `AUTO_SEND_SW=false` — intentional. T1s draft to Gmail for manual review + send.
- Harvest quality question open — `profitablepenny.com` / `scribd.com` in today's log needs investigation.

## What is NOT done (explicit)

- **SW email send logging** — NOT built. MUST be next session's first priority.
- **Harvest niche filter** — root cause of junk leads unknown. Monday logs needed.
- **M18 HALO** — not started. Target 50 traces by 2026-05-18.
- **Monday cron is session-only** — dies when this session closes.

## Open questions

- What does `sequence_engine.py _mark_sent()` write, and where? Does it update Supabase only, or also log to orc-postgres?
- How many T1s actually went out this week? Need to check Supabase `leads` table `sequence_touch` + `email_drafted_at` columns.

## Next session must start here

1. **Add SW email send logging to orc-postgres** — every T1-T5 draft/send writes a row to a new `sw_email_log` table: `(id, lead_email, touch, pipeline, status, created_at)`. Wire into `sequence_engine.py _mark_sent()`. This gives us the granularity we need.

2. **Check Supabase for actual send volume this week:**
   ```bash
   ssh root@72.60.209.109 "docker exec orc-crewai python3 -c \"
   import sys; sys.path.insert(0, '/app')
   from orchestrator.db import get_crm_connection
   conn = get_crm_connection()
   cur = conn.cursor()
   cur.execute(\\\"SELECT sequence_touch, COUNT(*), MAX(email_drafted_at) FROM leads WHERE email_drafted_at IS NOT NULL GROUP BY sequence_touch ORDER BY sequence_touch\\\")
   print(cur.fetchall())
   \"\""
   ```

3. **Diagnose harvest niche filter** — pull Monday harvest logs and find the GMB query producing `profitablepenny.com` / `scribd.com`.

## Files changed this session

- `orchestrator/newsletter_editorial_input.py`
- `docs/roadmap/atlas.md`
- `skills/outreach/SKILL.md`
- `memory/MEMORY.md` (orc-postgres container name)
- `memory/project_sw_pipeline_state_2026-05-09.md`

## Commits

- `a86c179` — fix(newsletter): make get_reply_for_week non-fatal + run migration 006
- `b93c834` — docs(atlas): mark newsletter_editorial_input fix done
- `ebcd77e` — chore(shutdown): atlas roadmap + outreach skill updates
- `ed4641f` — docs(handoff): this file
