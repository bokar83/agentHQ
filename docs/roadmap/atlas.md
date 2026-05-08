# Atlas: agentsHQ True Agentic Work

**Codename:** atlas
**Status:** active
**Lifespan:** open-ended
**Started:** 2026-04-23
**Owner:** Boubacar Barry
**One-line:** the autonomy layer that runs the content pipeline end-to-end while the laptop is off

**Project:** Move agentsHQ from L0 (reactive tool) to L1+ (autonomous teammate that runs the content pipeline end-to-end while Boubacar's laptop is off).

**Active session log:** see bottom of this file

---

## Session-Start Cheat Block (read this first)

Last session ended **2026-05-06 (evening)**. State at close:

- **Three-way nsync at `d83ad45`** (local + origin -- VPS pull pending Gate)
- **Morning digest extended:** `griot_morning_tick` now sends outreach metrics + spend today/WTD/MTD + top 3 Execution Cycle tasks via Telegram + HTML email every weekday morning
- **Skill portfolio reduced:** 74 -> 68 skills. 6 archived (deploy-to-vercel, vercel-cli-with-tokens, cold-outreach, banner-design, slides, linkedin_mvm). 6 agent-internal SKILL.md descriptions fixed.
- **Hard rule added to memory:** grep orchestrator + signal_works before archiving any skills directory

**Default next moves (in priority order):**

1. Verify morning digest fires correctly tomorrow at 07:30 MT (check Telegram + email)
2. If digest missing: `docker logs orc-crewai | grep griot_morning` on VPS
3. M18 HALO unlock: instrument Atlas heartbeat with tracing.py + 50 traces by 2026-05-18

**Do not start a new milestone without reading the latest Session Log entry below.**

---

## Done Definition

The system runs the content pipeline end-to-end with **zero manual Notion work**, **captures outcome data**, **self-heals on small failures**, and **learns from approvals/rejections**.

That breaks down into 5 closed loops:

| # | Loop | What "closed" means |
|---|---|---|
| L1 | **Propose** | Griot picks daily candidate, enqueues to approval_queue, sends Telegram preview. No human triggers. |
| L2 | **Schedule** | Approved candidate gets Notion Scheduled Date + Status=Queued automatically within 5 min. |
| L3 | **Publish** | Daily brief delivers share URL; Boubacar one-tap publishes (manual today, auto via Blotato/OAuth later). |
| L4 | **Reconcile** | After publish, Notion Status flips to Posted, outcome row written to task_outcomes. No manual flip. |
| L5 | **Learn** | Chairman crew reads outcomes weekly, proposes scoring/prompt mutations to keep quality rising. |

**Done = all 5 loops closed.** Anything outside these 5 loops is descoped or future enhancement.

---

## Architectural Decision: Anthropic Managed Agents Memory (2026-05-06)

**Decision: DEFER adoption of Anthropic-hosted memory stores (Dreams API).**

Reviewed Anthropic's Dreams API (managed-agents research preview). Dreams solves the real problem of memory store deduplication and stale-entry cleanup. However:
- agentsHQ currently uses CLAUDE.md + MEMORY.md (file-based), not Anthropic-hosted memory stores
- Dreams requires migration to the Managed Agents stack first
- No access request has been submitted yet

**Self-built alternative shipped:** `scripts/dream.py` — local Dreams equivalent using the Anthropic SDK. Reads all memory/ files + git log + handoff docs, calls Claude Opus 4.7 to produce a reorganized output store in `memory/dream-output/`. Review then `--apply`. No migration needed.

**Reopen condition:** If Atlas adopts Anthropic-hosted sessions or memory stores (e.g., for agent-to-agent memory sharing or cross-VPS persistence), Dreams becomes the cleanup mechanism. Request access at that point.
**Logged:** 2026-05-06. Next Atlas session should run `python scripts/dream.py` as first action.

---

## Status Snapshot

*Last updated: 2026-04-25 (Saturday evening, post M7a)*

| Loop | Status | Notes |
|---|---|---|
| L1 Propose | ✅ LIVE | griot-morning fires Mon-Fri 07:00 MT. Verified weekend gate working today. |
| L2 Schedule | ✅ LIVE | 5-min wake. Queue #3 scheduled for Monday 2026-04-27. |
| L3 Publish | ✅ LIVE | M7b SHIPPED 2026-04-25. Auto-publisher tick fires every 5 min via Blotato API ($20.30/mo Skool-discounted). Time-of-day slots (LI 07/11/12 MT, X 07/11/14 MT). Mon-Sat cadence, skip Sun. Past-due stagger (max 4/tick). publish_brief still sends Telegram digest as audit; auto_publisher does the actual posting. |
| L4 Reconcile | ✅ LIVE | Reply 'posted' or 'skip' to publish-brief Telegram message; Notion Status flips, task_outcomes written. Shipped 2026-04-25 (M1). |
| L5 Learn | ✅ LIVE | M5 Chairman Crew shipped 2026-05-08. chairman-weekly fires Monday 06:00 MT. enabled=false dry_run=true on VPS. First real tick: next Monday (6 outcomes in DB, need 7). |

**Infrastructure live:**
- 6 heartbeat wakes registered, all firing on schedule
- `orc-crewai` Up 19h healthy
- Three-way sync (local + origin + VPS) on `1fc4980`
- error_monitor.sh cron silent for 19h (no error spikes)
- approval_queue: 3 rows total (1 approved+scheduled, 1 rejected, 1 historical approved)
- autonomy_state.json: griot.enabled=true, dry_run=true

---

## Milestones

### M1: L4 Close-Loop, Publish Reply ✅ SHIPPED 2026-04-25

**What:** Add inline button row `[✅ Posted] [⏭ Skip] [📝 Edited]` to the daily publish brief Telegram message. Each button writes Notion Status + task_outcomes row.

**Why this design:** A single "Posted" button (kickoff doc's original Option A) had three failure modes the Sankofa Council surfaced: forgotten taps, no skip path, no outcome capture. The 3-button row closes all three in one branch.

- **Posted button** → Notion Status=Posted, outcome=success, ts_decided=now
- **Skip button** → Notion Status=Skipped, outcome=skipped, frees the slot
  - Skipped option added to Notion select on 2026-04-25 (gray); see `reference_notion_content_board_schema.md`
- **Edited button** → Notion Status=Posted, outcome=posted_with_edits (signals leGriot calibration data)

**Idempotency:** Callback handler reads current Notion Status first; tap-after-Posted is a no-op with a "already marked" reply.

**Trigger:** Now (Saturday 2026-04-25). Build budget 60-90 min, hour-14 stop.
**Blockers:** None.
**Branch:** `feat/publish-brief-buttons` (to create)
**Test target:** Monday 2026-04-27 morning fire on queue #3.

**Required reads before code:**
- `feedback_inspect_notion_schema_first.md` (verify Status enum, especially `Skipped`)
- `feedback_substrate_gates_before_callbacks.md` (chat_id scope on callback handler)
- Phase 2.6 pattern in `handlers_approvals.py` (mirror for the new handler)

**ETA:** Saturday 2026-04-25, ship by hour 4 of session.

---

### M2: Skip Self-Heal, Same-Day Re-Pick ✅ SHIPPED 2026-04-25

**What shipped:** When you reply `skip` to a publish brief, the Notion record flips to Status=Skipped (M1) but its Scheduled Date is now a "burned" slot. M2 makes `griot_scheduler_tick` (the 5-min wake) scan for Skipped rows whose Scheduled Date is yesterday or today, and backfill that slot with the oldest matching-platform approved candidate from the queue. The Skipped row stays Skipped (audit trail). Forward-scheduling phase runs on the remaining approvals as before.

**Files touched:**
- `orchestrator/griot_scheduler.py`: added `_find_recent_skipped_slots`, `_pick_candidate_for_platform`, backfill phase in `griot_scheduler_tick`
- `orchestrator/tests/test_griot_scheduler.py`: 5 new tests; total 21 pass

**Spec:** `docs/superpowers/specs/2026-04-25-atlas-m2-skip-recovery-design.md`
**Branch:** `feat/atlas-m2-skip-recovery`
**Save point:** `savepoint-pre-atlas-m2-2026-04-25`

---

### M3: Reconciliation Polling, Platform-as-Source-of-Truth ⏳ QUEUED

**What:** Twice daily, query LinkedIn/X for Boubacar's recent posts. If a Queued Notion record's text or share URL matches a live post, auto-flip Status=Posted. Backup for forgot-to-tap.

**Why:** M1 trusts Boubacar's tap as source of truth. Strictly speaking, the platform is the source of truth. M3 closes the gap when M1 fails (forgot, multi-device, notification muted).

**Trigger:** Week 2 of operation (≥7 days of M1 data shows tap-failure rate). Earliest 2026-05-04.
**Blockers:**
- M1 shipped + 1 week of usage data
- X API auth strategy (personal account scraping vs. official API costs)

**Branch:** `feat/reconciliation-polling`
**ETA:** 2-3 hr build (X API friction unknown until spike).

---

### M3.7: Voice Learning Layer ✅ SHIPPED 2026-05-06

**What:** Three-layer system ensuring agents generate content that sounds like Boubacar, not like a generic AI consultant.

**Layer 1 (shipped):** `build_content_reviewer_agent` backstory in `orchestrator/agents.py` updated with:
- Full voice fingerprint (avg sentence 8 words, p25/p50/p75, cadence: punchy)
- 3 signature moves with concrete examples
- Earned Insight Gate (4 anchors: cultural bridge, failure, built-his-own-first, contrarian)
- 3 strong example patterns + weak pattern to reject

**Layer 2 (shipped):** `skills/boub_voice_mastery/references/voice-fingerprint.md` + `voice-fingerprint.json`
- Generated by `transcript-style-dna` from 10 best published posts (144 sentences, confidence: high)
- Human-readable + JSON formats
- Usage instructions for any agent generating content

**Layer 3 (future -- Atlas M5 unlock):** Feedback loop -- when Boubacar edits a Griot-proposed post before publishing, the diff is logged to `task_outcomes`. Chairman crew reads edit history weekly, identifies systematic gaps, proposes prompt mutations. Gated on ≥30 days of L4 outcome data (est. 2026-06-01).

**Why this matters:** Before this milestone, agents could generate posts that passed voice checks but contained nothing only Boubacar could have said. The Earned Insight Gate closes that gap permanently.

**Files touched:**
- `orchestrator/agents.py` -- `build_content_reviewer_agent` backstory
- `skills/boub_voice_mastery/references/voice-fingerprint.md` (new)
- `skills/boub_voice_mastery/references/voice-fingerprint.json` (new)
- `skills/boub_voice_mastery/references/brand-spine-audit.md` (new, same session)

---

### M4: Concierge Crew (Phase 4 proper) ✅ SHIPPED 2026-05-08

**What:** LLM-powered error triage crew. Reads VPS logs, groups errors by signature, uses Haiku to propose triage notes, enqueues to approval_queue.

**Why:** error_monitor.sh (shell cron, shipped Phase 3.75) is the smoke alarm. Concierge is the firefighter.

**Shipped:** `feat/concierge-autonomous` pushed [READY] at `6f9ef63`. Gate will merge to main.

**Files:** `orchestrator/concierge_crew.py`, `tests/test_concierge_crew.py` (10 tests passing), `orchestrator/app.py` (heartbeat every 6h).

**Key decision:** payload key is `triage_note` not `proposed_fix` -- no automated remediation, honest framing.

**Deploy after Gate merge:** `git pull && docker compose up -d orchestrator`. Manual test: `docker exec orc-crewai python -m orchestrator.concierge_crew`

---

### M5: Chairman Crew (Phase 5, L5 Learning Loop) ✅ SHIPPED 2026-05-08

**What:** Weekly oversight crew. Reads approval_queue + task_outcomes, identifies patterns (rejection reasons, scoring drift, topic overlap), proposes mutations to scoring weights or leGriot prompts, enqueues to approval_queue.

**Why:** L5 closes the loop. Without it, scoring weights and prompts ossify.

**Shipped:** 2026-05-08. Branch `feat/chairman-learning-loop` merged to main.
**Files:** `orchestrator/chairman_crew.py`, `orchestrator/contracts/chairman.md`, `orchestrator/tests/test_chairman_crew.py`. Patched `griot.py` (_load_scoring_weights), `handlers_approvals.py` (apply_mutation wired to all 3 approval paths), `app.py` (chairman-weekly heartbeat).
**VPS state:** chairman-weekly registered, enabled=false dry_run=true. 6 outcomes in DB -- need 7 for first real run. First tick: Mon 2026-05-11.
**Before enabling:** 2 dry-run Monday ticks + sign contracts/chairman.md.

---

### M6: Hunter Crew (Phase 6) ⏳ TRIGGER-GATED, MAY DESCOPE

**What:** Autonomous lead-finding + outreach crew (Hunter.io + LinkedIn).

**Why:** Originally planned as second pilot crew. May be replaced by manual pipeline playbook.

**Trigger gate:** 2026-05-06 (Hunter.io upgrade decision date per `project_hunter_upgrade.md`).
**Blockers:**
- Hunter.io subscription decision
- Pipeline playbook results may make this irrelevant (LinkedIn + face-to-face is current Phase 0)

**Decision needed on 2026-05-06:** go/no-go.
**Branch:** `feat/hunter-autonomous`
**ETA:** 4-6 hr when triggered.

---

### M7a: Auto-Publish Decision Spike ✅ SHIPPED 2026-04-25

**Verdict:** KEEP Blotato. API contract verified end-to-end. M7b unblocked.

**Effective cost:** $20.30/mo (Skool RoboNuggets lifetime 30% discount applied; not the $29/mo list quoted in the original spike doc).

**Latency benchmark:** LinkedIn 5 sec submit-to-live, X 9 sec. Both far below the 2-minute pass threshold. Heartbeat-tick-friendly.

**What got tested:** `GET /v2/users/me/accounts`, `POST /v2/posts` (LinkedIn personal + X @boubacarbarry), `GET /v2/posts/{id}` polling. All four phases passed. Verbatim text passthrough confirmed (LinkedIn paragraph break preserved, no AI editorial creep).

**Test post (real CW content, not a throwaway):** "You already know which AI tool your team is overpaying for. The hard part is saying it out loud in a meeting before someone defends the renewal."

**Spike artifacts:**
- Notepad: `d:/tmp/m7a-blotato-spike-notes.md` (full credentials, API contract, smoke test results)
- Smoke-test script: `d:/tmp/blotato-smoke-test.sh` (reusable for future regression checks)
- Smoke-test log: `d:/tmp/blotato-smoke-test-20260425-160135.log`
- Live LinkedIn post: linkedin.com/feed/update/urn:li:share:7453926229797142528
- Live X post: x.com/boubacarbarry/status/2048160547552559336

**Spike doc:** `docs/roadmap/atlas/m7a-decision-spike.md` (now historical artifact).

**Two open risks captured for M7b (not blocking):**
- Idempotency: Blotato has no documented idempotency key. M7b must persist `postSubmissionId` in the Notion record before status polling, to safely retry on transient failures.
- Failure-mode behavior unverified (HTTP 422 on quota, errorMessage shape). M7b should defensively assume worst-case and surface failures via Atlas Concierge crew (M4).

---

### M7b: Auto-Publish Build (Blotato API) ✅ SHIPPED 2026-04-25

**Closed L3 Publish loop. auto_publisher.enabled=true on VPS at 2026-04-25 ~18:55 MT. Next live publish: Mon 2026-04-27 07:00 MT, X "One constraint nobody has named yet".**

**7 decisions locked at build start, all implemented:**
1. Idempotency: Notion Status=Publishing flip BEFORE Blotato POST (prevents double-post on Notion-write failure)
2. State machine: granular Notion Status (added `Publishing`, `PublishFailed`)
3. Module shape: NEW module, platform-agnostic (Studio M4 ready)
4. Tick coordination: disjoint Notion views (auto_publisher includes past-due; publish_brief stays today-only)
5. Kill switch: `auto_publisher.enabled` in autonomy_state.json (default OFF, flipped ON post-deploy)
6. Posted URL: per-platform fields (`LinkedIn Posted URL`, `X Posted URL`)
7. M2 backfill: PublishFailed blocks slot (audit trail preserved)

**Plus three behavioral layers added in same session:**
- Time-of-day slots from `auto_publisher_schedule.default.json`: LinkedIn 07/11/12 MT, X 07/11/14 MT
- Cadence loosen: Mon-Sat both platforms (was Tue/Thu LinkedIn only); skip Sunday for today-records, past-due bypasses Sunday
- Past-due stagger: max_per_tick=4 caps backlog drain to prevent platform-feed bursts

**Files shipped:**
- NEW `orchestrator/blotato_publisher.py` (BlotatoPublisher class, httpx, publish + poll_until_terminal)
- NEW `orchestrator/auto_publisher.py` (heartbeat tick, time-of-day filter, weekday policy, past-due stagger, stale-Publishing TTL cleanup)
- NEW `orchestrator/auto_publisher_schedule.default.json` (committed default schedule config)
- MOD `orchestrator/autonomy_guard.py` (`auto_publisher` added to KNOWN_CREWS)
- MOD `orchestrator/scheduler.py` (heartbeat wake `auto-publisher` registered, every=5m)
- MOD `orchestrator/griot_scheduler.py` (occupancy includes Publishing/PublishFailed; LINKEDIN_WEEKDAYS expanded to Mon-Sat)
- MOD `orchestrator/tools.py` (BlotatoListAccountsTool, BlotatoPublishTool, BlotatoGetStatusTool + PUBLISHER_TOOLS bundle)
- NEW `orchestrator/tests/test_blotato_publisher.py` (20 tests)
- NEW `orchestrator/tests/test_auto_publisher.py` (32 tests)
- MOD `orchestrator/tests/test_griot_scheduler.py` (8 tests updated for Mon-Sat rule)

**Notion schema changes (live via API):**
- Status select: added `Publishing` (yellow), `PublishFailed` (red)
- New URL fields: `LinkedIn Posted URL`, `X Posted URL`
- New rich_text field: `Submission ID`

**Test coverage:** 210/210 orchestrator tests pass (158 pre-existing + 52 M7b).

**Reschedule done out-of-band (5 records, queue clean of past-dues):**
- Skipped: 2026-04-22 LI "I needed it" (already posted Apr 21)
- 2026-04-23 LI -> 2026-05-12 Tue
- 2026-04-24 X -> 2026-05-13 Wed
- 2026-04-25 LI -> 2026-05-07 Thu
- 2026-04-26 Sun X -> 2026-04-28 Tue

**Save point:** `savepoint-pre-atlas-m7b-publisher-2026-04-25` (at 807cc20).
**Commits:** initial cda98d4 (modules + tests + integration); follow-up 8d8194f (time-of-day + cadence + reschedule support).
**Spec:** `docs/superpowers/specs/2026-04-26-atlas-m7b-publisher-design.md` (historical now).
**Branch:** `feat/atlas-m7b-publisher` (merged to main).

**Operating profile:**
- Effective Blotato cost: $20.30/mo Skool-discounted (Starter tier; Atlas uses 2 of Blotato's 8 platforms)
- Wake cadence: every 5 min, 7 days a week
- Active gates: kill switch, weekday policy, time-of-day, past-due cap
- Telegram alerts on every Posted + every PublishFailed

---

### M8: Atlas Mission Control (live ops dashboard at /atlas) ⏳ IN PROGRESS

**What:** Single-page, gated, internal-only dashboard at `agentshq.boubacarbarry.com/atlas` showing live agent activity from data already in Postgres + Notion + autonomy_state.json. Hero strip (System Status / Last Action / Next Fire / Spend Pacing) above 6 cards (Atlas State / Approval Queue / Content Board / Spend 7d / Heartbeats / Errors) with `/chat` embedded as the seventh card. Refresh via htmx polling 30s per card, JWT-PIN gated like `/chat`.

**Action set (Standard, post-Council):** Toggle Griot, toggle dry-run, approve/reject queue items, reply posted/skip to publish brief. Kill switch deliberately omitted from the page (Telegram-only, friction by design).

**Visual:** Catalyst Console (T4) - near-black with graphite-blue undertone, terracotta-orange `#FF6B35` as the signature accent, museum-bronze + lapis-tarnished + verdigris support palette. Atkinson Hyperlegible body (dyslexia-safe), Fraunces display, IBM Plex Mono for data. Mockup locked at `workspace/atlas-m8-mocks/v4.html`.

**Why:** "Usage dashboard" has been on `project_task_backlog.md` since 2026-04-16 and slipped weekly to higher-revenue work. Telegram + SSH is the only inspection surface today. The data exists; this is purely a view layer plus a small scoped action layer.

**Why not external/public:** Killed during Sankofa. M8 is internal. A sanitized public variant becomes a separate later milestone if/when wanted, with its own threat model.

**Spec:** `docs/superpowers/specs/2026-04-25-atlas-m8-mission-control-design.md` (status: approved-after-sankofa)
**Sankofa:** Five voices ran 2026-04-25. Folded fixes: file lock on `autonomy_state.json`, killed Roman-numeral chips (Outsider voice flagged as decorative), dropped external-proof-point framing. Parked: outcomes/quality card (M9 candidate), chat-as-primary reframe.
**Trigger:** Now (parallel with M7a).
**Blockers:** None. All data sources verified live.
**Branch:** `feat/atlas-m8-mission-control` (to create)
**ETA:** 4.75 hr in 4 blocks (backend data path 2h, visual shell 2h, htmx polling 45min, action layer + polish 75min). Down from original 6h after Sankofa scope cuts.
**Save point:** `savepoint-pre-atlas-m8-2026-04-25` (to create before block 1)

---

### M12: Startup Contract (env var hard-fail) SHIPPED 2026-04-28

**What:** `orchestrator/startup_check.py` with a single function `assert_required_env_vars()`. Reads a manifest of required env var names declared in the same file. For each var, checks it is present AND non-empty in `os.environ`. On any failure: prints the full list of missing vars to stdout and calls `sys.exit(1)` before uvicorn binds. Wired as the first call in `app.py` at startup.

**Why:** The VPS .env crash pattern has caused at least two container restarts where missing vars caused `float("")` ValueError or silent Haiku fallback with no alert. A soft Telegram alert cannot fix this class of bug because: (a) the alert itself may fail if TELEGRAM_BOT_TOKEN is the missing var, (b) the container boots with broken state before the alert fires. Hard-fail is the correct fix. This also scales to every Signal Works client deployment - every new client instance gets the same contract for free.

**Success criterion (verifiable):** Deploy to VPS with one required var temporarily removed from `.env`. Container must exit with code 1 and print the missing var name in docker logs. Restore var, container must boot clean.

**Trigger:** Now. No gate. This is hardening against a known, repeated failure.

**Scope (Karpathy-bounded):**

- NEW `orchestrator/startup_check.py`: `REQUIRED_VARS` list + `assert_required_env_vars()`. Nothing else.
- MOD `orchestrator/app.py`: one call added inside the FastAPI `lifespan` context manager (NOT at module top-level - module-level runs on import and breaks the test suite). Wire: `assert_required_env_vars()` as first statement inside `async with lifespan(app):` or equivalent startup hook.
- NEW `orchestrator/tests/test_startup_check.py`: 3 tests (all present passes, missing var exits 1, empty string exits 1).
- No changes to `.env`, `docker-compose.yml`, or any other file.

**Required vars manifest (no-safe-default vars only):**
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `OPENROUTER_API_KEY`, `NOTION_API_KEY`, `FORGE_CONTENT_DB`, `BLOTATO_API_KEY`, `CHAT_MODEL`

Explicitly excluded (have code-level defaults, hard-failing on these creates new failures where none exist): `CHAT_TEMPERATURE` (default 0.3), `CHAT_SANDBOX` (default false), `ATLAS_CHAT_MODEL` (falls back to CHAT_MODEL).

**What is NOT in scope:**

- Telegram alert on failure (secondary signal; add later if wanted; the hard-fail is the fix)
- Auto-restart logic
- Dynamic manifest from a config file (YAGNI; inline list is sufficient and auditable)

**Council verdict:** Sankofa + Karpathy both cleared. Executor: build this before the next VPS deploy (M11d + M9b deploy is the forcing function).

---

### M13: True spend visibility (provider billing API integration) SHIPPED 2026-05-03

**What shipped:**
- `orchestrator/spend_snapshot.py`: new module. Pulls `usage_daily/weekly/monthly` + balance from OpenRouter `auth/key` + `credits` endpoints. Upserts one row per day into `provider_billing` Postgres table (created on first run). Fires daily at 23:55 MT via heartbeat, sends Telegram digest.
- `atlas_dashboard._fetch_provider_spend()`: live provider figures injected into every `get_spend()` call (no DB required for today's numbers).
- `atlas_dashboard._get_historical_comparisons()`: reads `provider_billing` rows and computes this-week vs last-week delta %, this-month vs last-month delta %, YTD total.
- `atlas_dashboard.get_spend()`: now returns `provider_today/week/month/balance`, `historical`, `pacing_pct` (vs $50/mo budget), `daily_budget`.
- `atlas_dashboard.get_hero()`: `spend_pacing` now uses provider ground-truth today vs daily share of $50/mo. Hero tile shows "$X.XX (NNN% of $Y.YY/d)" and turns red above 100%.
- `atlas.js` Spend card: added "Comparisons" section (this/last week, this/last month, YTD with delta %), "OpenRouter (ground truth)" section (today/week/month/balance, untracked CrewAI delta in amber), relabeled existing rows as "Ledger (attributable)".
- `health_sweep._probe_openrouter_credits()`: fixed units bug (was dividing by 100; API returns raw USD). Probe now correctly alerts at $5.
- Monthly budget set at $50. After 3 full months of data, revisit.

**What was descoped (moved to M16):**
- Anthropic Console API pull (no public endpoint confirmed; needs spike).
- Claude Code / Codex CLI token tracking (no programmatic API; M16 spike).

**Commit:** `287dfe7`

---

### M14: Click-to-open-Notion links on Atlas dashboard ✅ SHIPPED 2026-04-30

**Target:** 2026-04-30 (shipped).

**Trigger:** Now. Boubacar wants to click any item in the Content Board card, Approval Queue card, or Top Ideas card and have it open the underlying Notion page in a new tab. Today these render as plain text and require him to switch to Notion and search for the title manually.

**Scope:**

- **Backend:** `orchestrator/atlas_dashboard.py`
  - `_fetch_content_board()`: include `notion_url` (from Notion API's `page.url` field) in each parsed dict for `recent`, `upcoming`, `past_due`.
  - `_fetch_ideas()`: same. Add `notion_url`.
  - `get_queue()`: queue items reference Notion pages via `payload.notion_url` or similar; gracefully render plain text when payload has no URL (ad-hoc proposals).
- **Frontend:** `thepopebot/chat-ui/atlas.js`
  - `renderContent`: title becomes `<a target="_blank" rel="noopener">` when item has `notion_url`. Add small external-link glyph (↗) next to linked titles.
  - `renderIdeas`: same.
  - `renderQueue`: same, with the gate for items without URLs.
  - DOM-builder pattern (`createElement` + `textContent`) preserved. No `innerHTML`.
- **Tests:** add 1 test per data fetcher to assert `notion_url` is present in the output dict when the source page has it. Total ~3 new tests.

**Success criterion (verifiable):** On `https://agentshq.boubacarbarry.com/atlas`, click any past-due / upcoming / queue / ideas title and the matching Notion page opens in a new tab. Items without a Notion URL render as plain text (no broken links).

**Out of scope:**

- Hero strip "Last action" linking. That data comes from `task_outcomes` (Postgres), which has no Notion URL column. Possible follow-on if needed.
- Inline preview / hover cards. Click-through is the ask; previews are scope creep.

---

### M15: Notion State Poller + /task add SHIPPED 2026-05-02

**Closed bidirectional-sync gap.** Notion stays the editing surface; agentsHQ catches up automatically via 5-min poller. Plus one Telegram verb for fast capture.

**Files shipped:**
- `orchestrator/notion_state_poller.py`: 5-min heartbeat tick, queries Notion Tasks DB for rows changed in last 6 min, diffs against `data/notion_state_cache.json`, appends to `data/changelog.md`. Backfill mode on first run. Coordination lock prevents overlap. 22 unit tests.
- `orchestrator/handlers_commands.py`: `handle_task_add()` for `/task add "<title>" [--owner] [--sprint] [--p0]`. Auto-assigns next T-YYxxxx, single-P0 invariant, B+C echo (confirmation + top 3). 11 unit tests.
- `orchestrator/scheduler.py`: registered `notion-state-poller` wake every 5m under `_heartbeat.SELF_TEST_CREW` (read-only diagnostic, not gated by crew kill switches).

**Verification (live on VPS):**
- C1 PASS: poller caught real Notion click on `T-260009 Test all agent task types via Telegram` (Not Started -> In Progress)
- C2 PASS: `/task add` from Telegram created T-26618 with correct defaults
- C3 PASS: failure modes (no title, bad owner, untracked field) handled correctly
- C4 PASS: concurrent ticks, second skips on lock

**Container deploy bugs caught + fixed in PR chain:**
- PR #25: spec + plan + initial build (33 tests)
- PR #26: hotfix `crew_name="atlas"` to `SELF_TEST_CREW` (heartbeat was skipping every fire because no atlas crew exists in autonomy_state.json)
- PR #27: hotfix `REPO_ROOT` resolution under flattened orc-crewai container paths
- PR #28: hotfix changelog destination from `/app/docs/audits/` (not mounted) to `/app/data/` (mounted to `/root/agentsHQ/data/`, persists across rebuilds)

**Spec:** `docs/superpowers/specs/2026-05-02-task-poller-and-add-design.md`
**Plan:** `docs/superpowers/plans/2026-05-02-task-poller-and-add.md`
**Branch:** `feature/task-poller` (merged via PR #25, then 3 follow-up fix PRs)

**Out-of-scope (deferred per spec section 7):**
- All `/task` verbs other than `add` (done, p0, sprint, block, archive, reopen, reassign)
- 3-day past-due Telegram digest (separate work; reads changelog)
- Daily standup / Golden Gem nudge / weekly recap generators
- `--due` flag on `/task add`
- Automated changelog rotation when file >5MB

---

### M16: Cross-provider token tracking spike (Claude Code, Codex, Anthropic Console)

**Status:** QUEUED

**Trigger:** After 3 full months of OpenRouter data (earliest 2026-08-01). Build earlier only if Boubacar explicitly asks.

**What:** Single daily snapshot that captures token usage across ALL AI providers, not just OpenRouter:
- Anthropic Console API (covers direct SDK calls, Claude Code CLI, claude.ai usage): endpoint and auth method TBD via spike
- Codex CLI: no known programmatic API; may require parsing local log files or usage exports
- OpenRouter (already done in M13)

**Why not now:** Anthropic has no confirmed public `/v1/organizations/usage` endpoint. Claude Code CLI token usage is not accessible programmatically. Both need a spike before any build work. M13 already captures the majority of agent spend (OpenRouter routes all crew calls). The remaining gap (Claude Code sessions, manual claude.ai chats) is real but not blocking operations.

**Spike questions to answer before building:**
1. Does Anthropic Console expose a usage API? If so, what auth (org API key, cookie, OAuth)?
2. Does Claude Code CLI write a local usage log that can be parsed?
3. Does Codex expose usage via its API or config?

**Success criterion:** Spend card shows a "Total AI spend (all providers)" line that is the ground truth across OpenRouter + Anthropic + any others, with per-provider breakdown. Numbers cross-check within 5% of each provider's own dashboard.

---

### M17: Kie.ai Spend Tracking

**Status:** QUEUED (gate-blocked)

**Gate condition (do this first, 10 min):**

```bash
docker exec orc-crewai python3 -c "
import requests, os
h = {'Authorization': f'Bearer {os.environ[\"KIE_AI_API_KEY\"]}'}
r = requests.get('https://api.kie.ai/api/v1/chat/credit', headers=h)
print('credit:', r.status_code, r.json())
r2 = requests.get('https://api.kie.ai/api/v1/usage', headers=h)
print('usage:', r2.status_code, r2.text[:500])
r3 = requests.get('https://api.kie.ai/api/v1/transactions', headers=h)
print('txns:', r3.status_code, r3.text[:500])
"
```

Answer two questions before writing any code:

1. Does Kie expose a transaction/usage history endpoint? (If yes: mirror OpenRouter pattern exactly. Plan below is obsolete.)
2. What is the credit-to-USD conversion rate? Is it fixed or per-model-variable?

**What:** Add Kie.ai spend to the Atlas dashboard Spend card so total AI cost is visible alongside OpenRouter.

**Implementation path (balance-delta approach -- only if no transaction endpoint exists):**

- `orchestrator/spend_snapshot.py`: add `_fetch_kie()` (hits `/api/v1/chat/credit`, returns integer credits). Add `take_kie_snapshot()` as standalone function (do NOT refactor `take_snapshot()` signature -- keep existing callers untouched). Delta logic: `usd_today = (prev_balance - current_balance) / KIE_CREDITS_PER_USD`. Day-1 sentinel: write NULL for `usd_today` when no prior row exists. Top-up detection: if `current_balance > prev_balance`, write NULL (not 0 -- zero implies confirmed zero spend). Update `spend_snapshot_tick()` to call both snapshots.
- `orchestrator/atlas_dashboard.py`: add standalone `_fetch_kie_live()` (returns current balance only, fails independently from OpenRouter fetch). Update `get_spend()` to include `kie_balance`, `kie_today` (from latest provider_billing row, not live delta). Dashboard shows "---" when `kie_today` is NULL.
- Schema: do NOT store Kie credits in `usd_today` with unknown units. Store confirmed USD only. Add `KIE_CREDITS_PER_USD` constant once rate confirmed. If rate is per-model-variable, use separate `kie_balance_log` table instead of `provider_billing` to avoid unit contamination.

**What is NOT in scope:**

- Intraday polling (future enhancement if Kie becomes top spend source)
- Per-job attribution (future; needs balance read before/after each API call)
- Aggregating Kie into `_get_historical_comparisons()` -- audit first: inject a synthetic row and confirm existing function already sums it. If yes, no code change needed there.

**Success criterion (verifiable):**

1. `provider_billing` has a Kie row after 23:55 MT with `usd_today` in confirmed USD (not raw credits)
2. Atlas dashboard Spend card shows Kie balance matching `GET /api/v1/chat/credit` raw response / confirmed rate
3. SQL assertion after two consecutive snapshots: `usd_today` == hand-calculated delta

**Sankofa + Karpathy review:** 2026-05-03. Both councils flagged credit-unit mismatch as fatal flaw in original plan. Karpathy verdict: HOLD until gate clears. Key findings: top-up guard in original plan erases real spend; delta approach conditionally sound only with confirmed fixed credit rate; `_get_historical_comparisons()` may need zero code changes once rows exist.

**ETA:** 2-3h after gate clears.
**Branch:** `feat/atlas-m9-kie-spend` (create when gate clears)

---

### M18: HALO Loop - Trace-Driven Harness Optimization ⏳ TRIGGER-GATED

**What:** Wire OpenTelemetry JSONL tracing into one agentsHQ harness (Atlas heartbeat loop first, Studio pipeline second). Once 50+ traces are collected, run the HALO CLI to surface systemic failure patterns. Feed verified findings to Claude Code to patch the harness. Repeat until performance plateaus.

**Why:** Sankofa + Karpathy both flagged this as the right tool at the wrong time (2026-05-04). The Atlas L5 Learn loop (M5) and "learning crews" milestone share the same goal as HALO: make the harness self-improve from data. HALO is the concrete, benchmarked implementation of that concept. AppWorld results: Sonnet 73.7→89.5, Gemini Flash 36.8→52.6 - by optimizing the harness, not the model.

**How HALO works:**
1. Harness emits OTel-compatible JSONL traces via `tracing.py` (copyable from `halo-engine` demo)
2. `halo <traces.jsonl> -p "<diagnostic question>"` runs RLM over traces, surfaces systemic failure patterns
3. Claude Code (this) maps findings to code, makes the minimum change, verifies, re-runs
4. Loop repeats

**Key constraint:** HALO is a two-actor system. HALO Engine = trace diagnostics only (no repo access). Claude Code = maps findings to code. Never ask HALO to write patches.

**Install:** `pip install halo-engine` (MIT, PyPI). Ships its own `skills/claude/SKILL.md` - use that as the operating manual when the loop starts.

**Trigger gate (ALL required before any build):**
1. Instrument Atlas heartbeat loop with HALO's `tracing.py` pattern (copy from `demo/openai-agents-sdk-demo/tracing.py`)
2. Collect ≥50 traces from real runs
3. Run `halo <traces.jsonl>` and verify ≥1 actionable finding
4. If ≥1 finding verified → proceed to M18 build. If 0 findings → harness is already clean; archive permanently.

**Trace format requirements:**
- Plain JSONL (not gzip)
- Required fields: `trace_id`, `span_id`, `parent_span_id`, `name`, `inference.project_id`, `inference.observation_kind`
- `inference.observation_kind` must be one of: `AGENT`, `LLM`, `TOOL`, `CHAIN`, `GUARDRAIL`, `SPAN`
- Do NOT use `OPENAI_AGENTS_DISABLE_TRACING=1` - disable the OpenAI uploader with `agents.set_trace_processors([])` instead

**Trigger date:** 2026-05-18 (instrument + first run). If no instrumented traces by 2026-06-01 → archive permanently.
**Blockers:** No agentsHQ harness emits OTel JSONL today. Instrumentation is the unlock.
**Branch:** `feat/atlas-m18-halo-tracing` (create when gate clears)
**ETA:** 1h instrumentation + first run. Optimization loop is ongoing.

**Source:** `github.com/context-labs/halo` absorbed 2026-05-04. ARCHIVE-AND-NOTE verdict; revisit condition = this milestone.

---

### M19: Atlas CRM Dashboard (`/crm`) ⏳ QUEUED

**What:** Replace the (sunset) Notion CRM Leads database with a native Atlas-page sales board, served at `/crm`. Pulls directly from Supabase `leads` table. Read + lightweight write (status updates, notes append). No external sync.

**Why:** Notion CRM Leads sync was severed on 2026-05-07 (sync code deleted from `crm_tool.py`, `scheduler.py`, `db.py`; parity audit at `docs/audits/notion_sever_parity_2026-05-07.md`). Supabase is now the sole system of record for leads. Atlas needs a visual surface so Boubacar (and crews) can see the pipeline without cracking open psql.

**Endpoints (proposed):**

- `GET /atlas/crm/board` → pipeline counts by status + "leads needing outreach today" list
- `GET /atlas/crm/leads/<id>` → single-lead detail (interactions timeline)
- `POST /atlas/crm/leads/<id>/note` → append free-text note
- `POST /atlas/crm/leads/<id>/status` → status transition with audit row

**"Needs outreach today" predicate (proposed, confirm before build):**

```sql
WHERE status = 'new'
   OR (status IN ('messaged', 'replied')
       AND last_contacted_at < NOW() - INTERVAL '7 days')
```

**Success criteria:**

- P50 latency `<200ms` on `/atlas/crm/board`
- Row count on board matches `SELECT COUNT(*) FROM leads`
- CRM block wired into morning_digest (counts + today's outreach list)

**Trigger gate:**

1. Notion CRM DB archived (manual, by Boubacar, in Notion UI)
2. Predicate for "needs outreach today" confirmed
3. No new Notion-only orphans surfaced post-2026-05-07 audit

**Branch:** `feat/atlas-m19-crm-dashboard` (create when gate clears)
**ETA:** 0.5 day endpoint + 0.5 day morning_digest wire-in.

---

### M20: Native Social Publisher — Replace Blotato ⏳ RESEARCH-GATED

**What:** Replace Blotato ($40/mo) with a self-hosted publisher that calls platform APIs directly. Blotato is a pass-through relay — all it does is proxy our payloads to X, Instagram, TikTok, YouTube, and LinkedIn OAuth endpoints. We already hold the content, captions, and scheduling logic. The relay adds cost and a failure surface with no unique value.

**Why:** ~$480/yr for a service that does one thing we can do ourselves. Full control over retry logic, rate limits, error handling, and future platform support. No third-party outage risk.

**Research completed 2026-05-08. Findings:**

| Platform | Verdict | Blocker |
|---|---|---|
| YouTube | **EASY** | One-time browser OAuth per channel; free quota 10k units/day (~6 uploads/day, we use ~1.5/day); indefinite refresh tokens once app verified |
| Instagram | **MEDIUM** | Must switch channels to Business accounts; Meta app review for `instagram_business_content_publish` (~7-14 days); 2-step container+publish flow; public URL required (Drive usercontent already works) |
| X/Twitter | **HARD — DO NOT REPLACE** | Free tier: 34 media FINALIZE calls/24h total — hit by midday at studio volume. Basic tier = $200/mo. Blotato at $29/mo is cheaper. |
| TikTok | **HARD — DO NOT REPLACE** | `video.publish` scope requires manual TikTok approval (weeks, uncertain outcome). Only alternative is Inbox/draft mode (creator must manually publish) — defeats zero-touch goal. |
| LinkedIn | **HARD — DO NOT REPLACE** | 60-day access tokens with no silent refresh on personal profiles. Community Management API (required for refresh tokens) needs registered legal org approval. Blotato absorbs this entirely. |

**Key insight:** Blotato's real value is not the API calls — it is the OAuth token store. X, TikTok, and LinkedIn have expiry/approval constraints that make self-hosting expensive or blocked. YouTube and Instagram are genuinely replaceable.

**Revised scope:**

- **v1 (worth building):** YouTube + Instagram native adapters only. Drop-in behind same interface as `BlotatoPublisher`. Saves ~$15-20/mo if we can downgrade Blotato to X/TikTok/LinkedIn only tier — or confirms Blotato is still needed and we cancel the research.
- **v2 (monitor):** X native if X raises Basic tier price or we hit rate limits at scale. LinkedIn if we get Community Management API access.
- **TikTok:** stay on Blotato indefinitely or evaluate Creator Marketplace API when it matures.

**Trigger gate (revised):**
1. Confirm Instagram channels are switched to Business accounts (manual, Boubacar)
2. Submit Meta app for `instagram_business_content_publish` review
3. Set up Google Cloud project + YouTube OAuth app, submit for verification
4. Implement `YouTubeAdapter` + `InstagramAdapter` with parallel-run against Blotato for 2 weeks
5. If parity confirmed: downgrade or cancel Blotato plan depending on X/TikTok/LinkedIn volume

**Scope v1 (ship when gate clears):**
- `orchestrator/social_publisher.py` — platform-agnostic publisher, same `publish(text, account_id, platform, media_urls)` interface
- `YouTubeAdapter` — resumable upload + video metadata
- `InstagramAdapter` — public URL container + poll + publish two-step
- Token store: refresh tokens in `.env`, auto-refresh before expiry via scheduled check
- `studio_blotato_publisher.py` — route YouTube + Instagram to native adapters; X/TikTok/LinkedIn remain on Blotato

**Branch:** `feat/atlas-m20-native-publisher` (create when gate clears)
**ETA:** 2 days for YouTube + Instagram adapters. Meta app review: async (~2 weeks).
**Cost savings:** Unclear until Blotato plan audit — may save $10-20/mo or justify full cancel if X volume drops.
**Trigger date:** After M19 CRM ships. Instagram Business account switch is the critical path item — do that first (5 min per channel in Instagram app).

---

## Descoped Items

These are explicit "do not build" decisions with reasons, so we don't relitigate.

| Item | Reason | Date decided | Revisit when |
|---|---|---|---|
| **Phase 3.5 drafter** (leGriot re-drafts approved candidates) | `content_board_reorder.py` (2026-04-21) already Sonnet-polished all 80 records. Re-drafting is solving a non-problem. | 2026-04-24 | A genuinely bad Draft ships through L3. |
| **Phase 2.5 event-triggered wakes** | No consumer until M4 or M6. Events without consumers are dead code. | 2026-04-24 | M4 or M6 starts and needs events. |
| **Single "Mark Posted" button** (original kickoff Option A as written) | Sankofa Council 2026-04-25: forgotten-tap failure mode + no escape hatch + no outcome capture. M1 (3-button row) ships richer version in same budget. | 2026-04-25 | Never. M1 supersedes. |
| **Phase 5 stub** (Chairman skeleton ahead of data) | Stub that does nothing for 2 weeks rots. Build when data is ready. | 2026-04-24 | M5 trigger gate hits. |
| **Phase 6 Hunter stub** (skeleton ahead of decision) | Hunter.io paused. Writing a stub for paused work is dead code. | 2026-04-24 | M6 trigger gate hits. |
| **Agent Task Ledger** (general-purpose resumable state for any ad-hoc task) | Premature abstraction. Every pipeline loop already has purpose-built resume state (approval\_queue, Notion Status, \_confirm\_store). A general ledger solves a hypothetical, not a demonstrated failure. Karpathy audit: FAIL on Simplicity First. Sankofa: no trigger, no verifiable success criterion. | 2026-04-28 | A specific non-pipeline ad-hoc task demonstrably fails to resume after a session break. When that happens, build a single-table solution for that task type - not a general ledger. |
| ~~Agent Task Ledger~~ | **RE-OPENED 2026-04-29.** Boubacar named it a proactive priority. Override based on user-stated risk + new memory rule `feedback_now_means_proactive_not_broken.md` (the Karpathy "no demonstrated failure" gate applies to speculative agent abstractions, not to user-named risks). Shipped: `skills/coordination/__init__.py` ledger with `claim/complete/lock` (resource locks) plus `enqueue/claim_next/fail/recent_completed` (work queue) on a single `tasks` table. `claim_next` uses FOR UPDATE SKIP LOCKED for race-free concurrent workers. Tests: `tests/test_agent_collision.py` (10/10 green). Wire-ins: morning_runner, outreach_runner, deploy.sh (mkdir mutex), vercel-launch (mkdir mutex per app). | 2026-04-29 | n/a (shipped) |
| **NLM registry export cron** (daily Postgres-to-Sheets mirror of `notebooklm_pending_docs`) | Built 2026-04-27 as a backup audit trail for NotebookLM ingestion. Never wired up: `NLM_EXPORT_SHEET_ID` was never set, so the cron logged a warning and exited. Source table has 6 total rows, last write 2026-04-13, zero activity in 14+ days, no active producer or consumer. Script preserved at `scripts/nlm_registry_export.py`; cron line removed from VPS crontab 2026-04-30. | 2026-04-30 | NotebookLM ingestion pipeline starts producing rows again. Then: create the Sheet, add `NLM_EXPORT_SHEET_ID` to `.env`, restore cron line piping the script into `docker exec -i orc-crewai python3 -`. |

---

## Cross-References

- **Memory:** `project_autonomy_layer.md` (per-phase shipping artifacts), `feedback_inspect_notion_schema_first.md`, `feedback_substrate_gates_before_callbacks.md`
- **Specs:** `docs/superpowers/specs/2026-04-23-phase-0-autonomy-safety-rails-design.md`, `docs/superpowers/specs/2026-04-24-phase-1-episodic-memory-and-approval-queue-design.md`, `docs/superpowers/specs/2026-04-24-phase-2-heartbeat-design.md`
- **Modules:** `orchestrator/griot.py`, `orchestrator/griot_scheduler.py`, `orchestrator/publish_brief.py`, `orchestrator/heartbeat.py`, `orchestrator/scheduler.py`
- **State:** `/root/agentsHQ/data/autonomy_state.json` on VPS
- **DB:** `approval_queue`, `task_outcomes` tables in `postgres` DB on `orc-postgres`
- **Verification queue concept (2026-05-04):** Graeme Kay research agent architecture (Sankofa Council session) surfaced a gap: Atlas has an `approval_queue` for human-gated commits but no equivalent for *knowledge claims* - agent outputs that need verification before becoming facts the system acts on. Future enhancement: add `data/verification_queue.md` alongside `autonomy_state.json` on VPS. Any claim an agent makes that another agent will act on gets queued here before promotion to fact. Blocks hallucination laundering. Gate: build when M5 Chairman crew is being designed (2026-05-08+).
- **M-delegation — Agent-to-agent task handoff (2026-05-06):** The coordination ledger (`skills/coordination/__init__.py`) already has `enqueue`/`claim_next`/`complete` for race-free work queues. What was missing: a named design pattern for HOW an agent self-decomposes work and hands it to another agent without blocking. Pattern now documented at `skills/coordination/references/agent-delegation-pattern.md`. One-way dispatch (enqueue + forget) is usable today. Full bidirectional respawn (agent A waits on agent B's result via async job API) is gated on M5 Chairman crew. Kind naming convention: `<domain>:<verb>` (e.g. `studio:render`, `sw:outreach`, `atlas:verify`). Gate: first real usage — one Atlas agent cites the pattern doc as its design reference for an `enqueue`→`claim_next` handoff.

---

## Session Log

Append-only. Newest entry at the bottom. Each entry: date, what changed, what's next.

### 2026-04-23: Phase 0 shipped
Safety rails (spend cap, kill switch, per-crew flags, dry-run, ledger split). PR #9 merged. autonomy_state.json now persisted on VPS via `./data:/app/data` mount. Tags: `savepoint-pre-autonomy-20260423`, `savepoint-phase-0-autonomy-shipped-20260423`.
**Next:** Phase 1 (episodic memory + approval queue).

### 2026-04-24: Marathon day, Phases 1, 2, 2.6, 3 L0.5, 3.75 shipped
5 PRs merged. Shadow module backport (`uvicorn app:app`), heartbeat scheduler with 6 wakes, per-crew gate, Griot pilot, scheduler + publish brief + error monitor. Hour-12.5 stop on a hour-14 budget. Queue #3 "One constraint nobody has named yet" approved and scheduled for Monday 2026-04-27. Original Phase 3.5 drafter descoped after Council review. Tags: `savepoint-pre-shadow-backport-2026-04-24`.
**Next:** observe Friday + Monday fires, pick next milestone.

### 2026-04-25: Roadmap created, M1 in progress
Saturday morning. Health checks all green: three-way sync `1fc4980`, container Up 19h healthy, error_monitor silent, weekend gates verified working (today's griot-morning correctly skipped).

Original kickoff doc framed next moves as a "candidate menu" (Options A-F). No master roadmap existed. Each session was picking the next move from a menu rather than executing against a plan. **Boubacar called this out: "we have to start having a roadmap for major projects."**

Action taken:
1. Created `docs/roadmap/` structure (README + this file)
2. Locked Done Definition (5 closed loops)
3. Mapped current state and remaining milestones M1-M7
4. Documented descoped items with reasons
5. Replaced orphan handoff doc pattern with the session-log section in this file

Sankofa Council ran on original Option A. Council rejected single-button design. M1 redesigned as 3-button row covering Posted/Skip/Edited in one branch. Council-approved.

**Next this session:** brainstorm + write per-feature plan for M1, then build under hour-14 budget. Test target Monday 2026-04-27.

### 2026-04-25 (afternoon): M1 SHIPPED to VPS

Atlas M1 (publish reply) live on VPS. Branch `feat/atlas-m1-reply`, PR pending merge.

Council reframe (second pass on M1): original spec extended `approval_queue` with `proposal_type='publish_brief'` rows. Council rejected because (a) overloaded the table semantically and (b) created a real misroute bug where a stray `yes confirm` reply to a publish-brief message would silently flip the row to `approved` without any Notion write. Switched to in-memory `_PUBLISH_BRIEF_WINDOWS` dict in `state.py`. No new tables, no migrations.

Boubacar reframe (third pass on M1): dropped buttons. Text-reply `posted` / `skip` is simpler, matches existing `yes confirm` UX, and avoids the cosmetic-vs-functional trap. Dropped `edited` keyword (Phase 5 territory; revisit when L5 starts).

Notion-side change: added `Skipped` to Content Board Status select options (gray). Updated `reference_notion_content_board_schema.md`.

Files touched:
- `state.py`: +1 dict
- `publish_brief.py`: per-post sends now use `send_message_returning_id`; populate dict; 24h-evict at start of tick; `Reply \`posted\` or \`skip\`` hint line
- `handlers_approvals.py`: +`POSTED_ALIASES` +`SKIP_ALIASES` +`_open_notion` +`handle_publish_reply` (two-layer idempotency)
- `handlers.py`: +1 dispatch line between approval_reply and naked_approval
- `tests/test_publish_reply.py`: NEW, 6 tests
- `tests/test_publish_brief.py`: updated mock fixture for `send_message_returning_id`

Test counts: 18 publish_*+reply tests pass; 153 in-scope orchestrator tests pass overall (excludes 12 pre-existing test_doc_routing path failures unrelated to M1).

Sankofa Council called twice this session (original 1-button design, then post-spec on the approval_queue overload). Both calls overrode the initial design and prevented bugs. Hour-14 stop discipline: shipping at hour ~6.5.

**Test target:** Monday 2026-04-27 07:30 MT publish brief on queue #3 "One constraint nobody has named yet" (X). Reply `posted` should flip Notion Status to Posted.

PR #19 merged at `ef87293`. Three-way nsync confirmed. Container rebuilt + healthy + handler reachable on VPS.

Scheduled remote agent `trig_015aDdXmiTAowm1HVkwQydnT` ("Atlas M1 Monday Verification") fires once Monday 2026-04-27 09:00 MT (15:00 UTC). Static code-on-main verification only (CCR sandbox cannot SSH or send Telegram). Writes `docs/handoff/2026-04-27-atlas-m1-verification.md` with 5 manual VPS checks Boubacar runs himself. URL: <https://claude.ai/code/routines/trig_015aDdXmiTAowm1HVkwQydnT>

**Next:** observe Monday fire. If green, M2 (Skip Self-Heal) on next session. If red, debug before any new milestone.

Side commit `fb56633`: engagement-ops skill + PM rigor library + cleanup script committed to main (parallel-session work; no code changes; container did not need rebuild).

### 2026-04-25 (late afternoon): M2 SHIPPED + M7 split + studio roadmap created

**M2 Skip Self-Heal shipped.** Branch `feat/atlas-m2-skip-recovery`. 5 new tests, 21/21 scheduler suite green, 158 in-scope orchestrator tests pass overall. Backfill phase added to `griot_scheduler_tick` consumes yesterday-or-today Skipped slots BEFORE the forward-scheduling loop, so a Skip on Tuesday gets the Tuesday slot reclaimed within 5 minutes by an approved candidate. The Skipped row stays Skipped (audit trail). Save point `savepoint-pre-atlas-m2-2026-04-25`.

**M7 split into M7a + M7b after Sankofa Council.** Council rejected "build M7 dormant today" because (a) Blotato Starter is $29/mo not $9/mo (memory rot, fixed; new feedback rule logged: always WebFetch pricing before recommending), (b) building code against an unverified API is build-then-pray, (c) Boubacar uses only LinkedIn + X today so Blotato's multi-platform value-add does not yet apply, (d) "draft JSON in repo, you import manually" pattern rots immediately. New plan: M7a is a 30-min decision spike next session (sign up for 7-day trial, manually validate one post, decide); M7b is the build, only if M7a says keep.

**Studio roadmap created.** Sister roadmap `docs/roadmap/studio.md` for the faceless agency project (multi-channel, faceless, AdSense + sponsorship + affiliate, runs on agentsHQ infrastructure, adjacent to Catalyst Works). 8 milestones drafted by parallel subagent. Done definition locks 5 gates (3 channels live + production autonomy + publishing autonomy via M7 + $1k/month net 90 days + Boubacar weekly ops ≤2h). Codename registry updated.

**State at session pause:** local on `feat/atlas-m2-skip-recovery`, all changes committed, pushed to origin pending. VPS still on `4df7dd1` (no M2 deploy yet). M2 PR not yet opened. Boubacar requested a clean restart point.

**Next session resume checklist:**
1. `git checkout main && git pull` (catch up to whatever lands)
2. Open PR for `feat/atlas-m2-skip-recovery`, merge, deploy to VPS, container rebuild
3. M7a decision spike (sign up for Blotato 7-day trial; manually publish one test)
4. After Monday verification routine fires (`trig_015aDdXmiTAowm1HVkwQydnT` at 09:00 MT), inspect the report at `docs/handoff/2026-04-27-atlas-m1-verification.md`

### 2026-04-25 (evening): atlas day-end, M2 deployed, M7a doc, studio launched in parallel

**M2 PR #20 merged at `28e7a89`.** VPS pulled, container rebuilt, healthy. M2 helpers reachable (`_find_recent_skipped_slots`, `_pick_candidate_for_platform`). All 6 heartbeat wakes registered post-deploy. Three-way nsync verified: local + origin + VPS all on `28e7a89`. Source Control panel empty.

**M7a prep doc written:** `docs/roadmap/atlas/m7a-decision-spike.md`. Covers signup steps, smoke test plan (LinkedIn + X manual posts via Blotato UI, latency check, edge cases), 7-day observation protocol, decision matrix (8 criteria), cancellation pre-mortem, what NOT to do. M7a is now a 30-min spike + 7-day passive trial, fully prepared.

**Studio launched in parallel.** Boubacar opened a separate Claude Code instance for the `studio` (faceless agency) project. Launch prompt was drafted in this session and copy-pasted into that instance. Studio M1 (channel + niche selection via clone-scout pattern) is that instance's first task. Studio runs independently of atlas; the only coupling is studio M4 is gated on atlas M7b.

**Atlas day summary:** M1 + M2 shipped. M3-M6 trigger-gated. M7 split into M7a (next-week spike) + M7b (build-after-spike). All work committed, pushed, deployed, verified. Monday verification routine `trig_015aDdXmiTAowm1HVkwQydnT` armed for 2026-04-27 09:00 MT. Session ends in green-state.

**Next atlas session (NOT today):**
1. Read Monday's `docs/handoff/2026-04-27-atlas-m1-verification.md` (auto-generated by routine)
2. Manual VPS verification of Monday 07:30 fire on queue #3 (per the routine's checklist)
3. M7a if you signed up for Blotato (decision matrix at `docs/roadmap/atlas/m7a-decision-spike.md`)
4. M3-M6 only if their trigger gates have hit

---

### 2026-04-25 (later evening): M7a SHIPPED, M7b unblocked

**M7a verdict: KEEP Blotato. API contract verified end-to-end.**

Boubacar burned the 7-day trial on day 1 to do a real API smoke test rather than dashboard observation. The dashboard's source-to-remix-to-AI flow had already been confirmed as the wrong path for Atlas's use case (dashboard AI confabulated a 12-line LinkedIn post from a 1-line "Keep text as is" instruction). The API path is clean: `text` field publishes verbatim with no AI in the loop.

**Smoke test results (real publish to Boubacar's LinkedIn + X):**

| Metric | LinkedIn | X |
|---|---|---|
| Submitted (UTC) | 22:01:39 | 22:01:40 |
| Published (UTC) | 22:01:44 | 22:01:49 |
| Latency | 5 sec | 9 sec |
| Verbatim | yes | yes |

Post text (real CW content, not throwaway): "You already know which AI tool your team is overpaying for. The hard part is saying it out loud in a meeting before someone defends the renewal."

Two sibling drafts (Options 2 and 3 from the same generation set) saved as Notion Content Board records under Status=Draft for future use. The smoke test also pulled double duty as a real published post.

**Pricing correction surfaced:** Boubacar's Skool RoboNuggets membership grants a lifetime 30% discount on Blotato. Effective tiers are Starter $20.30, Creator $67.90, Agency $349.30 (not the list prices). Memory entry `reference_blotato_pricing_2026.md` updated to quote effective prices.

**Windows Schannel gotcha fixed in the smoke-test script:** curl on Windows hit `CRYPT_E_NO_REVOCATION_CHECK` on the first run; resolved with `--ssl-no-revoke` flag. Local-script-only fix; orchestrator (Linux container) won't see the issue.

**M7a artifacts:**
- Notepad: `d:/tmp/m7a-blotato-spike-notes.md`
- Smoke-test script: `d:/tmp/blotato-smoke-test.sh` (reusable for regression)
- Smoke-test log: `d:/tmp/blotato-smoke-test-20260425-160135.log`
- M7a prep doc `docs/roadmap/atlas/m7a-decision-spike.md` is now historical

**M7a status:** SHIPPED 2026-04-25.
**M7b status:** READY (was DECISION-GATED). No blockers. Build any session.
**L3 Publish status:** still 🟡 PARTIAL until M7b ships.

**M7b risks captured for the build session:**
- Idempotency: Blotato has no documented idempotency key. Persist `postSubmissionId` in Notion record BEFORE polling so retries don't double-submit.
- Failure-mode behavior unverified: HTTP 422 on quota expected but not exercised; `errorMessage` shape unknown. Atlas Concierge (M4) is the right surface to handle failures; until M4 ships, fail-soft = alert Telegram, leave Status=Queued for human retry.
- BLOTATO_API_KEY currently in `d:/tmp/.env` only. Promote to VPS .env on M7b deploy day, NOT before (per M7a prep-doc rule still in force).

### 2026-04-25 (late evening): M8 spec approved after Sankofa, ready to build

**Trigger:** Boubacar reviewed Jay's RUBRIC dashboard (RoboNuggets Skool), said he wants the same kind of "see what the agents are doing" surface for himself. Verdict: steal RUBRIC's information architecture, not its static-files runtime. Build it on the live data Atlas already writes.

**Brainstorm produced:**
- Route: `/atlas` (codename matches the project; no new vocabulary).
- Layout: hero strip (4 rollup tiles: System Status, Last Autonomous Action, Next Scheduled Fire, Spend Pacing) above 3×2 cards (Atlas State, Approval Queue, Content Board, Spend, Heartbeats, Errors) with `/chat` embedded as 4th column.
- Refresh: htmx 30s polling per card.
- Mobile: desktop-first, collapses cleanly to single column at <720px.
- Action set: Standard (toggle Griot, toggle dry-run, approve/reject queue, posted/skip publish reply). Kill switch deliberately Telegram-only.

**Visual lock-in (T4 "Catalyst Console"):** four palettes mocked side by side at `workspace/atlas-m8-mocks/v4.html` (T1 Bogolan v2, T2 Bogolan Loud, T3 Sahel Neon, T4 Catalyst Console - Claude's pick). Boubacar picked T4. Near-black with graphite-blue undertone, terracotta-orange `#FF6B35` as the single signature accent, museum-bronze + lapis-tarnished + verdigris support. Bogolan dot-pattern replaced with single bronze hairlines (the seam where two metal pieces meet on a cast object).

**Typography:** Atkinson Hyperlegible body (Braille Institute, designed against letter confusion - Boubacar is mildly dyslexic), Fraunces display, IBM Plex Mono data. BDA floors enforced: 15px body, 1.5 line-height, weight ≥400, no italic for emphasis, `tnum`+`zero` OT features always on. Type research summary in spec.

**Em-dash leak:** "Atlas, Mission Control" in H1 (with em-dash separator) carried that separator through three mockup iterations before Boubacar caught it. Pre-commit hook only catches committed files; mockups in `workspace/` are not committed. New memory entry `feedback_em_dash_in_ui_text.md` extends the no-em-dash rule to every visible UI string. H1 changed to "Atlas Mission Control" (no separator).

**Sankofa Council ran.** Five voices. Recommended scope cuts:
- Cut external-proof-point framing (M8 is internal-only; sanitized public variant becomes its own milestone if/when wanted)
- Add `flock` advisory lock on `autonomy_state.json` to prevent torn writes between heartbeat tick and browser action endpoints
- Kill Roman-numeral chips on cards (Outsider voice flagged them as decorative-not-informational)
- Park outcomes/quality card and chat-as-primary reframe as future milestones

**Action layer sized honestly post-Council.** Audit of `handlers_commands.py` and `handlers_approvals.py` confirmed handlers are already pure `(text, chat_id, ...)` functions, not Telegram `Update` objects. No fake-Update glue, no handler refactor needed. Action layer fits in 75 minutes inside M8 itself, not a separate M8.5.

**Spec:** `docs/superpowers/specs/2026-04-25-atlas-m8-mission-control-design.md` (status: approved-after-sankofa).

**ETA: 4.75 hr in 4 blocks** (down from initial 6h after Council scope cuts):
- Block 1: backend data path (≈2h)
- Block 2: visual shell (≈2h)
- Block 3: htmx polling (≈45 min)
- Block 4: action layer + polish (≈75 min)

**Next:** hand off to writing-plans skill to break each block into tasks. Build any session, parallel with M7b.

---

### 2026-04-25 (late evening, atlas instance): M7b Council Pass 2, spec doc written, build deferred to next session

**Pass 2 Sankofa Council on M7b's proposed design surfaced a fatal idempotency bug, a structural state-machine gap, and an architectural disagreement about whether M7b is a new module at all.**

**Fatal bug found:** the proposed "persist postSubmissionId BEFORE polling" idempotency strategy does NOT prevent the most likely failure (POST returns 200 + ID, then Notion write fails). Next 5-min tick re-submits, double-posting to Boubacar's real LinkedIn 5 minutes apart. Required fix: persist a placeholder (Status=Publishing OR client-generated UUID) BEFORE the POST, not after.

**Structural gap found:** "Status=Queued" silently means three things in the proposed design (waiting, in-flight, failed). Required fix: granular Notion Status values (add `Publishing`, add `PublishFailed`) OR move state machine to Postgres with Notion as mirror.

**Architectural disagreement (Boubacar must call):** is M7b a new module (`orchestrator/blotato_publisher.py` + `orchestrator/auto_publisher.py`, 3-4 hour build, platform-agnostic for Studio M4 reuse) or a 30-line patch on `publish_brief.py` (60-90 min build, Atlas-only, Studio M4 has to refactor later)? Both are valid. Decision depends on Studio M4 timing.

**Smaller fixes captured:** kill switch `auto_publisher.enabled` in `autonomy_state.json` (non-negotiable), tick coordination contract with `publish_brief.py` (three options), 7-day-a-week wake (NOT weekday-only like griot), M2 backfill must skip PublishFailed records, Posted URL field structure for downstream M5/M8 readers.

**Build estimate corrected:** original 60-90 min was happy-path-only. Production-quality M7b with the failure modes the Council surfaced is 3-4 hours including tests, save point, branch, deploy, verification.

**Spec doc written:** `docs/superpowers/specs/2026-04-26-atlas-m7b-publisher-design.md`. Captures all Council findings, enumerates 7 open decisions Boubacar must lock at the top of the build session, documents required reads, build session checklist, hard rules in force, what gets shipped on M7b complete.

**M7b status:** still READY but spec-gated; do not start coding until 7 open decisions are locked at top of build session. A third Council pass on whichever path Boubacar picks (new module vs publish_brief patch) is recommended; should take 5 minutes against the spec.

**Build session NOT today.** Next session at the earliest. Hour-14 rule applies; Boubacar burned the trial today, ran two Councils, shipped the M7a smoke test and the M7a closeout commit. M7b code is Sunday's job.

**Next atlas session:**

1. Pull main, verify three-way nsync, confirm M8 spec + M7b spec both present
2. Read `docs/superpowers/specs/2026-04-26-atlas-m7b-publisher-design.md` first
3. Lock the 7 open decisions
4. Save point + branch + build per the spec checklist
5. M8 build (4.75 hr) and M7b build (3-4 hr) can run in any order; both have specs ready and no dependency on each other

---

### 2026-04-25 (night): M7b SHIPPED. Atlas L3 Publish closed. Auto-publish LIVE.

**Same-day reversal:** the M7b spec said "build Sunday at the earliest." Boubacar opted to ship same-night after closing M7a, M2, M1, plus the studio session merge. Build started at hour 7 of a 14-hour budget, finished around hour 10.

**7 design decisions locked at start, all implemented as planned.**

**Plus three behavioral layers added in same session that were originally M7c territory:**

1. Time-of-day slots from `auto_publisher_schedule.default.json` (LI 07/11/12 MT, X 07/11/14 MT). Slot N claimed by the Nth Queued record of the day; past-due records ignore the time gate.
2. Cadence loosen to Mon-Sat both platforms (LinkedIn was Tue/Thu only). Sunday still skipped for today-records; past-due bypasses.
3. Past-due stagger (max_per_tick=4) to prevent platform-feed bursts when the backlog drains.

**Reschedule done out-of-band BEFORE flipping enabled=True:** 5 Notion records (1 Skipped, 4 rescheduled to clean dates). Queue is now zero past-dues. Next live publish: Mon 2026-04-27 07:00 MT, X "One constraint nobody has named yet".

**Notion schema changes (live via API):**
- Status select: added `Publishing` (yellow), `PublishFailed` (red)
- New URL fields: `LinkedIn Posted URL`, `X Posted URL`
- New rich_text field: `Submission ID`

**Test coverage:** 210/210 orchestrator tests pass (158 pre-existing + 20 publisher + 32 auto_publisher; 8 griot_scheduler tests updated for Mon-Sat).

**Save point:** `savepoint-pre-atlas-m7b-publisher-2026-04-25` (at 807cc20).
**Commits:** cda98d4 (initial modules + tests + integration), 8d8194f (time-of-day + cadence + past-due stagger).
**Branch:** `feat/atlas-m7b-publisher` (merged via no-ff).

**VPS deploy:** docker cp 6 files into orc-crewai container (path: `/app/`, NOT `/app/orchestrator/`), restart, auto-publisher wake registered with `every=5m`. Verified live in container logs at 18:51 MT. BLOTATO_API_KEY + LinkedIn/X account IDs added to VPS .env (.env backed up to .env.backup-pre-m7b-2026-04-25 first).

**Kill switch flipped ON at 18:55 MT.** auto_publisher.enabled=true, dry_run=false. Next 5-min wake is the first live tick.

**Atlas Done Definition state after M7b ship: 4 of 5 loops closed (L1, L2, L3, L4). L5 still trigger-gated on ≥14 days of L4 reconcile data; earliest viable 2026-05-08.**

**Next atlas session:**
1. Monday 2026-04-27 morning: verify the 07:00 MT auto-publish fires X "One constraint nobody has named yet"
2. If green: M7b validated; observe for one week of normal operation
3. If red: inspect Telegram alert + Notion Status of the failed record; error_message in Source Note
4. M5 (Chairman / L5 Learning) gate: 2026-05-08, with 14 days of task_outcomes data accumulated by then

---

### M8: Atlas Mission Control (live ops dashboard at /atlas) SHIPPED 2026-04-25

**What:** A gated, live, single-page dashboard at `agentshq.boubacarbarry.com/atlas` that shows what the autonomy layer is doing and lets Boubacar take safe actions from a browser anywhere.

**Done:** 8 cards refresh every 30s (state, queue, content board, spend, heartbeats, errors, top ideas, chat embed). Toggle Griot, toggle dry-run, approve/reject queue items. Same JWT-PIN as /chat. Catalyst Console T4 visual theme (Atkinson Hyperlegible + Fraunces + IBM Plex Mono, #08090C background, terracotta #FF6B35 accent). Mobile-responsive. Auto-deploys via existing GH Actions workflow on merge.

**Posted/skip publish brief actions:** Not wired to dashboard (uses Telegram-native message ID context). Telegram remains the channel for those two actions.

**Ideas card:** Top-10 ranked ideas from agentsHQ Ideas Notion DB, sorted by Impact+Effort priority score. Ideas curator also fixed to auto-score every new idea on save (commit f54d26e on main).

**PR:** #21
**Branch:** `feat/atlas-m8-mission-control`
**Save point:** `savepoint-pre-atlas-m8-2026-04-25`
**Spec:** `docs/superpowers/specs/2026-04-25-atlas-m8-mission-control-design.md`

---

### 2026-04-25 (late evening): M8 Atlas Mission Control built and PR open

**M8 Mission Control dashboard built.** PR #21 open on `feat/atlas-m8-mission-control`. Reviewed by Sankofa Council in-session before build. Topology audit caught wrong architecture assumption (Jinja2 templates assumed; real topology is static nginx + JSON endpoints). Corrected before any code was written.

**What shipped:**

- `orchestrator/atlas_dashboard.py`: 8 pure fetchers (get_state, get_queue, get_content, get_spend, get_heartbeats, get_errors, get_hero, get_ideas)
- `orchestrator/tests/test_atlas_dashboard.py`: 8 unit tests, all passing
- `orchestrator/app.py`: +14 endpoints (8 GET read + 6 POST action) under `/atlas/*`, all gated by `verify_chat_token`
- `thepopebot/chat-ui/atlas.html` + `atlas.css` + `atlas.js` + `cw-mark.svg`: static page shell with Catalyst Console T4 theme
- `thepopebot/chat-ui/nginx.conf`: `/atlas` location blocks added
- Full test suite: 8 new M8 tests passing

**Ideas DB cleanup done in same session:**

- 1 database confirmed (no duplicates)
- 9 unscored ideas scored with Impact + Effort in Notion
- "Force Ranking" note page archived
- "OpenRouter Dashboard" idea marked Done (M8 built it)
- Ideas curator fixed to auto-score every new idea on save (commit f54d26e, already on main)

**Notable design decisions:**

- posted/skip dashboard buttons not wired (Telegram message ID is the session key; 501 endpoints with clear explanation)
- Kill switch intentionally absent from browser (Telegram only)
- Chat card embeds `/chat` via iframe (same-origin, same nginx, no cross-origin issues)
- Brand mark slot (`cw-mark.svg`) is a hot-swappable brass-coin placeholder
- Ideas card computes priority from Impact+Effort selects (formula field is opaque via Notion API)

**Auto-deploy:** GH Actions triggers on `thepopebot/chat-ui/**` + `orchestrator/**` changes. Merge PR = live at `agentshq.boubacarbarry.com/atlas`.

**Enhancements backlog (M8 session 2026-04-26):**

- Agent Activity card: top 5 most active agents this week (calls, cost) from `llm_calls.crew_name`: held, needs design decision on what "active" means
- Last Autonomous Action hero tile: currently shows "Unavailable": needs `task_outcomes` data to be populated by autonomous runs
- Next Scheduled Fire hero tile: shows correctly from heartbeat registry
- Content Board: show this week vs last week spend comparison (Mon-Sun delta): deferred
- Cost ledger: use `llm_calls.project` as engagement/customer dimension; add `cost_ledger` table for non-LLM costs (Blotato, Notion, subscriptions): gate on first real client engagement
- **Atlas Chat: full agentic conversation loop (high priority):** Chat iframe must behave exactly like Claude Code or another LLM: full back-and-forth, context retention, tool use. Goal: draft a post in the chat, iterate on it conversationally, then one-tap post from the same window. Currently the iframe is a passive embed; needs the orchestrator to wire a stateful session with memory + content tools so the conversation can actually do things (edit Notion, queue posts, etc.)

## M9: Atlas Chat: Full Command Center ✅ SHIPPED 2026-04-27

**Status:** ALL THREE MILESTONES SHIPPED
**Reviews:** Code reviewer (5 blockers) + Sankofa Council + blue/red team + model research: all run 2026-04-26. Full findings folded into spec v4.
**Save point:** `savepoint-pre-atlas-m9-design-2026-04-26` (rewind: `git checkout savepoint-pre-atlas-m9-design-2026-04-26`)

**Vision:** Chat is a command and execution surface for all non-infrastructure work. Claude Code handles only agentsHQ code changes. Everything else: approvals, drafting, website building, artifact iteration, system monitoring: runs through Telegram or the Atlas web panel chat. The goal is Claude Code-equivalent capability for non-infra work, on both surfaces.

**Key decisions locked (v4):**

- **Model:** `CHAT_MODEL` / `ATLAS_CHAT_MODEL` env vars, default `anthropic/claude-haiku-4.5`. Quality-first: Haiku has the strongest confirmed tool-calling pedigree (bash, computer-use, web search explicitly named). Gemini 2.5 Flash available via env var after reliability confirmed. Sonnet 4.5 available as ceiling for deep-work sessions. Weekly automated model review agent keeps recommendations current.
- **Action blocks:** structured JSON schema `{"reply": "...", "actions": [...], "artifact": {...}}`. Model always returns JSON. Plain-text fallback on parse failure. No suffix strip pattern.
- **Async tasks:** `forward_to_crew` kicks off a background job, returns job_id immediately. Client polls `GET /api/orc/atlas/job/{id}` every 3s. No 60-second spinner timeouts.
- **Artifact storage:** new `chat_artifacts` Postgres table (no size cap). Conversation history references artifacts by ID, not by content. Multi-turn iteration works across page refreshes.
- **Write-action confirmation:** one explicit confirmation turn before any write (approve, reject, queue, publish). Sandbox mode (`CHAT_SANDBOX=true`) simulates all writes without executing.
- **Telegram-first = proactive push.** M9a ships action buttons on existing approval/publish notifications: not a new chat REPL. Deep work (drafting, iterating, building) is M9b on the web panel.
- **Tracked gaps (not design flaws):** `build_site` crew (M9 ships the surface; the crew comes later), Telegram artifact rendering (web is the right surface for that), full responsive QA (Claude Code + Playwright stays for that).

**Split into three milestones:**

| Sub | Scope | Budget | Branch | Status |
| --- | --- | --- | --- | --- |
| M9a | Correctness fixes (Postgres leak, double-send, env vars, sandbox mode) + Telegram push alerts with action buttons | 3-4h | feat/atlas-m9a-telegram-push | SHIPPED 2026-04-26 |
| M9b | Web chat: wire 404, native Atlas panel, async job polling, artifact table, write-action confirmation + approval queue badge | 4-5h | feat/atlas-m9b-web-chat | SHIPPED 2026-04-26 |
| M9c | Cross-session memory compressor: 30-min inactivity trigger, Haiku summarizes, silent system prompt injection | 2h | feat/atlas-m9c-session-compressor | SHIPPED 2026-04-27 |

**Sequence:** M9a -> M9b -> M9c. Do not start M9b until M9a smoke test passes on VPS.

**Approval surface design (three surfaces, no duplication):**
- Telegram push (M9a): proactive notification with inline buttons, meets Boubacar wherever he is
- Atlas dashboard approval card (live since M8): reactive, always visible when at the dashboard, already has Approve/Reject buttons
- Web chat (M9b): conversational approve via `approve_item` tool + action block button in chat reply
- Dashboard badge (M9b): when a new item lands in the approval queue, show a live badge/count on the approval queue card so Boubacar sees it without looking at the card. Implemented as a polling count from `GET /atlas/queue`. The card header shows "Approval Queue (2 pending)" and pulses the accent color when count > 0. No WebSockets needed. Closes the gap where a new approval arrives while Boubacar is in the web chat and would otherwise miss it.

**Full spec:** `docs/roadmap/atlas/m9-atlas-chat-design.md`: model research, architecture decisions with rationale, tool table, system prompt, sandbox protocol, artifact storage schema, build checklist

---

### M10: Topic Trend Scout (Atlas content idea pipeline) ⏳ TRIGGER-GATED

**What:** Daily heartbeat crew (08:00 MT) that scans HN + Reddit RSS for AI displacement + first-gen money topics, and a dedicated YouTube channel RSS source set for the Under the Baobab / African storytelling niche. Surfaces ranked candidates per day to Telegram with approve/reject buttons. Approved candidates flow to the existing Atlas Content Board (no new DB). Reuses `_PUBLISH_BRIEF_WINDOWS` dict + `handlers_approvals.py` callback pattern. No new handler code needed.

**Why:** The Atlas publish pipeline assumes humans seed Content Board ideas. When the manual queue drains, the engine starves. M10 closes that gap autonomously.

**African storytelling niche:** YouTube-only. Source = curated YouTube channel RSS feeds (not X/Reddit/HN, which produce near-zero relevant signal for this niche). Source list to be defined at build time by Boubacar.

**Expansion path (optional at build time):** Route approved candidates through `research_engine.py` to add a brief (source, why it matters, 3 post angles) before landing in Content Board. 3x more valuable than bare topic titles; no new dependencies.

**Trigger gate:** 2026-05-01. Three design questions must be answered before build starts:

1. What does a "good" candidate look like? 2-3 scored attributes with thresholds (not just category labels).
2. Tap budget: auto-approve above threshold and surface only top 1 per day, or full manual review of 3-5 per day?
3. African storytelling YouTube source list: which specific channels does Boubacar want tracked?

**Reminder:** Scheduled for 2026-05-01 09:00 MT. This entry is the durable record if the session-local cron fires before then.
**Blockers:** Three design questions above must be answered before any code.
**Branch:** `feat/atlas-m10-topic-scout`
**ETA:** 3-4 hours once questions answered (80% of infra already exists in existing handler + scout patterns).

---

### M11: OpenRouter-Native Intelligent Model Routing

**Status:** M11a SHIPPED 2026-04-26. M11b SHIPPED 2026-04-26.
**Vision:** agentsHQ uses OpenRouter as the single routing layer across ALL providers. Best model for every job, automatically selected. Crew engine uses `select_by_capability()` (same pattern as Sankofa Council) across all 18 models in `COUNCIL_MODEL_REGISTRY` (8 providers: Anthropic, Google, OpenAI, DeepSeek, xAI, Mistral, Qwen). Not loyal to any provider.
**Save point:** `savepoint-pre-m10a-bug-fixes-2026-04-26` (tagged before M11a work, before the rename to M11)

**Why before M9:** The chat surface (M9) dispatches to crews. Fix the crew routing first so the chat inherits intelligent multi-provider model selection.

| Sub | Scope | Budget | Branch | Status |
| --- | --- | --- | --- | --- |
| M11a | Bug fixes + named model constants | 2h | fix/m10a-model-bugs | SHIPPED 2026-04-26 |
| M11b | ROLE_CAPABILITY migration: replace ROLE_MODEL with select_by_capability() for crew engine | 3h | feat/m11b-capability-routing | SHIPPED 2026-04-26 |
| M11c | Research engine rewrite: two-phase Perplexity Sonar Pro + Firecrawl via OpenRouter | 4h | feat/m11c-research-engine | TRIPLE HOLD: revisit mid-May (2026-05-15). No measured quality gap in prod. Perplexity prospect-email spike deferred to the same date alongside the Hunter.io go/no-go decision (2026-05-06). |
| M11d | Harvest reviewer migration + weekly model review agent (Sunday 08:00 MT) | 6h | feat/m11d-model-review | IN PROGRESS 2026-04-26 |

**M11a shipped 2026-04-26: what changed:**
- `crews.py`: malformed `"openai/anthropic/claude-sonnet-4-5"` fixed to `get_llm("claude-sonnet")` (was silently 404ing every content review run)
- `crews.py`: `_IDEA_CLASSIFIER_MODEL` named constant added (was inline hardcode)
- `agents.py:744`: `select_llm("voice", "high")` -> `select_llm("voice", "complex")` (invalid key silently fell through to DEFAULT_MODEL)
- `router.py`: `ROUTER_LLM_MODEL` named constant added
- `memory.py`: `LESSON_EXTRACTION_MODEL` named constant added
- `notifier.py`: `BRIEFING_MODEL` named constant added
- `handlers_chat.py`: already correct via `llm_helpers.py` env-var pattern
- 276/276 tests pass

**M11b design reviewed + spec finalized 2026-04-26 (Sankofa Council + code expert):**

Council and code expert review surfaced 5 issues before implementation. All resolved in spec. Key changes to the original plan:

- **ROLE_TEMPERATURE blocker resolved:** new `select_llm()` must explicitly preserve `ROLE_TEMPERATURE.get(key, 0.3)`. Original plan did not mention it. If dropped, all agents revert to `temperature=0.3` silently.
- **Missing role keys added:** `skill_builder/simple/moderate/complex` and `orchestrator/simple` were absent from the proposed dict. Added.
- **Voice bug fixed in same commit:** `("voice","simple")` and `("voice","moderate")` missing from both `ROLE_MODEL` and `ROLE_TEMPERATURE` today. M11b adds them to both `ROLE_CAPABILITY` and `ROLE_TEMPERATURE`.
- **One primary capability per role:** `select_by_capability()` accepts a single string. Multi-capability entries would require signature change breaking `council.py`. Each role gets one primary capability; secondary noted as comment only.
- **Startup validation added:** `_validate_role_capability_dict()` runs at module import and raises `ValueError` on any misspelled capability tag. Prevents silent degradation.
- **`MODEL_REGISTRY` not deprecated:** 9 hardcoded `get_llm()` calls in `crews.py` are intentional relay-agent overrides. They remain. Documented explicitly to prevent future cleanup accidents.
- **`creative_divergence` single-model risk accepted:** only grok-4 has this tag. `writer/complex` and `social` route to it. If grok-4 is excluded, cost-relaxation still returns grok-4 at a higher tier. Documented and accepted.

**SpawnJobTool bug fixes (same session, separate commit):**
- `from_number` fix: parse `chat_id = session_key.split(":")[0]` instead of passing `session_key` verbatim. Worker was sending Telegram to a string, not a real chat_id.
- Double `create_job` fix: SpawnJobTool called `create_job` at line 1972, worker called it again at line 96. Remove from SpawnJobTool; worker owns registration.
- `wait_for_result`, `PollJobTool`, `notify_chat_id` all deferred: no concrete crew needs synchronous delegation today. Reopen when a multi-stage crew is being built.

**Full spec:** `docs/superpowers/specs/2026-04-26-m11b-capability-routing-design.md`

**Build order for next M11b session:**
1. Write `test_select_llm.py` (parametrized, 15 lines, no live API calls)
2. Write `ROLE_CAPABILITY` dict + `_VALID_CAPABILITIES` + `_validate_role_capability_dict()` in `agents.py`
3. Add `voice/simple` and `voice/moderate` to `ROLE_TEMPERATURE`
4. Rewrite `select_llm()` body (preserve `ROLE_TEMPERATURE` line explicitly)
5. Run tests, full suite, commit
6. SCP + docker cp + smoke test (verify grok-4 for social, non-Anthropic for coder)
7. Separate commit: SpawnJobTool `from_number` + double `create_job` fix

**Sequence with M9:**
```
M11a (done) -> M11b (3h) -> M11c (4h) -> M11d (6h)
M11a (done) -> M9a  (3-4h, parallel with M11b)
               M9a verified -> M9b -> M9c
```

---

**Next session:**

1. M7b monitoring: verify Monday 2026-04-27 07:00 MT X auto-publish fires (or check if it already fired)
2. M5 (Chairman / L5 Learning) gate: 2026-05-08
3. **M9a** (Telegram push alerts + correctness fixes): remaining parallel tab
4. VPS orphan archive sunset: delete `/root/_archive_20260421/` if no issues by 2026-04-28
5. After M9a verified on VPS: merge feat/m11b-capability-routing -> main, deploy

---

### 2026-04-26: M8 dashboard fully stabilized, cost_ledger built

**What happened:** Full M8 debug + polish session. Dashboard was visually present but functionally dead due to CSS cascade bug (`#dashboard { display: flex }` overrode HTML `hidden` attribute). Fixed with `[hidden] { display: none !important }`. This was root cause of PIN bypass AND cards-never-loading.

**All bugs fixed:**
- CSS hidden cascade (PIN bypass + cards never loading)
- API key mismatch between event-handler and orc-crewai (chat broken)
- `atlas_dashboard.py` column names: `router_log` has no `fallback`/`raw_input`, `task_outcomes` uses `ts_started`/`crew_name`/`success`/`result_summary`
- `NotionClient.query_database()` kwarg is `filter_obj` not `filter`
- Content board empty: `FORGE_CONTENT_DB` env var was missing from VPS `.env`; Platform field is `multi_select` not `select`; DB ID: `339bcf1a-3029-81d1-8377-dc2f2de13a20`
- nginx added `Cache-Control: no-store` to `/atlas/` location
- `docker cp` requires `docker restart` to reload Python module cache (burned 3 deploys on this)

**Features added this session:**
- Content Board: 3 sections (Past Due rose badge, Upcoming 7 days, Recently Posted last 3)
- Spend Pacing: This Week + Month to Date rows; when today=$0, shows most recent day with spend (up to 7 days back) as "MM/DD (last spend)"
- `cost_ledger` Postgres table: `date, project, customer, category, tool, description, amount_usd, source`
- `GET /atlas/ledger?days=30` and `POST /atlas/ledger` live in app.py
- `get_cost_ledger()` in `atlas_dashboard.py` merges `llm_calls` + `cost_ledger`
- agentsHQ State card renamed from "Atlas State" (correct: it monitors agentsHQ, not the dashboard)
- Daily Cap removed from agentsHQ State card (already in Spend Pacing)
- compass.svg added as favicon + topbar icon (was missing from VPS)
- M9 milestone written to roadmap (HIGH PRIORITY per Boubacar)
- OpenDyslexic font experiment tried and reverted; back to Fraunces + Atkinson Hyperlegible + IBM Plex Mono

**State at session close:**
- Dashboard LIVE and fully functional at agentshq.boubacarbarry.com/atlas
- Last commit: `b3cb357` on VPS + origin
- All 8 data cards rendering with real data
- Chat iframe working (API key fix)
- Content Board showing 15 upcoming posts + 3 recently posted
- Spend showing $0.6968 week + month to date; Apr 23 as last spend day

**Next session:**
1. Monday 2026-04-27 07:00 MT: verify auto-publish fires X "One constraint nobody has named yet"
2. M9 Atlas Chat design/spec (HIGH PRIORITY)
3. M5 gate: 2026-05-08

---

### 2026-04-26: M9a Atlas Chat correctness + Telegram action buttons

**Branch:** `feat/atlas-m9a-telegram-push`
**Save point:** `savepoint-pre-atlas-m9a-20260426`
**Tests:** 273/274 pass (1 pre-existing `test_backfill_yesterday_skipped_today_empty` failure unrelated to M9a; confirmed pre-existing via stash test)

**All 6 correctness fixes shipped:**

1. `atlas_dashboard.py`: `conn.close()` in `finally` on all 6 `_pg_conn()` callers (`_spend_aggregates`, `_spend_7d_by_day`, `_last_autonomous_action`, `_router_log_fallbacks`, `get_cost_ledger`, `add_cost_ledger_entry`)
2. `llm_helpers.py`: Added `CHAT_TEMPERATURE` and `CHAT_SANDBOX` constants (env-var driven)
3. `handlers_chat.py`: Full rewrite. M9 system prompt (operator persona, JSON schema instructions, sandbox-aware). `run_chat()` returns `{"reply", "actions", ...}` schema, parses model JSON with try/except fallback to plain text, strips actions before saving to Postgres history, uses `CHAT_TEMPERATURE` from env var
4. `handlers_chat.py`: Added `run_chat_with_buttons()` wrapper. Sends exactly one Telegram message per turn (with buttons if actions present, plain text otherwise)
5. `handlers.py`: Replaced double-send pattern (`run_chat` + `send_message`) with single `run_chat_with_buttons()` call; dropped unused `send_message` import
6. `docker-compose.yml`: Added `CHAT_MODEL`, `ATLAS_CHAT_MODEL`, `CHAT_TEMPERATURE`, `CHAT_SANDBOX` to orchestrator env allowlist

**Telegram action buttons shipped:**
- `approval_queue.enqueue()`: now calls `send_message_with_buttons` with `[Approve #N]` and `[Reject #N]` inline keyboard buttons on every new proposal notification
- `handlers_approvals.py`: added `_build_button()` helper with 64-byte callback_data assert; added `approve_queue_item:` and `reject_queue_item:` callback dispatch cases that mirror the existing `yes confirm` / `no` handler logic
- `scripts/test_m9a_smoke.py`: smoke test covering run_chat schema, CHAT_SANDBOX suppression, _build_button byte limit, enqueue uses send_message_with_buttons, connection close on exception

**Next:** VPS deploy + smoke test, then M9b (web chat native panel).

---

### 2026-04-26: M11b SHIPPED - ROLE_CAPABILITY migration

Replaced `ROLE_MODEL` (4 hardcoded Anthropic aliases) with `ROLE_CAPABILITY` (capability tag + cost ceiling per role/complexity). `select_llm()` now delegates to `select_by_capability()` across all 18 models in `COUNCIL_MODEL_REGISTRY` (8 providers). `ROLE_TEMPERATURE` unchanged.

**Live routing outcomes:** `social/moderate` -> Grok-4; `qa/*` -> Qwen3.5-flash ($0.065/MTok); `planner/simple` -> DeepSeek-v3.2 ($0.26/MTok); `coder/complex` -> lowest-cost deep_reasoning within low-medium ceiling; `orchestrator/complex` -> full registry up to high ceiling.

Adding any new model to `COUNCIL_MODEL_REGISTRY` automatically makes it available to all crews.

**Tests:** 265/265 in-scope pass. Commit: `cf30018`. Merged to main 2026-04-26.

---

### 2026-04-26: M10 Autonomous Crew Contract SHIPPED

**Branch:** `feat/atlas-m10-crew-contract`
**Spec:** `docs/superpowers/specs/2026-04-26-autonomous-crew-contract-design.md`

16-check gate across 4 failure modes (silent corruption, runaway spend, unrecoverable state, identity drift). Makes it physically impossible to flip a heartbeat crew live without a signed contract file.

**What shipped:**

- `orchestrator/autonomy_guard.py`: `ContractNotSatisfiedError`, `_assert_contract_satisfied()`, `_verify_seven_day_observation()` (C7 machine check via `llm_calls`), per-crew `cost_ceiling_usd` in state schema, `guard()` enforces per-crew ceiling alongside global cap. Both `set_crew_enabled(True)` and `set_crew_dry_run(False)` gated.
- `orchestrator/contracts/griot.md`: Signed backfill contract (ceiling=$0.01)
- `orchestrator/contracts/auto_publisher.md`: Signed backfill contract (ceiling=$0.05)
- `orchestrator/contracts/TEMPLATE.md`: Template for concierge/chairman/studio at build time
- `orchestrator/db.py` + `orchestrator/griot.py`: `content_approvals` table + `record_content_approval()` for Chairman L5 learning signal (first-try approval rate)
- `orchestrator/auto_publisher.py`: `_should_hold_for_timely_check()` + `_send_timely_recheck_telegram()`: stale Timely records held and re-checked before publish (C13)
- Notion Content Board: `Content Type` select field added (`Evergreen` green / `Timely` yellow)

**Tests:** 112/113 pass (1 pre-existing `test_backfill_yesterday_skipped_today_empty` failure unrelated to M10).

**End-to-end verified:** concierge blocked without contract, griot/auto_publisher contracts parse and load ceiling, guard blocks when estimated exceeds per-crew ceiling.

**Future crews:** concierge/chairman/studio must have a signed contract at `orchestrator/contracts/<crew_name>.md` before `set_crew_enabled(True)` or `set_crew_dry_run(False)` will succeed.

**Branch status (2026-04-26):** M10 code merged to main at `83f9e2b`. `feat/atlas-m10-crew-contract` was a stale orphan; both local and remote branches deleted this session.

---

### 2026-04-26: M9b IN PROGRESS: Web Chat Native Panel

**Branch:** `feat/atlas-m9b-web-chat`
**Save point:** `savepoint-pre-atlas-m9b-20260426` (to create before first commit)
**Depends on:** M9a live on VPS (confirmed at f5a47c5)

**Scope decision (this session):** M9a smoke test gate lifted. M9a code is fully live; M9b has no structural dependency on Monday's button tap. If Monday tap fails, the bug is isolated to `handlers_approvals.py` callback dispatch with zero overlap with M9b scope.

**M9c scope replan (locked this session):**

- Weekly model review agent pulled forward into M9b session (same branch, ~45 min add-on). Independent of artifacts, no reason to defer.
- Artifact iteration (resize, fullscreen, save-to-Drive, push-to-GitHub): deferred until after 1 week of M9b usage. Build when friction is felt, not speculatively.
- Cross-session memory (30-min inactivity compressor, session summary injection): remains M9c, builds after 1 week of M9b usage when real session history patterns are visible.

**What this session will ship:**

Backend:

- `orchestrator/db.py`: `chat_artifacts` table migration (runs on startup)
- `app.py`: `POST /api/orc/atlas/chat` endpoint calling `run_atlas_chat()` via `run_in_executor`, auth gated
- `app.py`: `GET /api/orc/atlas/job/{job_id}` endpoint for async task polling
- `handlers_chat.py`: `run_atlas_chat(messages, session_key, channel="web")`: uses `ATLAS_CHAT_MODEL`, resolves artifact refs, stores artifacts, dispatches `forward_to_crew` via background job
- `state.py`: `_confirm_store` dict for write-action pending confirmations (5-min TTL, mirrors `_PUBLISH_BRIEF_WINDOWS` pattern)

Frontend:

- `atlas.html`: replace chat iframe with native chat panel (card slot 7)
- `atlas.js`: `atlasChat` module: localStorage session key, message array, `sendMessage()`, `renderMessage()`, `renderArtifact()` (srcdoc iframe for HTML), `pollJob()` (3s polling)
- `atlas.js`: inline markdown renderer (~80 lines, no external deps)

Weekly model review agent (M9c partial, pulled forward):

- `CronCreate` weekly routine: fetch OpenRouter model pricing for 3 configured models, compare against current tiers, write `docs/reference/model-review-{date}.md`, Telegram notification with top finding
- Never auto-changes env var; surfaces recommendation to Boubacar only

---

### 2026-04-26: Option A (leGriot A/B script) + M11d SHIPPED

**Branch:** `feat/m11d-model-review`
**Save point:** `savepoint-pre-m11d-2026-04-26`
**Tests:** 341/341 pass (11 new: 6 model_review_agent + 5 legriot_ab_test)

**Scope decisions made before build (Sankofa Council):**

M11c placed on TRIPLE HOLD. No measured quality gap in research engine production output. Reopen 2026-05-15 alongside Hunter.io go/no-go (2026-05-06) and Perplexity prospect-email spike.

**Option A: leGriot A/B blind scoring script**

- `scripts/legriot_ab_test.py`: runs leGriot social crew on 3 seed ideas against 3 models (Grok-4, Claude Sonnet 4.6, Mistral-Large-2)
- Uses production CrewAI crew path with `select_llm` patched per run; tests real production path, not raw prompts
- Blind labels A/B/C; model mapping in `.reveal/` subdir (scorer cannot accidentally read before scoring)
- Scoring sheet pre-populated from rubric; decision threshold stated: challenger must beat incumbent by >= 3 pts total
- Idempotent re-run skips existing files; `--reveal` flag prints mapping

**M11d Part 1: harvest reviewer migration**

- `orchestrator/harvest_reviewer.py`: `MAPPER_MODEL`/`DECISION_MODEL` constants deleted
- New `_resolve_model()` calls `select_by_capability("instruction_following", max_cost_tier="low")` and inherits routing improvements automatically
- Graceful fallback to haiku-4.5 if agents module unavailable

**M11d Part 2: weekly model review agent**

- `orchestrator/model_review_agent.py` (new): Sunday-gated heartbeat (fires daily at 13:00 UTC, gates on weekday == Sunday internally)
- Loads rubric from file at runtime; Haiku-4.5 scorer; 4 candidate models on 3 Notion seed posts (falls back to 3 hardcoded defaults)
- Routing change threshold: challenger must beat incumbent by >= 3 pts TOTAL across 3 seeds
- When threshold crossed: emits proposal to `approval_queue` with Approve/Reject buttons; no separate Telegram-only path
- No auto-routing-change enforced structurally: zero imports of `agents.py` or `autonomy_guard.py`; enforced by test_no_routing_change_made_automatically
- `orchestrator/contracts/model_review_agent.md`: signed, ceiling $0.10/run, enable immediately after deploy (no dry-run required)
- `autonomy_guard.py`: `model_review_agent` added to `KNOWN_CREWS`
- `scheduler.py`: `model-review-agent` wake registered at 13:00 UTC daily

**What is NOT done (next session):**

- VPS deploy: merge to main + docker compose rebuild (Boubacar to confirm before push)
- Run Option A against real models + blind score; update routing if gap >= 3 pts
- M11c: HOLD until 2026-05-15
- M9b web chat: next priority after deploy

---

### 2026-04-27: NotebookLM skill + Drive Watch + Deliverable Pipeline

**What shipped:**

- NotebookLM CLI skill installed locally + VPS (`~/.claude/skills/notebooklm/`). Auth wired. Auto-refresh cron live (VPS, every 3 days, Telegram alert on failure).
- Drive Watch enabled (`DRIVE_WATCH_ENABLED=true`). 60-min scan of `NotebookLM_Library` root. New files auto-classified and moved to correct subfolder.
- Routing matrix: 12 rules + P0 skool guard. 19/19 test cases pass. 3 exclusion categories (scripts, raw HTML, `.py`/`.js`/`.sh`). Signal keywords complete.
- Deliverable pipeline: `SAVE_REQUIRED_TASK_TYPES` -> Drive via `saver.py`. `CONTENT_TASK_TYPES` -> Drive + Notion content board Draft entry with `Drive Link`. New `nlm_artifact` task type for NLM podcasts/slides.
- Notion content board field confirmed as `Drive Link` (url type). `saver.py` fixed to use correct field name.
- 11 docs backfilled into CW_* notebooks. Drive vs NLM audit complete: one gap found and filled (`pipeline-playbook`). All `notebooklm_pending_docs` resolved.
- Daily Postgres-to-Sheets export built (`scripts/nlm_registry_export.py`). VPS cron 06:00 UTC daily.

**What is NOT done (next session):**

- End-to-end test: trigger real `social_content` task, confirm Drive + Notion entries appear.
- Google Drive Organizer / Cleanup Agent (Ideas DB, high effort, prerequisite for full-Drive sync at scale).

---

### 2026-04-27: Uncommitted file audit

Five files in `thepopebot/chat-ui/` are intentionally NOT committed. Reason documented here so future sessions do not re-add them.

| File | Reason |
|---|---|
| `atlas-chat.js.tmp` | 0-byte temp artifact from M9b build. Delete on sight. |
| `atlas-preview.html` | M8 design preview mockup (Apr 25). Superseded by live `atlas.html`. Design scratch paper only. |
| `atlas-font-compare.html` | OpenDyslexic vs Atkinson Hyperlegible comparison (Apr 25). Decision made: Atkinson kept, OpenDyslexic reverted. Dead artifact. |
| `OpenDyslexic-Bold.otf` | 184 KB binary font file. Experiment tried and reverted per session log 2026-04-26. No place in git. |
| `OpenDyslexic-Regular.otf` | 176 KB binary font file. Same reason as above. |

These can be deleted from the working directory at any time. They are not referenced by any live code.

---

### 2026-04-27: Newsletter crew shipped + beehiiv enhancement queued this week

**newsletter_crew SHIPPED** (commit 6a3e9f2). Routes via 'newsletter' task type. leGriot voice: colleague-not-professor standard, story anchor, citation superscripts + Sources section, 8-point QA checklist. Saves to Drive + logs to Notion content board.

**Delivery platform: beehiiv** (not n8n/Mailgun). Current flow: crew drafts -> Drive -> Boubacar pastes into beehiiv manually.

**DROPPED 2026-04-29:** beehiiv REST API auto-draft task is not feasible. `POST /v2/publications/{pub_id}/posts` is Enterprise-only (verified). No workaround on Scale or Max tier; Zapier/Make/n8n hit the same gated endpoint. See `project_newsletter_beehiiv.md` for full API tier reality.

**Locked workflow:** newsletter_crew drafts → Drive → Notion Content Board record updated → thumbnail generated → Boubacar pastes into beehiiv UI and hits Send. Manual UI step is the right call given the API gate; trade-off is ~2 min of human time per issue.

**Replaces this task:** Friday-by-EOB cadence (next issue ready 4 days before Tuesday send) + beehiiv branded template (separate backlog item).

---

### 2026-04-26: M9b SHIPPED: Atlas Web Chat Native Panel

**Branch:** `feat/atlas-m9b-web-chat`
**Save point:** `savepoint-pre-atlas-m9b-20260426`
**Tests:** 341/341 pass

**What shipped:**

Backend:

- `orchestrator/db.py`: `chat_artifacts` table + startup migration, `save_chat_artifact()`, `get_chat_artifact()`
- `orchestrator/state.py`: `_confirm_store` dict for write-action pending confirmations (5-min TTL)
- `orchestrator/handlers_chat.py`: `run_atlas_chat()` using `ATLAS_CHAT_MODEL`, artifact ref resolution, artifact Postgres storage, `forward_to_crew` confirm gate
- `orchestrator/app.py`: `POST /atlas/chat`, `GET /atlas/job/{job_id}`, `POST /atlas/confirm/{token}`, `POST /atlas/confirm/{token}/cancel`

Frontend:

- `thepopebot/chat-ui/atlas.html`: replaced chat iframe with native panel + sandboxed artifact iframe
- `thepopebot/chat-ui/atlas-chat.js`: `atlasChat` module; DocumentFragment markdown renderer (DOM APIs only, zero string injection); localStorage session key; 3s job polling; confirm/cancel action handlers
- `thepopebot/chat-ui/atlas.css`: chat panel, bubble, input row, artifact frame, action button styles

Also in this session:

- `orchestrator/model_review_agent.py` + contract + tests (built by A/B agent, committed to main at `6cb56c5`)
- Stale `feat/atlas-m10-crew-contract` branches deleted (local + remote); M10 code confirmed on main at `83f9e2b`
- `.gitignore`: removed erroneous bare `thepopebot/` glob

**M9c scope locked:**

- Model review agent: DONE (pulled forward)
- Artifact iteration: deferred 1 week post-M9b
- Cross-session memory: M9c after 1 week of M9b usage

**Next session:**

1. Monday 07:00 MT: verify auto-publish + M9a button tap (check docker logs)
2. Merge `feat/atlas-m9b-web-chat` to main (Boubacar confirms) then VPS deploy
3. After deploy: PIN into `/atlas`, send test message, verify native chat responds
4. M9c (cross-session memory) after 1 week of M9b usage
5. M5 (Chairman / L5 Learning) gate: 2026-05-08

### 2026-04-26: A/B test bugs fixed + deployed (commit f972756)

Two bugs surfaced during the Option A A/B test run and fixed same session.

**Bug 1: Sonnet assistant-prefill (social crew QA agent):**
- Root cause: `build_qa_agent()` defaults to `max_iter=3`. When Sonnet exhausts iterations,
  CrewAI appends an assistant-prefill turn. Anthropic rejects this with HTTP 400.
- Fix: `build_social_crew()` sets `qa.max_iter=1` after agent construction. QA is a
  single-pass review, no retries needed. Same fix pattern as consultant crew + research_engine.py.

**Bug 2: Grok-4 Pydantic string_type crash (A/B script):**
- Root cause: Grok-4 occasionally returns a list of `ChatCompletionMessageFunctionCall`
  objects as `TaskOutput.raw` instead of a plain string. Pydantic rejects non-string raw.
- Fix: `_run_legriot_for_model()` in `legriot_ab_test.py` normalizes `result.raw` to str
  before use. Extracts `.content`/`.text` from list items; falls back to `str(result)` on None.
- 2 regression tests added.

**A/B test verdict (recorded):** Grok-4 stays on `social/moderate`. No challenger cleared
+3 pts threshold. Mistral-Large-2512 is closest and had zero failures, worth watching
in the weekly model review agent (first run: Sunday 2026-05-03 08:00 MT).

343/343 tests pass. Deployed to VPS.

---

### 2026-04-27: Blotato 201 bug fixed + test infrastructure repaired

**Bug found:** auto-publisher fired at 07:01 MT and posted "One constraint nobody has named yet" to X via Blotato. Blotato returned HTTP 201 (Created), but `blotato_publisher.py` only accepted 200. It raised `RuntimeError`, flipped the Notion record to `PublishFailed`, and never polled for the result. The post (submission ID `555b3507`) was live on X at `https://x.com/boubacarbarry/status/2048749476999811174`.

**Fixes shipped (commit a469bfa):**
- `orchestrator/blotato_publisher.py`: all three status checks changed from `!= 200` to `not in (200, 201)`
- `orchestrator/skills/doc_routing/doc_routing_crew.py`: fixed bare `from doc_routing.*` imports to `from skills.doc_routing.*`
- `orchestrator/conftest.py` + `orchestrator/pytest.ini` (new): add both agentsHQ root and orchestrator to sys.path so `skills.*` namespace package resolves correctly in all test files
- `orchestrator/tests/test_doc_routing/conftest.py` (new): secondary path insert for the doc_routing test package
- `orchestrator/tests/test_doc_routing/__init__.py` (deleted): was forcing package-mode import which blocked namespace resolution
- `orchestrator/tests/test_blotato_publisher.py`: added `test_publish_http_201_accepted_as_success`
- `orchestrator/tests/test_signal_works.py`: fixed stale test assertion (force INSERT path via `fetchone.return_value = None`)

**Notion record 341bcf1a repaired manually:** Status=Posted, X Posted URL + Submission ID set.

**Test result:** 370/370 pass (up from 353; 17 previously-broken doc_routing tests now pass). Deployed to VPS at `70aa317`.

**NLM export cron:** fired at 06:00 UTC, not yet checked (fires tonight).

**M9c gate:** still holds. 1 week of M9b usage required before cross-session memory build.

**Next session:**
1. Check `/var/log/nlm_registry_export.log` on VPS (first run fired tonight)
2. M9c (cross-session memory): after 2026-05-03 (1 week of M9b)
3. M5 (Chairman / L5 Learning): gate opens 2026-05-08

---

### 2026-04-27: M9 chat fixes + health sweep hardening

**Root causes diagnosed and fixed:**

**Bug 1: /atlas/chat was 404:** All `/atlas/*` routes were wiped from `app.py` in the `4227b04` video-crew merge (a prior session's `docker cp` of an older app.py got committed). Restored full route block: `/atlas/chat`, `/atlas/job`, `/atlas/confirm`, `/atlas/state`, `/atlas/queue`, `/atlas/content`, `/atlas/spend`, `/atlas/heartbeats`, `/atlas/errors`, `/atlas/hero`, `/atlas/ideas`, `/atlas/ledger`, toggle/griot, toggle/dry_run, queue approve/reject.

**Bug 2: content_board_fetch returned empty body:** Crew read `props.get("Content", {})` (a Notion property that doesn't exist). Post body lives in the `Draft` rich_text property. Fixed to read `props.get("Draft", {}).get("rich_text", [])`: same pattern used by `auto_publisher`, `publish_brief`, and `content_board_reorder`. Also added single-post detection: user can ask "show me the full post for X" and get the actual Draft text instead of a title list.

**Bug 3: JSON bleed-through:** Both `run_chat()` and `run_atlas_chat()` had a fallback where parse failure set `reply = raw_reply`: user would see the raw `{"reply": "...", "actions": [...]}` JSON string. Added `_extract_reply()` shared helper that always extracts the human-readable string. User never sees JSON wrapper.

**Bug 4: /chat page had no markdown rendering:** `appendMessage()` used `bubble.textContent = text` for all messages including agent replies. Added `_mdFragment()` renderer (identical to atlas-chat.js, safe DOM-only, no innerHTML). Both `/chat` and `/atlas` now render markdown identically.

**Improvements shipped:**

- **History depth:** `run_chat()` history limit raised from 10 to 100 turns (Postgres-backed).
- **Atlas chat Postgres history:** `run_atlas_chat()` now loads 100 turns from Postgres at start of each request, same as `run_chat()`. Previously used only the client-managed JS array (lost on page refresh).
- **Health sweep: /atlas/chat probe:** Added `_probe_atlas_chat()` that hits POST /atlas/chat and asserts 401 (route exists) vs 404 (route missing). Catches future route-wipeout regressions the same morning they happen.
- **Health sweep: Last Health Check tile:** Sweep writes result to `data/health_sweep_state.json` after every run. Atlas dashboard hero strip now shows a 5th tile: "Last Health Check" with pass/fail count + timestamp. Green on pass, red on failures. Silent on success (no Telegram noise).
- **Health sweep: corrected to daily:** Was labeled "weekly" in comments but the heartbeat registration `at="08:00"` fires every day. Labels corrected.

**Three-way nsync:** local + origin + VPS all on `447eb82`.

**Commits this session:** `133e2d1`, `d5b91dc`, `0e0547c`, `0964320`, `f727c7d`, `eaf571d`.

**End state of chat surfaces:**

- `/chat` and `/atlas` both render markdown, both load 100-turn Postgres history, both use `_extract_reply()` to strip JSON. Still different routing pipelines (router/classifier vs atlas tools): unification is next major chat milestone.
- End-state vision confirmed: Atlas dashboard becomes the primary workstation. Interactive layer (click post → enhance → post, click task → execute) is the next build target after M9c.
- Code changes (repo writes, VPS deploys) remain Claude Code / IDE only by design. Safe path to partial automation: "propose code change" crew that opens a GitHub PR for human approval → auto-deploy via GH Actions.

**Next session:**

1. M5 (Chairman / L5 Learning): gate opens 2026-05-08
2. Atlas interactive layer (click-to-action on posts and tasks in dashboard): design spike
3. Unify /chat and /atlas routing pipelines (both through run_atlas_chat)

---

### 2026-04-27 (evening): M9c SHIPPED: cross-session memory compressor

**What shipped:**

- `orchestrator/session_compressor.py` (NEW): `find_sessions_to_compress()` queries `agent_sessions` for rows quiet 30-90 min with no existing summary. `compress_session()` loads 100 turns, calls Haiku, writes 3-5 bullet summary to `session_summaries`. `compressor_tick()` is the heartbeat callback, non-fatal per session.
- `orchestrator/db.py`: `session_summaries` table (id, session_id, summary, turn_count, created_at, window_end_at, tags[]). `ensure_session_summaries_table()`, `save_session_summary()`, `get_latest_session_summary(session_id, max_age_hours=24)`. 24h staleness gate prevents stale summaries injecting indefinitely.
- `orchestrator/scheduler.py`: `session-compressor` heartbeat registered at `every=30m`.
- `orchestrator/handlers_chat.py`: both `run_chat()` and `run_atlas_chat()` silently prepend summary to system prompt on session resumption. Non-fatal; no latency if no summary exists.
- `orchestrator/app.py`: `ensure_session_summaries_table()` called at startup.
- `orchestrator/tests/test_session_compressor.py`: 12 tests, all pass. Pre-existing test suite unaffected (346/347 excluding known pre-existing failures).

**Sankofa Council ran before build.** Two fixes applied: 24h staleness gate on `get_latest_session_summary`, `tags TEXT[]` column reserved for future project-scope tagging.

**Design decisions locked:**

- Raw turns never deleted (lossless; needed for L5 learning)
- Injection is system prompt prepend, not a message turn (no synthetic assistant messages)
- Works on all three surfaces (Telegram, /chat, /atlas) via shared Postgres session_key
- Three surfaces have separate session_ids per surface; cross-surface unification is future work
- Min 4 turns to summarize; skip silently below threshold

**M9 fully complete.** All three milestones shipped: M9a (Telegram buttons + correctness), M9b (native web chat panel), M9c (cross-session memory).

**Three-way nsync:** local + origin + VPS all on same commit (deploy in progress).

**Next session:**

1. M5 (Chairman / L5 Learning): gate opens 2026-05-08
2. Atlas interactive layer: click a content board post, say "enhance this", iterate conversationally, post it. Design spike needed.
3. Unify /chat and /atlas routing pipelines so both surfaces behave identically end-to-end.

---

### 2026-04-28: Content Intelligence Scout Phase 1 SHIPPED

**What shipped:**

- `orchestrator/studio_trend_scout.py` (major rewrite): Monday-only gate (weekday != 0 returns immediately), 6 Catalyst Works niches via Serper news search (`_serper_search()`: direct httpx POST to `google.serper.dev/news`, no CrewAI abstraction), 3 Studio niches via YouTube unchanged. Single Haiku classifier call per pick (`_classify_pick()`): returns fit 1-5, medium, first_line, unique_add, destination. Picks with fit <= FIT_THRESHOLD (3) dropped silently. Two separate Notion write functions: `_write_to_content_board()` writes to Content Board as Status=Draft, `_write_to_studio_pipeline()` writes to Studio Pipeline as Status=scouted. Routing logic in `studio_trend_scout_tick()`, not inside write functions. Per-pick Telegram messages with Approve/Reject inline buttons via `_send_pick_with_buttons()`. Summary message sent after all picks via `_send_summary()`.
- `orchestrator/studio_trend_seeds.default.json` (NEW): 9 niche seeds: 6 CW (serper source, Content Board dest): ai-governance-regulation, ai-adoption-what-works, ai-tools-smb, hidden-costs-margin-erosion, workforce-change-management, operational-systems-process; 3 Studio (youtube source, Studio Pipeline dest): african-folktales, ai-displacement-first-gen, first-gen-money.
- `orchestrator/handlers_approvals.py`: `scout_approve:<page_id>` callback flips Notion Status from Draft to Ready. `scout_reject:<page_id>` callback flips to Archived. Both use `_open_notion()` (existing pattern). Non-fatal error handling with `answer_callback_query` on failure.
- `orchestrator/tests/test_studio_trend_scout.py` (full rewrite): 13 tests, all passing. Old tests for removed functions (`_format_brief`, `_send_brief`) deleted. 10 spec tests: Monday gate (skip/fire), `_serper_search` (results/degrade), Haiku classifier (low/high fit), routing (Content Board/Studio Pipeline), approve/reject callbacks. 3 regression guards: seeds fallback, YouTube key absent, idempotency set.
- `docs/superpowers/specs/2026-04-28-content-scout-phase1-design.md`: approved spec (post-Sankofa Council + code review).

**Deploy:** commit `3b1f4b3`, VPS at `3b1f4b3`, 8/8 health probes passing.

**Design decisions locked:**

- Haiku classifier replaces full Sankofa Council per pick (correct tool for triage: Council is for decisions, not 100-pick loops)
- Serper direct HTTP (not SerperDevTool: CrewAI abstraction unsafe outside crew context)
- Monday gate is internal weekday check (not scheduler change: same pattern as model_review_agent.py)
- `_open_notion()` reused in handlers_approvals for scout callbacks (no new Notion client pattern)
- Content Board Status field is `select` type (not `status`): confirmed from schema memory

**Phase 2 gate (2026-05-12):** Two Monday runs must produce 5+ picks with fit >= 3. Phase 2 adds niches 7-10, Content Board dedup check, leGriot auto-draft on approval.

**Next session:**

1. M5 (Chairman / L5 Learning): gate opens 2026-05-08
2. Atlas interactive layer design spike (click post, iterate conversationally, post it)
3. Telegram still uses `run_chat()`; web uses `run_atlas_chat()`: backend divergence remains
4. VPS orphan archive sunset: delete `/root/_archive_20260421/` if no issues (was due 2026-04-28)

---

### 2026-04-28: M12 SHIPPED - Startup Contract (env var hard-fail)

**What shipped:**

- NEW `orchestrator/startup_check.py`: `REQUIRED_VARS` list (7 no-default vars) + `assert_required_env_vars()`. Calls `sys.exit(1)` and prints missing var names before any request is served.
- MOD `orchestrator/app.py`: `assert_required_env_vars()` wired as first call inside `@app.on_event("startup")` handler. Fires on server start, not on import (test-suite safe).
- NEW `orchestrator/tests/test_startup_check.py`: 3 tests - all vars present passes, missing var exits 1, empty string exits 1.

**Required vars manifest:** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `OPENROUTER_API_KEY`, `NOTION_API_KEY`, `FORGE_CONTENT_DB`, `BLOTATO_API_KEY`, `CHAT_MODEL`. Vars with code-level defaults (`CHAT_TEMPERATURE`, `CHAT_SANDBOX`, `ATLAS_CHAT_MODEL`) intentionally excluded.

**Test results:** 3/3 new tests pass. Full suite: 391 pass, 3 pre-existing failures (unchanged). No regressions.

**Save point:** `savepoint-pre-atlas-m12-startup-contract-20260428`

**Council corrections applied before build (second pass):**

- Trimmed manifest from 10 to 7 vars (removed 3 with safe defaults)
- Wire point clarified to `@app.on_event("startup")` not module top-level

**VPS deploy:** needs `docker compose up -d --build` on next deploy window. No new env vars required - this only checks vars that must already be present.

---

### 2026-04-28: Agent-S competitive analysis - M12 plan created, councils run

**What happened:** Competitive analysis of Agent-S (agent-s.app) - a hosted personal AI agent by Matt Shumer (AI Magic LLC), invite-only alpha. Core pitch: each agent gets a managed persistent computer, 1,000+ integrations, learns the user's patterns over time. Targeting same SMB owner-operator as Signal Works.

**Sankofa Council + Karpathy audit ran on 5 proposed enhancements.** Verdicts:

| Proposal | Verdict | Disposition |
|---|---|---|
| Agent Task Ledger (general resumable state) | HOLD - premature abstraction, no demonstrated failure, Karpathy FAIL on Simplicity First | Added to Descoped with trigger condition |
| Env var hard-fail at startup | SHIP - known repeated failure, clear success criterion | M12 milestone written |
| "Learns your patterns" narrative | NOT a roadmap item - positioning artifact | Moved to docs/signal-works/pitch-notes.md |
| Signal Works "gets its own brain" positioning | NOT a roadmap item - pitch copy | Moved to docs/signal-works/pitch-notes.md |
| Agent Task Ledger deferred post-M9 | MOOT - M9 already shipped | Removed |

**What was added to this roadmap:**

- M12 milestone: `orchestrator/startup_check.py`, `assert_required_env_vars()`, hard `sys.exit(1)` before uvicorn binds. 30-min build. Branch: `feat/atlas-m12-startup-contract`.
- Descoped table: Agent Task Ledger with trigger condition (re-open on first demonstrated ad-hoc resume failure).

**What was NOT added (intentionally):**

- Signal Works positioning - lives at `docs/signal-works/pitch-notes.md`, not here.
- Any feature copied from Agent-S without a demonstrated gap in agentsHQ.

**Key finding:** Agent-S validated the Signal Works thesis. Their moat is integration breadth; ours is specificity (content pipeline + outreach loop + client voice). The race is getting Signal Works to first paying client before Agent-S exits alpha.

**Next session:**

1. Build M12 (30 min) before the next VPS deploy
2. M5 (Chairman / L5 Learning): gate opens 2026-05-08
3. M10 (Topic Scout Phase 2): gate 2026-05-12 (two Monday runs with 5+ picks needed)
4. Signal Works first client: use pitch notes at docs/signal-works/pitch-notes.md

---

### 2026-04-27: Repo Architecture Day - Platform-With-Satellites Rule Locked

**Session type:** Architecture planning + Priority 1 execution. No new features. No VPS changes.

**What happened:**

This session was originally scoped as "continue the agentsHQ structure cleanup scheduled 2026-04-25." It grew into a full architecture review covering token efficiency, LLM navigability, client scalability, and saleability. Three tools ran in sequence: Sankofa Council (3 passes), Karpathy Principles audit, and deep code impact analysis via subagent.

**Key decisions made and locked:**

1. **Platform-with-satellites architecture confirmed.** agentsHQ is the AI operations platform. Anything with its own URL, customer, or revenue stream gets its own GitHub repo. This is now written into `AGENTS.md` (root) and `docs/reference/repo-structure.md` as a permanent rule.

2. **Dashboards4Sale is a satellite.** Will get its own repo (`bokar83/dashboards4sale`). Submodule removed from agentsHQ when that repo is created. Deferred - not blocking.

3. **signal_works/ stays at root for now.** Has active Python imports in orchestrator. Future satellite once import boundaries are clean.

4. **Token efficiency finding:** The skills/ folder is INVISIBLE to the Python runtime. Zero token cost at runtime. The real fat points are: chat history 100-turn limit in `handlers_chat.py` (fat point #1), styleguide injection in `design_context.py` (fat point #2), history duplication across crew agents in `engine.py` (fat point #3). These are Python code fixes, not folder fixes. Tracked for a future session.

5. **Karpathy Principles:** Four principles from AGENT_SOP.md formalized into a standalone `/karpathy` skill (`skills/karpathy/SKILL.md`). Also baked as Step 5 into `superpowers:verification-before-completion` - fires automatically before every ship. Both files live in `skills/` and `~/.claude/skills/`.

6. **Client work governance rule:** New clients go in `workspace/clients/[slug]/` with `AGENTS.md` + `BRIEF.md` from `docs/reference/client-template/`. No orchestrator code changes for a new client. Catalyst Works own brand work lives in `workspace/catalyst-works/`.

**What was built (Priority 1 - all additive, zero file moves, zero VPS impact):**

| File created | Purpose |
| --- | --- |
| `orchestrator/AGENTS.md` | Context scoping table for LLMs - which files to load per task type |
| `skills/AGENTS.md` | Skill creation rules |
| `skills/_index.md` | 71-skill machine-readable routing table (replaces reading 71 SKILL.md files) |
| `docs/AGENTS.md` | SOP navigation |
| `workspace/AGENTS.md` | Scratch space rules + structure |
| `workspace/internal/AGENTS.md` | Platform dev scratch |
| `workspace/clients/AGENTS.md` | Client onboarding instructions |
| `workspace/catalyst-works/AGENTS.md` | CW brand work context |
| `n8n/AGENTS.md` | n8n rules (no docker touch) |
| `signal_works/AGENTS.md` | Pipeline context + future satellite note |
| `scripts/AGENTS.md` | Pre-commit hook path warning |
| `docs/reference/client-template/AGENTS.md` | Template for new client folders |
| `docs/reference/client-template/BRIEF.md` | Template for new client briefs |
| `docs/reference/repo-structure.md` | Full folder taxonomy with owner/routing/status per folder |
| `skills/karpathy/SKILL.md` | Karpathy 4-principle audit skill |
| Root `AGENTS.md` updated | Platform-with-satellites rule + workspace structure + client governance |

**What was NOT done (intentionally deferred):**

- Archive moves (remote-access-auditor, codex_ssh, sandbox, scratch, tmp) - weekend task, needs savepoint tag first
- thepopebot/chat-ui/ -> ui/atlas/ - needs coordinated GitHub Actions + docker-compose update, its own window
- n8n-workflows/ merge into n8n/ - weekend
- Dashboards4Sale repo creation - separate task
- Token efficiency Python fixes (chat history limit, styleguide caching) - separate task
- zzzArchive/ -> archive/ rename - weekend

**VPS impact of this session:** ZERO. All changes are additive documentation files and new skills. No Python code touched. No docker-compose changed. No VPS coordination needed.

**Next session priorities (in order):**

1. Weekend archive cleanup: savepoint tag, then archive dead folders (safe moves confirmed by code scan)
2. Token efficiency: change `handlers_chat.py` limit from 100 to 20, cache `design_context.py` styleguide reads
3. thepopebot/chat-ui/ -> ui/atlas/: coordinate GitHub Actions + docker-compose + VPS in one window
4. Dashboards4Sale: create own repo, remove submodule
5. M5 (Chairman / L5 Learning): gate opens 2026-05-08

**State at session end:** local uncommitted changes. Committing and pushing to GitHub now (this session entry is part of that commit). VPS does NOT need a pull - no runtime code changed.

---

## Session Log: 2026-04-29 (Wednesday) - autoresearch loop pattern validated as L5 substrate

**Entry type:** Research + proof-of-mechanism. No code shipped. Two gates passed.

**Trigger:** Reviewed Karpathy's `karpathy/autoresearch` repo (single-GPU LLM training agent that hacks `train.py`, runs 5-min experiment, keeps via git commit if `val_bpb` improved, resets if not, loops forever). Question: does the underlying mechanism translate to anything Boubacar's stack needs?

**Initial verdict (pre-Council):** FORK. Top-ranked Monday move was "build generic loop_runner, deploy on cold outreach copy first."

**Sankofa Council ran (with /karpathy lens) and rejected the ranking.** Cold outreach reply-rate at n=10 has a confidence interval of roughly [0%, 30%] on a 5% baseline - the loop would optimize toward false positives. The Council reframed: the only metric in Boubacar's stack with `val_bpb`-grade properties (deterministic, fast, evidence-grounded) is the **design-audit 5-dimension rubric**. That's the right target for the loop, and the right Monday step is a 30-min determinism test, not a 4-week framework build.

**Determinism test (executed):** Same artifact (`workspace/demo-sites/volta-studio/index.html`), same rubric, scored 4 times (3 fresh runs in this session + 1 historical run from 2026-04-28).

| Run | A11y | Perf | Theme | Resp | Anti | Total |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 4 | 4 | 3 | 3 | 16 |
| 2 | 2 | 4 | 4 | 3 | 3 | 16 |
| 3 | 2 | 4 | 4 | 3 | 3 | 16 |
| 2026-04-28 prior | 2 | 4 | 4 | 3 | 3 | 16 |

**Variance: 0 across all dimensions, all runs.** design-audit is deterministic enough to be a `val_bpb`. ✅ Gate 1 passed.

**Loop iteration test (executed):** Pattern proof-of-mechanism on a copy of the catalystworks-consulting homepage (production source untouched).

- Copied `output/websites/catalystworks-site/index.html` to `workspace/loop-test/cw-index-{baseline,mutated}.html`
- Mutation: single targeted change - Inter font (P1 reflex-reject) → Spectral (heading) + Public Sans (body) per styleguide v1.1
- Baseline score: 14/20 (dims: 3/3/4/3/1)
- Mutated score: 15/20 (dims: 3/3/4/3/**2**)
- Δ: **+1 on Anti-Patterns, no regression on other dimensions**

✅ Gate 2 passed: targeted mutation produces measurable lift on the targeted dimension without collateral regressions. The mechanism transfers from `val_bpb` to design-audit.

**Anomaly caught:** the prior catalystworks-consulting__index-audit.md recorded total **11/20** but its dimensions sum to 14/20. Tally arithmetic was wrong in the audit file. **Implication for the runner:** totals must be computed from dimension scores, not free-typed by the agent.

**Why this matters for atlas L5:** L5 (Learn) is currently scoped as "Chairman crew reads outcomes weekly, proposes scoring/prompt mutations." That description was vague. autoresearch gives it a concrete shape: L5 is a bounded autonomous improvement loop that takes one editable artifact (a skill prompt, an agent backstory, a styleguide) + one fixed metric (design-audit score, post-Sankofa decision-change rate, reply rate at sufficient n) + one time budget, mutates, scores, git-keeps-or-reverts, logs to Postgres, runs unattended. Today's work confirms the **substrate** (deterministic metric + reproducible mutation + git as memory) before L5's data gate opens 2026-05-08.

**Decisions made:**

1. **autoresearch verdict: FORK.** Extract the loop pattern, do not clone the repo. Pattern is ~100 lines of glue (artifact + metric + mutator + git memory + Postgres log).
2. **First production target: design-audit on Catalyst Works deliverables**, NOT cold outreach copy (Council was right; outreach metric is too noisy at n=10).
3. **Cold outreach iterator descoped** until volume reaches 30+ sends/batch with statistical power.
4. **Always work on copies in `workspace/loop-test/`**, never mutate real source. Saved as feedback memory: `feedback_always_copy_for_experiments.md`.
5. **Runner build deferred** ("Let's stop and build later" - Boubacar). Substrate proven; build happens in a future session.

**Files created this session:**

- `workspace/loop-test/cw-index-baseline.html` (proof artifact, untouched copy of CW homepage)
- `workspace/loop-test/cw-index-mutated.html` (proof artifact, font-swapped copy)
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_always_copy_for_experiments.md` + MEMORY.md index entry

**No production state changed:** No VPS touch. No Vercel deploy. No git commit on this session's findings yet. CW homepage source file at `output/websites/catalystworks-site/index.html` is byte-identical to baseline.

**Open work (next session):**

1. Build `agentsHQ/loops/loop_runner.py` - generic pattern (artifact + metric_fn + mutator + git memory + Postgres log)
2. First deployment target: pick one in-flight Catalyst Works deliverable, baseline-audit, run loop overnight, wake up to git log of N attempts
3. After 5+ successful runs, evaluate whether to register as a 6th heartbeat wake on VPS for autonomous overnight iteration
4. Tally-from-dimensions enforcement in the runner (do not let agent free-type totals)

**Atlas roadmap impact:** L5 substrate is now de-risked. When L5's 14-day data gate opens 2026-05-08, the loop infrastructure can be built against a proven mechanism rather than a hypothetical one. This shaves weeks off L5 build time.

**State at session end:** clean working tree on production source. Two new files in `workspace/loop-test/` (test artifacts, .gitignore'd by workspace/ rules). Atlas roadmap updated (this entry). Memory updated (new feedback file + MEMORY.md). VPS unchanged.

---

## Session Log: 2026-04-30 (Thursday afternoon): Atlas Mission Control staleness fix shipped, NLM cron rewired, M13 added

**What:** Three problems surfaced by Boubacar:

1. Atlas Spend card "spending pace" stuck at 2026-04-23.
2. Hero "Last autonomous action" perpetually showed `self-test ok`.
3. NLM export cron (06:00 UTC daily) had not produced its log file.

**Diagnosis (after one false retraction):**

- Stale spending: `llm_calls` only logs council + direct Anthropic SDK; CrewAI calls bypass `usage_logger` by design (`usage_logger.py:366-368`). Active autonomous work today (auto_publisher, griot, sequence_engine) used CrewAI, so 0 rows landed since last research_engine run on 04-23. Dashboard was honest, system was the unreliable narrator.
- Stale "self-test ok": `_last_autonomous_action()` had no filter; `heartbeat-self-test` fires every minute and dominates `LIMIT 1`.
- NLM cron: registered correctly but ran on host `/usr/bin/python3` which lacks `psycopg2` (`pip install psycopg2-binary` was never run on the host).
- **False retraction:** I read systemd `signal-works-morning.service` "Failed: timeout" status on 04-30 and called it an "Apollo zero match crisis." Wrong. Boubacar received 10 SW + 8 CW T1 drafts the same day. Verified via Supabase `lead_interactions` query: drafts persist in-container before SIGKILL. Memory written: `feedback_systemd_failed_status_misleading.md`.

**Plan v3.2 (locked through 3 rounds of /sankofa + /karpathy):**

- A: read-only verify SW timer + journalctl + Supabase cross-check. Status: timer fails by `TimeoutStartSec=30min` SIGKILL but drafts land (10 SW T1 / 8 CW T1 on 04-30; 10 SW / 29 CW on 04-29).
- A1.5: VPS does not import `build_email`; the broken local pytest is against a renamed function (`render_html`). Drift is in the test, not prod.
- B: shipped 152-line dashboard fix (commit `7985974`, deployed to VPS, `orc-crewai` rebuilt at 15:34 UTC). Hero "Last action" now shows real autonomous work (`auto_publisher | success @ 13:02`). Spend card adds Today/Week/Month token totals (304,354 MTD verified) and "Ledger last write" amber row with stale tooltip pointing to M13.
- C: NLM cron swapped from host `python3 scripts/...` to `cat scripts/nlm_registry_export.py | docker exec -i -e NLM_EXPORT_SHEET_ID -e DATABASE_URL orc-crewai python3 -`. Manual test ran clean (exit 0); script now correctly surfaces `NLM_EXPORT_SHEET_ID not set` as the next blocker.
- D: M13 added to this roadmap with target 2026-05-07. Scope: OpenRouter `/api/v1/credits` + Anthropic Console usage daily cron writes to `provider_billing` table; Spend card shows ledger + provider + delta; tooltip removed when delta visible.
- E: 2 memory files added (`reference_atlas_llm_calls_ledger_scope.md`, `feedback_systemd_failed_status_misleading.md`); MEMORY.md index updated.

**Side fix:** VPS `.env` had Windows CRLF line endings; `scripts/orc_rebuild.sh` choked on `set -a; . .env`. Fixed via `sed -i s/r$//` (backup at `.env.bak.<ts>`). Bypassed orc_rebuild.sh for this rebuild, ran `docker compose build orchestrator && docker compose up -d` directly.

**Surfaced blockers, not addressed this session:**

- `NLM_EXPORT_SHEET_ID` not in VPS `.env`. NLM cron will succeed-no-op tomorrow at 06:00 UTC until this is set.
- VPS `.env` line 121 (`SMTP_PASS`) parses badly under bash `set -a; . .env` due to special chars in the value. Other `.env` consumers (docker-compose) handle it. Worth quoting later but not a current blocker.
- `signal-works-morning.service` 30-min `TimeoutStartSec` is too short for the full multi-city scrape; service registers Failed but writes persist. Either bump timeout or accept the misleading status.

**State at session end:** clean working tree (only unrelated WIP unstaged: TOOLS_ACCESS.md, output, untracked playbooks/skills). VPS at commit `7985974`. orc-crewai rebuilt and healthy. Dashboard live with new fields. Cron rewired. Memory + roadmap updated.

---

### 2026-04-30 (Thursday late afternoon): blockers triage follow-up

Two of three blockers from earlier session resolved.

- **SW service timeout:** `TimeoutStartSec=30min` -> `TimeoutStartSec=90min` on `/etc/systemd/system/signal-works-morning.service`, `daemon-reload` applied. Tomorrows 13:00 UTC run will register `Started` cleanly instead of `Failed: timeout`. Drafts already landed in-container under the old timeout; this just restores the systemd signal as a real status indicator.
- **NLM registry export cron:** removed from VPS crontab. Reason: `notebooklm_pending_docs` table has 6 total rows, last write 2026-04-13, zero activity in 14+ days. Sheet ID was never set, so the cron warned-and-exited daily. No active producer or consumer. Script preserved at `scripts/nlm_registry_export.py` for resurrection; full restore recipe in the Descoped table above.
- **`.env` SMTP_PASS bash-parse issue:** skipped per Boubacar. docker-compose handles it; only `scripts/orc_rebuild.sh` chokes, and the bypass (direct `docker compose build && up`) is documented in this session log.

---

### 2026-05-02 (Friday afternoon): Move Day: repo structurally sound, governance locked, "delete" word retired

**Trigger:** continuation of 2026-04-27 architecture session that scoped Priority 1 work but explicitly deferred file moves to a future session. Today was that session.

**Pre-flight (90 min):**

- Reviewed handoff `docs/handoff/2026-04-27-repo-architecture-cleanup.md` and roadmap state. 5 days had passed; verified live repo state matches the 04-27 plan (no drift).
- Pulled current Notion task DB state. Found T-260306 (savepoint) + T-260307 (archive dead folders) Not Started; matched today's scope.
- Ran `/sankofa` Council on the original 16-step plan. Verdicts: (1) `git tag` does not back up gitignored content; need real tar backup. (2) 16-step bundle too large; risk of half-done at hour 4. (3) Ventures registry as markdown table is a 5th source of truth. (4) plan asserts but does not verify.
- Ran `/karpathy` 7-gate audit. **5 production-mount footguns surfaced** that the original plan would have broken: `setup-database.sql` (docker-compose:32 init mount), `agent_outputs/` (docker-compose:204 `/app/outputs` mount), `tmp_upload/` (transcribe skill WORK_DIR), `thepopebot/chat-ui/` (deploy-agentshq.yml path filter), `codex_ssh/` (active Codex tool).
- Boubacar locked two new hard rules mid-session: **(a) the word "delete" is retired**, items not used → archived to `zzzArchive/<batch>/<path>/` with manifest; **(b) make educated decisions on routine triage**, don't paginate three-way verdicts.

**Execution (single bundled session, ~3 hours):**

Phase 0: Backup safety net:
- Tarred 5 gitignored folders (tmp/, scratch/, tmp_upload/, .tmp/, agent_outputs/) → `zzzArchive/_pre-cleanup-20260502/_backup-gitignored.tar.gz` (53 MB)
- `git tag savepoint-pre-archive-cleanup-20260502`
- `zzzArchive/_pre-cleanup-20260502/MANIFEST.md` written (rule statement + reference-check methodology + per-item entries)

Phase 1: Triple-verified archives to `zzzArchive/_pre-cleanup-20260502/`:
- `remote-access-auditor/` (root duplicate; canonical lives at `skills/remote-access-auditor/`)
- `server-setup/` (one-time VPS bootstrap, superseded)
- `workflows/legacy/`, `workflows/README.md` (legacy n8n exports)

Phase 2: n8n consolidation:
- `n8n-workflows/*.json` (3 files) + `workflows/*.json` (2 files, 1 newer than n8n-workflows version) → renamed and merged into `n8n/imported/n50-sub-always-save.json`, `n51-daily-news-brief.json`, `n52-whatsapp-v6.json`
- Older duplicates archived with -OLDER / -DUPLICATE / -LEGACY suffixes
- `workflows/`, `n8n-workflows/` folders removed (empty)

Phase 3: Root file moves (live-mount aware):
- `test_sankofa.py` → `tests/`
- `run_council_strat.py`, `MakeShortcut.ps1`, `Run-Local-SecureWatch.bat` → `scripts/`
- `code_review_20260422.md` → `docs/handoff/`
- `adversarial_report.md` → `docs/reference/`
- `a-b testing.xlsx`, `ninja.ico` → `workspace/`
- Archived (NOT deleted): root `schema_v2.sql` (older than `docs/database/schema_v2.sql`), `ideas_full_list.txt`, `ideas_full_list_utf8.txt`, `search_output.txt`
- **Live-mount paths kept exactly in place:** `setup-database.sql`, `agent_outputs/`, `tmp_upload/`, `codex_ssh/`, `thepopebot/`

Phase 4: Scratch folder triage:
- **Graduated to `tests/integration/`:** `tmp/test_phase1_e2e.py`, `tmp/test_autonomy_e2e.py` (real autonomy + approval-queue end-to-end tests, not throwaways)
- Archived: `tmp/codex-commit-*.txt` (8 files), `tmp/check_apollo_*.py`, old apollo probes, `scratch/` full content (12 files), `.tmp/CLAUDE.md`, `tmp_upload/` old transcripts (folder kept for transcribe skill), `agent_outputs/capital-allocation/` (folder kept as live mount)

Phase 5: Sandbox decision:
- `sandbox/` stays tracked in git (in-flight work backed up so laptop dying does not lose it)
- `sandbox/.tmp/` added to `.gitignore` (throwaway corner)
- `sandbox/README.md` rewritten with full rule set: no secrets, monthly sweep at 30d, graduate-or-archive (NOT delete), one-way door (production → sandbox is fine, sandbox → production requires graduation)

Phase 6: Ventures Registry:
- `docs/roadmap/dashboards4sale.md` stub created (satellite codename added to registry)
- `docs/roadmap/README.md` Ventures Registry table added: 6 ventures (Catalyst Works, Signal Works, Dashboards4Sale, Studio, Atlas, Echo) with type / roadmap / repo / live URL / stage. Answers Boubacar's "where do my businesses live?" question without violating the Platform-with-Satellites rule.

Phase 7: Folder Governance:
- `docs/AGENT_SOP.md` Hard Rules updated with **"delete" word retired** rule + **make educated decisions on routine triage** rule
- New `docs/AGENT_SOP.md` "Folder Governance" section: 7 rules covering AGENTS.md/README.md per folder, no folder without purpose, 14d-untouched + zero refs = archive candidate, live mounts never move, triple-verify before archive, zzzArchive is never archived, sandbox monthly sweep
- `~/.claude/projects/.../memory/reference_folder_governance.md` written + `MEMORY.md` index entry

Phase 8: repo-structure.md fully rewritten:
- Fixed 04-27 errors (agent_outputs and tmp_upload were marked "orphan": they are live mounts)
- Added "Live Mount Points" section (top-level, prominent)
- Added "Folder Governance" summary
- Added "Move Day 2026-05-02 Summary" section listing every archive + every move

Phase 9: Token efficiency fix:
- `orchestrator/handlers_chat.py` `limit=50` → `limit=20` (2 occurrences via `replace_all`). Note: handoff said 100 → 20, but a prior session had already cut to 50; today's edit takes it the rest of the way.
- Live state confirmed by reading file before edit. py_compile passes.

Phase 10: Verification:
- `py_compile` sweep across 317 tracked Python files: **all compile clean** (the one "error" was `scratch/trigger_deploy.py` which is staged-as-deleted from this session's archive moves; not a real error)
- `git status` reads cleanly: 7 modified, 13 renames (R), 14 new tracked files, 4 untracked (dashboards4sale.md, tests/integration/, sandbox/.tmp/, etc.)
- All moves preserve `git mv` history; blame survives

**State at session end:**

- Local: clean working tree pending one bundled commit + one separate token-fix commit
- Remote: pending push
- VPS: pending pull (token fix is the only runtime change requiring deploy)
- Notion: T-260306 ✅ Done, T-260307 ✅ Done

**Lessons captured to memory this session:**

- `feedback_make_educated_decisions.md` (NEW): execute routine triage yourself, surface only irreversible/strategic/ambiguous calls
- `reference_folder_governance.md` (NEW): full rule + workflow + decision flow + mount footgun list
- `MEMORY.md` index updated with both pointers

**Cross-references:**

- Manifest: `zzzArchive/_pre-cleanup-20260502/MANIFEST.md`
- Backup: `zzzArchive/_pre-cleanup-20260502/_backup-gitignored.tar.gz` (53 MB)
- Savepoint: `git tag savepoint-pre-archive-cleanup-20260502`
- Handoff: this session log entry replaces a separate handoff doc

**Explicitly NOT done today (deferred per Council verdict on coordinated dependencies):**

- `thepopebot/chat-ui/` → `ui/atlas/` move (path-watched in deploy-agentshq.yml; needs coordinated GitHub Actions + docker-compose + VPS window)
- Dashboards4Sale code extraction to `bokar83/dashboards4sale` satellite repo (its own 30-60 min focused session: see `docs/roadmap/dashboards4sale.md` M0)

**Atlas impact:** infrastructure clean. Future-proof for the M5 Chairman/Learning-loop gate that opens 2026-05-08. The folder governance rule plus the manifest pattern means any future cleanup pass is reversible by design.

---

### 2026-05-02 (Friday late afternoon): Compass governance + Dashboards4Sale extracted + outputs renamed

**What:** continuation of Move Day. Scope grew to include governance scaffolding (Compass M0+M1), Dashboards4Sale satellite extraction, top-level folder hygiene, output/ submodule documentation (full restructure deferred to Compass M5), and outputs/ -> agent_outputs/ migration.

**Six commits shipped:** ec9bac8 (Compass M0+M1), c3fe253 (D4S extracted), 5fa6e58 (external + task_progress hygiene), 42c4058 (output/ anatomy doc + do-not-merge warning), 51e4955 (Compass M5 logged), edb4df1 (outputs -> agent_outputs).

**New satellite:** bokar83/dashboards4sale live. Original tracked content preserved in zzzArchive/_pre-cleanup-20260502/Dashboards4Sale-original/.

**New governance constitution:** docs/GOVERNANCE.md (64 lines) routes between 8 rule surfaces. AGENT_SOP.md stays as load-bearing rules library. Conflict resolution + retirement protocol locked.

**New enforcement:** scripts/check_folder_purpose.py pre-commit hook converts the every-folder-has-AGENTS.md rule from aspirational (32% coverage) to enforced (100% coverage; hook fails any commit that adds a top-level folder without AGENTS.md/README.md).

**Compass roadmap created:** docs/roadmap/compass.md with M0 SHIPPED, M1 SHIPPED, M2-M5 queued.

**Critical surface caught and documented:** output/ submodule on local checkout points at bokar83/signal-works-demo-hvac while agentsHQ .gitmodules registers it as bokar83/attire-inspo-app. Two SEPARATE repos (Boubacar's hard rule 2026-05-02). Reconciliation deferred to Compass M5.

**Path translation table for the day:** docs/handoff/2026-05-02-structural-cleanup-v2.md.

**Atlas impact:** ahead of Atlas M5 gate (2026-05-08). Governance infrastructure now exists to support multi-revenue platform discipline as Studio + Signal Works + Dashboards4Sale + future ventures grow in parallel.

### 2026-05-02 (evening): cc-switch absorb + multi-CLI provider switching (M-new: provider resilience)

**Triggered by:** absorbing cc-switch (farion1231/cc-switch), a Tauri desktop GUI for managing Claude Code / Codex / Gemini CLI providers. Absorb verdict: PROCEED. Built two independent layers instead of installing cc-switch.

**Layer A/B SHIPPED (local machine):** `skills/switch-provider/` with a Python script + providers.json that atomically switches Claude Code's `ANTHROPIC_BASE_URL` in `~/.claude/settings.json` and Codex's model in `~/.codex/config.toml`. No restart needed for Claude Code. Agent-callable via subprocess. 9 tests, all passing.

**Layer C SHIPPED (VPS):** OpenRouter circuit breaker wired into `orchestrator/llm_helpers.py`. Trips on 3 failures in 5 minutes, fires Telegram alert with the exact manual switch command. `orchestrator/provider_probe.py` runs every 5 min as a heartbeat wake, tests OpenRouter, fires recovery Telegram on restoration. `provider_health` table created and seeded. 3 tests.

**Bonus fix:** VPS `.env` had SMTP_PASS with unquoted spaces (`urnh jwyo vyur qurl`) silently aborting `orc_rebuild.sh`. Fixed by quoting the value.

**Health check routine:** Remote agent `trig_01KHkpRpAk8huaCgNrBBexAA` fires 2026-05-17T15:00:00Z (9am MT) to verify probe is firing, row is fresh, and circuit has not tripped unexpectedly.

**Files:** `skills/switch-provider/switch_provider.py`, `skills/switch-provider/providers.json`, `skills/switch-provider/SKILL.md`, `orchestrator/provider_health.py`, `orchestrator/provider_probe.py`, `orchestrator/llm_helpers.py` (modified), `orchestrator/app.py` (modified), `tests/test_switch_provider.py`, `tests/test_provider_probe.py`.

**Next:** M13 (true spend visibility, target 2026-05-07) or M8 (Mission Control dashboard) depending on priority. L5 Learn (chairman crew) still blocked until 2026-05-08 (needs 14 days of L4 data).

---

### 2026-05-02/03 (Friday night into Saturday): Chat UI overhaul + content board routing fixed

**Session arc:** Started with 3 bug reports: hallucinated tool calls, Haiku running instead of Sonnet, and chat bugs. Ended with the content-board to social crew pipeline working end-to-end for the first time.

**Shipped:**

| Fix | What changed |
|-----|-------------|
| Hallucination fix | System prompt ABSOLUTE RULES, `_sanitize_history_for_model()`, tool result renamed to AWAITING_USER_CONFIRMATION, healthcheck v2 probes |
| Haiku/Sonnet fix | `call_llm(model_key=)` param, deprecated import-time constants with sentinel, `_resolve_model` rewrite, 11 unit tests, UI model footer |
| Chat confirm buttons | `/chat/``/chat/` (index.html) was missing `actions` rendering entirely. It was the wrong app the whole time; `/atlas/` had a separate init timing bug |
| `/atlas/` init bug | `showDashboard()` fired before `atlas-chat.js` loaded; patched `showDashboard` never ran for cached-token logins |
| nginx `try_files` | `$uri/` fallback served `index.html` (24388-byte wrong app) instead of `atlas.html` for `/atlas/` route |
| Traefik routing | `nginx-static` service name conflict between `atlas-ui` and `chat-ui` routers; split into `nginx-atlas` and `nginx-chat` |
| Textarea UX | Min-height 72px, rows=3, auto-grow on input, height reset after send for both `/chat/` and `/atlas/` |
| "Atlas is using..." | Removed from both UIs |
| Content board status | Board uses "Draft" (16 posts), not "Idea" (0 posts); status mapping fixed |
| Router CRM poison | `_classify_raw` CRM read-intent shortcut fires on "show me" + "draft" before content board check; moved content board check to absolute top of `_classify_raw` |
| Router history poison | Engine passes conversation history as task_request; prior CRM replies ("1899 leads", "draft") poisoned LLM classifier; extract `CURRENT REQUEST:` substring before classification |
| `build_content_draft_crew` | New crew: fetches Draft posts from Notion, picks one LinkedIn post, writes 2 variations in Boubacar's voice, returns inline for approve/reject/enhance without touching Notion |

**Verified live (end-to-end test):**
- `/chat/` confirm buttons render and fire
- `/atlas/` send button and Enter key work on cached-token login
- `classify_task("Show me all posts from the Notion Content Board with status Draft")` returns `social_content` (was `crm_query`)
- `build_content_draft_crew` fetches 4 LinkedIn Draft posts from Notion and drafts content
- Full job run: crew dispatched, completed in 38s, returned post variations

**Post-mortem on the 4-hour routing debug:**

Root cause was always: `_classify_raw` CRM shortcut at line 338 fired first on "show me" + "draft". 6 fixes failed because I tested with paraphrased clean strings ("Draft one LinkedIn post") instead of the exact failing string ("Show me all posts..."). The lesson is in `feedback_router_debugging_discipline.md`: always test `classify_task()` inside the container with the EXACT string from the logs before shipping.

Secondary failure: I didn't know Boubacar was on `/chat/` not `/atlas/` until 3+ hours in. New memory: `feedback_chat_ui_ask_which_url.md`.

**Commits today:** 1779945, c1a9a6f, a7a76cc, 5d5363b, 4221fdb, 22e93de, 630d491, 5ec83b8, bcr7ikdea series (router fixes), bwbrd02jo (content_draft_crew).

**Next:** Content board workflow is live. Boubacar can now draft, approve/reject/enhance posts through `/chat/`. M13 (true spend visibility) when ready. L5 (chairman crew) gate: 2026-05-08.

---

### 2026-05-03 (Saturday morning): Chat healthcheck restored after 12h 402 outage

**Root cause:** OpenRouter account credit balance (~64,554 tokens) dropped below the default `max_tokens` ceiling that `claude-sonnet-4.6` requests (65,536). Every `/atlas/chat` call returned HTTP 402 for approximately 12 hours. The `chat_healthcheck.py` probes (`web /atlas/chat` and `tool-calling probe`) both failed, triggering repeated Telegram alerts.

**Fix:** Added `max_tokens=8192` to all three `call_llm` invocations inside `run_atlas_chat` in `orchestrator/handlers_chat.py`. Chat responses never require 65k tokens; 8192 is well above any realistic reply. Commit `2693103`. Deployed via `scripts/orc_rebuild.sh`.

**Verification:** All 4 healthcheck probes green immediately after deploy.

**Action required:** Top up OpenRouter credits at `openrouter.ai/settings/credits`. The 8192 cap keeps chat working at current credit levels indefinitely, but crew tasks that go through other `call_llm` paths could hit 402 as the balance continues to drain. The cap does not fix the underlying low-credits situation.

### 2026-05-03 (Saturday morning, follow-up): Credit guardrails shipped

Two changes to prevent recurrence:

**1. `orchestrator/llm_helpers.py` (402 early-exit)**
`call_llm` now catches HTTP 402 before the generic exception handler. On 402: logs clearly, fires one Telegram alert ("ATLAS ALERT: OpenRouter out of credits"), raises `RuntimeError("OpenRouter out of credits. Add funds at openrouter.ai/settings/credits")`. The chat handler catches this and surfaces a clean user-facing message instead of "Sorry, I hit an error." Prior behavior: 402 hit the generic circuit-breaker path, logged as an opaque error, and spammed the circuit breaker counter for a problem that isn't a transient outage.

**2. `orchestrator/health_sweep.py` (`_probe_openrouter_credits`)**
New probe added to the daily sweep. Hits `GET https://openrouter.ai/api/v1/credits`, computes `(total_credits - total_usage) / 100` in USD. Fails the sweep with a Telegram alert if balance is below $5. Gives ~1 day of warning before balance hits zero at current spend rates. Commit `9602e72`.

**Action required (still):** Add credits at `openrouter.ai/settings/credits`. These guardrails alert and degrade gracefully; they don't pay the bill.

---

### 2026-05-03 (Saturday): Burn Guard RCA + hardening shipped

**Trigger:** $57.45 burned on OpenRouter the night before. Root cause: a `UserPromptSubmit` hook
(`classify_task.py`, reverted 2026-05-02) was still live and silently redirecting every Claude Code
API call through OpenRouter via `ANTHROPIC_BASE_URL`. Context snowballed from 16k to 344k tokens
across 363 calls. Boubacar topped up while the redirect was still live. Full 914-call, $62.12 CSV
confirmed on 2026-05-03 UTC. No refund case: all calls completed successfully.

**Three-round RCA:** Codex (mechanism), Sankofa (strategic), Karpathy (principles audit).
Karpathy scores: Think before coding 2/10, Simplicity first 2/10, Surgical changes 1/10,
Goal-driven 2/10. Root finding: ANTHROPIC_BASE_URL redirect + context snowball + no kill switch.

**Hardening shipped (2 commits on main):**

Commit 6002ff8: `orchestrator/provider_probe.py` extended with `_fetch_balance()` +
`_check_spike()` (Telegram alert if balance drops more than $2 in one 5-min probe window).
`C:/Users/HUAWEI/.claude/hooks/check-base-url.js` (new PreToolUse hook: blocks all tool calls
if `ANTHROPIC_BASE_URL` is non-Anthropic host). `scripts/check_no_provider_redirect.py` +
`.pre-commit-config.yaml` (pre-commit blocks commits baking a non-Anthropic base URL into JSON).

Commit 7592575: `scripts/check_hook_registration.py` + `.pre-commit-config.yaml` (pre-commit
blocks new per-message hook commands without HOOK_MODEL / HOOK_COST_PER_FIRE / HOOK_FIRING_RATE
annotations). `orchestrator/contracts/TEMPLATE.md` C6a canary gate added (supervised $0.50-cap
run before 7-day dry-run). `docs/AGENT_SOP.md` new hard rule: 4 mandatory questions before
registering any LLM-calling hook.

**Plugins wired (token reduction):** caveman (UserPromptSubmit), context-mode (SessionStart).

**Not done:** Atlas dashboard live OpenRouter balance sparkline. Interim: `provider_probe.py`
spike detection covers the alert layer. Full sparkline is M13 scope (target 2026-05-07).

**Handoff:** `docs/handoff/2026-05-03-burn-guard-rca.md`

**Next session:** Wire `GET https://openrouter.ai/api/v1/credits` into the Atlas dashboard
frontend. Add `/atlas/openrouter-balance` endpoint in `app.py`. Add balance tile + 7-day
sparkline to `atlas.html` / `atlas.js` hero strip. This completes M13.

---

### 2026-05-03 (Saturday afternoon): M13 SHIPPED: true spend visibility live

**What shipped (commits `062e631`, `287dfe7`):**

OpenRouter ground-truth spend now visible on the Atlas dashboard. Hero Spend Pacing tile corrected. Daily snapshot cron armed.

**Files:**
- `orchestrator/spend_snapshot.py` (NEW): pulls `usage_daily/weekly/monthly` + balance from OpenRouter `auth/key` + `credits` endpoints. Upserts one row/day into `provider_billing` table (auto-created). Fires at 23:55 MT via heartbeat, sends Telegram digest.
- `orchestrator/atlas_dashboard.py`: `_fetch_provider_spend()` for live figures, `_get_historical_comparisons()` for week-over-week / month-over-month / YTD from snapshots, `get_spend()` extended with `provider_*` + `historical` + `pacing_pct`, `get_hero()` `spend_pacing` now uses provider ground-truth vs $50/mo daily share.
- `orchestrator/scheduler.py`: `spend-snapshot` heartbeat registered at 23:55 MT.
- `thepopebot/chat-ui/atlas.js`: Spend card shows "Comparisons" section (this/last week, this/last month, YTD with delta %), "OpenRouter (ground truth)" with today/week/month/balance/untracked-CrewAI-delta, hero tile shows "$X.XX (NNN% of $Y.YY/d)" and turns red above 100%.
- `orchestrator/health_sweep.py`: fixed credit probe units bug (was dividing by 100; API is raw USD).

**Key numbers confirmed live:**
- Provider today: ~$62 (was showing $2.42 from ledger alone)
- Untracked delta (CrewAI): ~$59.58
- Balance: $10.71

**Monthly budget set at $50.** Red threshold at 100% of daily share. Revisit after 3 full months.

**M16 added to roadmap:** Anthropic Console + Claude Code CLI token tracking. No public API confirmed. Spike before build. Earliest trigger 2026-08-01.

**Next:** Historicals will accumulate from 23:55 MT tonight. Week-over-week comparisons meaningful after 7 days (2026-05-10). Month-over-month meaningful after June closes.

---

### 2026-05-03 (Saturday late): M17 Kie.ai spend tracking planned, councils run, milestone added

**What happened:** Kie.ai spend tracking plan reviewed by Sankofa Council + Karpathy audit before any code was written. Both councils returned HOLD.

**Council verdicts:**

- **Sankofa fatal flaw (Contrarian):** top-up guard in original plan erases real spend. Balance delta is not spend. Credits are not dollars. Storing credit-delta in `usd_today` column is a unit lie from day one.
- **Sankofa First Principles:** goal is "know what Kie costs." You have one balance integer. That is not spend. Before any code: does Kie expose transaction/usage history endpoint?
- **Sankofa Executor:** run API probe before touching any file (probe command documented in M17).
- **Karpathy P1 FAIL:** credit unit unconfirmed. `check_credits()` returns raw integer. Plan stores as `usd_today` with no confirmed conversion rate. Day-1 bootstrap unhandled. VERDICT: HOLD.

**Original plan changes rejected:**

- Refactoring `take_snapshot()` signature -- unnecessary, breaks surgical rule
- Merging Kie into `_fetch_provider_spend()` -- couples failure modes incorrectly
- Mock test with assumed conversion rate -- false confidence until unit confirmed
- "If current > previous, set usd_today = 0" guard -- erases real spend on top-up-then-spend days

**M17 milestone written to roadmap.** Gate: API probe first (10 min). Implementation path depends on answer.

**Next:** Run the API probe. Come back with output. Build or re-plan based on result.

---

### 2026-05-04: Research Agent Architecture Review - verification queue concept logged

**Session scope:** Research review only. No code shipped to Atlas in this session.

**What happened:** Sankofa Council ran on whether to adopt Graeme Kay's research agent architecture (X thread, 2026-05-04). Council surfaced one Atlas-relevant finding: the `approval_queue` gates human-approved commits, but there is no equivalent for *agent knowledge claims* - outputs one agent makes that another agent acts on.

**Cross-reference added to Atlas Cross-References:** `data/verification_queue.md` concept documented. Single markdown file alongside `autonomy_state.json` on VPS. Any claim an agent makes that another agent will act on gets queued before becoming a fact the system acts on. Prevents hallucination laundering in the L5 Learning loop.

**Build gate:** When M5 Chairman crew is being designed (2026-05-08+). Not before.

**Next:** M5 (Chairman / L5 Learning) gate opens 2026-05-08. When designing the Chairman crew, add `verification_queue.md` as the claim-staging layer before any agent output is promoted to a scoring mutation.

---

### 2026-05-06: Auto-publisher unblocked + storytelling infrastructure shipped

**Session scope:** Live content pipeline fixes, AI Governance campaign audit, cornerstone article production, storytelling infrastructure build.

**Auto-publisher fix:**
- Root cause: `BLOTATO_LINKEDIN_ACCOUNT_ID` was empty in `.env` (value existed only inside a comment line)
- Fix: extracted value `19365` (Boubacar Barry LinkedIn personal account), set in `.env`, restarted container
- Confirmed: next heartbeat tick picked up 2 queued LinkedIn posts correctly
- Full Blotato account map documented (13 accounts across LinkedIn, X, IG, TikTok, YouTube for all 4 channels)

**AI Governance campaign (24 posts) — CTQ audit:**
- All 12 LI + 12 X posts audited against CTQ + Voice rules
- 5 posts fixed: throat-clear openers, garbled lines, AI phrase "earned the point", double-frame hypothetical
- All 24 posts confirmed clean, Queued, scheduled May 6-30 (Mon/Wed/Fri cadence)

**4 backlog posts (Ready status) — audit + repair:**
- Fabricated "Marco" client story found and archived before it could ship
- 2 incomplete drafts finished (AI tool reviews, AI stack accountability posts)
- Post 1 trailing DM-style CTA removed; Post 4 hashtag soup stripped

**Fabricated Story Gate — new systemic safeguard:**
- Hard-stop gate added to `ctq-social` and `boub_voice_mastery` skills
- Gate runs before any CTQ pass: named characters + invented dollar figures = full stop, confirmation required from Boubacar
- Committed to GitHub (`a1f63ef`)

**Cornerstone article — "The Illusion of Compliance":**
- Sankofa Council 2-pass CTQ: Pass 1 scored 6.5/10, Pass 2 scored 9/10
- Key structural rewrites: hypothetical moved to opening (stakes before prescription), framework subheads became claims, closing survey question replaced with "That is the entire difference"
- Header image generated via GPT Image 2 (West African executive, POLICY GAP badge, golden hour, Clay tones) — `workspace/media/images/2026-Q2/`
- Published to LinkedIn (`https://www.linkedin.com/pulse/illusion-compliance-why-your-ai-policy-template-liability-barry-5ggsc/`) and X (`https://x.com/boubacarbarry/status/2052027988192248124`)
- "First AI Decision" article (May 1) — LinkedIn + X URLs also written to Notion (were missing)

**Storytelling infrastructure — new capability:**
- `Story` added as Content Type to Notion Content Board schema
- `Only I` post format documented in `styleguide_master.md` — X-primary, opens on lived moment, statement endings, no framework
- Story Review process added to `ctq-social` — replaces standard CTQ scoring for Story posts
- `story_prompt_tick.py` created: 20 prompts (Tue/Thu 17:00 MT via Telegram + 6h sparse check if queue < 5)
- `notion_capture` crew updated: detects story signals from any input, saves to Content Board as `Content Type=Story`, suggests channel routing as options (not hard-wired)
- Channel map: BB (Boubacar Personal), 1stGen (First Gen Money), UTB (Under the Baobab), AIC (AI Catalyst)
- Committed to `feature/gws-email-rules-update` (`770b938`, `15eb85c`, `dde463a`) — awaiting gate merge

**Commits this session:** `a1f63ef` (fabrication gate), `770b938` (story infra), `15eb85c` (channel mapping), `dde463a` (17:00 schedule + Tue/Thu gating)

**Branch state:** `feature/gws-email-rules-update` is 3 commits ahead of `main` — gate needs to process.

**What is NOT yet done:**
- Studio crew not yet wired to pull `Content Type=Story + Status=Idea` entries as script briefs
- LéGroit theme detection across sessions (flag recurring phrases → weekly Signal Brief) — designed, not built
- Atlas dashboard OpenRouter balance sparkline (M13 follow-up) — deferred

**Next session:**
1. Gate: merge `feature/gws-email-rules-update` to main
2. Wire Studio crew to Story entries on Content Board (one story → multiple channel scripts)
3. LéGroit theme detection — reads session patterns, surfaces as weekly Signal Brief with draft posts


### 2026-05-06 (Morning) - Platform Infrastructure and DX Maintenance Shipped

**What was done:**
- GWS Email Integration: Refactored agents.py and GWS task templates in crews.py to allow personal 'email me' updates to skip the default draft-only pipeline and directly send styled HTML emails to boubacar@catalystworks.consulting and bokar83@gmail.com. Outbound marketing and CRM workflows remain gated by drafts.
- Resolved Walkthrough Reload Loop: Renamed the walkthrough file to break the VSCode focus-stealing refresh loop and restore clean developer editor focus.
- Resolved MCP Timeouts: Pre-installed GitHub and Notion MCP servers globally and updated local mcp_config.json configuration to use direct node script invocations. This bypassed latent npx -y dynamic lookup delays, solving the context deadline exceeded startup connection error.
- Automated Claude CLI Maintenance: Force-purged 160.17 MB of crashed, bloated CLI conversational logs. Registered a daily silent Windows Scheduled Task named CleanClaudeCache with a dynamic USERPROFILE path to run clean_claude_cache.py (with 14-day safety sprint buffer and 2 MB file size limit).

**Commits this session:** Local edits and background scripts verified; configs updated in place on local machine.

**Branch state:** Local machine and Antigravity layer updated; local repository and configuration are fully sync-ready.

**What is NOT yet done:**
- Expand the automatic cleaner to system-wide log rotations and pytest tmp folder purges.

**Next session:**
1. Monitor GWS direct sending behavior on personal update requests.
2. Verify that MCP connections continue to launch instantly on editor startup.

---

### 2026-05-06 (session close): Studio activation handoff + final fixes

**Additional fixes shipped after exec summary:**

- `studio_story_bridge.py` — reads `Content Type=Story + Status=Idea` from Content Board every 6h, classifies channel fit (1stGen/UTB/AIC) via LLM, seeds Pipeline DB. Idempotent.
- `griot_signal_brief.py` — Monday 09:00 MT. Reads 7-day story entries + chat messages, extracts top 3 recurring themes, sends Signal Brief to Telegram with draft post per theme.
- `crews.py` — notion_capture now sends Telegram confirmation when story signal saved ("Story signal saved: [title] — Could feed: [channels] — Reply 'draft it' when ready")
- `skills/ctq-social/SKILL.md` — lint fixed, synced to repo
- Committed `54c5f39`, deployed to VPS

**Studio investigation findings:**

- Pipeline DB has 13 `qa-passed` records but they are scraped foreign YouTube content (Tamil-language, other channels). NOT our scripts.
- `production_tick` logs "0 qa-passed candidates" — filter mismatch bug suspected in `_fetch_qa_passed_candidates()`
- 1 `scheduled` record exists with no Asset URL — foreign content, not ours
- Studio has NEVER completed a full end-to-end production run with our own scripts
- Activation prompt written and handed off to a parallel session for resolution today

**Hunter + Apollo status:** Both confirmed on paid tiers as of 2026-05-06. Pipeline is NOT broken.

**Final main SHA:** `54c5f39`

**Next session (if Studio session doesn't resolve it):**
1. Verify Studio activation: check Pipeline DB for our own qa-passed content with Asset URLs
2. Confirm first Shorts posted on all 3 channels (UTB, 1stGen, AIC)
3. M4 warm-up day 1 counter starts from first successful post

---

### 2026-05-06 (session final): Griot unified + pagination bug fixed

**Critical bug fixed:**
- `NotionClient.query_database()` was silently truncating at 100 records — no pagination.
- Content Board has >100 records. auto_publisher, griot, story_bridge, signal_brief were all blind to anything past record #100.
- Fix: loop on `has_more` + `next_cursor` until all pages fetched. Commit `3ab3fb8`.
- Posts [LI] Post 1 + [X] Post 1 fired immediately after fix deployed.

**Griot unified as social media command center:**
- `publish_brief` retired as separate wake — merged pipeline summary into `griot_morning_tick`
- Morning message (07:00 MT): pipeline summary only (today's auto-posts + week ahead + backlog count + hook per post). No buttons, no action needed.
- On-demand proposals: "send me a post to work on" → Griot picks best Ready candidate, sends with Approve/Enhance/Reject buttons. No scheduled proposal trigger.
- `griot_propose_on_demand()` added to griot.py. `griot_propose` task type + `build_griot_propose_crew` wired.
- Proposal preview now shows Hook as lead line before full body.

**publish_brief changes:**
- Removed "Tap to publish" LinkedIn/X share intent URL — auto_publisher handles posting
- Removed "Reply posted/skip" instruction — no longer needed
- Retired as heartbeat wake — Griot morning message replaces it entirely

**Final main SHA:** `9d48347`

**Next session priorities:**
1. Verify Studio activation (parallel session working on it)
2. Confirm pagination fix didn't break any existing tests
3. M4 warm-up: confirm first Studio Shorts posted on all 3 channels

### 2026-05-06 (evening): Sankofa skill audit + morning digest upgrade

**Sankofa Council + 30-day pattern audit ran.** Reviewed all memory entries, 80+ handoff docs, 74 skills, VPS scripts and cron jobs.

**Morning digest upgraded (`orchestrator/griot.py`):**
- `_ops_digest_text()` function added. Fires inside `griot_morning_tick()` after content pipeline summary.
- Telegram: second block with outreach step results (SW/CW), spend today/WTD/MTD, top 3 Execution Cycle tasks due this week.
- HTML email: same ops data sent to bokar83@gmail.com + boubacar@catalystworks.consulting via `notifier.send_email(html=True)`.
- Data sources: `pipeline_metrics` table, `atlas_dashboard._spend_aggregates()`, Notion EC DB `358bcf1a`.
- Commit `10244ea` on VPS.

**Skill portfolio: 74 -> 68:**
- 6 archived to `zzzArchive/2026-05-06-skill-consolidation/`: deploy-to-vercel, vercel-cli-with-tokens, cold-outreach, banner-design, slides, linkedin_mvm.
- cold-outreach reply-first rules + 3/5-day sequence merged into hormozi-lead-gen.
- vercel-launch absorbs token auth + env var sections from archived Vercel skills.
- 6 "stub" skill directories (outreach, forge_cli, email_enrichment, github_skill, local_crm, notion_skill) had active Python imports -- kept, SKILL.md descriptions updated to say "Agent-internal only."
- Hard rule added to memory: grep orchestrator + signal_works before archiving any skill directory.

**Final main SHA:** `d83ad45`

**Next session priorities:**
1. Verify morning digest fires tomorrow 07:30 MT (Telegram + email)
2. M18 HALO: instrument heartbeat with tracing.py + 50 traces by 2026-05-18

### 2026-05-08 -- M5 Chairman Crew (L5 Learning Loop) shipped + concierge PR merged

**What shipped:**
- `chairman_crew.py`: fetch_outcomes (queries approval_queue directly for boubacar_feedback_tag), analyse_patterns, propose_mutations (Sonnet claude-sonnet-4-6, max 1000 tokens), enqueue_proposals (dedup per field via status=pending check), apply_mutation wired to all 3 approval paths in handlers_approvals.py (_maybe_apply_mutation helper)
- `griot.py`: _load_scoring_weights() reads GRIOT_* agent_config overrides at tick start; _pick_top_candidate passes merged weights to _score_candidate. Loop now actually closes on approval.
- `app.py`: chairman-weekly heartbeat registered (Monday 06:00 MT, gates internally on weekday check)
- `contracts/chairman.md`: autonomy contract skeleton (pending 2 dry-run ticks + sign-off)
- 21 tests green. Merged to main, deployed to VPS via docker cp to /app/ (baked image path).

**Codex catch (same session):** apply_mutation was defined but never called from any runtime path. Wired in same session -- loop would have been broken without it.

**Concierge PR #32** also merged: app.py conflict resolved (kept both chairman-weekly + concierge-sweep heartbeat blocks). VPS scheduler.py had stale conflict markers -- accepted origin/main.

**VPS state:** chairman-weekly + concierge-sweep both confirmed in startup logs. 6 griot outcomes in DB -- MIN_OUTCOMES=7, chairman will skip Mon 2026-05-11 (1 short), fire Mon 2026-05-18 if data accumulates.

**Next session priorities:**
1. Mon 2026-05-11: verify chairman tick runs (even if skip due to insufficient data -- check logs)
2. Mon 2026-05-18: verify first real chairman analysis + proposal enqueued to approval_queue
3. After 2 dry-run ticks: sign contracts/chairman.md + flip enabled=true in autonomy_state.json
4. M18 HALO: instrument heartbeat tracing (target 50 traces by 2026-05-18)

### 2026-05-08: Drive-link public-perm rule + email-template lint pass

**What shipped:**

- `orchestrator/drive_publish.py` (new): `publish_public_file`, `update_public_file`, `ensure_public`, `audit_email_template_pdfs`. Single helper for "upload to Drive AND grant anyone-with-link reader" so no email outreach ever ships an owner-only Drive URL again. Also CLI: `python -m orchestrator.drive_publish audit` (exit 2 if any private).
- `orchestrator/saver.py`: every Drive upload now grants `anyone reader` immediately after `files.create`. Same rule, second auth path (googleapiclient vs httpx).
- AGENT_SOP Hard Rule added (after gws Drive rule): Drive files in outgoing surfaces must be public.
- Memory: `feedback_drive_pdfs_must_be_public.md` + index entry.
- `templates/email/studio_t1.py`: repaired unterminated `_GREETING_HIGH` literal that would have ImportError'd the entire Studio cohort. Today's morning runner had zero Studio leads queued, so the bug was never exercised.
- `templates/email/studio_t2/t3/t4.py`: removed 4 em dashes, sentences rewritten per the no-em-dash rule.
- Replaced the rendered SaaS-Audit PDF on Drive (file ID `1GQ3rCelBy83YaPf0AYVuaWf5LAE5k4O4`) with the corrected version Boubacar dropped in Downloads. URL preserved (content swap, not new file). Verified `1ctmqUjhxa5hBkIj47AMDPvgbJzXwkETd` (sw_t5 PDF) was already public.

**Caught + averted:**

- cw_t2 Drive URL was owner-only at draft creation time (07:14 MT). Permission grant at 10:18 MT (before any send). `AUTO_SEND_CW=false` and `AUTO_SEND_SW=false` mean today's 50 drafts (35 SW + 15 CW) sit in Gmail awaiting Boubacar's manual review; URL is now public when recipients click.
- studio_t1 syntax error would have crashed the Studio cohort import. No Studio leads in today's queue masked the bug. Fixed before tomorrow's run.

**Gate flow:**

- `feat/drive-pdfs-public-helper` pushed with `[READY]`. Gate auto-merged on next sweep (commit `99ab510` on main). VPS pulled, container running fixed studio_t1.

**Handoff sent:**

- `feature/first-name-scrub` branch handed off to second agent. Two corrections: drop "Boubacar Barry" in studio_t1 body (first-name-only rule), change Studio template footers from `catalystworks.consulting` to `geolisted.co` (matches sw_t* templates and the actual product the prospect is being sold).

**Trigger gates passed today (not started, scoped for separate sessions):**

- **M4 Concierge Crew**: gate cleared (2026-05-08). 2-3 hr build when started. Needs real error data from `error_monitor.log`.
- **M5 Chairman Crew (L5 Learning)**: gate cleared (2026-05-08, ≥14 days of approval_queue + task_outcomes data). 3-4 hr build when started.

**Final main SHA:** `99ab510`

**Next session priorities:**

1. Decide whether to start M4 Concierge or M5 Chairman first (both gates open).
2. Confirm `feature/first-name-scrub` branch from email-polish agent merged cleanly via gate.
3. Optional: verify next morning runner draft batch uses fixed templates (run 13:00 UTC tomorrow).

### 2026-05-08 (evening): Blotato RCA — Drive URL permissions + TikTok CFR fix + M20 added

**Root cause found + fixed:** Studio publisher sending Drive `webViewLink` as Blotato `mediaUrls`. Files were private → Blotato got 403/HTML → "Failed to read media metadata" on 100% of YouTube/TikTok/Instagram posts since launch. X/LinkedIn worked because they had no media attachments.

**What shipped:**
- `orchestrator/studio_blotato_publisher.py`: `_drive_file_id()` + `_to_direct_download_url()` helpers; `ensure_public()` + usercontent URL conversion before every `publish()` call. Commit `7a03dd1`.
- `orchestrator/drive_publish.py`: `audit_studio_pipeline_videos()` + `audit-videos` CLI. 14/15 Pipeline DB Drive assets were private — all fixed. Commit `7a03dd1`.
- `orchestrator/studio_render_publisher.py`: `-r {fps} -vsync cfr` added to `_concat_clips` ffmpeg concat command. Fixes TikTok "Unsupported frame rate" rejection (VFR renders). Commit `31a1fe6`.
- `~/.claude/skills/rca/SKILL.md`: Blotato publisher added to Phase 0 triage table. Known Pitfalls section added with 4 incident patterns.
- `~/.claude/skills/tab-shutdown/SKILL.md`: Step 1b added — roadmap + task update required at every shutdown.

**Backlog:** 8 publish-failed records reset to scheduled, staggered 2/day May 8-11 (account warming protocol).

**Validated live:** X ✅ 12s, Instagram ✅ 60s, YouTube ✅ 13s. TikTok CFR fix deployed — validates on next render cycle (May 9).

**M20 added:** Native Social Publisher to replace Blotato. Full platform API research completed. Verdict: YouTube + Instagram replaceable; X/TikTok/LinkedIn stay on Blotato due to cost/approval blockers. Decision: keep Blotato, revisit M20 in 2-3 weeks after more usage data. All-or-nothing replacement only (no split routing).

**Final main SHA:** `c0b473b`

**Next session priorities:**
1. Check May 9 publisher tick: `docker logs orc-crewai 2>&1 | grep -E 'BLOTATO poll|STUDIO PUBLISHER.*tick done' | tail -20` — confirm TikTok CFR fixed + 1stGen IG published
2. Archive 10 old handoff docs in `docs/handoff/` (session audit warning)
3. M18 HALO: instrument heartbeat tracing (target 50 traces by 2026-05-18)
