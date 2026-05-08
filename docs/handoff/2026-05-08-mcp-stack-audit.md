# Session Handoff - MCP Stack Audit + Plugin Fixes - 2026-05-08

## TL;DR
Full audit and repair of the Claude Code MCP/plugin stack. Started with telegram broken, context7/playwright/context-mode all failing. Fixed root causes across multiple sessions: wrong .mcp.json format, bun SSL issues, stale lock files, missing env vars, plugin loader timing out on Windows. Stack is now largely healthy with a health monitor wired in.

## What was built / changed

**Config changes (`~/.claude/settings.json`):**
- Added env: `TELEGRAM_BOT_TOKEN`, `CC_TELEGRAM_BOT_TOKEN`, `CC_TELEGRAM_CHAT_ID`, `NODE_EXTRA_CA_CERTS`
- Added mcpServers: `sequential-thinking`, `context7`, `playwright`, `ctx-mode`
- Disabled plugins: `code-simplifier`, `ralph-loop`, `typescript-lsp`
- Added SessionStart hook: `python "C:/Users/HUAWEI/.claude/hooks/mcp-health-check.py"` (async)

**Config changes (`~/.claude.json`):**
- Removed `caveman-shrink` from project mcpServers (broken — no upstream arg)

**Plugin .mcp.json fixes:**
- `telegram/0.0.6/.mcp.json`: changed command to `npx tsx`, added `env.TELEGRAM_BOT_TOKEN`
- `context7/unknown/.mcp.json`: wrapped in `mcpServers` object (was missing)
- `playwright/unknown/.mcp.json`: wrapped in `mcpServers` object (was missing)

**New files:**
- `~/.claude/hooks/mcp-health-check.py`: SessionStart health monitor (reads plugin cache, checks commands, diffs baseline, Telegram alert on new failures)
- `~/.claude/hooks/mcp-baseline.json`: baseline state (context-mode, telegram, playwright, context7 all OK)

**Docs:**
- `docs/AGENT_SOP.md`: added Context-Mode Rule section
- `CLAUDE.md`: added Context-Mode section
- `docs/roadmap/atlas.md`: added MCP Stack Evolution milestone + session log
- `docs/reviews/absorb-followups.md`: line 16 marked DONE

**Memory:**
- `feedback_n8n_is_cloud_mcp.md`: n8n = cloud auth via claude.ai web
- `feedback_telegram_plugin_stale_locks.md`: rm -f .in_use/* fix
- `feedback_context_mode_direct_registration.md`: ctx-mode bypass pattern

## Decisions made

- **context-mode registered as `ctx-mode`** in settings.json mcpServers — plugin loader on Windows/Antigravity fails; direct node path is the fix. When upgrading context-mode, update the path in settings.json.
- **caveman-shrink removed** — it's a proxy that needs an upstream arg; registered with none = always broken. Low value given we already have caveman plugin.
- **pyright-lsp + mcp-server-dev kept** — pyrightconfig.json active in repo; mcp-server-dev useful for future builds.
- **context7 + playwright registered in both plugin AND settings.json mcpServers** — belt-and-suspenders; if plugin fails, settings.json path still works.

## What is NOT done

- **Codebase index**: context-mode `ctx_execute` available but codebase not yet indexed. Do `ctx_execute` with a shell find/scan on first multi-file exploration session.
- **n8n auth**: cloud MCP, needs periodic re-auth via claude.ai web. Not a local fix.
- **Calendly auth**: same — cloud MCP, re-auth via claude.ai web when needed.
- **10 stale handoff docs** in `docs/handoff/` root — session audit keeps warning. Run `/nsync` or archive manually.
- **`plugin:context-mode:context-mode`** still shows `✘ failed` in /mcp — this is the plugin loader entry, not the working `ctx-mode` entry. Cosmetic; ignore it.

## Open questions

- Sequential-thinking MCP: verify it actually shows ✔ connected after restart (depends on `NODE_TLS_REJECT_UNAUTHORIZED=0` in env being inherited by MCP process).
- Health monitor Telegram chat ID (7792432594) — confirm this is the correct @bokar83 DM chat ID with @CCagentsHQ_bot.

## Next session must start here

1. Run `/mcp` — verify `ctx-mode`, `sequential-thinking`, `telegram`, `context7`, `playwright` all ✔ connected
2. If sequential-thinking still fails: it needs `NODE_TLS_REJECT_UNAUTHORIZED=0` inherited — check if env is passed to MCP subprocess
3. Archive stale handoff docs: `mv docs/handoff/*.md docs/handoff/archive/` (keep files newer than 2026-05-05)
4. Resume normal work (M18 HALO tracing, newsletter_editorial_input fix, etc.)

## Files changed this session

```
~/.claude/settings.json                          — env, mcpServers, enabledPlugins, hooks
~/.claude.json                                   — removed caveman-shrink
~/.claude/hooks/mcp-health-check.py             — new: SessionStart health monitor
~/.claude/hooks/mcp-baseline.json               — new: baseline MCP state
~/.claude/plugins/cache/.../telegram/.mcp.json  — npx tsx + env block
~/.claude/plugins/cache/.../context7/.mcp.json  — mcpServers wrapper fix
~/.claude/plugins/cache/.../playwright/.mcp.json — mcpServers wrapper fix
~/.claude/projects/.../memory/MEMORY.md         — 2 new pointers
~/.claude/projects/.../memory/feedback_n8n_is_cloud_mcp.md
~/.claude/projects/.../memory/feedback_telegram_plugin_stale_locks.md
~/.claude/projects/.../memory/feedback_context_mode_direct_registration.md
d:/Ai_Sandbox/agentsHQ/CLAUDE.md               — context-mode section
d:/Ai_Sandbox/agentsHQ/docs/AGENT_SOP.md       — Context-Mode Rule section
d:/Ai_Sandbox/agentsHQ/docs/roadmap/atlas.md   — MCP Evolution milestone + session log
d:/Ai_Sandbox/agentsHQ/docs/reviews/absorb-followups.md — line 16 DONE
```
