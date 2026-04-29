# agentsHQ Roadmaps

This folder is the single source of truth for any multi-session project at agentsHQ.

## How this works

One roadmap per major project. Each roadmap is a living document, not a snapshot.

```text
docs/roadmap/
├── README.md                  (this file)
├── atlas.md                   (autonomy: agentsHQ true agentic work)
├── harvest.md                 (revenue: Catalyst Works pipeline)
└── future-enhancements.md     (backlog of architecturally-sound ideas not yet prioritized)
```

## Anatomy of a roadmap

Every roadmap has these sections in this order:

1. **Done definition.** The locked goalpost. What "complete" means. Changes only with explicit re-scoping.
2. **Status snapshot.** What is live today. Updated every session.
3. **Milestones (M1..Mn).** Ordered list with status, trigger, blockers, ETA.
4. **Descoped items.** Explicit no-builds with reason. Prevents relitigating.
5. **Session log.** Append-only journal. Each entry: date, what changed, what's next. Replaces orphan handoff docs.

## Discipline

- **At session start:** read the active roadmap. Read the latest session log entry. Confirm the next milestone is still the right next milestone.
- **At session end:** update milestone statuses. Append a session log entry. Push.
- **No code on a roadmapped project without first checking the roadmap.** If the next move isn't on the roadmap, add it to the roadmap before building.
- **Trigger gates** (date thresholds, data thresholds, external decisions) live in the roadmap. They prevent blocked items from drifting forward by accident.

## When NOT to roadmap

Single-session work, bug fixes, content reviews, one-off scripts. Roadmaps are for projects that span multiple sessions and have meaningful sequencing decisions.

## Codename Registry

Every roadmap gets a one or two word lowercase codename. Codenames are claimed forever (active, shipped, OR archived) and never reused. Sorted alphabetically.

| Codename | Status | Lifespan | One-line | File |
|---|---|---|---|---|
| atlas | active | open-ended | the autonomy layer that runs the content pipeline while the laptop is off | [atlas.md](atlas.md) |
| echo | active | open-ended | async partnership substrate: agent proposes commits and acks, human responds asynchronously, neither blocks on the other | [echo.md](echo.md) |
| harvest | active | open-ended | Catalyst Works revenue pipeline (stub until first revenue session) | [harvest.md](harvest.md) |
| studio | active | open-ended | faceless agency running multiple branded channels on agentsHQ as adjacent revenue to Catalyst Works | [studio.md](studio.md) |

**To add a new codename:** invoke the `roadmap` skill with `roadmap new <codename>`. The skill validates the name, scaffolds the file, and adds the registry entry.

**Reserved / will-not-reuse:** none yet.

## Cross-references

- Phase-specific specs and plans still live in `docs/superpowers/specs/` and `docs/superpowers/plans/`. Roadmap milestones link to them.
- Memory entries (`C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\`) capture *why* and *how to apply* knowledge across sessions. Roadmaps capture *what* is being built and *when*.
- Handoff documents in `docs/handoff/` are deprecated for any project that has a roadmap. Use the session log section instead.
- Roadmap skill: `skills/roadmap/SKILL.md` (mirrored to `~/.claude/skills/roadmap/SKILL.md`).
