# Session Handoff — Compass C8 + C9 shipped — 2026-05-12

## TL;DR

Session arc: agentmemory absorb evaluation → discovered MEMORY.md cap pressure → shipped C8 (hygiene prune, 217→174 lines) + C9 (autonomous monthly hygiene agent on Windows Task Scheduler). 2 new hard rules in AGENT_SOP.md. agentmemory absorb = ARCHIVE-AND-NOTE. Branch `compass/c8-c9-memory-hygiene` pushed with [READY] at HEAD. Gate handles merge.

## What was built / changed

**Memory infrastructure (LOCAL, not in repo):**

- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md` — 217 → 174 lines (20% cut, 6-line headroom under 180 cap)
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY_ARCHIVE.md` — +32 lines, 24 entries archived
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.pre-c8-2026-05-11.md` — backup of pre-prune state (per never-delete rule)
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/project_compass_c8_memory_hygiene.md` — SHIPPED record
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_run_it_dont_propose_it.md` — new rule
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_autonomous_jobs_local_when_data_local.md` — new rule

**Repo files:**

- `docs/AGENT_SOP.md` — 3 new hard rules: Memory→Skill promotion (line 108), Run-it-don't-propose-it (line 110), Autonomous-jobs-local (line 112)
- `docs/reviews/absorb-log.md` — rohitg00/agentmemory ARCHIVE-AND-NOTE entry
- `docs/roadmap/compass.md` — C8 SHIPPED milestone, C9 SHIPPED milestone, session log 2026-05-11 + 2026-05-12, status snapshot bumped to 2026-05-12
- `scripts/memory_hygiene_agent.py` — ~200-line autonomous agent (new): line count + promotion scan + cold-entry scan + Telegram exception alert. Existence-filter fix landed in 2nd commit (typo'd handoff paths inflated 17 candidates → 3 real)
- `scripts/memory_hygiene_schedule.md` — Task Scheduler install + WSL cron fallback docs

**System changes:**

- Windows Task Scheduler: task `agentsHQ_memory_hygiene` registered via `schtasks.exe /Create /TN ... /SC MONTHLY /D 1 /ST 06:00`. Next run: **2026-06-01 06:00 MT**.
- VPS Postgres `memory` table: 5 AgentLesson + 1 ProjectState + 1 SessionLog rows written via `docker exec orc-crewai python ...` (DNS doesn't resolve from Windows, run via SSH+container)

## Decisions made

1. **agentmemory (rohitg00/agentmemory v0.9.9) = ARCHIVE-AND-NOTE.** Distinct gap from claude-mem (web UI) and context-mode (within-session output compression) — genuine cross-session auto-capture + hybrid search. BUT collides with curated MEMORY.md philosophy (verified-stats-only, 1stGen, sabbath, send rules); auto-capture pollutes signal. Privacy filter trust unknown on cw OAuth/Apollo keys. Heavy install (iii-engine binary + npm pkg + MCP shim + 12 hooks + ports 3111/3113). Pre-1.0 — #149 Stop-hook recursion still warned in docs.
   **Reopen conditions:** v1.0 + sandbox refactor + INJECT_CONTEXT default-on + #149 resolved, OR MEMORY.md hits >250 lines with critical rules dropping after C8 hygiene fails.

2. **C9 = local Windows Task Scheduler, NOT VPS cron.** Memory dir is local-only by design. Don't sync data to a different host just to run cron there. New AGENT_SOP rule codified.

3. **Promotion rule shape:** verb-protocol ("BEFORE X, do Y, then Z") fired 3+ times = skill candidate. Pure-fact rules ("Guinea not Senegal") stay in memory.

4. **Existence-filter on promotion candidates:** citation-count signal must validate target file exists. 14 typo'd paths inflated initial signal from 3 to 17 candidates.

5. **Karpathy WARN on principle 2 (Simplicity First):** memory_hygiene_agent.py is 200 lines, could be 50. Defer trim until 2026-06-01 first production fire reveals real signal value.

## What is NOT done (explicit)

- **Postgres memory writes from Windows: BLOCKED.** `agentshq-postgres-1` is container-network DNS. Must SSH+docker exec to write. Tab-shutdown skill says "If VPS Postgres unreachable, skip and note." Worked around via SSH this session, but Step 2b workflow is friction for future tab-shutdowns.
- **C9 first production fire = 2026-06-01.** Smoke-tested today, not yet observed running on the schedule itself. If `python.exe` PATH or `WorkingDirectory` is wrong in the registered task, won't catch until 2026-06-01. Mitigation: I would run `Start-ScheduledTask` to manually trigger before walking away, BUT it would send a real Telegram alert (WARN tier, 3 candidates) which is noise. Decision: accept 2026-06-01 as first real fire.
- **17 promotion candidates from first smoke-test were all noise** (typo'd paths or never-created files OR rules already in MEMORY.md hot zone). After filter: 3 real candidates, all already in hot zone. Lane B "promote 2-3 rules" = no-op tonight. Promotion rule + hot-zone curation working as designed.
- **VPS sync verification (Step 3c):** branch `compass/c8-c9-memory-hygiene` not on VPS until gate merges to main. Verification deferred to next session OR will happen automatically via gate.

## Open questions

- Will C9 fire correctly on 2026-06-01? Could break silently if `python.exe` not found, `.env` not readable in scheduled context, OR Telegram creds env vars wrong.
- 17 → 3 candidate compression from existence filter — but is "rule cited in handoff that doesn't exist as memory file" itself a signal we should track? Could surface "lessons mentioned but never codified." Deferred.
- Concurrent-session commits to same branch (`bc8797b`, `489402c`, `78723d0` from another session): not blocking but means branch contains work beyond C8/C9 scope. Gate review will see all of it.

## Next session must start here

1. **Check gate merge status.** `git log origin/main --oneline -5` — has `compass/c8-c9-memory-hygiene` merged? If yes, pull. If no after 30+ min, check `gate_agent` logs on VPS.
2. **If merged: pull main + verify VPS got it.** `ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && ls scripts/memory_hygiene_agent.py"`. Script doesn't run on VPS (local-only by design) but needs to exist there for repo parity.
3. **Verify Task Scheduler still registered.** `schtasks.exe /Query /TN "agentsHQ_memory_hygiene" /FO LIST` — task should show "Status: Ready" and next-run = 2026-06-01.
4. **Monitor 2026-06-01 first production fire.** Memory hygiene agent should write digest to `agent_outputs/memory_hygiene/memory_hygiene_2026-06-01.md` AND send Telegram if any exception triggers.
5. **Address concurrent session's atlas-second-brain Phase A spec.** Files `docs/roadmap/atlas-second-brain-phase-a.md` (untracked) + commits `489402c`/`bc8797b` on branch came from concurrent session — review what got shipped there, possibly handoff doc reference.

## Files changed this session

**Local (memory dir):**
- `MEMORY.md` (rewritten)
- `MEMORY_ARCHIVE.md` (+24 entries appended)
- `MEMORY.pre-c8-2026-05-11.md` (new, backup)
- `project_compass_c8_memory_hygiene.md` (new)
- `feedback_run_it_dont_propose_it.md` (new)
- `feedback_autonomous_jobs_local_when_data_local.md` (new)

**Repo:**
- `docs/AGENT_SOP.md` (modified, 3 new hard rules at lines 108-112)
- `docs/reviews/absorb-log.md` (modified, +1 entry)
- `docs/roadmap/compass.md` (modified, C8/C9 milestones + session log + status snapshot)
- `scripts/memory_hygiene_agent.py` (new, ~200 lines)
- `scripts/memory_hygiene_schedule.md` (new)

**System:**
- Windows Task Scheduler: `agentsHQ_memory_hygiene` task registered
- VPS Postgres `memory` table: 7 rows written (5 lessons + 1 project_state + 1 session_log)
- Branch: `compass/c8-c9-memory-hygiene` pushed to origin, [READY] at HEAD

## Cross-references

- Roadmap: `docs/roadmap/compass.md` C8/C9
- Absorb log: `docs/reviews/absorb-log.md` 2026-05-11 entry for rohitg00/agentmemory
- New hard rules: `docs/AGENT_SOP.md` lines 108-112
- Memory: `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/project_compass_c8_memory_hygiene.md`
