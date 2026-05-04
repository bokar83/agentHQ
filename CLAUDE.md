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

None. All rules shared. Claude-only rule emerges → add here.

## Caveman (installed 2026-05-03)

Caveman plugin installed via `irm .../install.ps1 | iex`. Reduces output tokens ~65%, auto-activates every session via SessionStart hook.

**What changed:**

- `~/.claude/hooks/` - 7 hook files added (caveman-activate.js, caveman-mode-tracker.js, caveman-stats.js, caveman-statusline.sh/ps1, caveman-config.js, package.json)
- `~/.claude/settings.json` - SessionStart + UserPromptSubmit hooks registered, statusline badge wired
- `claude mcp add caveman-shrink` - MCP proxy registered; compresses tool `description` fields before Claude reads them

**This file + all memory files** compressed via `caveman:compress` (2026-05-03). Originals backed up as `*.original.md` alongside each file. Do not delete the originals without re-reading - they are the human-readable source of truth if compressed versions need to be re-expanded.

**Do not manually edit hook files** in `~/.claude/hooks/caveman-*.js` - they are owned by the caveman plugin. Update via `irm .../install.ps1 | iex --force`.
