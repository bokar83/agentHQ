---
name: General feedback and preferences
description: Corrections and preferences Boubacar has given — apply these without being reminded
type: feedback
---

# General Feedback and Preferences

## File Location

- **Never create files or directories on C: drive.** All project files go in D:\Ai_Sandbox\agentsHQ or D:\Ai_Sandbox\ at minimum.
- If the memory system path points to C:, do NOT create it. Store context files in D:\Ai_Sandbox\agentsHQ\docs\memory\ instead.
- If a directory doesn't exist before writing files, ask before creating it — unless it's clearly inside D:\Ai_Sandbox\.

## Memory / Context

- Session context lives at D:\Ai_Sandbox\agentsHQ\docs\memory\ and is excluded from git via .gitignore.
- At the start of each session, read this folder for context before doing anything.

## GWS CLI / Bash Permissions

- Boubacar has granted blanket authorization to run ALL GWS CLI and Bash commands without prompting.
- **The permission prompt loop is a Claude Code tool permission issue, NOT a user authorization issue.**
- To actually bypass it, the session must be started with `claude --dangerously-skip-permissions` in the terminal, OR `"allow": ["Bash(*)"]` must be set in settings.json.
- **`--dangerously-skip-permissions`** = runtime flag, one terminal session only, dies when terminal closes.
- **settings.json `"allow": ["Bash(*)"]`** = permanent, applies to all sessions in that project directory.
- The settings.json fix is preferred — add it to `D:\Ai_Sandbox\agentsHQ\.claude\settings.json`.
- When running sub-agents via the Agent tool, also pass `"mode": "bypassPermissions"` — but this only works if the parent session also has bypass enabled.
- **Never stop mid-build to ask for Bash permission.** If prompts appear despite authorization, complete the work using `dangerouslyDisableSandbox: true` on each Bash call.
