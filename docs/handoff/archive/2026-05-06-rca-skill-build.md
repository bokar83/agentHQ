# Session Handoff - /rca Skill Build - 2026-05-06

## TL;DR

Built and shipped the `/rca` global skill from scratch. Pulled full RCA history (5 incidents, 3 handoff docs, 6 memory files) to extract the real pattern. Ran Sankofa + Karpathy before writing a single line. Both councils caught real flaws. Wrote the skill directly (Codex sandbox blocked writes). Synced to VPS. Skill is live and in the Claude Code skills list.

## What was built / changed

- `~/.claude/skills/rca/SKILL.md` — new global skill, 173 lines, 6 phases with hard exit gates
- `/root/.claude/skills/rca/SKILL.md` — VPS copy, synced via scp
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/reference_rca_skill.md` — new reference memory
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md` — added /rca pointer
- `~/.claude/skills/boubacar-skill-creator/SKILL.md` — added Codex sandbox fallback note to Step 4

## Decisions made

- **Skill is global, not project-scoped.** Lives at `~/.claude/skills/rca/` not in agentsHQ repo. Available every session, every project.
- **No sub-skill invocations inside /rca.** Karpathy P2 WARN: `superpowers:systematic-debugging` inside Phase 2 = skill-within-a-skill = two conflicting phase structures. Replaced with 3 direct actions (read file, grep, one targeted diagnostic).
- **Agent proposes success criterion, user confirms.** Karpathy P1 WARN: asking user to write criterion defeats the skill. Agent derives it from subsystem + symptom.
- **2-attempt hard cap before mandatory Codex dispatch.** Karpathy P4 FAIL: unbounded loop = hope-driven not goal-driven. Every gate RCA had 6 failed attempts before Codex was called. Cap enforces the lesson.
- **Phase exit gates on every phase.** Sankofa: agent cannot proceed without writing required output. Root cause in writing. Criterion confirmed. Criterion met. These are the three gates that every past RCA skipped.
- **VPS sync command lives inside the skill file.** Sankofa: otherwise VPS copy silently goes stale.
- **Never dispatch Codex to write skill files.** Codex sandbox = read-only. Skill files use Write tool directly. Added to boubacar-skill-creator Step 4.

## What is NOT done (explicit)

- No repo commit. The /rca skill is global, not in agentsHQ. Nothing belongs in the repo from this session.
- No TDD baseline test run (skill-writing TDD process). Session was focused on shipping the working skill from proven real-world pattern, not from a synthetic subagent test. The 5 real RCAs ARE the baseline.

## Open questions

- Should the triage table expand? Currently 6 subsystems. Add new rows whenever a new subsystem RCA is discovered (self-improvement note is already in the skill).
- VPS Codex agents: do they load from `/root/.claude/skills/`? If so they get /rca automatically. If not, a separate instruction in AGENTS.md may be needed.

## Next session must start here

1. No carry-over from this session.
2. Check `/nsync` status — 1 modified file was flagged at session start.
3. Pick up from active roadmap: `docs/roadmap/atlas.md` or `docs/roadmap/studio.md` per priority.
4. First /rca invocation: use it on a real incident and note any gaps in the triage table.

## Files changed this session

```
~/.claude/skills/rca/SKILL.md                                       -- CREATED (global skill)
~/.claude/skills/boubacar-skill-creator/SKILL.md                    -- updated (Codex sandbox note)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/reference_rca_skill.md  -- CREATED
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md          -- updated (pointer added)
/root/.claude/skills/rca/SKILL.md                                   -- CREATED (VPS copy)
docs/handoff/2026-05-06-rca-skill-build.md                          -- this file
```
