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

### Echo M1: async commit proposals via /propose

When work reaches a coherent stop point, call `/propose` instead of pausing for the user to commit. Triggers:

- A logical unit completed (one feature, one bugfix, one refactor) AND tests are green or N/A.
- Multiple changes touched the same files and the diff now reads as one cohesive narrative.
- About to switch to a different task or a different file area.
- The user said "stop and let me commit." Replace that pattern with `/propose`.

Do NOT block on the user. After `/propose` queues the proposal (Telegram fires), state "Proposal queued. Continuing." and move on. The user `/ack`s on their cadence; the agent never waits for approval to keep working.

Counter-cases (do NOT call `/propose`):

- Working tree is mid-refactor; tests would not pass. Finish the refactor first.
- Single typo fix or one-line tweak; just continue, the next coherent unit will absorb it.
- The user explicitly says "do not propose, I'm reviewing manually." Honor that for the rest of the session.
