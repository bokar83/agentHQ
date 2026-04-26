# agentsHQ: Shared Agent SOP

Applies to every coding-agent session (Claude Code, Codex, any future agent). Agent-specific addenda live in `CLAUDE.md` and `CODEX.md` at the repo root.

## Session Start

1. Read `D:\Ai_Sandbox\agentsHQ\docs\memory\MEMORY.md` and every linked file.
2. Check `docs/roadmap/` for active roadmaps. If any roadmap covers the work being asked about, read that roadmap and the latest session-log entry FIRST. The roadmap's next milestone is the default next move unless explicitly redirected.
3. Check `docs/superpowers/plans/` for a handoff. Legacy: roadmaps supersede handoff docs for any roadmapped project.

## Session End

1. If a roadmap was touched this session, append a session-log entry to that roadmap. Date, what changed, what's next.
2. Update milestone statuses in the roadmap (queued / in-progress / shipped / blocked / descoped).
3. Push (local + VPS, per hard rule below).

## Who Boubacar Is

Diagnostic problem-solver. Eight lenses, equally weighted: Theory of Constraints, Jobs to Be Done, Lean, Behavioral Economics, Systems Thinking, Design Thinking, Org Development, AI Strategy. TOC is one tool, not his identity. Never name a framework in any output Boubacar might show a client (emails, site copy, proposals, posts). Defaulting to TOC costs him clients.

## Hard Rules

- Files live in `D:\Ai_Sandbox\agentsHQ` or `D:\Ai_Sandbox\`. Never C:. *Why: past sessions scattered files on C: and lost them.*
- Never create directories without confirming location.
- End every session with git push (local + VPS).
- No em dashes anywhere. Not `--`, not `—`. Rewrite the sentence. *Why: Boubacar edits every one out by hand when they slip through. A pre-commit hook also blocks them.*
- WebFetch: blanket permission. Never ask before fetching a URL.
- **`orchestrator.py` no longer exists.** Sunset 2026-04-25 in commit `4d1aeb3`. The 2800-line monolith was split into modular files (`engine.py`, `constants.py`, `handlers_chat.py`, `state.py`, `handlers.py`, etc.) and `app.py` is the canonical entrypoint. **Never recreate `orchestrator.py`.** All imports use the modular stack. See `project_orchestrator_sunset.md` in memory for the full import map. *Why: agents kept "fixing" missing-orchestrator.py errors by recreating the file, undoing the refactor.*

## Coding Principles (Karpathy)

1. **Think before coding**: state assumptions; ask when ambiguous.
2. **Simplicity first**: minimum code that solves the problem.
3. **Surgical changes**: touch only what must change.
4. **Goal-driven execution**: verifiable success criteria, checkpoints, loop back.

## Automatic Skill Triggers

Fire without being asked. Check each trigger on every user message.

| # | Trigger | Action |
| --- | --- | --- |
| 1 | Website / UI / HTML-CSS output requested | `superpowers:brainstorming` first, localhost preview with 3 options, user picks ONE before any code |
| 2 | After #1 pick, or any site edit | `frontend-design` skill to load design standards before writing code |
| 3 | 2+ independent tasks in one message | `superpowers:dispatching-parallel-agents` |
| 4 | Bug, error, failing test, unexpected behavior | `superpowers:systematic-debugging`. Four phases: reproduce, isolate root cause, form hypothesis, fix. No edits before root cause is confirmed. |
| 5 | Before any deploy, docker cp, git push, or SCP | `superpowers:verification-before-completion`. No skipping, even if the fix looks trivial. |
| 6 | Multi-file change or new orchestrator feature | `superpowers:brainstorming`. No code until the plan is written and confirmed. |
| 7 | New skill being created or substantially rewritten | `superpowers:writing-skills` first. |

Full workflow for new features: brainstorming then writing-plans then executing-plans.

Non-Claude agents (Codex, etc): translate each skill trigger to the equivalent discipline (plan first, confirm before multi-file edits, verify before deploy, root-cause before fix).

## Skill SOPs Live With the Skills

Each skill keeps its own rules in `skills/<name>/SKILL.md`. Read the skill file when you touch that skill. This SOP does not repeat skill-specific detail.
