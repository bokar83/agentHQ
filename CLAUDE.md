# agentsHQ: Claude Code SOP

**Read `docs/AGENT_SOP.md` first, every session. No exceptions.** All shared rules, session-start steps, hard rules, coding principles, and skill triggers live there. This file exists only for Claude-Code-specific additions.

## Active Roadmaps

Multi-session projects are tracked in `docs/roadmap/<codename>.md`. The `roadmap` skill manages them (list / show / next / log / new / archive). Read at session start, log at session end.

| Codename | One-line |
|---|---|
| `atlas` | agentsHQ true agentic work (autonomy layer) |
| `echo` | async partnership substrate (agent proposes commits, human acks async) |
| `harvest` | Catalyst Works revenue pipeline (stub) |

Full registry: `docs/roadmap/README.md`.

## Claude-Code-Only

### Echo M1: async commit proposals via /propose (MANDATORY)

**HARD RULE.** After every coherent work unit, you MUST call `/propose`. The default mode of working in this repo is async: agent proposes, human acks at his cadence, neither blocks on the other. Pausing the user to commit is the failure mode this rule prevents.

A "coherent work unit" is any of:

- A logical task is complete (one feature, one bugfix, one refactor, one set of related edits).
- Tests are green or no test was run for this unit (don't propose with red tests).
- About to switch to a different task or a different file area.
- Multiple recent changes now read as one cohesive narrative in the diff.

**Workflow after every coherent unit:**

1. Call `/propose` (with optional context message).
2. State "Proposal queued. Continuing." in chat.
3. Move immediately to the next task. Do NOT wait for the user.

**The only allowed exemptions** (be honest with yourself, do not over-apply):

- **User opted out for this session.** They said "do not propose, I'm reviewing manually." Honor for the rest of the session.
- **Tests are red.** Finish the work that turns them green first; the propose at the end of THAT covers both.
- **Trivial one-liner.** A typo fix that the next coherent unit will absorb. If you're tempted to claim this exemption more than once per hour, you're hiding from the rule. Just propose.
- **Mid-refactor with no clean state.** Continue until clean. Then propose.

**The Stop-hook nag will catch you.** A repository-level Stop hook fires at the end of every Claude Code turn. If the turn ended with uncommitted changes AND no proposal was filed AND the changes are non-trivial, you (and the user) will see a Telegram nag. The nag is not punitive; it's a feedback signal that the convention drifted. Aim for zero nag fires per session.

**One propose per coherent unit, not per file.** Don't propose six times for six files in one logical unit. Propose once with all six files at the unit boundary.
