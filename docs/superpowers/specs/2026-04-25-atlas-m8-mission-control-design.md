---
codename: atlas
milestone: M8
title: Atlas Mission Control - live ops dashboard at /atlas
status: approved-after-sankofa
date: 2026-04-25
owner: Boubacar Barry
sankofa: docs/superpowers/specs/2026-04-25-atlas-m8-mission-control-design.md (council in conversation 2026-04-25)
revisions_after_sankofa:
  - dropped external proof-point framing; M8 is internal-only
  - replaced Roman-numeral chips with per-card icon slot
  - added flock on autonomy_state.json for browser-driven action concurrency
  - kept action layer (sized at 75 min after handler audit)
  - read-only ships first within the same milestone; actions wired in block 4
revisions_after_topology_audit:
  - 2026-04-25, before writing-plans hand-off
  - original spec assumed FastAPI would host /atlas as a Jinja-templated HTML route
  - actual topology: /chat is a static page in thepopebot/chat-ui/ served by nginx; FastAPI only exposes /api/orc/* JSON endpoints (Traefik strips the /api/orc prefix)
  - corrected approach: /atlas is a sibling static page in thepopebot/chat-ui/, JS calls JSON endpoints, no template engine added
  - downstream effect: iframe embed risk drops from Medium to Low (same-origin same-host); no new Python dependency; deploy already wired via thepopebot/chat-ui/** path filter in deploy-agentshq.yml
---

# Atlas M8: Mission Control

## One-line

A gated, live, single-page dashboard at `agentshq.boubacarbarry.com/atlas` that shows what the autonomy layer is doing, lets Boubacar take safe actions on it from a browser anywhere, and embeds `/chat` so the page is the one place to operate Atlas.

## Why now

Boubacar has had "Usage dashboard - HTML page on VPS showing OpenRouter spend + tasks run per day" sitting in `project_task_backlog.md` since 2026-04-16. Two adjacent items have been added but unbuilt: "Sankofa Council Phase 2 - cost/token tracking dashboard" and "Real-time agent activity streaming." The reason it has slipped is that each week brought a higher-revenue task. It will keep slipping unless it lands on the atlas roadmap as a real milestone.

The data layer is already in place. Phases shipped 2026-04-20 to 2026-04-25 wrote every backend table M8 needs. Today the only ways to inspect Atlas are SSH + `docker logs`, or six different Telegram commands. That gap is what RUBRIC (RoboNuggets, reviewed earlier this session) is pointing at; M8 is our answer to the same gap, built on data we already own.

M8 is internal-only. A sanitized public variant for sharing alongside Catalyst Works is explicitly out of scope; if Boubacar ever wants it, it becomes its own milestone with its own threat model. The visual bar is still high (it's the surface he'll be on every day), but the audience is one person.

## Done definition

A single page at `agentshq.boubacarbarry.com/atlas` that:

1. **Reads live** - six cards show real data from `llm_calls`, `router_log`, `approval_queue`, `task_outcomes`, `autonomy_state.json`, `error_monitor.log`, and the Notion Content Board, refreshed every 30 seconds.
2. **Acts safely** - Boubacar can toggle Griot, toggle dry-run, approve/reject queue items, and reply `posted`/`skip` to the daily publish brief, all from the page. Kill switch deliberately omitted from the page (Telegram only).
3. **Hosts chat** - the existing `/chat` UI is embedded in a card. The page is the one place to see + interact with Atlas.
4. **Is gated** - same JWT-PIN flow as `/chat`. No anonymous access.
5. **Is mobile-readable** - desktop-first, but collapses cleanly to a single column at <720px so phone glance-checks work.
6. **Looks like Boubacar** - Catalyst Console visual treatment (T4): near-black with graphite-blue undertone, terracotta-orange `#FF6B35` as the single signature accent, museum-bronze + lapis + verdigris support palette, dyslexia-safe typography (Atkinson Hyperlegible body + Fraunces display + IBM Plex Mono data).

## What's out of scope (intentional)

Captured here so we don't relitigate or scope-creep mid-build.

- **Kill switch in the browser** - too risky for a one-click click-through. Stays Telegram-only (`/pause_autonomy`).
- **Historical timeline / charts beyond 7-day spend** - M8 is a now-state snapshot. Trend charts come later (M11+ if ever).
- **Alerts / notifications from the dashboard** - error_monitor.sh already pushes Telegram. Don't double-channel.
- **Multi-user / role-based access** - single user (Boubacar). Same JWT-PIN posture as `/chat`.
- **Dark/light mode toggle** - Catalyst Console is dark by design, full stop.
- **Per-card settings or layout customization** - RUBRIC's "ask your agent to add tabs" pattern is good for a static-files product; for a live-data app it just creates surface to break. Layout is fixed in M8; we ship what's in the spec.
- **Mobile-app-quality interactions** - gestures, swipe-to-approve, pull-to-refresh. Desktop is the primary surface.
- **Replacement of `/chat`** - `/chat` keeps its standalone URL and continues to work independently. M8 embeds it; it does not own it.

## Architecture

### Surface

**Topology (verified 2026-04-25):** Two containers behind one Traefik on `agentshq.boubacarbarry.com`:
- `thepopebot-chat-ui` (nginx) serves `/chat/*` from `thepopebot/chat-ui/` static files. M8 adds `/atlas/*` to the same container , sibling static page, same nginx config (one new `location` block).
- `orc-crewai` (FastAPI) serves `/api/orc/*` (Traefik strips the `/api/orc` prefix; the app sees `/run`, `/chat-token`, etc.). Port 8000 bound to localhost only.

| Component | Tech | Notes |
|---|---|---|
| Page | Static HTML + CSS + JS in `thepopebot/chat-ui/atlas.html` | Mirrors how `/chat` is served. No template engine, no Python rendering. |
| Card data endpoints | FastAPI JSON endpoints, gated by `verify_chat_token` | one per card: `GET /api/orc/atlas/state`, `/atlas/queue`, `/atlas/content`, `/atlas/spend`, `/atlas/heartbeats`, `/atlas/errors`, `/atlas/hero` |
| Action endpoints | FastAPI POST endpoints, gated by `verify_chat_token` | `POST /api/orc/atlas/toggle/griot`, `/atlas/toggle/dry_run`, `/atlas/queue/{id}/approve`, `/atlas/queue/{id}/reject`, `/atlas/publish/posted`, `/atlas/publish/skip` |
| Refresh model | Vanilla JS `setInterval` polling 30s per card | Each card has its own fetch + render function; one slow endpoint doesn't block the others. No htmx dependency needed (was overkill given the static-page pattern). |
| Auth | JWT issued by `POST /api/orc/chat-token` (existing PIN flow). Stored in localStorage, sent as `Authorization: Bearer <jwt>` on every fetch. | Reuse `verify_chat_token` dependency from `app.py:147`. Same posture as `/chat`. |
| Chat embed | Direct anchor + iframe to `/chat` inside the chat card | Same Traefik host, same nginx, same auth , no cross-origin issues. iframe risk neutralized vs original spec. |

### Data sources (all already exist, verified Apr 24-25)

| Card | Source | Where |
|---|---|---|
| Atlas State | `autonomy_state.json` (kill, griot, dry_run, spend cap) | `/root/agentsHQ/data/autonomy_state.json` on VPS |
| Approval Queue | `approval_queue` table where `status='pending'` order by `ts_created` desc | `005_autonomy_memory.sql` |
| Content Board | Notion Content Board, this-week filter | `NOTION_CONTENT_BOARD_DB_ID` |
| Spend 7d | `llm_calls` rolled up by day + by `agent_name` | `001_llm_calls.sql` + `004_autonomous_flag.sql` |
| Heartbeats | `heartbeat.py` registered wakes + last-fire timestamps | in-process state; expose via `/heartbeat_status` payload |
| Errors | tail of `/var/log/error_monitor.log` + `router_log` rows where `fallback=true` last 24h | shell read + `003_router_log.sql` |
| Hero · System Status | derived: AND of (heartbeats green, errors=0, spend cap healthy, nsync clean) | computed in app |
| Hero · Last Action | latest `task_outcomes` row | `005_autonomy_memory.sql` |
| Hero · Next Fire | earliest scheduled wake from `heartbeat.py` registry | in-process |
| Hero · Spend Pacing | `llm_calls` 7d total vs configured weekly budget in `autonomy_state.json` | both already wired |

No new tables. No migrations. Read-only on Postgres for everything except the 6 action endpoints, which use the same write paths Telegram handlers already use (so all guardrails carry over for free).

### Action contract (the "Standard" bundle from brainstorm)

Every action endpoint:
1. Reuses the same handler the corresponding Telegram command uses (no parallel implementation)
2. Returns the **updated card data dict** so the JS render function swaps the card in place after the action - no full page reload
3. Logs the action to `router_log` with `task_type='atlas_dashboard_action'` for audit
4. Hits the same autonomy guard rails (`autonomy_guard.py`) - if Griot is killed, the toggle still updates the state file but the next tick respects the kill

### File layout (corrected after topology audit)

```
orchestrator/
  app.py                          # +13 api endpoints (no page route - page is static)
  atlas_dashboard.py              # NEW - data fetchers, one function per card; pure (no FastAPI imports)
  tests/
    test_atlas_dashboard.py       # NEW - unit tests for each fetcher

thepopebot/chat-ui/
  atlas.html                      # NEW - static page (HTML + inline CSS for fast first paint)
  atlas.css                       # NEW - Catalyst Console theme, ~600 LOC (linked from atlas.html)
  atlas.js                        # NEW - PIN gate (reuses /chat pattern), 7 fetcher fns, render fns, action wiring
  cw-mark.svg                     # placeholder; Boubacar to swap his CW logo
  nginx.conf                      # MODIFY - add `location /atlas` block (mirrors `/chat`)
```

Total new code:
- One Python module (`atlas_dashboard.py`, ~250 LOC) + 13 thin FastAPI handler functions in `app.py`
- One HTML shell, one CSS, one JS in `thepopebot/chat-ui/`
- One nginx config addition (~6 lines)

The CSS is the longest file because the visual treatment is bespoke; everything else is glue. **No new Python dependencies.** No Jinja2 added. No `templates/` or `static/` directory created. Auto-deploy already covers both `orchestrator/**` and `thepopebot/chat-ui/**` via the existing GitHub Actions workflow.

### Visual system (locked from mockup v4 / T4)

**Palette - Catalyst Console**
- Background: `#08090C` near-black with graphite-blue undertone
- Card: `#10131A` with 1px inner bronze hairline `rgba(193,154,107,0.06)`
- Signature accent: terracotta-orange `#FF6B35` (the "Boubacar color" - every primary glow, every "you" message)
- Brass `#C19A6B`, lapis-tarnished `#4A7A8C`, verdigris `#6F9B6E`, bronze `#B87333`, fired-clay rose `#C25A6E`
- Bone ink: `#F4EEE0` for primary text, `#B9B09A` for secondary, `#76705F` for tertiary
- Status: green `#6F9B6E` (verdigris), amber `#C19A6B` (brass), rose `#C25A6E`

**Typography**
- Body: Atkinson Hyperlegible 400/700 (Braille Institute, designed against letter confusion; floor 15px, line-height 1.5+)
- Display: Fraunces variable (opsz, SOFT, wght axes) for H1, card titles, body row text in queue/content/chat
- Mono: IBM Plex Mono 400/500/600 for all numbers, labels, codes, timestamps
- OT features always on: `tnum` (tabular figures so columns align), `zero` (slashed zero so it never confuses with O)
- No italics for emphasis (BDA dyslexia rule); use weight or color
- Concrete sizes - H1 34px, card H2 22px, body 15px, hero number 40px, mono label 11px with +10% tracking

**Layout (locked, hybrid of A + B from earlier brainstorm)**
- Topbar: brand mark (CW logo placeholder for now) + H1 "Atlas Mission Control" + sync/health badges (top right)
- Hero strip: 4 stat tiles - System Status (traffic light + word) · Last Autonomous Action · Next Scheduled Fire · Spend Pacing
- Main grid: 3 columns × 2 rows of cards on the left, 1 full-height chat card docked right (4-column desktop layout: 1fr 1fr 1fr 400px)
- Cards in order: Atlas State (i), Approval Queue (ii), Content Board (iii), Spend (iv), Heartbeats (v), Errors (vi), Chat (vii)
- Each card has a 5px left border in its claimed color, a Roman-numeral chip in its accent, and the second word of its title in the same color
- Bottom-right of every card: subtle bronze hairline (replaces v1/v2 bogolan dot pattern; T4 swaps decorative pattern for tactile inlay feel)
- Topbar runner: single 1px bronze hairline, 12-88% horizontal fade, beneath the topbar

**Brand mark slot**
- 56px square hot-swappable container with class `.brand-mark`
- Default: brass-coin "A" with recessed inner ring (current placeholder)
- Replacement plan: drop CW logo SVG into `static/atlas/cw-mark.svg`; CSS already handles padding and shadow
- Decision deferred (Boubacar's call: refine current mark, design a new one, or use CW logo)

**Mobile responsive**
- ≤1180px: grid collapses to 2 columns, chat card spans full width, hero collapses to 2 columns
- ≤720px: everything single-column, padding tightened, H1 28px, hero number 32px, spend 36px

### Non-functional requirements

- **Latency:** each card endpoint < 200ms p95. Spend rollup is the slowest; if it crosses 200ms, cache for 30s in-process.
- **Refresh load:** 7 cards × 1 page open × 1 refresh/30s = 14 req/min. Negligible. Even 5 tabs open = 70 req/min, also fine.
- **Failure mode:** if any card endpoint errors, that card shows a small "couldn't reach data - retrying" line in the affected card; the rest of the page continues. No full-page error states.
- **Auth fail:** identical behavior to `/chat` - redirect to PIN prompt.
- **No write batches, no transactions across cards** - each action endpoint is independent and idempotent.

## Build sequence

Estimated 4.75 hours after Sankofa-driven scope cuts. Read-only ships at end of block 3; action layer is block 4. Both fit in M8.

### Block 1: backend data path (≈2h)

1. Create `orchestrator/atlas_dashboard.py` with 7 read functions (one per card + hero rollup), each returning a plain dict ready to JSON-serialize
2. Wire 7 GET endpoints in `app.py` under `/atlas/*`, each gated by `Depends(verify_chat_token)` and returning the dict from step 1 as JSON
3. Add unit tests in `orchestrator/tests/test_atlas_dashboard.py` for each fetcher (mocked DB rows, mocked Notion responses, mocked autonomy_state.json)
4. Smoke test: hit each endpoint with curl + a fresh `/chat-token` JWT; verify JSON shape matches what the JS will consume

### Block 2: visual shell (≈2h)

1. Add `location /atlas { ... }` block to `thepopebot/chat-ui/nginx.conf` (mirrors `/chat`)
2. Create `thepopebot/chat-ui/atlas.html` , semantic HTML for topbar + 4-tile hero + 6-card grid + chat-slot card. PIN gate copied from `index.html` (the `/chat` UI)
3. Create `thepopebot/chat-ui/atlas.css` with the Catalyst Console (T4) palette + type system from the locked v4 mockup
4. Local test: serve `thepopebot/chat-ui/` with `python -m http.server` against a local orchestrator; confirm visual matches mockup v4

### Block 3: client polling + chat embed (≈45 min)

1. Create `thepopebot/chat-ui/atlas.js`: PIN-gate function (lifted from `/chat`), 7 fetcher functions, 7 render functions, one `setInterval(refreshAll, 30_000)` after auth
2. Each render function targets one `<section data-card="...">` and rebuilds its inner HTML from the JSON; per-card try/catch so one failure doesn't break the page
3. Add `<iframe src="/chat" loading="lazy">` inside the chat card; verify the JWT in localStorage carries through (same origin)
4. Visually confirm one full 30s tick cycle in the browser console (no errors, all 7 cards refresh)

### Block 4: action layer + polish (≈75 min)

Handler audit (during this conversation) confirmed `handlers_commands.py` and `handlers_approvals.py` already expose pure `(text, chat_id, ...)` functions. No fake Telegram Update needed; no handler refactor.

1. Add `flock` advisory lock helper around `autonomy_state.json` reads/writes (~6 lines)
2. Wire 6 POST endpoints, each calling the existing primitive directly:
   - `/atlas/api/toggle/griot` -> `AutonomyGuard.set_crew_enabled('griot', bool)`
   - `/atlas/api/toggle/dry_run` -> new `AutonomyGuard.set_dry_run(bool)` setter (~8 lines added to guard)
   - `/atlas/api/queue/{id}/approve` -> `approval_queue.approve(qid)`
   - `/atlas/api/queue/{id}/reject` -> `approval_queue.reject(qid)`
   - `/atlas/api/publish/posted` -> `handle_publish_reply("posted", chat_id, ...)`
   - `/atlas/api/publish/skip`   -> `handle_publish_reply("skip", chat_id, ...)`
3. Each endpoint logs to `router_log` with `task_type='atlas_dashboard_action'` and returns the updated card data dict (same shape as the GET); the JS calls the matching render function to swap the card in place
4. Empty-state fragments (no pending queue, no scheduled posts this week, no errors)
5. Mobile screenshot pass at 375px width

## Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Action endpoint accidentally bypasses `autonomy_guard.py` | Low | All actions call the same primitives (`AutonomyGuard`, `approval_queue.approve/reject`, `handle_publish_reply`) Telegram already uses. Audited 2026-04-25. |
| `autonomy_state.json` torn writes when browser action coincides with heartbeat tick | Medium | `flock` advisory lock added in block 4 (~6 lines). Council-flagged. |
| iframe of `/chat` breaks | Low (was Medium pre-audit) | Topology audit 2026-04-25 confirmed `/chat` and `/atlas` will be served by the same nginx container at the same Traefik host, sharing the same JWT in localStorage. No cross-origin, no SameSite issue. iframe is the simplest path; if cosmetic friction appears, swap for a tab-style "Switch to chat" link that opens `/chat` in same window. |
| Spend rollup is slow (`llm_calls` is the largest table) | Low | Indexed on `(ts DESC)` and `(agent_name, ts DESC)` per `001_llm_calls.sql`. 7-day rollup tested in dev <50ms. Fallback is 30s in-process cache. |
| Polling thunders on multiple tabs | Low | 7 cards × 30s = ~14 req/min per tab. FastAPI handles trivially. Page Visibility API used in `atlas.js` to pause polling when tab hidden. |
| CSS bloat (T4 is bespoke) | Low | Single file, ~600 LOC, ~12KB gzipped. No Tailwind, no framework, no build step. |
| New surface for unauthorized access | Low | Reuses `/chat` JWT-PIN exactly; no separate auth code path |
| Em-dash sneaks into UI text | Already happened in this session | New memory `feedback_em_dash_in_ui_text.md`; pre-deploy grep step in block 4 |
| First-week regret about action layer being underbuilt or overbuilt | Medium | Block 4 ends with a 14-day usage check. If actions go unused, mark them descoped. If new ones are wanted, M9. |

## Open decisions (post-Sankofa)

1. **Brand mark** - refine current brass coin, design a new mark, or drop CW logo SVG. Default: ship with placeholder; hot-swappable slot wired so swap is one file.
2. **Card chips** - Roman numerals (i, ii, iii) killed per Council; Outsider voice flagged as decorative-not-informational. Slot now holds a per-card icon (small bronze-ringed monoline). Boubacar to approve icon set or drop.
3. **Hero "Last Autonomous Action"** linkability deferred to M11+.

## Sankofa output (recorded for posterity)

Five voices ran 2026-04-25. Verdict: cut external-proof-point framing, ship internal-only, build read-only first inside the same milestone, action layer fits in block 4 because handlers are already pure. Two Council recommendations folded in (file lock, kill Roman numerals). Two Council recommendations parked as future milestones (outcomes-quality card, chat-as-primary reframe).

## Cross-references

- **Roadmap:** `docs/roadmap/atlas.md` (M8 entry to be added after Sankofa)
- **Memory:** `project_autonomy_layer.md`, `project_token_economy.md`, `feedback_no_em_dashes.md`, `feedback_em_dash_in_ui_text.md`, `feedback_always_show_visuals.md`
- **Modules:** `orchestrator/app.py`, `orchestrator/autonomy_guard.py`, `orchestrator/heartbeat.py`, `orchestrator/handlers_approvals.py`, `orchestrator/handlers_commands.py`
- **DB:** `001_llm_calls.sql`, `003_router_log.sql`, `004_autonomous_flag.sql`, `005_autonomy_memory.sql`
- **Mockups:** `workspace/atlas-m8-mocks/v4.html` (theme T4 - locked)
- **Typography research:** in-session 2026-04-25; sources listed at the end of the spec

## Typography sources (for the record)

- Braille Institute - Atkinson Hyperlegible design rationale (brailleinstitute.org)
- Shaver-Troup & Renne 2019 - Lexend reading-fluency study (Vision Council)
- British Dyslexia Association - Style Guide 2023 (12-14pt minimum, 1.5 line height, weight ≥ 400, no italics for emphasis)
- WCAG 2.1 SC 1.4.12 - Text Spacing
- Adobe - Source Sans 3 specimen
- IBM - Plex specimen
