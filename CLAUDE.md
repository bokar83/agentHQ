# agentsHQ — Claude Code SOP

## Before Starting Any Work

Read the memory files first:

```
D:\Ai_Sandbox\agentsHQ\docs\memory\
```

Start with `MEMORY.md` (index), then read each linked file. This gives you full project context, known bugs, pending priorities, and working preferences before touching anything.

## Who Boubacar Is — Non-Negotiable Context

Boubacar Barry is a **diagnostic problem-solver**. He uses multiple lenses to find the right problem and remove it. He is NOT a TOC consultant, a constraints expert, or primarily focused on bottleneck analysis.

Theory of Constraints is one of eight lenses he uses -- all equally weighted:

1. Theory of Constraints
2. Jobs to Be Done
3. Lean / Waste Elimination
4. Behavioral Economics
5. Systems Thinking
6. Design Thinking
7. Organizational Development
8. AI Strategy

**Never** default to TOC or constraints when describing his work, suggesting resources, or framing ideas. The diagnostic determines which lens applies -- it is never predetermined. His brand is the outcome, not any single framework. No framework names ever appear in client-facing language.

Defaulting to TOC misrepresents him and costs him clients.

## Key Rules

- All files go in `D:\Ai_Sandbox\agentsHQ` or `D:\Ai_Sandbox\` — never on C: drive
- Never create directories without confirming location first
- End every session with git push on both local AND VPS (see session commands in memory)
- Use the superpowers skills workflow (brainstorming → writing-plans → executing-plans) before building any new agent or feature

## Superpowers Skill Triggers — Automatic, No Prompt Needed

These fire without being asked. Apply them every time the condition is met.

### Visual Companion (localhost brainstorming)
**Trigger**: Any task that produces a website, UI, or visual artifact — catalystworks-site, Baobab app, any HTML/CSS output.
**Action**: Invoke `superpowers:brainstorming` before writing any code. Spin up the localhost visual companion showing 3 design options with pros/cons. Do not write a single line of UI code until the user picks an option.

### Parallel Agent Dispatching
**Trigger**: User message contains 2 or more independent tasks (e.g. "update outreach copy + scan Drive + update Notion").
**Action**: Invoke `superpowers:dispatching-parallel-agents`. Do not execute sequentially. Dispatch sub-agents in parallel for each independent task.

### Systematic Debugging
**Trigger**: Any bug, error, failing test, or unexpected behavior reported by the user.
**Action**: Invoke `superpowers:systematic-debugging` before touching any code. Four phases: reproduce, isolate root cause, form hypothesis, fix. No edits before root cause is confirmed.

### Verification Before Deploy
**Trigger**: Any task that ends with a deploy, docker cp, git push, or SCP to VPS.
**Action**: Invoke `superpowers:verification-before-completion` before executing the deploy step. Do not skip this even if the fix looks trivial.

### Brainstorming Gate for Multi-File Changes
**Trigger**: Any change that touches more than one file, or adds new functionality to the orchestrator.
**Action**: Invoke `superpowers:brainstorming` before writing any code. No inline execution until the plan is written and confirmed.

### Writing Skills for New Skill Builds
**Trigger**: Any session where a new Claude Code skill is being created or substantially rewritten.
**Action**: Invoke `superpowers:writing-skills` first. Use its test-driven principles to structure the skill before writing the SKILL.md.

## Writing Style — Hard Rules

- **No em dashes. Ever.** Not `--`, not `—`. Rewrite the sentence instead.
- This applies to all output: code comments, markdown, responses, file content, everything.

## Coding Principles (Karpathy)

These four principles apply to every coding action in every session, regardless of task type or target environment.

**Think Before Coding**: State assumptions explicitly before writing anything. If a requirement is ambiguous, present the two possible interpretations and ask. Clarifying questions come before mistakes, not after.

**Simplicity First**: Write the minimum code that solves the problem. Nothing speculative. No unrequested features, no premature abstractions, no speculative error handling. If a senior engineer would call it overcomplicated, it is overcomplicated.

**Surgical Changes**: Touch only what must be touched. Preserve existing style and conventions. Clean up only your own mess. Do not refactor pre-existing code, rename unrelated things, or remove dead code that predates the current task.

**Goal-Driven Execution**: Convert every task into verifiable success criteria before starting. Use explicit checkpoints throughout. Loop back to verify each checkpoint before moving to the next step.

## Hyperframes Video Production Skill

- Skill location: skills/hyperframes/
- Soul file: skills/hyperframes/SKILL.md
- Implementation: skills/hyperframes/skill.py
- Knowledge doc: docs/agentsHQ-hyperframes-knowledge-update.md
- Phase gate: Phase 0 = knowledge only. Phase 1 = active.
- To activate: set PHASE_GATE = "phase_1" in skill.py after first revenue confirmed.
- Relationship to website_build: sibling skill. Both write HTML. Different output
  contexts. Do not merge. See SKILL.md for full distinction.
- Prompt guide: [hyperframes.heygen.com/guides/prompting](https://hyperframes.heygen.com/guides/prompting)

## Permissions

- **WebFetch**: blanket permission to fetch any legal website during any session, no confirmation needed. Never ask before fetching a URL.

## Project Quick Reference

- VPS: `72.60.209.109` — orchestrator runs on port 8000
- Telegram bot: `@agentsHQ4Bou_bot`
- GitHub: `https://github.com/bokar83/agentHQ`
- n8n: `https://n8n.srv1040886.hstgr.cloud`
