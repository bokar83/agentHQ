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

*Last updated: 2026-04-25 (Saturday)*

| Loop | Status | Notes |
|---|---|---|
| L1 Propose | ✅ LIVE | griot-morning fires Mon-Fri 07:00 MT. Verified weekend gate working today. |
| L2 Schedule | ✅ LIVE | 5-min wake. Queue #3 scheduled for Monday 2026-04-27. |
| L3 Publish | 🟡 PARTIAL | Brief sends with share URL. Tap-to-publish is manual. Auto-publish (M7) is future. |
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

### M2: Skip Self-Heal, Same-Day Re-Pick ⏳ QUEUED

**What:** When M1's Skip button fires, the slot for today is now empty. Today's brief already went out, but tomorrow's griot-morning should *also* check "any Skipped from yesterday" and re-pick or backfill if needed.

**Why:** Without this, a Skip on Tuesday means Wednesday's slot is also empty (or whatever was already scheduled keeps that slot, but the Skipped post is dead). Need a clean re-pick path.

**Trigger:** After M1 ships, on Sunday 2026-04-26 (if Saturday lands clean) or next session.
**Blockers:** M1 must ship first.
**Branch:** `feat/griot-skip-recovery`
**ETA:** 30-60 min build.

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

### M7: Auto-Publish (L3 Closure) ⏳ DECISION-GATED

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

**Next:** observe Monday fire. If green, M2 (Skip Self-Heal) on next session. If red, debug before any new milestone.

---
