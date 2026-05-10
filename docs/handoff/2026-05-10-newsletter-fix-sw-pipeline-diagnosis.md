# Session Handoff - Newsletter Fix + SW Pipeline Diagnosis - 2026-05-10

## TL;DR

Sunday session. Fixed the long-standing `newsletter_editorial_input` table-missing error by running migration 006 on VPS `orc-postgres` and wrapping `get_reply_for_week()` non-fatally. Diagnosed SW pipeline end-to-end: `AUTO_SEND_SW=false` and harvest is pulling wrong businesses (scribd.com, profitablepenny.com instead of contractors). Zero T1 emails have ever been sent. Monday cron scheduled to diagnose and fix harvest query.

## What was built / changed

- `orchestrator/newsletter_editorial_input.py` — `get_reply_for_week()` wrapped in try/except; returns None on any DB error instead of raising UndefinedTable
- `migrations/006_newsletter_editorial_input.sql` — run on VPS `orc-postgres`; table now exists with correct schema (week_start_date PK, reply_text, received_at, chat_id)
- `docs/roadmap/atlas.md` — session log + cheat block updated; item 4 marked DONE; new next-moves order
- `skills/outreach/SKILL.md` — added zero-volume diagnosis rule (check harvest lead quality before flipping AUTO_SEND)
- Memory: `project_sw_pipeline_state_2026-05-09.md` updated with AUTO_SEND=false finding + fix sequence
- Memory: `MEMORY.md` line 23 updated with `orc-postgres` container name
- Postgres memory table: 3 AgentLessons + 1 ProjectState + 1 SessionLog written

## Decisions made

- **Do NOT flip AUTO_SEND_SW=true yet.** Harvest is producing garbage leads. Enable only after niche filter fixed and 5-10 correct leads verified.
- **Monday diagnosis first** — then fix harvest query — then enable.

## What is NOT done (explicit)

- **Harvest GMB niche filter** — not fixed yet. Need weekday logs to see what query produces `profitablepenny.com`. Root cause unknown.
- **AUTO_SEND_SW=true** — deliberately left false until harvest fixed.
- **M18 HALO** — not started. Target 50 traces by 2026-05-18.
- **Monday cron is session-only** — if this Claude session is closed before Monday 08:00 MT, the cron dies. Run the harvest diagnosis manually if needed (see Next session must start here).

## Open questions

- What GMB search query / niche config is producing non-contractor leads? Look in `orchestrator/scheduler.py` `_run_daily_lead_harvest()` or the sw_harvest crew for the search terms.
- Is the `leads` table schema correct? Did the `gmb_opener` column get added? (It was added in 2026-05-09 session via `_ensure_sequence_columns` — verify it exists on VPS.)

## Next session must start here

1. **Pull Monday harvest logs** (if cron fired automatically, review its output; if not):
   ```bash
   ssh root@72.60.209.109 "docker logs orc-crewai --since 12h 2>&1 | grep -iE 'harvest|gmb|niche|hunter|T1|dropped|deliverable'"
   ```
2. **Find the GMB search query** — grep `orchestrator/scheduler.py` and any sw_harvest crew for the niche search terms producing junk leads
3. **Fix the query** — should target local service businesses (roofing/HVAC/plumbing) in specific cities by GMB category, not generic web searches
4. **Verify 5-10 leads** look correct (real contractor businesses with phone + address)
5. **Flip the flag**: edit VPS `.env` `AUTO_SEND_SW=true` + `docker compose up -d orchestrator`
6. **After first batch fires**: send `/callsheet` to @CCagentsHQ_bot — call the list within the hour

## Files changed this session

- `orchestrator/newsletter_editorial_input.py`
- `docs/roadmap/atlas.md`
- `skills/outreach/SKILL.md`
- `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md`
- `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/project_sw_pipeline_state_2026-05-09.md`

## Commits

- `a86c179` — fix(newsletter): make get_reply_for_week non-fatal + run migration 006
- `b93c834` — docs(atlas): mark newsletter_editorial_input fix done 2026-05-09
- `ebcd77e` — chore(shutdown): atlas roadmap + outreach skill updates 2026-05-10
