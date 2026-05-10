---
# Session Handoff - Gate Conflict RCA + Coordination Hardening - 2026-05-10

## TL;DR

Diagnosed and fixed the recurring "stepping on toes" multi-agent git conflict. Root cause was NOT a missing pre-push hook (Council killed that proposal). Root cause: agent sessions dying without calling `complete()` left phantom `running` leases in Postgres, blocking any agent trying to claim the same files. Fixed with a lease reaper in gate_poll.py, AGENT_SOP rule, and claim() docstring. Also hardened pre-commit filter-repo guard to distinguish invocations from prose, synced tracked hook source with installed hook, and added Sankofa/Council escalation trigger to the sankofa skill.

## What was built / changed

- `scripts/gate_poll.py` -- `_reap_stale_leases()` added, uses `docker exec orc-postgres psql` (no host psycopg2). Fires every 5 min.
- `skills/coordination/__init__.py` -- `claim()` docstring updated with mandatory try/finally pattern + crash explanation
- `docs/AGENT_SOP.md` -- new hard rule: every claim() must wrap work in try/finally: complete()
- `.git/hooks/pre-commit` + `scripts/pre-commit-hook.sh` -- filter-repo guard upgraded (invocation vs prose, self-exclusion, whitelist for historical doc references). Tracked source synced with installed hook (was missing checks 7+8).
- `~/.claude/skills/sankofa/SKILL.md` -- COUNCIL ESCALATION CHECK block added (pre-run 4-signal scoring table, post-run tension flag)
- `docs/roadmap/atlas.md` -- session log + cheat block updated
- `docs/roadmap/compass.md` -- session log appended
- Memory: `feedback_coordination_claim_try_finally.md`, `feedback_proactive_skill_system_proposals.md`

## Decisions made

- **Council > Sankofa for high-stakes architectural decisions.** When irreversibility + insider fog + stakes asymmetry all fire (2+/4 signals), stop Sankofa and run Council. Pre-push hook was exactly this case.
- **Lease reaper = safety net, not contract.** The contract is try/finally in caller code. Reaper catches crashes. Both layers needed.
- **gate_poll.py must use docker exec for Postgres operations.** Host has no psycopg2. Pattern confirmed: `docker exec orc-postgres psql -U postgres -d postgres -t -c "<sql>"`.
- **Pre-commit hook source of truth = `scripts/pre-commit-hook.sh`.** Installed hook at `.git/hooks/pre-commit` must stay in sync. Any hook edit = update both.
- **AUTO_SEND_SW stays FALSE** until Boubacar explicitly flips it. Not an infra decision.

## What is NOT done (explicit)

- sw_email_log verification query -- Sunday, no emails go out, not urgent
- Echo M1 (slash commands) -- READY, no blockers, next feature session
- Atlas M18 HALO (tracing.py) -- target 2026-05-18, next feature session
- Atlas M9d-A (Weekly Synthesis crew) -- target 2026-05-18

## Open questions

- None blocking. Filter-repo guard whitelist may need further expansion if other historical doc references surface.

## Next session must start here

1. Read `docs/roadmap/atlas.md` cheat block -- Gate is clean, lease reaper live
2. Pick next feature: Echo M1 (fastest, READY) or Atlas M18 HALO (deadline 2026-05-18)
3. Verify gate_poll lease reaper firing: `ssh root@72.60.209.109 "tail -20 /tmp/gate_poll.log"`

## Files changed this session

- `scripts/gate_poll.py`
- `scripts/pre-commit-hook.sh`
- `.git/hooks/pre-commit` (not tracked, synced from above)
- `skills/coordination/__init__.py`
- `docs/AGENT_SOP.md`
- `~/.claude/skills/sankofa/SKILL.md`
- `docs/roadmap/atlas.md`
- `docs/roadmap/compass.md`
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_coordination_claim_try_finally.md` (new)
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_proactive_skill_system_proposals.md` (new)
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md` (updated index)
