# Session Handoff - Echo M1 Shipped - 2026-04-29

## TL;DR

Started as "agentic collaboration improvement: asynchronous is truly collaborative." Built the coordination substrate (Postgres tasks table with claim/lock/queue/heartbeat), wired four single-fire callers (morning_runner, outreach_runner, deploy.sh, vercel-launch), then realized via Sankofa+Karpathy councils that the actual goal was async commit proposals. Built Echo M1 end-to-end: proposal.py module, four slash commands (/propose /ack /reject /list-proposals), mandatory CLAUDE.md rule, Stop-hook nag with Telegram. E2E smoke test passed live in production. Worktree pattern adopted to escape cross-session branch interference. Branch `feature/echo-m1` pushed to origin; PR-ready.

## What was built / changed

### New code
- `skills/coordination/__init__.py` (~250 lines) - `claim/complete/lock` (single-holder locks), `enqueue/claim_next/fail/recent_completed` (work queue, FOR UPDATE SKIP LOCKED), `renew` (heartbeat), `init_schema`, `list_running`. Race-free via partial unique index on `tasks(resource) WHERE status='running'`.
- `skills/coordination/cli.py` (~60 lines) - bash shim. `python -m skills.coordination.cli with-lock <resource> --ttl N -- <cmd>`. Exits 75 if held.
- `skills/coordination/proposal.py` (341 lines) - Echo M1 propose/ack/reject/list_pending. Synthesizes Conventional Commits messages from working-tree diff. Telegram via urllib.
- `tests/test_agent_collision.py` (14 tests, all green) - concurrent-claim-one-winner, lease-expiry-handover, complete-releases, visibility-query, queue-FIFO, queue-stale-revive, fail-stays-failed, recent-completed-readback, runner-serialization × 2, renew-extends-lease, renew-returns-false-after-reclaim.
- `.claude/commands/propose.md`, `ack.md`, `reject.md`, `list-proposals.md` - project-level slash commands.
- `.claude/hooks/echo-nag.py` (194 lines) - Stop-hook nag. Fires Telegram if turn ended with non-trivial uncommitted work AND no recent /propose for this branch.
- `docs/roadmap/echo.md` - Echo roadmap, Done definition, M1-M5 milestones, Descoped table.

### Wired callers (single-fire prevention via lock)
- `signal_works/morning_runner.py:67-83` - `task:morning-runner`, TTL 1800s. Body extracted to `_main_body()`.
- `signal_works/outreach_runner.py:33-44` - `task:outreach-runner-cw`, TTL 900s.
- `deploy.sh` lines 11-17 - mkdir-mutex (Linux+Windows portable) on temp lockdir.
- `skills/vercel-launch/scripts/launch.sh` lines 24-30 - mkdir-mutex per app name.

### Configuration
- `CLAUDE.md` - Echo added to active-roadmaps; `/propose` upgraded from guidance to HARD RULE with three named exemptions only.
- `.claude/settings.json` - hooks.Stop array wired to `echo-nag.py`.
- `docs/roadmap/atlas.md` - Agent Task Ledger descoped row re-opened with rationale (proactive priority overrides 2026-04-28 Sankofa+Karpathy descope per `feedback_now_means_proactive_not_broken.md`).
- `docs/roadmap/README.md` - `echo` codename registered.

### Infrastructure (VPS)
- `tasks` table created in prod `orc-postgres` (database `postgres`). Schema: id pk, resource, status, claimed_by, claimed_at, lease_expires_at, result jsonb, created_at, kind, payload jsonb, error.
- Two indexes: partial unique on `(resource) WHERE status='running'`, partial on `(kind, created_at) WHERE status='queued'`.
- `orc-crewai` container rebuilt (twice) to bake new `skills/coordination/` and updated runners.
- SSH tunnel 5432->VPS:5432 active for laptop access.

### Git state
- Branch `feature/coordination-layer`: 7 commits pushed (substrate, wire-ins, atlas docs, heartbeat, integration tests, Echo roadmap, slash commands, proposal.py).
- Branch `feature/echo-m1`: 4 commits in worktree at `d:/Ai_Sandbox/agentsHQ-echo`. All pushed.
- PRs ready (not opened): https://github.com/bokar83/agentHQ/pull/new/feature/coordination-layer and https://github.com/bokar83/agentHQ/pull/new/feature/echo-m1.

## Decisions made

1. **Ledger over locks for the substrate.** Sankofa Expansionist's reframe. One `tasks` table with two operating modes (resource locks + work queue) instead of two tables. Locked 2026-04-29.
2. **VPS-only Postgres for coordination.** Not laptop Postgres. Laptop reaches via SSH tunnel; VPS-side callers reach via discrete env vars. Locked.
3. **Convention-driven /propose, not auto-detection.** Both councils ratified. M4 (auto-detection) deferred indefinitely. Locked.
4. **Echo M1 reuses existing `tasks` table with `kind='commit-proposal'`** instead of building a new `proposals` table. Future M3 will unify with `orchestrator/approval_queue.py`. Locked.
5. **Worktrees for session isolation.** When multiple Claude Code sessions are open on the same repo, separate working trees prevent branch flips and file reverts. Used for Echo work; recommended for other long-lived feature branches. Locked.
6. **mkdir-mutex over flock for portable bash.** flock missing on Windows Git Bash. mkdir is atomic on POSIX + NTFS. Used in deploy.sh and vercel-launch. Locked.
7. **Step B (soft nag) before Step C (auto-propose).** Don't auto-fire propose without first measuring whether the convention alone catches the cases. Auto-propose deferred to after one day of nag data. Locked.

## What is NOT done (explicit)

- **Auto-propose at Stop hook (Step C).** Waiting for one day of nag data first. Trigger: if nag fires more than ~3 times per day, escalate.
- **CLAUDE.md propagation to main checkout.** The mandatory /propose rule lives on `feature/echo-m1`. Other sessions on different branches do NOT see this rule until merged to main. Echo enforcement is currently scoped to sessions opened in `d:/Ai_Sandbox/agentsHQ-echo`.
- **CrewAI / n8n / cron integration (M3).** The substrate supports it (just need to enqueue with new `kind` values), but no producer wired yet. Gated on M2 success.
- **Second proposal kind (M2).** Trigger date: 2026-05-06. If 7 days of /propose use shows 50%+ friction reduction, build publish-proposal or deploy-proposal next.
- **Cosmetic fix in `_suggest_commit_message()`.** Subject and body collapse onto one line when git commit -m gets a multi-line string. Need `git commit -F-` with stdin, ~10 lines change. Filed as known issue in echo.md session log.
- **Session-log update for echo.md is stashed.** Stash named `echo-m1-session-log-pending` on `feature/echo-m1`. Got blocked by an unrelated session deleting `docs/ai-governance/WIP-AI Governance/AI-Governance-Foundation-Landscape-Research-2026-04-16.md` in the worktree, which broke pre-commit's stash-unstaged step.
- **MEMORY.md is at 208 lines (cap=200).** Truncation kicks in past 200. Needs a cleanup pass next session: collapse three Newsletter Voice entries, shorten long descriptions, or move stale rules to MEMORY_ARCHIVE.md.

## Open questions

- **Did the orphan deletion in `docs/ai-governance/` come from another active session, or is the worktree's git index just inconsistent?** If active session, expect more interference. If index drift, `git checkout HEAD -- <path>` should restore in a fresh shell.
- **Will the nag fire false positives at acceptable rates?** First day of real use answers this. If it nags on every minor turn, the trivial-line threshold (currently 6) needs raising.
- **Should the nag escalate if it fires N times in a row without a /propose response?** v1 deliberately does not; one nag per turn is the contract. Revisit after data.
- **PR or no PR?** Both `feature/coordination-layer` and `feature/echo-m1` are PR-ready. Boubacar can merge directly to main if he wants the convention enforced for all sessions, OR keep them as feature branches and use only from the worktree.

## Next session must start here

1. **Open the worktree:** `cd d:/Ai_Sandbox/agentsHQ-echo`. Confirm branch is `feature/echo-m1`.
2. **Verify SSH tunnel:** `netstat -an | grep ':5432 '`. If not listening, `ssh -fN -L 5432:127.0.0.1:5432 root@agentshq.boubacarbarry.com`.
3. **Pop the stashed session-log update:** `git stash list` → find `echo-m1-session-log-pending`, `git stash pop`. Resolve the orphan deletion (`git checkout HEAD -- 'docs/ai-governance/...'` may work in a fresh shell). Commit and push the session log addition to echo.md.
4. **Use /propose for the day's real work.** Every coherent unit gets a propose call. Watch the Telegram nag. Note any false-positive nags and any missed-propose moments.
5. **Fix the cosmetic commit-message issue** in `proposal.py` `ack()` - switch from `git commit -m '<multi-line>'` to `git commit -F-` with stdin. ~10 lines.
6. **MEMORY.md cleanup:** wc -l, target ≤195. Either collapse Newsletter Voice triplet, shorten descriptions, or archive stale entries to MEMORY_ARCHIVE.md.
7. **End-of-day:** check `tasks` row count for `kind='commit-proposal' AND created_at::date = current_date` to baseline daily usage. Counts toward 7-day M2 trigger.

## Files changed this session

```
skills/coordination/__init__.py     [new, on feature/coordination-layer]
skills/coordination/cli.py          [new, on feature/coordination-layer]
skills/coordination/proposal.py     [new, on feature/echo-m1]
tests/test_agent_collision.py       [new, on feature/coordination-layer]
.claude/commands/propose.md         [new, on feature/echo-m1]
.claude/commands/ack.md             [new, on feature/echo-m1]
.claude/commands/reject.md          [new, on feature/echo-m1]
.claude/commands/list-proposals.md  [new, on feature/echo-m1]
.claude/hooks/echo-nag.py           [new, on feature/echo-m1]
.claude/settings.json               [modified - hooks.Stop wired]
CLAUDE.md                           [modified - mandatory /propose rule]
docs/roadmap/echo.md                [new]
docs/roadmap/README.md              [modified - codename registry]
docs/roadmap/atlas.md               [modified - re-opened descoped row]
deploy.sh                           [modified - mkdir-mutex]
skills/vercel-launch/scripts/launch.sh  [modified - per-app mkdir-mutex]
signal_works/morning_runner.py      [modified - lock wrap]
signal_works/outreach_runner.py     [modified - lock wrap]
```

Memory:
```
~/.claude/.../memory/feedback_now_means_proactive_not_broken.md  [new]
~/.claude/.../memory/feedback_mkdir_mutex_for_portable_bash.md   [new]
~/.claude/.../memory/feedback_worktree_for_session_isolation.md  [new]
~/.claude/.../memory/project_async_partnership_substrate.md     [new, then updated with M1 SHIPPED]
~/.claude/.../memory/reference_echo_substrate.md                 [new]
~/.claude/.../memory/MEMORY.md                                    [updated - 4 new pointers]
```
