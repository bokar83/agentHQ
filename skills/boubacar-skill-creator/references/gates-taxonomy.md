# Gates Taxonomy

Canonical checkpoint types for any skill that spawns subagents, runs review loops, or has human-approval pauses. Name every checkpoint by type. Answer three questions per gate. No "what do we do now?" at runtime.

Adapted from GSD project (MIT © 2025 Lex Christopherson, gsd-build/get-shit-done). First absorbed via NousResearch/hermes-agent (MIT). agentsHQ adaptation: 2026-05-03.

---

## The Four Gate Types

### 1. Pre-flight

**Purpose:** Validate preconditions before starting. No partial work created.

**Behavior:** Block entry if unmet. Bail before anything changes.

**Recovery:** Fix precondition, retry.

**Examples:**
- Plan file exists before subagent starts writing code
- Required env vars set before API calls
- Tests pass before commit

---

### 2. Revision

**Purpose:** Evaluate output quality, route back to producer if insufficient.

**Behavior:** Loop with specific feedback. Bounded by iteration cap (default: 3). Stall detection: if issue count does not decrease between iterations, escalate immediately  -  do not wait for cap to exhaust.

**Recovery:** Producer addresses feedback, checker re-evaluates. After max iterations: escalate unconditionally.

**Examples:**
- Plan reviewer returns issues → planner revises → re-read (max 3)
- Code reviewer checks must-haves → subagent fixes → re-check
- absorb skill Sankofa shifts placement → proposal revised → re-scored

---

### 3. Escalation

**Purpose:** Surface unresolvable issues to human. Never guess, never pick a default.

**Behavior:** Pause, present options, wait. Workflow resumes on human-chosen path.

**Recovery:** Human picks action, workflow continues.

**Examples:**
- Revision loop exhausted (3 iterations, no convergence)
- Ambiguous requirement with two valid interpretations that change the approach
- Subagent: "plan says X, codebase does Y"  -  human decides which is right
- approval_queue item older than 48h with no clear signal

---

### 4. Abort

**Purpose:** Stop immediately to prevent damage or waste.

**Behavior:** Stop, preserve state (checkpoint current progress), report specific reason.

**Recovery:** Human investigates, fixes, restarts from checkpoint.

**Examples:**
- Context window POOR tier (>70%) mid-execution  -  abort cleanly, don't produce truncated output
- Critical dependency unavailable mid-run (API key revoked, VPS unreachable)
- Safety invariant violated (agent attempted irreversible destructive action outside approved scope)

---

## How to Use in a Skill

Every validation checkpoint in an orchestration skill must answer three questions:

1. **What condition triggers this gate?**
2. **What happens when it fails?** (block / loop back / ask human / abort)
3. **Who resumes, and from where?**

Answer these upfront in the skill's "Checkpoints" section. Never leave them implicit.

---

## Example  -  Review Loop with All Four Gates

```
[Pre-flight]  plan.md exists and non-empty?        → no: bail, ask user to write plan
                ↓ yes
[Execute]     subagent implements task
                ↓
[Revision]    reviewer checks must-haves           → fail: loop back (max 3); stall → escalate
                ↓ pass (or stall → escalate)
[Pre-flight]  tests pass?                          → no: bail, report failures
                ↓ yes
[Commit]
                ↓
(context POOR tier during any step)
[Abort]       "context at 73%, checkpointing"      → stop cleanly, report progress
```

---

## agentsHQ Skills That Need This Most

- `boubacar-skill-creator`  -  orchestration skills it produces should cite this
- `agentshq-absorb`  -  Sankofa loop is a Revision gate (bounded, stall-detect)
- `superpowers:executing-plans`  -  plan execution has implicit checkpoints; name them
- `superpowers:subagent-driven-development`  -  already has 2-stage review; label gates explicitly
- Atlas M5 Chairman Crew  -  approval_queue mutation loop needs bounded Revision + Escalation gates
