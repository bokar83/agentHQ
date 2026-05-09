# Session Handoff - RTK Install + Absorb Skill Fix - 2026-05-03

## TL;DR

Absorbed and installed RTK (Rust Token Killer) - a Rust binary that compresses Bash output 60-90% before it reaches Claude's context. Wired it into Windows Claude Code via WSL2 hook and into Antigravity via rules file. Fixed the agentshq-absorb skill to properly handle external tools (tool-vs-skill detection gate, README-first rule, tool-bloat Sankofa/Karpathy framing).

## What was built / changed

- `C:\Users\HUAWEI\.claude\settings.json` - added PreToolUse Bash hook: `wsl -d Ubuntu -- /root/.local/bin/rtk hook claude`
- `skills/agentshq-absorb/SKILL.md` - added: README-first hard rule, tool-vs-skill detection gate before Phase 0, Tool Fit Check with tool-bloat Sankofa/Karpathy framing, fixed duplicate common-mistake entry, two new common-mistake rows
- `docs/reviews/absorb-log.md` - appended RTK PROCEED entry
- `docs/reviews/absorb-followups.md` - appended RTK install follow-up (target 2026-05-07)
- `.agents/rules/antigravity-rtk-rules.md` - created by `rtk init --agent antigravity`; instructs Antigravity to prefix shell commands with `rtk`
- WSL2 Ubuntu: `/root/.local/bin/rtk` - RTK v0.38.0 binary

## Decisions made

- RTK = external tool, not a skill. Evaluated via Tool Fit Check path, not placement taxonomy.
- Absorb skill now distinguishes tools from skills at detection time. Tools get fit check + Sankofa/Karpathy with tool-bloat lens. Phase 3 placement taxonomy skipped for tools entirely.
- Sankofa/Karpathy still run for tools - Boubacar explicitly wants this to prevent tool bloat.
- RTK hook uses hardcoded WSL absolute path (`/root/.local/bin/rtk`) - Git Bash expands `$PATH` and breaks `bash -c 'export PATH=...'` form.
- RTK wired for Windows Claude Code (WSL hook) + Antigravity (rules file). VPS Linux would get full auto-rewrite natively if RTK installed there.

## What is NOT done (explicit)

- RTK not installed on VPS (`root@72.60.209.109`). Would give full auto-hook on `docker logs`, `git log`, etc. Not done - not requested this session.
- absorb-followups entry for RTK (2026-05-07) not yet executed - that's just the logged target date.

## Open questions

- RTK hook cold-start latency: first Bash call after WSL idle may take a few seconds (WSL spin-up). Monitor if it causes timeouts. Timeout currently set to 10s in settings.json.
- Should RTK be installed on VPS too? Would improve Atlas autonomy infra Bash output compression on the server side.

## Next session must start here

1. No blocking action required - this was infrastructure work, all shipped.
2. If RTK hook causes Bash timeouts (>10s on cold WSL), increase timeout in `settings.json` PreToolUse Bash hook from 10 to 15.
3. Run `wsl -d Ubuntu -- /root/.local/bin/rtk gain` after a few sessions to verify savings are materializing.

Note: RTK/caveman/context-mode are NOT relevant on the VPS. VPS has no Claude Code - no hook mechanism to intercept CLI output. Token savings on VPS happen at the LLM API call level, already handled by max_tokens caps.

## Files changed this session

```
C:\Users\HUAWEI\.claude\settings.json
C:\Users\HUAWEI\.claude\skills\agentshq-absorb\SKILL.md  (= d:/Ai_Sandbox/agentsHQ/skills/agentshq-absorb/SKILL.md)
d:\Ai_Sandbox\agentsHQ\docs\reviews\absorb-log.md
d:\Ai_Sandbox\agentsHQ\docs\reviews\absorb-followups.md
d:\Ai_Sandbox\agentsHQ\.agents\rules\antigravity-rtk-rules.md  [new]
WSL2:/root/.local/bin/rtk  [installed]
WSL2:/root/.claude/RTK.md  [written by rtk init]
WSL2:/root/.claude/CLAUDE.md  [@RTK.md reference added by rtk init]
memory/reference_rtk_install.md  [new]
memory/feedback_absorb_tool_vs_skill.md  [new]
memory/feedback_wsl_hook_path_quoting.md  [new]
memory/MEMORY.md  [updated - 3 new pointers + RTK capability line]
```
