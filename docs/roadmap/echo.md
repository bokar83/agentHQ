# Echo - Async Partnership Substrate

**Codename:** `echo`. Async human-review layer for ALL autonomous agent actions — commits, deploys, content, outreach drafts. Agent queues proposals, human batch-acks via Telegram. Neither blocks on the other.

---

## Done Definition

**Reframed 2026-05-10 after Sankofa Council.** The commit-proposal use case is descoped — Gate already handles commits autonomously. Echo's real value is a unified async review queue for autonomous AGENT ACTIONS (content proposals, outreach drafts, deploy approvals, spend gates).

Echo is "done" when:

1. CrewAI agents (Griot, Hunter, Studio, Concierge) route proposals through the Echo queue instead of firing direct Telegram alerts.
2. Boubacar batch-acks proposals from one Telegram surface on his cadence.
3. Agents do not block on acks — they queue and continue.
4. At least 3 distinct proposal kinds flow through the same queue.
5. The queue handles ≥10 proposals/week from autonomous agents without manual intervention.

---

## Status Snapshot

*Last updated: 2026-05-10*

**Substrate:** SHIPPED. `tasks` table live on orc-postgres. `claim/complete/enqueue/proposal.propose/ack/reject` all operational.

**M1 infrastructure:** SHIPPED. `skills/coordination/proposal.py` + Telegram handlers + `.claude/commands/` shims all wired. Smoke tested 2026-05-10.

**Commit-proposal use case:** DESCOPED 2026-05-10. Gate handles commits autonomously. Not a problem Boubacar has.

**Next:** M3 — wire CrewAI agents to queue proposals through Echo instead of direct Telegram alerts. `approval_queue.py` is the existing pattern to unify.

---

## Milestones

### M1 - Slash command surface ✅ SHIPPED 2026-05-10

**Status:** SHIPPED. Commit-proposal use case DESCOPED — Gate owns commits. Infrastructure stays for M3.

**What shipped:** `/propose`, `/ack`, `/reject`, `/list-proposals` Telegram handlers + CC slash commands + `skills/coordination/proposal.py`. Smoke tested end-to-end. 19 gate tests green.

**Descoped:** commit-proposal workflow. Boubacar confirmed Gate already handles this. The queue infra is the asset; the commit use case was the wrong first instance.

---

### M2 - Second proposal kind DESCOPED

**Status:** DESCOPED 2026-05-10. The "7 days of real use + 50% friction reduction" gate assumed commit-proposals were the product. They are not. Skipping directly to M3.

---

### M3 - Multi-agent ingestion

**Status:** NEXT. No gate. Build when a session has 2+ hours.

**Goal:** Extend the queue to ingest from CrewAI runs and n8n workflows. Same schema, same ack UI. The queue becomes the single ack surface for ALL autonomous work in agentsHQ.

**Scope:**
- CrewAI flows write to `tasks` via `enqueue` instead of direct Telegram alerts.
- n8n HTTP node writes to `tasks` via Postgres directly.
- Single Telegram bot or web view consolidates all pending proposals across kinds.

**Trigger:** at least 2 proposal kinds in real use AND at least one CrewAI flow or n8n workflow producing surfaces that Boubacar acks.

---

### M2.5 - Push Gate: file-locking discipline + conflict detection

**Status:** PLANNED. Gated on M2 (`deploy-proposal` kind in real use).

**Goal:** Eliminate three failure modes confirmed 2026-05-04: merge conflicts on GitHub, push overwrites on shared branches, VPS wrong-code from concurrent deploys. Designed for 5+ concurrent agents (local Claude Code sessions + CrewAI subagents on VPS).

**Three layers, built in order:**

**Layer 1: File-locking discipline (rule + zero new code)**

- Hard rule in `AGENT_SOP.md`: before writing any file, agent calls `claim(resource='file:<path>', holder='<agent-id>', ttl_seconds=3600)`. Second agent gets `None` and waits.
- CLAUDE.md convention: "Never write a file without claiming it first."
- Verification: extend `test_agent_collision.py` with `file:` prefix test.

**Layer 2: Conflict detection in proposal queue (~20 lines in proposal.py)**

- Before queuing, `propose()` checks all `status='queued'` proposals for overlapping files.
- If overlap found: Telegram warning fires BEFORE enqueue.
- No new schema. No new table.

**Layer 3: VPS deploy gating + Gate Agent service**

- `orchestrator/gate_agent.py`: heartbeat service (60s tick), sole entity that merges to main, pushes GitHub, deploys VPS.
- Merge policy: auto-merge docs/tests/skills if tests green + no overlap. Ask via Telegram for orchestrator/pipeline/deploy changes.
- Priority escalation: send "PRIORITY: P-xxxx" to Telegram bot; gate processes within 60s, no manual push needed.
- `/nsync` becomes gate-aware: Step 0 flushes gate queue before sync verification.
- Hard gate: no agent ever pushes to main directly. Emergency = priority message to gate, not a bypass.

**Exit criteria:**

- C1: Two agents claim `file:orchestrator/pipeline.py` simultaneously; second returns None. Verified by test.
- C2: Two proposals with overlapping files fire Telegram conflict warning before either merges.
- C3: VPS deploy only fires after `deploy-proposal` acked.
- C4: Gate auto-merges a docs-only proposal without prompting.
- C5: `/nsync` runs clean after gate flushes queue.

**Trigger to start:** Gate already ships Layers 1+3. Layer 2 (conflict detection in proposal queue) builds when multi-agent collision occurs in practice.

**Council verdicts (2026-05-04):** Sankofa + Karpathy both say build discipline first. Gate Agent is Layer 3, not Layer 1. Layers 1+3 already SHIPPED via gate_agent.py + file-lock protocol in CLAUDE.md.

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

### 2026-05-10: Sankofa reframe — commit-proposal descoped, Echo repivoted to agent-action queue

Sankofa Council run against all five roadmaps. Echo verdict: commit-proposal use case was solving a problem that doesn't exist. Gate already handles commits from coding agents autonomously. Direct sessions have Boubacar present.

**Changes this session:**
- Done Definition rewritten: Echo is a unified async review queue for autonomous AGENT ACTIONS, not commits.
- M1 marked SHIPPED (infrastructure is real and useful for M3).
- M2 (second proposal kind) DESCOPED — gate assumed wrong use case.
- M3 ungated — it is now the next milestone with no prerequisite.
- M2.5 Layer 1+3 noted as already shipped via gate_agent.py + CLAUDE.md file-lock protocol.
- Status Snapshot updated to reflect 2026-05-10 reality.

**Next:** M3 — wire Griot/Hunter/Studio/Concierge to queue proposals through Echo queue instead of direct Telegram. `approval_queue.py` is the pattern; M3 unifies it.

### 2026-05-10: M1 slash commands SHIPPED — exit criteria pending

**What shipped:**

- `orchestrator/gate_agent.py`: 60s heartbeat, sole entity that merges/pushes/deploys. Detects [READY] branches, conflict-checks file overlap, runs tests, auto-merges clean branches, notifies Telegram on conflict/failure only.
- `orchestrator/contracts/gate.md`: signed autonomy contract (required by autonomy_guard).
- `scripts/gate_cron_install.sh`: one-shot host cron installer.
- `AGENTS.md`: hard rules (no agent push/deploy), [READY] sentinel, [GATE-NOTE] format, host-cron note.
- `CLAUDE.md`: Gate mode rule + task table live registry rule.
- Gate disabled in container heartbeat (no .git inside container). Moved to VPS host cron. Runs every 60s from `/etc/cron.d/gate-agent`. Telegram wired.

**Key fixes during session:**
- REPO_PATH -> DATA_DIR (Codex fix, 3 previous attempts failed without container FS inspection)
- `_gate_enabled()` reads `crews.gate.enabled` not `gate.enabled` (wrong key)
- Gate cron env vars wired: GATE_DATA_DIR=/root/agentsHQ/data, REPO_ROOT=/root/agentsHQ, Telegram tokens from .env

**Lessons locked in memory:**
- Inspect container FS before writing path code (`docker exec find /app`)
- Use Codex for surgical fixes, not iterative self-edits under pressure
- Define success criterion before deploy (`gate: tick start` in logs)
- Write+stage+commit atomically -- Edit tool writes reverted by hook stash cycle

**Gate verified:** `gate: nothing to process` firing every 60s. Telegram wired. Studio re-enabled. All 3 locations synced at f2acd29.

**Next session:** handlers_chat.py double-wrap fix (agent has branch, needs [READY] push). Gate spec doc in docs/superpowers/specs/ (optional, design already in echo.md + AGENTS.md).

### 2026-05-04: M2.5 Push Gate specced, Sankofa + Karpathy councils ratified

**What happened:**

Boubacar raised the multi-agent collision problem: 5+ concurrent agents (local Claude Code + CrewAI on VPS) stomping each other on commits, pushes, and VPS deploys. Three failure modes confirmed: merge conflicts on GitHub, push overwrites on shared branches, VPS wrong-code from concurrent deploys.

Sankofa verdict: do not build a monolithic Push Gate Master agent. Build resource-claiming discipline first (Layer 1, zero new code), then extend the existing Echo proposal queue with conflict detection (Layer 2), then add the Gate Agent service (Layer 3). Bureaucracy does not fix discipline gaps at the source.

Karpathy verdict: HOLD on a new agent. `claim()` and `proposal.py` already exist. Close the gap, do not rebuild. Gate policy confirmed: hard gate, no agent pushes to main directly, priority-message escalation for emergencies (not a bypass).

Resolution: M2.5 added between M2 and M3. Three-layer design documented. Gate Agent will be Claude acting as the gate for now, until `orchestrator/gate_agent.py` is built. `/nsync` will become gate-aware in Layer 3.

**Next session:** start Layer 1 (AGENT_SOP.md hard rule + test) when M2 (`deploy-proposal`) is in real use.

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
