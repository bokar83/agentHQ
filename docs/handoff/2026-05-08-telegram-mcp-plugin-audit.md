# Session Handoff - Telegram MCP + Plugin/MCP Audit - 2026-05-08

## TL;DR
Investigated whether claude-telegram-remote repo could control Claude Code in Antigravity (no — macOS+tmux only). Pivoted to native Telegram plugin (`telegram@claude-plugins-official`). Got the plugin enabled, bot token wired, channelsEnabled set, bun installed, node_modules installed — but MCP server still failing due to bun CJS resolution bug on Windows (grammy). Also discovered context-mode had a stale version path since 2026-05-03 and fixed it. Found that multiple MCP servers have been silently broken for 6+ weeks with no alerting. A second session is running to complete the work.

## What was built / changed

- `C:\Users\HUAWEI\.claude\settings.json` — added `telegram@claude-plugins-official` to enabledPlugins, `channelsEnabled: true`, `BUN_CA_BUNDLE_PATH` env var, `Read(.env)` permission allow entry
- `C:\Users\HUAWEI\.claude\channels\telegram\.env` — created, contains `TELEGRAM_BOT_TOKEN=<token>`
- `C:\Users\HUAWEI\.claude\plugins\cache\claude-plugins-official\telegram\0.0.6\` — node_modules installed (99 packages via npm)
- `C:\Users\HUAWEI\.claude\plugins\cache\context-mode\context-mode\1.0.111\.mcp.json` — fixed stale path from `1.0.107/start.mjs` → `1.0.111/start.mjs`
- `C:\Users\HUAWEI\.bun\bin\bun.exe` — bun v1.3.13 installed
- `C:\Users\HUAWEI\.bun\ca-bundle.crt` — Windows root certs exported (74 certs, for future bun SSL fix attempts)
- `docs/reviews/absorb-log.md` — logged oscarsterling/claude-telegram-remote as DON'T PROCEED
- Memory files: `feedback_bun_ssl_windows.md`, `feedback_telegram_mcp_bun_cjs.md`, `feedback_mcp_plugins_broken_6weeks.md`

## Decisions made

- **Telegram control = native plugin**, not oscarsterling/claude-telegram-remote (macOS+tmux incompatible with Windows/Antigravity)
- **Remoat stays** for Antigravity agent control; telegram plugin is for Claude Code direct control
- **bun install = use npm instead** on this machine; bun run still works for execution
- **MCP health monitoring needed** — 6 weeks of silent failures is unacceptable; build SessionStart hook

## What is NOT done

- Telegram MCP server not running — bun crashes with `Cannot find module './core/api.js' from grammy/out/bot.js` (CJS resolution on Windows)
- Telegram bot not paired — blocked on MCP running
- context7, playwright failures not fully diagnosed (npx works standalone, /mcp still shows failed — may be slow start)
- n8n MCP auth not done
- MCP health monitor not built
- Plugin pruning (code-simplifier removal) not done
- context-mode not indexed/activated

## Open questions

- Does `npx tsx server.ts` fix the grammy CJS issue? (Try first in next session)
- Are context7/playwright slow-start or genuinely broken in /mcp?
- n8n API key location on VPS — is it N8N_API_KEY in /root/agentsHQ/.env?

## Next session must start here

The second session already has the full prompt. If starting a third session from scratch:

1. Try `npm install -g tsx` then patch telegram `.mcp.json` `command` to `npx`, `args` to `["tsx", "C:\\Users\\HUAWEI\\.claude\\plugins\\cache\\claude-plugins-official\\telegram\\0.0.6\\server.ts"]`
2. Test: `node_modules` exists at telegram plugin path (99 packages) ✅
3. Restart Claude Code — verify context-mode shows ✔ connected in /mcp
4. After telegram MCP green: run `/telegram:access` to pair bot
5. Test from phone to @CCagentsHQ_bot
6. Fix n8n auth (SSH to VPS, get API key)
7. Build MCP health monitor SessionStart hook
8. Run plugin audit (see full prompt written at end of this session)

## Files changed this session

```
C:\Users\HUAWEI\.claude\settings.json
C:\Users\HUAWEI\.claude\channels\telegram\.env  (created)
C:\Users\HUAWEI\.claude\plugins\cache\context-mode\context-mode\1.0.111\.mcp.json
C:\Users\HUAWEI\.claude\plugins\cache\claude-plugins-official\telegram\0.0.6\node_modules\  (created)
C:\Users\HUAWEI\.bun\bin\bun.exe  (installed)
C:\Users\HUAWEI\.bun\ca-bundle.crt  (created)
docs/reviews/absorb-log.md
memory/feedback_bun_ssl_windows.md  (created)
memory/feedback_telegram_mcp_bun_cjs.md  (created)
memory/feedback_mcp_plugins_broken_6weeks.md  (created)
memory/MEMORY.md  (updated)
```
