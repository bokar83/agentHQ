# Session Handoff — Gate alert spam RCA + fix — 2026-05-11

## TL;DR
Killed a 5+ hour Telegram alert spam loop from gate_poll.py. Root cause: gate_poll scanned 7 branch prefixes while gate_agent scanned only 3 — docs/+chore/ `[READY]` branches got detected + alerted forever but never reviewable. Expanded gate_agent prefix list to match (canonical 7), added gate_poll dedup sentinel as belt-and-suspenders, and resolved a self-caused secondary spam loop from scp-without-commit. 4 branches auto-merged + deleted during verification. 2 new memory rules. VPS at commit `f98a9ba`.

## What was built / changed

**Code:**
- `orchestrator/gate_agent.py:229` — prefix tuple expanded from `(feature/, feat/, fix/)` → `(feature/, feat/, fix/, docs/, chore/, refactor/, test/)`. Single-line change, syntax-clean, matches `gate_poll.py:49` canonical list
- `scripts/gate_poll.py` — added `_load_alerted_state()` / `_save_alerted_state()` helpers + `/tmp/gate_poll_alerted.json` dedup sentinel keyed on `branch:tip_sha`; modified `_ready_branches()` to return `(branch, sha)` tuples; `poll_once()` skips re-alert if sentinel matches current tip. GC: state entries dropped for branches no longer in READY set; full reset on empty queue.

**Memory (flat-file):**
- `feedback_gate_poll_gate_agent_prefix_parity.md` — gate_poll + gate_agent prefix lists MUST match; change both in same commit; canonical = 7 prefixes
- `feedback_never_scp_uncommitted.md` — never scp code to VPS without git commit first; scp reserved for non-code artifacts only

**Memory index:**
- `MEMORY.md` lines 180-181 — two new pointers under `Pipeline State / Gate`

**Roadmaps:**
- `docs/roadmap/echo.md` — appended 2026-05-11 session log entry covering fix + RCA + secondary incident

**Docs:**
- `docs/handoff/2026-05-11-gate-poll-prefix-coverage-rca.md` — full 6-phase RCA writeup

**Commits (chronological, all on main):**
- `666bac0` merge(fix/gate-agent-prefix-coverage): gate auto-merge
- `f98a9ba` docs(echo): log gate prefix-parity fix + scp-without-commit incident
- 4 branches auto-merged during verification: `chore/gitignore-tmp-screenshots` (`822d8ef`), `docs/atlas-session-log-2026-05-08` (`8a0ce5b`), `docs/roadmap-studio-2026-05-11` (`8fde0ff`), `fix/gate-agent-prefix-coverage` itself

## Decisions made

1. **Canonical branch-prefix list = 7:** `(feature/, feat/, fix/, docs/, chore/, refactor/, test/)`. gate_poll and gate_agent MUST agree. Any change to either MUST change both in the same commit.
2. **scp to VPS for code is banned.** Even for verified-working hotfixes. Use git push + VPS pull only. scp only for non-code (sql migrations into orc-postgres, drive uploads, secret rotation).
3. **Pre-populate dedup state at deploy time.** When adding a new sentinel to a recurring cron, populate the state file BEFORE the first tick fires so deploy itself doesn't burst alerts.
4. **Did NOT kill gate_poll.py despite it being redundant.** gate_agent does the real work (detect + review + merge). gate_poll only detects + alerts. Considered removing gate_poll cron entirely but left as-is — dedup sentinel + prefix parity neutralize the spam, and removal felt risky without more observation. Revisit if alert volume becomes a problem again.

## What is NOT done (explicit)

1. **Postgres memory writes failed (non-fatal).** `agentshq-postgres-1` hostname doesn't resolve from Windows host (docker-internal DNS). Tried 4× writes, all failed with `could not translate host name`. Flat-file memory is the fallback per tab-shutdown skill. Next session: verify memory_store config or use VPS exec for memory writes. Known limitation — not a regression.
2. **VPS stash@{0} preserved** ("pre-fix-gate-agent-prefix-coverage-merge: VPS scp dirty state"). Content was identical to merged fix branch (CRLF vs LF only). Can be dropped: `ssh root@72.60.209.109 "cd /root/agentsHQ && git stash drop stash@{0}"`. Left intact for one more session as paranoia hedge.
3. **gate_poll.py cron not removed.** Still runs `*/5 * * * *`. Redundant with gate_agent but neutralized by dedup sentinel. Open question for future: kill it or keep belt-and-suspenders?
4. **Unrelated dirty files on local main:** `M docs/AGENT_SOP.md`, `M docs/reviews/absorb-log.md`, `M docs/roadmap/compass.md`. Not from this session. Not staged. Belong to prior in-flight work.
5. **11 untracked PNG screenshots** at repo root (`audit-*.png`, `gov-*.png`, `lens-*.png`, `signal-final.png`). The merged `chore/gitignore-tmp-screenshots` branch added the gitignore rule — `/nsync` warning should clear next session.

## Open questions

1. Should gate_poll.py be removed entirely now that gate_agent handles detect+act in one pass? Or keep as detect-only safety net with dedup?
2. Why did Postgres memory hostname stop resolving from Windows host? Was it ever working from there, or have all flat-file→postgres writes silently failed across sessions?

## Files changed this session

```
orchestrator/gate_agent.py            (line 229 — prefix tuple)
scripts/gate_poll.py                  (+47 lines — dedup sentinel logic)
docs/handoff/2026-05-11-gate-poll-prefix-coverage-rca.md   (new — RCA writeup)
docs/handoff/2026-05-11-gate-shutdown.md                    (new — this file)
docs/roadmap/echo.md                  (+17 lines — session log)

~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_gate_poll_gate_agent_prefix_parity.md   (new)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_never_scp_uncommitted.md                (new)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md                                        (+2 pointers)
```

## VPS verification at session close

- Local HEAD: `f98a9ba`
- Origin HEAD: `f98a9ba`
- VPS HEAD: `f98a9ba`
- Gate prefix line live: confirmed at `orchestrator/gate_agent.py:229`
- gate_poll status: empty queue, 0 alerts
- gate_agent status: silent (no READY branches outstanding)
