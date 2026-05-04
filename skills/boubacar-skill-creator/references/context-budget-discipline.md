# Context Budget Discipline

Rules for keeping orchestrator context lean when spawning subagents or reading large artifacts. Apply whenever running multi-step agent loops: plan execution, subagent orchestration, review pipelines, multi-file refactors.

Adapted from GSD project (MIT © 2025 Lex Christopherson, gsd-build/get-shit-done). First absorbed via NousResearch/hermes-agent (MIT). agentsHQ adaptation: 2026-05-03.

---

## Universal Rules

1. **Never read agent definition files** - `Agent` tool auto-loads them. Reading them too doubles cost.
2. **Never inline large files into subagent prompts** - tell the subagent to read from disk. It gets full content; orchestrator stays lean.
3. **Read depth scales with context window** - see table below.
4. **Delegate heavy work to subagents** - orchestrator routes, does not execute.
5. **Proactively warn Boubacar** when context is getting heavy - "Context heavy, consider checkpointing before we continue."

---

## Read Depth by Context Window

Assume smaller window if unknown. Err toward leanness.

| Context window | Subagent output | Summary files | Verification files | Other phase plans |
|---|---|---|---|---|
| < 500k (200k Sonnet) | Frontmatter only | Frontmatter only | Frontmatter only | Current phase only |
| >= 500k (1M models) | Full body OK | Full body OK | Full body OK | Current phase only |

"Frontmatter only" = read enough to see final status/verdict/conclusion. If subagent wrote 3000-line debug log, read its summary section, not the log.

---

## Four-Tier Degradation Model

Monitor context usage. Shift behavior before hitting the wall, not after.

| Tier | Usage | Behavior |
|---|---|---|
| **PEAK** | 0–30% | Full ops. Read bodies, spawn parallel agents, inline results freely. |
| **GOOD** | 30–50% | Normal ops. Prefer frontmatter reads. Delegate aggressively. |
| **DEGRADING** | 50–70% | Economize. Frontmatter-only reads, minimal inlining. **Warn Boubacar.** |
| **POOR** | 70%+ | Emergency. **Checkpoint immediately.** No new reads unless critical. Finish current task, stop cleanly. |

---

## Early Warning Signs (Before Thresholds Fire)

Quality degrades gradually before hard limits hit. Watch for:

- **Silent partial completion** - subagent claims done but implementation is incomplete. Self-checks catch file existence, not semantic completeness. Always verify against must-haves, not just "did a file appear?"
- **Increasing vagueness** - agent uses "appropriate handling" or "standard patterns" instead of specific code or decisions. Context pressure showing up before budget warnings fire.
- **Skipped protocol steps** - agent omits steps it would normally follow. If success criteria has 8 items and report covers 5, suspect context pressure, not intentional skip.

When these appear: checkpoint work, either reset context or hand off to fresh subagent.

---

## agentsHQ Application Points

**VPS orchestrator (orc-crewai):** Atlas publish loop runs multi-step pipelines on VPS. Context overruns cause silent truncation mid-publish. Apply four-tier model in orchestrator loop.

**`superpowers:executing-plans`:** Spawns multiple subagents per plan. Apply read-depth table - never inline subagent full output when at GOOD or lower tier.

**`superpowers:subagent-driven-development`:** Two-stage review pipeline. Reviewer subagent output = frontmatter-only read at GOOD tier.

**`agentshq-absorb`:** Deep artifact reads can burn 30–40% context. Run at PEAK only. If GOOD or lower at absorb time, warn before starting.

**Atlas M5 Chairman Crew:** Weekly crew reading approval_queue + task_outcomes. Largest context risk in Atlas. Apply aggressive delegation - Chairman reads summaries, not full outcome records.
