# Session Handoff — Atlas M26 Live Roadmap DB — 2026-05-10

## TL;DR

Big UX + infrastructure session. Roadmap dashboard page went through multiple design iterations (lighter theme, 17px fonts, Notes column, unified nav bar, Daily Cap fix). Then built Atlas M26 end-to-end: milestones table in orc-postgres, flip_milestone() single write path, Telegram /shipped + /milestones commands, webchat "mark shipped" intent, roadmap.html live DOM rendering from API. Sankofa Council ran on DB vs markdown architecture — DB won for concurrent agent writes. All 70 milestones seeded, 7 tests pass, VPS verified.

## What was built / changed

**Roadmap page UX (thepopebot/chat-ui/):**
- `roadmap.html` — lighter bg (#0E1117), 17px base font, Notes column always visible (min-width 960px table), tab navigation reordered Dashboard→Roadmap→Spend, ctx blocks use surface2
- `atlas.html` — replaced inline nav links with 3-tab nav (Dashboard active)
- `cost.html` — replaced back-link with 3-tab nav (Spend active), font bumped to 17px
- `atlas.js` — Daily Cap now uses `d.daily_budget` (prorated monthly) not `today.cap_usd` ($1 guard kill-switch)

**Atlas M26 — Live Roadmap DB:**
- `scripts/migrations/009_milestones.sql` — milestones table DDL + indexes + comments
- `scripts/seed_milestones.py` — idempotent 70-row seed across 5 roadmaps. Run via `docker exec orc-crewai python scripts/seed_milestones.py`
- `scripts/check_routing_gaps.py` — added `--json` flag (was silently failing; fallback was hardcoded 11)
- `orchestrator/atlas_dashboard.py` — `_VALID_MILESTONE_STATUSES`, `flip_milestone()`, extended `get_roadmap_metrics()` with milestones array + 30s cache, cache vars `_roadmap_metrics_cache/_ts/_TTL`
- `orchestrator/handlers_commands.py` — `_cmd_shipped`, `_cmd_milestones` added + in `_COMMANDS`
- `orchestrator/handlers_chat.py` — `_SHIP_PATTERNS` + `_is_milestone_ship` block before `_is_read_intent`
- `thepopebot/chat-ui/roadmap.html` — `renderMilestoneRows()` + `STATUS_BADGE_MAP` + `STATUS_DS_MAP` + `applyMetrics()` tail calls render
- `tests/test_milestone_db.py` — 4 unit tests for flip_milestone (happy, not-found, invalid-status, notes)
- `tests/test_routing_gaps_json.py` — 3 unit tests for --json flag

**VPS state:**
- Migration 009 ran: milestones table exists
- 70 rows seeded: atlas 23, compass 11, echo 7, harvest 17, studio 12
- M26 marked shipped in DB via flip_milestone('atlas','M26','shipped')
- All services restarted, healthchecked

## Decisions made

- **DB over markdown for milestones** — Sankofa Council unanimous. Concurrent agent writes → Postgres row locks, not git conflicts on .md files.
- **flip_milestone() is the single write path** — Telegram, webchat, agents all call it. Never write directly to milestones table from handlers.
- **roadmap.html static rows = fallback only** — if API returns milestones, DOM render replaces them. If API fails, static HTML remains visible.
- **No innerHTML anywhere in roadmap.html** — DOM methods only. Badge labels from trusted internal lookup table (STATUS_BADGE_MAP).
- **Daily Cap display** — always use `daily_budget` (MONTHLY_BUDGET_USD / days_in_month), never `cap_usd` (the $1 autonomy guard kill-switch).
- **System status AMBER** = spend 401% of daily budget ($7.77 vs $1.94/day). Not an error condition — active dev session. `MONTHLY_BUDGET_USD = 60.0` in atlas_dashboard.py.

## What is NOT done

- **Compass M6-audit** — queued, first auto-run 2026-05-16. No action needed.
- **Chairman M5 enable** — has 629 task_outcomes (gate cleared), still `enabled=false dry_run=true`. Needs explicit enable in autonomy config. One targeted session.
- **Rod follow-up (Harvest R1)** — hold ends 2026-05-14. One bump allowed then drop. All R3+ gates on R1 closing.
- **catalystworks.consulting v3 Tier 2 (R1e)** — social proof strip + 5 SEO pages. Due 2026-05-15.
- **M25 Event-Driven Message Bus** — gates on M23+M24 stable 30 days → unblocks 2026-06-10.

## Open questions

- Should `MONTHLY_BUDGET_USD` be raised from $60 to $100+ to stop amber on active dev days? Currently $7.77/day triggers amber because daily budget = $1.94.
- Chairman M5: enable now (629 outcomes >> 7 threshold) or wait for another Monday cycle first?

## Next session must start here

1. Check `/atlas/roadmap` live — confirm milestone rows rendering from DB (not static HTML). Look for M26 row showing SHIPPED badge.
2. Send `/milestones atlas` in Telegram — verify list returns correctly from DB.
3. Decide: enable Chairman M5 now (`flip_milestone('atlas','M5','shipped')` then update autonomy config `enabled=true`).
4. Start R1e Tier 2 (catalystworks.consulting social proof + SEO) — due 2026-05-15.
5. Rod bump on 2026-05-14 if no reply.

## Files changed this session

```
orchestrator/
  atlas_dashboard.py        — flip_milestone(), get_roadmap_metrics() + cache
  handlers_commands.py      — /shipped, /milestones
  handlers_chat.py          — mark-shipped intent
  app.py                    — (no new routes, roadmap-metrics already existed)

scripts/
  migrations/009_milestones.sql
  seed_milestones.py
  check_routing_gaps.py     — --json flag + stderr fix

tests/
  test_milestone_db.py      — 4 tests
  test_routing_gaps_json.py — 3 tests

thepopebot/chat-ui/
  roadmap.html              — live render + UX fixes
  atlas.html                — 3-tab nav
  cost.html                 — 3-tab nav, 17px font
  atlas.js                  — daily_budget fix

docs/roadmap/atlas.md       — M26 session log
docs/handoff/               — this file
```
