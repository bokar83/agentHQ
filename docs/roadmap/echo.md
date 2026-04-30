# Echo - Async Partnership Substrate

**Codename:** `echo`. The agent and the human echo each other's work asynchronously: agent proposes, human acks, neither blocks on the other.

---

## Done Definition

The pause-to-commit ceremony is gone. Boubacar can let Claude (or any autonomous agent in agentsHQ) work for an extended stretch without ever having to stop the agent to commit, push, or acknowledge a checkpoint. Concretely:

1. Agent proposes commits asynchronously (via slash command). Boubacar acks them on his cadence.
2. Acks happen in 1 keystroke (Telegram tap, slash command, or web one-click).
3. Agent does not block on acks. It moves to the next task. Backlog of un-acked proposals does not stall the agent.
4. Multiple proposal kinds (commit, deploy, publish, draft) flow through the same queue.
5. After 1 week of real use, the count of "pause and commit" interruptions in chat history is at least 50% lower than baseline.

---

## Status Snapshot

**Substrate (the foundation, NOT the product):** SHIPPED on `feature/coordination-layer`.

- `skills/coordination/__init__.py` - Postgres `tasks` table with `claim/complete/lock/enqueue/claim_next/fail/recent_completed/renew`.
- `skills/coordination/cli.py` - bash shim (`with-lock` subcommand).
- 14 tests green, 4 callers wired (morning_runner, outreach_runner, deploy.sh, vercel-launch).
- Schema live on prod orc-postgres.

**Echo product:** NOT STARTED. M1 begins when Phase 1 ships.

---

## Milestones

### M1 - Slash command surface (THE SVP)

**Status:** READY. Build any session.

**Goal:** Prove the async-partnership flow with the smallest possible surface. Three slash commands plus one new proposal `kind` in the existing queue.

**Scope:**

- `/propose` slash command:
  1. Run `git status --porcelain` and `git diff --stat HEAD`.
  2. Run a configurable test command (default `pytest -q`).
  3. Generate a commit message from the diff via the active model.
  4. `enqueue(kind='commit-proposal', payload={files, suggested_message, tests_status, branch, repo_path, diff_summary})`.
  5. Send a Telegram message via the existing helper to Boubacar's chat ID with proposal ID + summary + reply instructions.
  6. Print "Proposal queued. Continuing." to chat. Agent moves on.
- `/ack <N>` slash command: read proposal N, run `git add <files> && git commit -m '<msg>'`, mark row done.
- `/reject <N>` slash command: mark row rejected, no commit, no further action.
- CLAUDE.md addition: convention for when Claude should call `/propose` (after a coherent unit hits green tests).

**No new schema work.** `tasks` table already has `kind` and `payload jsonb`.

**Build sequence:** see Session log entry at the bottom for the actual checklist.

**Exit criterion:**
- Boubacar uses `/propose` for one full work day.
- Telegram acks work end-to-end.
- Agent never blocks waiting for an ack.

**Blockers:** None. Substrate exists.

**ETA:** 90-120 minutes.

---

### M2 - Second proposal kind

**Status:** GATED on M1 + 1 week of real use.

**Goal:** Generalize the queue to a second proposal type. Validates the "ack queue as platform" hypothesis from Sankofa Expansionist.

**Candidates (pick whichever has highest ack-friction in real workflow):**

- `kind='publish-proposal'` - newsletter/social drafts surface as proposals.
- `kind='deploy-proposal'` - deploy.sh drops a proposal, ack-to-deploy from Telegram.
- `kind='draft-proposal'` - outreach drafts queue as proposals you batch-ack.

**Trigger to start:** M1 has been in real use for at least 7 days AND interruption-rate measurement shows 50%+ reduction (validates the substrate is doing what we hoped).

**Trigger to NOT start:** if M1 has not produced friction reduction, debrief and consider the Outsider's hypothesis (the friction was ack-cost, not detection) before generalizing.

---

### M3 - Multi-agent ingestion

**Status:** GATED on M2.

**Goal:** Extend the queue to ingest from CrewAI runs and n8n workflows. Same schema, same ack UI. The queue becomes the single ack surface for ALL autonomous work in agentsHQ.

**Scope:**
- CrewAI flows write to `tasks` via `enqueue` instead of direct Telegram alerts.
- n8n HTTP node writes to `tasks` via Postgres directly.
- Single Telegram bot or web view consolidates all pending proposals across kinds.

**Trigger:** at least 2 proposal kinds in real use AND at least one CrewAI flow or n8n workflow producing surfaces that Boubacar acks.

---

### M4 - Auto-detection (DEFERRED INDEFINITELY)

**Status:** DEFERRED.

**Why:** Both Sankofa and Karpathy councils on 2026-04-29 said convention-driven proposal is the right primitive. Auto-detection requires harness changes Claude Code does not have, AND is the wrong abstraction (judgment problem dressed as detection problem).

**Trigger to revisit:** real data from M1-M3 shows that Claude is consistently calling `/propose` at the wrong moments (too early, too late, missing entire units). Until then, this stays deferred.

---

### M5 - Reversible redirection across dependent tasks (DEFERRED)

**Status:** DEFERRED.

**Why:** Today's `git stash` + `git reset --hard <sha>` is enough for single-task rollback. The harder capability ("redo Action 2 without losing Action 3 that was built on top") is a real distributed-system problem and requires M1-M3 to be in steady use first so we have data on actual rollback patterns.

**Trigger to revisit:** Boubacar hits at least 3 cases where rolling back a proposal forces him to manually replay later work. At that point, design the dependency-aware revert.

---

## Descoped Items

| Item | Reason | Date decided | Revisit when |
|---|---|---|---|
| **Automatic checkpoint detection in M1** | Sankofa Contrarian + Karpathy: Claude Code has no "tests just turned green" hook; weak detection (Stop hook + git status poll) is fragile and proposes commits at false maxima. Convention-driven `/propose` collapses the AI problem into mechanics. | 2026-04-29 | M4 trigger fires (Claude consistently calls /propose at wrong times). |
| **Web dashboard for proposals in M1** | Sankofa Outsider + Karpathy: Telegram 1-tap ack covers 90% of the value at zero new infra cost. Building a web view first is overdesign. | 2026-04-29 | Telegram ack flow proves insufficient (Boubacar wants to see diffs in browser before acking). |
| **Generic ML observer that watches all tool calls** | Karpathy: this is "self-observation when you can have self-reporting." Self-reporting is one line of code per checkpoint. Self-observation is an ML problem dressed as infrastructure. | 2026-04-29 | M1 in real use shows that self-reporting is missing critical events. |
| **Five-capability framing** | Karpathy: "spec is overbuilt by 4 of 5 capabilities." Only #3 (proposal queue) and #5 (revert wrapper) have standalone value. #1, #2, #4 collapse into "agent calls /propose by convention." | 2026-04-29 | Never. The 5-capability frame is replaced by M1-M5 above. |

---

## Cross-References

- **Substrate code:** `skills/coordination/__init__.py`, `skills/coordination/cli.py`.
- **Existing async approval pattern (study, do not duplicate):** `orchestrator/approval_queue.py` - Telegram-mediated human approvals for autonomous actions. Uses Postgres rows with proposal_type, callback_data, ack workflow. M1 should match this pattern's shape so M3 can unify them.
- **Telegram send helper:** `signal_works/morning_runner.py:_telegram_alert` (urllib pattern).
- **Memory:** `project_async_partnership_substrate.md` (the actual goal, named).
- **Tasks table:** prod `orc-postgres`, schema in `skills/coordination/__init__.py:init_schema`.
- **Hard rule:** `feedback_now_means_proactive_not_broken.md` - proactive prevention is fine; do NOT demand demonstrated past failures to ship Echo work.

---

## Session Log

### 2026-04-29: Echo conceived, M1 specced, councils ratified the plan

**What happened:**

After shipping the coordination substrate (claim/lease + queue + heartbeat) on `feature/coordination-layer`, Boubacar named the actual goal: a self-observing work ledger that detects checkpoints and proposes commits asynchronously, so he never has to pause the agent to commit. Two councils ran in parallel.

**Sankofa verdict:** Build `/propose`, `/ack`, `/reject` slash commands today (90-120 min). Use the existing `tasks` table with a new `kind='commit-proposal'`. Convention-driven, not detection-driven. The agent calls `/propose` at logical work boundaries; CLAUDE.md teaches it when. Defer auto-detection indefinitely.

**Karpathy verdict:** Spec is overbuilt by 4 of 5 capabilities. Only the proposal-queue capability and the revert-wrapper capability have standalone value. Convention-driven `/propose` is BUILDABLE NOW on top of the existing substrate. Self-observation should be replaced with self-reporting (one line per checkpoint, not an ML observer).

**Resolution:** Both councils agree. Build `/propose` first. Defer everything else until M1 produces real-use data.

**M1 build checklist (next session):**

1. Add `proposal.py` to `skills/coordination/` - three functions: `propose(repo_path, branch=None) -> proposal_id`, `ack_proposal(proposal_id) -> commit_sha | None`, `reject_proposal(proposal_id, reason=None)`.
2. Use `enqueue(kind='commit-proposal', payload={...})` to drop the proposal row.
3. Telegram send to `OWNER_TELEGRAM_CHAT_ID` (already in container env) using urllib pattern from morning_runner.
4. Build `.claude/commands/propose.md`, `.claude/commands/ack.md`, `.claude/commands/reject.md` slash commands that wrap the Python.
5. Add a CLAUDE.md note: "after a coherent unit of work hits green tests, call /propose."
6. Smoke test: make a 1-line code change, call /propose, confirm Telegram arrives, /ack from chat, confirm git commit lands.
7. Commit Echo M1 on `feature/coordination-layer` (or new `feature/echo-m1`, decide at build time).

**Substrate state at session pause:**
- `skills/coordination/__init__.py`: 14 tests green, 4 callers wired, `renew()` heartbeat shipped, queue mode operational.
- 2 new tests added (`test_morning_runner_lock_serializes_concurrent_invocations`, `test_outreach_runner_lock_serializes_concurrent_invocations`) per Karpathy's missing-test note.
- 2 new heartbeat tests (`test_renew_extends_lease_and_blocks_competing_claim`, `test_renew_returns_false_after_reclaim`).
- All 14 tests green on `feature/coordination-layer`.
- M1 has not started yet. Boubacar approved start "right now" at end of session.

**Next session:** start M1 build at step 1 above.

### 2026-04-29 (later): Echo M1 SHIPPED end-to-end

**What happened:**

Same session as the design above. Boubacar approved continuing instead of waiting. Build took roughly 45 minutes once moving (most of the council-time was the design that landed in this same doc). Worktree at `d:/Ai_Sandbox/agentsHQ-echo` on branch `feature/echo-m1` to escape cross-session branch mutation.

**What shipped:**

- `skills/coordination/proposal.py` (341 lines): `propose()`, `ack()`, `reject()`, `list_pending()`. Synthesizes Conventional Commits messages from working-tree diff. Sends Telegram via existing urllib pattern. Marks rows in the existing `tasks` table with `kind='commit-proposal'`.
- `.claude/commands/propose.md`, `ack.md`, `reject.md`, `list-proposals.md`: project-level slash commands that wrap the Python module.
- `CLAUDE.md` updated: convention for when to call `/propose` (logical unit complete + tests green or N/A; do NOT block on user). Added `echo` to active-roadmaps table.

**E2E smoke test (real, observed):**

1. Edited `proposal.py` (added "Shipped 2026-04-29." line in module docstring).
2. Called `proposal.propose()` from worktree -> proposal `0b417e46` queued in prod Postgres, Telegram message arrived.
3. Called `proposal.ack('0b417e46')` -> staged the file, ran `git commit`, real commit `40372e9` landed on `feature/echo-m1`. Suggested message used. `list_pending()` confirms zero pending after ack.
4. Branch pushed to origin.

**Known cosmetic issue (not blocking ship):**

- `_suggest_commit_message()` produces multi-line strings; git collapses them into the subject line under `-m`. Subject reads "feat(coordination): proposal.py Branch: feature/echo-m1" instead of "feat(coordination): proposal.py" with branch in body. Fix: use `git commit -F-` with a temp file, or split subject and body explicitly. Defer to next session.

**Cross-session interference fix:**

Echo work runs from `d:/Ai_Sandbox/agentsHQ-echo` worktree on `feature/echo-m1`. Main checkout `d:/Ai_Sandbox/agentsHQ` keeps doing what other sessions need. Worktrees prevent the "branch flips underneath me" pattern that cost ~30 min today.

**M2 trigger:**

7 days of real `/propose` use starting 2026-04-30. If interruption count drops 50%+, build the second proposal kind (publish/deploy/draft).

### 2026-04-30: Day 1 of M2 7-day clock + cosmetic fix shipped

**What happened:**

Resumed in `d:/Ai_Sandbox/agentsHQ-echo` worktree. Popped the `echo-m1-session-log-pending` stash cleanly (orphan deletion was gone in fresh shell). Fixed the cosmetic commit-message issue in `skills/coordination/proposal.py`: `_git()` now accepts an optional `stdin` arg, and `ack()` calls `git commit -F -` with the message piped in instead of `-m '<multi-line>'`. Verified with a `--dry-run` smoke test that git accepts the stdin path on Windows.

Ran 2 `/propose` calls this session:

- `fb18ddba` (queued): docs (handoff + echo session log).
- `a4581326` (queued): docs + proposal.py -F- fix.

Both pending Boubacar's ack.

**Tasks ledger baseline (start of M2 7-day clock):**

```text
Today (2026-04-30): 3 commit-proposals, 0 acked, 2 queued, 1 failed.
All-time: 5 total | done=1, queued=2, failed=2.
```

**M2 friction observation #1: bundle creep.**

`propose()` snapshots ALL unstaged + untracked files in the working tree, not just the unit just finished. If I propose unit A, then start unit B and propose B before Boubacar acks A, the B snapshot includes A's files. After Boubacar acks A, B's queued row is stale (those files are already committed). Today this was visible: `fb18ddba` had 2 files; `a4581326` included those same 2 files plus the new one. Fix candidates for M2: (a) `propose()` stages-then-snapshots so each row is scoped to one unit; (b) `ack()` GC's superseded queued rows on the same paths. Defer until day 7.

**No nag fires observed today.** Stop-hook ran after each turn; nothing nagged because every coherent unit had a fresh `/propose` call.

**MEMORY.md cleanup:** 198 lines down to 197 by collapsing duplicate Newsletter Voice pointers into one bullet. Buffer back to 3 lines under cap.
