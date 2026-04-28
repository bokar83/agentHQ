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

Last session ended **2026-04-25 (evening)**. State at close:

- **Three-way nsync at `75e1c71`** (local + origin + VPS)
- **M1 SHIPPED**, **M2 SHIPPED**, both verified live in container
- **M7 split** into M7a (decision spike, prep at `docs/roadmap/atlas/m7a-decision-spike.md`) + M7b (build, blocked on M7a)
- **Scheduled remote agent** `trig_015aDdXmiTAowm1HVkwQydnT` armed for 2026-04-27 09:00 MT, writes `docs/handoff/2026-04-27-atlas-m1-verification.md`
- **Studio roadmap** (`docs/roadmap/studio.md`) is sibling project, runs in a SEPARATE Claude Code instance; do not pivot here

**Default next moves (in priority order):**

1. Read `docs/handoff/2026-04-27-atlas-m1-verification.md` if Monday has passed
2. Manual VPS check: `ssh root@agentshq.boubacarbarry.com 'docker logs orc-crewai --since 6h | grep -E "publish_brief|griot_morning"'`
3. M7a if Boubacar signed up for the Blotato trial (decision matrix in m7a doc)
4. M3-M6 only when their date/data triggers hit (see milestone block)

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

## Status Snapshot

*Last updated: 2026-04-25 (Saturday evening, post M7a)*

| Loop | Status | Notes |
|---|---|---|
| L1 Propose | ✅ LIVE | griot-morning fires Mon-Fri 07:00 MT. Verified weekend gate working today. |
| L2 Schedule | ✅ LIVE | 5-min wake. Queue #3 scheduled for Monday 2026-04-27. |
| L3 Publish | ✅ LIVE | M7b SHIPPED 2026-04-25. Auto-publisher tick fires every 5 min via Blotato API ($20.30/mo Skool-discounted). Time-of-day slots (LI 07/11/12 MT, X 07/11/14 MT). Mon-Sat cadence, skip Sun. Past-due stagger (max 4/tick). publish_brief still sends Telegram digest as audit; auto_publisher does the actual posting. |
| L4 Reconcile | ✅ LIVE | Reply 'posted' or 'skip' to publish-brief Telegram message; Notion Status flips, task_outcomes written. Shipped 2026-04-25 (M1). |
| L5 Learn | ❌ OPEN | Blocked: needs ≥14 days of L4 data. Earliest viable 2026-05-08. |

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

### M4: Concierge Crew (Phase 4 proper) ⏳ TRIGGER-GATED

**What:** LLM-powered error triage crew. Reads VPS logs, groups errors by signature, uses Haiku to propose fixes, enqueues to approval_queue.

**Why:** error_monitor.sh (shell cron, shipped Phase 3.75) is the smoke alarm. Concierge is the firefighter.

**Trigger gate:** ≥3 error_monitor.sh alerts in a single week, OR 2026-05-08, whichever comes first.
**Blockers:** Need real error data. Currently 19h of silence on error_monitor.log.
**Branch:** `feat/concierge-autonomous`
**ETA:** 2-3 hr when triggered.

---

### M5: Chairman Crew (Phase 5, L5 Learning Loop) ⏳ TRIGGER-GATED

**What:** Weekly oversight crew. Reads approval_queue + task_outcomes, identifies patterns (rejection reasons, scoring drift, topic overlap), proposes mutations to scoring weights or leGriot prompts, enqueues to approval_queue.

**Why:** L5 closes the loop. Without it, scoring weights and prompts ossify.

**Trigger gate:** ≥14 days of approval_queue + task_outcomes data accumulated. Earliest viable 2026-05-08.
**Blockers:** M1 shipping (provides task_outcomes data); 14 days of pipeline operation.
**Branch:** `feat/chairman-learning-loop`
**ETA:** 3-4 hr when triggered.

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

## Descoped Items

These are explicit "do not build" decisions with reasons, so we don't relitigate.

| Item | Reason | Date decided | Revisit when |
|---|---|---|---|
| **Phase 3.5 drafter** (leGriot re-drafts approved candidates) | `content_board_reorder.py` (2026-04-21) already Sonnet-polished all 80 records. Re-drafting is solving a non-problem. | 2026-04-24 | A genuinely bad Draft ships through L3. |
| **Phase 2.5 event-triggered wakes** | No consumer until M4 or M6. Events without consumers are dead code. | 2026-04-24 | M4 or M6 starts and needs events. |
| **Single "Mark Posted" button** (original kickoff Option A as written) | Sankofa Council 2026-04-25: forgotten-tap failure mode + no escape hatch + no outcome capture. M1 (3-button row) ships richer version in same budget. | 2026-04-25 | Never. M1 supersedes. |
| **Phase 5 stub** (Chairman skeleton ahead of data) | Stub that does nothing for 2 weeks rots. Build when data is ready. | 2026-04-24 | M5 trigger gate hits. |
| **Phase 6 Hunter stub** (skeleton ahead of decision) | Hunter.io paused. Writing a stub for paused work is dead code. | 2026-04-24 | M6 trigger gate hits. |

---

## Cross-References

- **Memory:** `project_autonomy_layer.md` (per-phase shipping artifacts), `feedback_inspect_notion_schema_first.md`, `feedback_substrate_gates_before_callbacks.md`
- **Specs:** `docs/superpowers/specs/2026-04-23-phase-0-autonomy-safety-rails-design.md`, `docs/superpowers/specs/2026-04-24-phase-1-episodic-memory-and-approval-queue-design.md`, `docs/superpowers/specs/2026-04-24-phase-2-heartbeat-design.md`
- **Modules:** `orchestrator/griot.py`, `orchestrator/griot_scheduler.py`, `orchestrator/publish_brief.py`, `orchestrator/heartbeat.py`, `orchestrator/scheduler.py`
- **State:** `/root/agentsHQ/data/autonomy_state.json` on VPS
- **DB:** `approval_queue`, `task_outcomes` tables in `postgres` DB on `orc-postgres`

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

**THIS WEEK (by 2026-05-03):** Wire beehiiv REST API so newsletter_crew auto-creates a draft in beehiiv. ~1h Codex task.
- New file: orchestrator/beehiiv.py (create_draft via POST /v2/publications/{pub_id}/posts)
- New tool: BeehiivCreateDraftTool in tools.py, WRITING_TOOLS bundle
- New env vars: BEEHIIV_API_KEY + BEEHIIV_PUBLICATION_ID (.env + docker-compose.yml)
- Update build_newsletter_crew() task_write to call create_draft() after save_output
- Ideas DB entry: 34fbcf1a-3029-815c-b1bc-de7364215adb

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
