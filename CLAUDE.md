# agentsHQ: Claude Code SOP

**Read `docs/AGENT_SOP.md` first, every session. No exceptions.** Shared rules, session-start steps, hard rules, coding principles, skill triggers live there. File = Claude-Code-specific additions only.

## Active Roadmaps

Multi-session projects tracked in `docs/roadmap/<codename>.md`. `roadmap` skill manages them (list / show / next / log / new / archive). Read at session start, log at session end.

| Codename | One-line |
|---|---|
| `atlas` | agentsHQ true agentic work (autonomy layer) |
| `compass` | governance model: rules live, enforce, retire, anti-sprawl |
| `echo` | async substrate: agent proposes commits, human acks asynchronously |
| `harvest` | Catalyst Works revenue pipeline (stub) |
| `studio` | faceless agency: branded channels as adjacent revenue to CW |

Full registry: `docs/roadmap/README.md`.

## Claude-Code-Only

**Gate mode (2026-05-04):** When Boubacar sends agent outputs for review/push, this Claude session acts as the Gate. Gate has ONE job: arbitrate writes to shared state (GitHub, VPS, main). Refuse all other work until queue is clear. See AGENTS.md Gate section for full rules.

**No push/deploy without gate review.** Never `git push`, `ssh ... orc_rebuild.sh`, or merge to main in any session unless explicitly acting as Gate with Boubacar's inputs. Other Claude sessions = coding agents only.

## Hard Rule: Task Table as Live Registry (2026-05-04)

Every Claude Code session acting as a coding agent MUST update the coordination task table in real time. Not after. Not at the end. As work happens.

```python
from skills.coordination import claim, complete

# 1. Session start -- claim the branch
branch_task = claim('branch:feature/<name>', '<agent-id>', ttl_seconds=7200)
# If None: branch already claimed by another agent. Stop. Pick different task.

# 2. Before editing any file -- claim the file
file_task = claim('file:<relative-path>', '<agent-id>', ttl_seconds=1800)
# If None: file claimed. Wait or edit a different file.

# 3. After editing + committing the file
complete(file_task['id'])

# 4. All work done. Final commit MUST contain [READY].
# complete() the branch claim, then push.
complete(branch_task['id'])
# git commit -m "feat(x): description [READY]"
# git push origin feature/<name>
```

Skipping any step breaks multi-agent coordination. Gate checks the task table before processing any branch. Unclaimed = in-flight = gate skips it.

## Caveman (installed 2026-05-03)

Caveman plugin installed via `irm .../install.ps1 | iex`. Reduces output tokens ~65%, auto-activates every session via SessionStart hook.

**What changed:**

- `~/.claude/hooks/` - 7 hook files added (caveman-activate.js, caveman-mode-tracker.js, caveman-stats.js, caveman-statusline.sh/ps1, caveman-config.js, package.json)
- `~/.claude/settings.json` - SessionStart + UserPromptSubmit hooks registered, statusline badge wired
- `claude mcp add caveman-shrink` - MCP proxy registered; compresses tool `description` fields before Claude reads them

**This file + all memory files** compressed via `caveman:compress` (2026-05-03). Originals backed up as `*.original.md` alongside each file. Do not delete the originals without re-reading - they are the human-readable source of truth if compressed versions need to be re-expanded.

**Do not manually edit hook files** in `~/.claude/hooks/caveman-*.js` - they are owned by the caveman plugin. Update via `irm .../install.ps1 | iex --force`.
