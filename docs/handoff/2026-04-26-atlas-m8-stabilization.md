# Session Handoff -- Atlas M8 Stabilization -- 2026-04-26

## TL;DR

Long session that started with a completely broken dashboard (PIN bypassed, all cards stuck on "Loading...") and ended with a fully functional ops dashboard at agentshq.boubacarbarry.com/atlas. Root cause was a CSS cascade bug: `#dashboard { display: flex }` in atlas.css overrode the HTML `hidden` attribute, making the dashboard visible without auth and preventing `startPolling()` from ever being called. Along the way: content board wired to real Notion data, spend pacing shows week/month totals and last-spend-day fallback, cost_ledger Postgres table created, agentsHQ State card renamed, M9 Atlas Chat milestone written, and a dozen deploy pitfalls documented.

## What was built / changed

**Bug fixes:**
- `thepopebot/chat-ui/atlas.css` line 19: `[hidden] { display: none !important; }` -- fixes CSS cascade overriding `hidden` attribute (root cause of both PIN bypass + cards never loading)
- `thepopebot/chat-ui/atlas.js`: `TOKEN_TTL_MS` restored to 4 hours (was 0 as failed workaround)
- `thepopebot/chat-ui/atlas.js`: `apiFetch()` throws on any non-2xx, not just 401
- `thepopebot/chat-ui/nginx.conf`: `Cache-Control: no-store` on `/atlas/` location block
- `/root/agentsHQ/thepopebot/.env`: `ORCHESTRATOR_API_KEY` fixed to match orc-crewai's key (`4a4688f6...`); event-handler restarted
- `/root/agentsHQ/.env`: `FORGE_CONTENT_DB=339bcf1a-3029-81d1-8377-dc2f2de13a20` added
- `orchestrator/atlas_dashboard.py`: fixed `router_log` column names (no `fallback`/`raw_input`), `task_outcomes` columns (`ts_started`/`crew_name`/`success`/`result_summary`), `NotionClient` kwarg `filter_obj` not `filter`, Platform field is `multi_select`

**Features:**
- Content Board: 3 sections (Past Due / Upcoming 7 days / Recently Posted last 3); correct Notion DB + field parsing
- Spend Pacing: This Week + Month to Date rows; "MM/DD (last spend)" when today=$0
- `cost_ledger` Postgres table created with indexes
- `GET /atlas/ledger?days=30` + `POST /atlas/ledger` endpoints in `orchestrator/app.py`
- `get_cost_ledger()` + `add_cost_ledger_entry()` in `orchestrator/atlas_dashboard.py`
- agentsHQ State card renamed from "Atlas State"
- Daily Cap removed from agentsHQ State card
- compass.svg pushed to VPS (was missing -- caused broken favicon + topbar icon)
- M9 Atlas Chat milestone written to `docs/roadmap/atlas.md`
- Version query string on atlas.js/css (`?v=20260426e`) for cache busting

**Files changed:**
- `thepopebot/chat-ui/atlas.html` -- agentsHQ State rename, version bump, compass favicon
- `thepopebot/chat-ui/atlas.css` -- `[hidden]` fix, no-cache, past-due style, content-date style
- `thepopebot/chat-ui/atlas.js` -- all render logic for content/spend/state cards
- `thepopebot/chat-ui/nginx.conf` -- no-store cache headers
- `thepopebot/chat-ui/compass.svg` -- new file pushed to VPS
- `orchestrator/atlas_dashboard.py` -- all fetchers rewritten/fixed + cost_ledger functions
- `orchestrator/app.py` -- `/atlas/ledger` GET+POST endpoints
- `docs/roadmap/atlas.md` -- M9 milestone + 2026-04-26 session log
- `docs/handoff/2026-04-26-atlas-m8-stabilization.md` -- this file

## Decisions made

- **agentsHQ State not Atlas State:** the card monitors agentsHQ the system, not Atlas the dashboard. Renamed.
- **OpenDyslexic reverted:** Boubacar tried it, decided it was "too much." Back to Fraunces + Atkinson Hyperlegible + IBM Plex Mono.
- **cost_ledger approach:** use `llm_calls.project` for engagement tracking now; `cost_ledger` for non-LLM costs (Blotato, Notion, subscriptions); customer column ready for first real engagement.
- **M9 Atlas Chat is HIGH PRIORITY:** Boubacar explicitly called it out. Do ASAP after M8 is stable.
- **Daily Cap stays in Spend Pacing only** (removed from agentsHQ State -- redundant).
- **Last spend day fallback:** when today=$0, show most recent day with spend (up to 7 days back) labeled "MM/DD (last spend)" -- always show real numbers.

## What is NOT done (explicit)

- `POST /chat` to orc-crewai returns 404 -- this is the Atlas Chat iframe trying to call the orchestrator. Intentionally left; M9 scope.
- "Last Autonomous Action" hero tile shows "self-test ok" -- `task_outcomes` not yet populated by real autonomous runs (data will accumulate naturally).
- Spend card has no drill-down into the ledger table (shows totals only). Deferred -- can add as a future card or modal.
- VPS orphan archive at `/root/_archive_20260421/` sunset date was 2026-04-28 -- delete if nothing broke.
- atlas-preview.html is localhost-only (relative paths) -- kept for dev use only, not deployed.

## Open questions

- None blocking. M9 design is the next decision point.

## Next session must start here

1. Check if Monday 2026-04-27 07:00 MT auto-publish fired: `ssh root@agentshq.boubacarbarry.com 'docker logs orc-crewai --since 24h | grep -E "auto_publisher|publish|Posted"'`
2. Check `docs/handoff/2026-04-27-atlas-m1-verification.md` if the Monday verification routine fired
3. Read `docs/roadmap/atlas.md` Session-Start Cheat Block before anything else
4. Start M9 Atlas Chat design/spec (HIGH PRIORITY -- Boubacar wants full LLM-grade chat in the Atlas panel)
5. Delete `/root/_archive_20260421/` on VPS if past 2026-04-28 and nothing broke

## Files changed this session

```
thepopebot/chat-ui/
  atlas.html          -- agentsHQ State rename, version bust, compass favicon
  atlas.css           -- [hidden] fix, no-cache, .past-due, .content-date
  atlas.js            -- content/spend/state renderers, TOKEN_TTL_MS, apiFetch throw
  atlas-preview.html  -- chip spans removed (localhost dev only)
  nginx.conf          -- Cache-Control: no-store on /atlas/
  compass.svg         -- new, pushed to VPS

orchestrator/
  atlas_dashboard.py  -- all 8 fetchers fixed + cost_ledger functions
  app.py              -- /atlas/ledger GET+POST endpoints

docs/
  roadmap/atlas.md    -- M9 milestone + 2026-04-26 session log
  handoff/2026-04-26-atlas-m8-stabilization.md  -- this file

VPS only (not in git):
  /root/agentsHQ/.env           -- FORGE_CONTENT_DB added
  /root/agentsHQ/thepopebot/.env -- ORCHESTRATOR_API_KEY fixed, FORGE_CONTENT_DB added
```
