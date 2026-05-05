# Handoff: Autonomy Layer Phases 0/1/2 Shipped

**Date:** 2026-04-24 (late night session 2026-04-23 into 04-24)
**Session:** end-of-session handoff; next session picks up with Phase 3 (Griot pilot) design
**Status:** Phases 0, 1, and 2 live on VPS. Fully verified including Telegram smoke tests.

## System state on 2026-04-24 end-of-session

**Live on VPS (`72.60.209.109`, `/root/agentsHQ`, branch `main`):**

Commits on main after the session (top to bottom, newest first):

```
bdb8401 Phase 2: heartbeat scheduler (#12)
25213f0 fix(phase1): address Codex review round 2 on PR #11 (#13)
2f85ed7 fix(phase1): address Codex review findings on PR #10 (#11)
39ee56f Phase 1: episodic memory + approval queue (#10)
64dd319 Phase 0: autonomy safety rails (spend cap, kill switch, feature flags) (#9)
```

**`orc-postgres` tables added or extended:**

- `llm_calls` + columns `autonomous BOOLEAN` and `guard_decision TEXT` (migration 004)
- `approval_queue` (migration 005)
- `task_outcomes` (migration 005)

**`orc-crewai` container runtime state:**

- State file: `/root/agentsHQ/data/autonomy_state.json` (volume-mounted, survives container rebuild). All 4 crews `enabled=false, dry_run=true`. No autonomous work fires.
- Heartbeat thread registered 3 default wakes at 07:00, 13:00, 19:00 MT, all using `heartbeat-self-test` crew which is exempt from the kill switch.
- Digest thread registered at 07:00 MT.

**Env vars on VPS `.env` (already in place):**

```
AUTONOMY_ENABLED=true
AUTONOMY_DAILY_USD_CAP=1.00
AUTONOMY_STATE_FILE=data/autonomy_state.json
```

## What works right now (can verify on phone)

- `/autonomy_status` → autonomy live, `$0.0000 / $1.00`, all crews off/dry-run
- `/pause_autonomy` → kill switch flips, persists across restart
- `/resume_autonomy` → restores
- `/spend` → spend snapshot + per-crew breakdown
- `/queue` → currently empty (2 test proposals from Phase 1 smoke already decided)
- `/approve <id>` / `/reject <id> [tag] [note]` → command-line approval paths
- `/outcomes <crew> [days]` → crew_stats rollup with top feedback tags
- `/heartbeat_status` → lists 3 default wakes with next-fire times and guard status
- `/trigger_heartbeat <wake_name>` → dry-run only in Phase 2 (reports what would fire)
- Reply-to-message approvals with natural-language aliases (yes/no/approve/reject/edit:...)
- Inline button rejection feedback (off-voice / wrong-hook / stale / too-salesy / other / skip)
- 5-minute free-text rejection-tag window after a reject (guards prevent random chat being eaten as tags)
- HTTP `POST /autonomy/approve/:id` (API-key gated, laptop parity)
- Morning 07:00 MT digest with pending approvals count (true count, not capped)

## What's NOT running (intentional)

- No crew produces autonomous proposals. Phase 3 is where Griot starts doing that.
- No event-triggered wakes (Supabase realtime, webhook listeners). Phase 2.5.
- No learning loop / prompt mutation. Phase 5 Chairman.
- The `crew_lessons` table is NOT in migration 005 (deferred to Phase 5 per the Council gate).

## Save points (rollback menu, newest first)

```
savepoint-phase-2-shipped-20260424
savepoint-pre-phase-2-20260424
savepoint-phase1-codex-round2-shipped-20260424
savepoint-pre-hotfix-codex-round2-20260424
savepoint-phase1-codex-hotfix-shipped-20260424
savepoint-pre-hotfix-codex-phase1-20260424
savepoint-phase-1-shipped-20260424
savepoint-pre-phase-1-20260424
savepoint-phase-0-autonomy-shipped-20260423
savepoint-pre-autonomy-20260423
```

Rollback pattern for any of them:

```
git reset --hard <tag>
docker compose up -d --build orchestrator
```

## Standing rules locked during this session (in memory)

- `feedback_sankofa_major_plans.md`: Council mandatory for every major plan (new module, migration, autonomous behavior, infra change). Don't ask; just run it.
- `feedback_deploy_autonomously.md`: Once local unit + E2E + static pass, go straight to VPS. No ultrareview gate. Only Telegram/HTTP/UX testing needs Boubacar.
- `feedback_test_before_live.md`: Claude tests code in virtual envs / with mocks before claiming anything works. Boubacar only tests live endpoints.
- `feedback_monitor_permission.md`: Blanket approval for the Monitor tool.
- `feedback_hotfix_scope_discipline.md`: Smallest change that fixes the exact reported bug. Don't overcorrect on hotfixes.
- `feedback_db_split.md`: agentsHQ-internal operational data → local Postgres (orc-postgres). Data Boubacar / Notion / n8n need to see → Supabase. Not anti-Postgres, just anti-Airtable.

## Numbers from the session

- 5 PRs merged: #9, #10, #11, #12, #13 (two hotfix rounds on Phase 1 after Codex reviews)
- 6 save-point tags pushed to origin
- 86/86 regression tests green end-of-session (up from 35 at start)
- ~3000 lines of production code across 6 new modules + 3 migrations + 4 test files
- 2 Telegram smoke tests verified by Boubacar on phone (approve path + reject+button-tag path + /heartbeat_status + /trigger_heartbeat)

## What the next session picks up

**Primary candidate: Phase 3 (Griot pilot).** This is the first real autonomous crew. Requires:

- Griot crew definition (role, goal, backstory, tools) registered as a wake callback via `heartbeat.register_wake("griot-morning", crew_name="griot", at="07:00", callback=griot_morning_tick)`
- `griot_morning_tick` function that reads Notion Content Board + ideas backlog, decides what to propose, calls `approval_queue.enqueue("griot", "post_draft", payload)`
- Griot's decision logic: how does it pick? This is where the Council gate really matters. Voice match, cadence, engagement patterns from `task_outcomes`, avoiding duplicate angles.
- Reading approved proposals and actually publishing them. (Consider whether to ship L1-propose-only first, then add publishing in a second PR.)
- Cost control: Griot's first morning fire should cost <$0.10. Lots of work to precompute state before calling the LLM.
- Council will raise: voice drift, token cost, duplicate-post risk, "what if the ideas backlog is empty," and error-on-publish behavior.

**Secondary candidate (if Boubacar chooses): Phase 2.5 (events).** Smaller, mostly-plumbing. No callbacks consume events yet, so it's preparatory.

**Suggested approach for Phase 3:**
1. Run Sankofa Council on the design BEFORE writing the spec (per standing rule)
2. Write spec with Council fixes integrated
3. Owner approves
4. writing-plans → inline execution
5. Test virtually with mocked Notion + LLM before deploy
6. Ship with `griot.enabled=false` still; flip only after dry-run logs look right for 48h

## Known open items (not blocking)

- The `adversarial_report.md`, `code_review_20260422.md`, and `docs/handoff/2026-04-23-hermes-inspired-upgrades-prompt.md` files are untracked in the working tree and pre-date this session. Leave alone unless Boubacar mentions them.
- `skills/opencli_skill/README.md` and `skills/opencli_skill/SKILL.md` have in-working-tree modifications from before this session. Intentional per notes; ignore.
- Tomorrow at 07:00 MT, the first scheduled heartbeat fire will write `task_outcomes` row with `crew_name='heartbeat-self-test'`. Easy sanity check on the heartbeat loop.

## Next-session prompt is at the end of this handoff or in the chat.
