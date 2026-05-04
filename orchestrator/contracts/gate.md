# gate Autonomy Contract

Gate Agent (Echo M2.5): autonomous merge/deploy arbiter.
Sole entity that merges branches to main, pushes GitHub, deploys VPS.

---

## Gate 1: Silent Corruption

**C1: Output scope**
- Merges only feature branches with [READY] in last commit message
- Never merges protected branches (main, feature/coordination-layer, feature/echo-m1, fix/chat-empty-model-resolution)
- Never merges branches with file overlap against other queued branches
- Never merges if tests fail (pytest exit code != 0)
- High-risk files (orchestrator/scheduler.py, gate_agent.py, app.py, orc_rebuild.sh) require explicit approval

**C2: Dry-run not applicable**
- Gate is read-only until a branch qualifies for merge
- All merge/push/deploy actions are logged to container logs at INFO level
- Telegram notification sent on every merge batch (silent FYI) and every failure/conflict (urgent)

**C3: All writes logged**
- Every merge attempt logged: gate: merging <branch>
- Every push logged: gate: push main result
- Every deploy trigger logged: gate: deploy trigger written

**C4: Conflict detection**
- File overlap between any two queued branches blocks BOTH branches
- Telegram alert fires before any merge attempt when conflict detected

---

## Gate 2: Runaway Spend

**C5: Per-crew cost ceiling**
- Gate uses zero LLM calls in current implementation (git operations only)
- Ceiling: $0.01/tick (effectively $0 -- no LLM)

**C6: Max iteration count**
- No per-tick limit needed: processes all ready branches each tick
- Tick interval: 60s (registered in scheduler.py)
- Each merge + deploy is rate-limited by rebuild time (~3 min)

**C7: 7-day dry-run observation**
- Gate has no LLM calls; C7 DB check waived (zero autonomous llm_calls rows expected)
- Waived by owner: Boubacar Barry 2026-05-04

---

## Gate 3: Unrecoverable State

**C8: In-progress sentinel**
- Branch claim in tasks table: resource='branch:<name>', status='running'
- Gate skips claimed branches (fail-open if DB unreachable)

**C9: Stale sentinel TTL**
- Branch claim TTL: 7200s (2 hours) -- set by coding agents
- Gate does not set branch claims; it only reads them

**C10: Forced failure test**
- Merge failure: _merge_branch() calls git merge --abort on conflict
- Push failure: notifies Telegram, does not delete branch
- Deploy failure: logs error, notifies Telegram, branch still deleted (merge already done)

**C11: Idempotency**
- [READY] check: gate re-reads last commit each tick; already-merged branches disappear from branch-ahead-of-main list automatically

---

## Gate 4: Identity Drift

**C12: Output class**
Merge feature branches to main, push to GitHub origin, deploy VPS via trigger file.
No content generation. No LLM calls. No Notion writes. No email. No social posting.

**C13: Scope hard limits**
- Never touches main branch directly (only via merge)
- Never force-pushes
- Never deletes protected branches
- Only processes branches matching: feature/*, feat/*, fix/* prefixes

**C14: No generative content**
- Zero LLM calls in gate_agent.py
- All decisions are deterministic: file diff, test exit code, [READY] string match

**C15: Kill switch**
- Disable: set gate.enabled=false in autonomy_state.json OR docker exec set_crew_enabled('gate', False)
- Takes effect on next 60s tick

**C16: Contract gate**
- This file satisfies ContractNotSatisfiedError requirement
- Owner has reviewed and approved gate behavior before enabling

---

COST_CEILING_USD: 0.01
OUTPUT_CLASS: Merge feature branches to main, push GitHub, deploy VPS. No content generation. No LLM calls.
SIGNED: boubacar 2026-05-04
