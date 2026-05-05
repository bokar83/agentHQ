# Session Handoff - Spend Tracking + Atlas Cost Report - 2026-05-05

## TL;DR

Built end-to-end spend tracking for all 3 paid API providers (OpenRouter, ElevenLabs, Kie) and a standalone `/atlas/cost` report page with Chart.js graphs. Fixed `/cost` Telegram command to use OpenRouter as ground truth (was showing $14 from llm_calls; actual MTD = $89). ElevenLabs spend now logged per TTS render. Kie daily credit snapshots fire tonight at 23:55 MT for the first time.

## What was built / changed

- `orchestrator/studio_voice_generator.py` -- `_log_elevenlabs_spend()` called after each `_elevenlabs_tts()` call; writes to `cost_ledger` table with tool=elevenlabs_tts, $0.0003/char rate
- `orchestrator/atlas_dashboard.py` -- `_fetch_elevenlabs_spend()` for dashboard card; `get_cost_report()` for /atlas/cost endpoint; ElevenLabs subsection in `get_spend()` return
- `orchestrator/spend_snapshot.py` -- `kie_billing` table creation; `take_kie_snapshot()` (daily Kie credit balance); `get_kie_historical()`; `_fetch_elevenlabs_mtd()` added to Telegram summary
- `orchestrator/handlers_commands.py` -- `/cost` rewritten to lead with OR live figures + EL + Kie balance; `/spend` command deleted (was duplicate of `/autonomy_status`)
- `orchestrator/app.py` -- `GET /atlas/cost?days=N` endpoint wired
- `thepopebot/chat-ui/cost.html` -- standalone spend report page: 7 summary tiles, OR bar chart, EL bar chart, Kie credit line chart, data tables, range selector 7/30/60/90d, PIN auth
- `thepopebot/chat-ui/nginx.conf` -- `location = /atlas/cost` using root+try_files pattern
- `thepopebot/chat-ui/atlas.html` -- "Spend Report" link added to topbar
- `thepopebot/chat-ui/atlas.js` -- ElevenLabs TTS subsection added to spend card renderer

## Decisions made

- **OpenRouter = LLM ground truth.** `llm_calls` table ($14 MTD) only captures direct Anthropic SDK calls. OR actual = $89 MTD. All reporting leads with OR.
- **ElevenLabs has no billing API** -- per-render logging to `cost_ledger` IS the historical record. No snapshot needed.
- **Kie has no spend API** -- only credit balance. Daily snapshot captures burn rate over time. Per-render USD not trackable yet.
- **`/spend` Telegram command deleted** -- exact duplicate of `/autonomy_status`. One command per function.
- **nginx exact-match single file pattern** -- `root + try_files /filename.html` not `alias`. Burned 30 min on this.

## What is NOT done (explicit)

- **Kie per-render spend** -- no `media_generations` table exists; credits are opaque units not USD. Left as "credits remaining" only. Future: add table when Kie exposes USD pricing.
- **OR historical charts sparse** -- only 2 days of `provider_billing` snapshots exist. Charts fill automatically as daily tick runs. No action needed.
- **ElevenLabs table empty** -- no Studio renders have fired yet. Will populate on first video render.

## Open questions

- None blocking. All 3 providers tracked. Page live and verified 200.

## Next session must start here

1. Nothing spend-related is blocked -- charts fill passively.
2. If Studio renders a video, check `/atlas/cost` ElevenLabs section populated correctly.
3. After 2026-05-06 23:55 MT, Kie credit snapshot #1 fires -- verify row in `kie_billing` via `docker exec -w /app/orchestrator orc-crewai python3 -c "from spend_snapshot import get_kie_historical; print(get_kie_historical())"`.
4. Hotel Club de Kipe rebuild is next major project -- see `docs/handoff/hotelclubkipe-rebuild-prompt.md`. Run /website-teardown + /design-audit before writing a line of code.

## Files changed this session

```
orchestrator/
  atlas_dashboard.py        -- _fetch_elevenlabs_spend, get_cost_report, EL in get_spend
  handlers_commands.py      -- /cost rewrite, /spend deleted
  spend_snapshot.py         -- kie_billing table, take_kie_snapshot, get_kie_historical, EL MTD in tick
  studio_voice_generator.py -- _log_elevenlabs_spend added
  app.py                    -- GET /atlas/cost endpoint

thepopebot/chat-ui/
  cost.html                 -- new spend report page (Chart.js)
  atlas.html                -- Spend Report link in topbar
  atlas.js                  -- ElevenLabs TTS subsection in renderSpend
  nginx.conf                -- /atlas/cost route

deleted:
  thepopebot/chat-ui/atlas-cost.html  -- duplicate of cost.html
```
