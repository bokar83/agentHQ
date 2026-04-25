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
| L3 Publish | 🟡 PARTIAL | Brief sends with share URL. Tap-to-publish is manual. M7a SHIPPED (Blotato API verified, $20.30/mo Skool-discounted, 5-9 sec latency). M7b READY to build any session. |
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

### M7b: Auto-Publish Build (Blotato API) ⏳ READY

**What:** Build `orchestrator/blotato_publisher.py` against the verified Blotato API contract from M7a. Wire it into the publish-brief tick so Scheduled posts auto-fire on Scheduled Date instead of requiring Boubacar's tap-share-paste.

**Path locked by M7a:** Blotato API at $20.30/mo Skool-discounted. Direct LinkedIn/X OAuth path descoped (Blotato API verified working with 5-9 sec latency).

**Module shape (sketch, finalize during build session):**
- `BlotatoPublisher.publish(text, accountId, platform) -> postSubmissionId`
- `BlotatoPublisher.poll_until_terminal(postSubmissionId, max_wait_sec=120) -> (status, publicUrl|errorMessage)`
- Persist `postSubmissionId` in Notion record BEFORE polling (idempotency safeguard since Blotato has no documented idempotency key)
- On `published`, write `publicUrl` back to Notion as Posted URL, flip Status=Posted, write task_outcomes row (M1 reconcile path)
- On `failed`, log errorMessage and route to Atlas Concierge (M4 dependency, fail-soft until M4 ships: alert Telegram, leave Status=Queued for human retry)
- Auth: `BLOTATO_API_KEY` added to VPS .env on first deploy day (NOT before; per M7a prep doc rule kept until M7b is real)

**Why:** Final gap in L3 (currently 🟡 PARTIAL). Without M7b, the system requires Boubacar's daily tap-share-paste.

**Trigger:** Any session.
**Blockers:** None.
**Branch:** `feat/atlas-m7-auto-publish` (named after decision is made)
**ETA:** 60-90 min after M7a.

**What:** Replace manual one-tap publish with automatic posting on Scheduled Date.

**Two paths:**
1. **Blotato** ($9/mo, n8n workflow already built and inactive). 60-min activation.
2. **LinkedIn/X OAuth apps**. Multi-day app review per platform. Free.

**Why:** Final gap in L3 (currently 🟡 PARTIAL). Without M7, system requires Boubacar's daily tap.

**Trigger gate:** Boubacar's decision on Blotato spend OR willingness to wait for OAuth approvals.
**Blockers:** External (paid subscription or platform approval).
**Branch:** `feat/auto-publish-blotato` or `feat/auto-publish-oauth`
**ETA:** 60 min (Blotato) or several days wall-clock + 90 min build (OAuth).

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

---
