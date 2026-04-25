---
name: roadmap
description: Manage living roadmaps for multi-session projects in docs/roadmap/. Use when user says "roadmap", "roadmaps", "list roadmaps", "show me the roadmap", "what's next on <codename>", "where are we on <codename>", "create a roadmap", "new roadmap", "log session", or starts/ends a session that touched a roadmapped project. Roadmaps live at d:/Ai_Sandbox/agentsHQ/docs/roadmap/. Each roadmap has a one-or-two-word codename (e.g. atlas, harvest). Read at session start, update at session end. Replaces orphan handoff docs for any project that spans multiple sessions.
---

# Roadmap Skill

Living roadmaps for multi-session projects. Small, focused, no planning logic. Per-milestone planning happens via `superpowers:brainstorming` and `superpowers:writing-plans`.

## Where roadmaps live

```
d:/Ai_Sandbox/agentsHQ/docs/roadmap/
├── README.md          (codename registry + system rules)
├── <codename>.md      (one file per project, e.g. atlas.md, harvest.md)
└── future-enhancements.md  (legacy backlog, not a roadmap)
```

Roadmaps are git-tracked. They sync to VPS via `git pull` like all other code. Crews on VPS do NOT read roadmaps. Roadmaps are planning artifacts for the human plus planning agent.

## Codename rules

- One word (preferred) or two words (max), lowercase, hyphenated if two
- Memorable not descriptive. `atlas` not `autonomy-layer`. `harvest` not `revenue-pipeline`.
- No reuse ever, even after a project ships
- Filename = `<codename>.md` (no `-roadmap` suffix; folder already says roadmap)
- Branches use the codename: `feat/<codename>-<milestone>` like `feat/atlas-m1-buttons`

## Header schema (every roadmap has this at top)

```markdown
# <Codename Title-Cased>: <one-line description>

**Codename:** <codename>
**Status:** active | shipped | archived
**Lifespan:** 1 day | 1 week | 1 month | open-ended
**Started:** YYYY-MM-DD
**Owner:** <name>
**One-line:** <what this project is in one sentence>
```

## Body sections (in order)

1. **Done Definition.** Locked goalpost. Changes only with explicit re-scoping.
2. **Status Snapshot.** What's live today. Updated every session.
3. **Milestones.** M1..Mn with status (queued / in-progress / shipped / blocked / descoped), trigger gates, blockers, ETA.
4. **Descoped Items.** Explicit no-builds with reason. Prevents relitigating.
5. **Cross-References.** Memory entries, specs, modules, related skills.
6. **Session Log.** Append-only journal. Each entry: date, what changed, what's next.

## Commands

The skill responds to these intents. Match the user's phrasing to the closest one.

### `roadmap list` (default: active only)

When user says: "list roadmaps", "show me the roadmaps", "what roadmaps do we have", "active roadmaps"

Action:
1. Read `docs/roadmap/README.md` registry section
2. Read header of every `*.md` file in `docs/roadmap/` except README and `future-enhancements.md`
3. Filter: status=active
4. Return a table: codename | one-line | started | lifespan | next milestone

### `roadmap list all`

When user says: "list all roadmaps", "all roadmaps", "every roadmap"

Action: same as above but include status=shipped and status=archived. Group by status.

### `roadmap show <codename>`

When user says: "show me atlas", "show me the atlas roadmap", "where are we on harvest", "atlas status"

Action: read `docs/roadmap/<codename>.md` and return it. If file missing, error with available codenames.

### `roadmap next <codename>`

When user says: "what's next on atlas", "what should I build next on atlas", "next milestone for atlas"

Action: read `docs/roadmap/<codename>.md`, find the first milestone with status `IN PROGRESS` (return that), else first with status `QUEUED` and no unmet blockers (return that), else surface that everything queued is blocked and explain why.

### `roadmap log <codename>`

When user says: "log session for atlas", "update atlas", "session done for atlas", "close session"

Action:
1. Read `docs/roadmap/<codename>.md`
2. Append a session-log entry: `### YYYY-MM-DD: <one-line summary>` followed by what changed and what's next
3. Update milestone statuses if any changed during the session
4. Save the file

### `roadmap new <codename>`

When user says: "new roadmap atlas", "create a roadmap called atlas", "start a new roadmap for X"

Action:
1. Validate codename: one or two words, lowercase, hyphenated, ≤20 chars total
2. Check registry in `README.md`. Error if codename already used (active, shipped, OR archived)
3. Ask user for: one-line description, lifespan, owner, done definition
4. Scaffold `docs/roadmap/<codename>.md` from the template (see Body sections above)
5. Add entry to registry table in `README.md`
6. Commit message suggestion: `roadmap: scaffold <codename>`

### `roadmap archive <codename>`

When user says: "archive atlas", "atlas is done", "ship atlas"

Action: change Status header to `shipped` (if all milestones complete) or `archived` (if abandoned). Update registry in README. File stays in place. Never delete.

## Session-start protocol

Every session that opens with roadmap-related work:

1. Read `docs/roadmap/README.md` (small, fast)
2. Determine which roadmap is in scope (from user's first message or recent session-log entries)
3. Read the active roadmap's session-log section first (latest entry tells you state)
4. Read the milestone block for whatever's next
5. Confirm with user that the next milestone is still the right next move BEFORE writing code

## Session-end protocol

Every session that touched a roadmapped project:

1. Run `roadmap log <codename>` (append session-log entry, update milestone statuses)
2. Commit the roadmap update with the session's other commits
3. Push (per agentsHQ session-end rule)

## What this skill does NOT do

- **Plan milestones.** Use `superpowers:brainstorming` then `superpowers:writing-plans` per milestone.
- **Track in-session todos.** Use `TodoWrite`.
- **Replace memory.** Memory captures *why* and *how to apply*. Roadmaps capture *what* and *when*.
- **Sync to VPS specially.** Git already does that on `git pull`.
- **Read by crews.** Crews on VPS run logic, not planning docs.

## Hard rules

- Codename comes first. No file gets created without one.
- Roadmaps are git-tracked. They commit with code changes.
- Session-log is append-only. Never edit past entries; correct via a new entry.
- Status changes (queued → in-progress → shipped) happen in the milestone block, not the log.
- Done Definition is locked. Re-scoping requires an explicit re-scope entry in the session log.
- One project, one roadmap. Don't fragment a project across multiple files.
