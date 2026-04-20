---
name: worktreeConfig Guardrail Hook
date: 2026-04-20
status: design
---

# worktreeConfig Guardrail Hook

## Background

AntiGravity IDE silently failed on the agentsHQ repo. Root cause: a prior Claude Code session left `extensions.worktreeConfig=true` set in the repo's git config. With that flag on, git expects a per-worktree config file (`.git/config.worktree`) that AntiGravity does not create or read. Result: AntiGravity's agent initialization broke without a visible error.

Current repo state (verified 2026-04-20): flag is not set, no stray `.git/config.worktree`, no active worktrees. Damage from the prior session has already cleared. This spec is about preventing recurrence, not repairing current state.

## Goal

Prevent `extensions.worktreeConfig=true` from ever persisting into a repo that Claude Code touches on this machine. One user-level hook, runs silently before any tool call, unsets the flag if present. No manual step, no alias to remember.

## Non-Goals

- Not fixing AntiGravity's handling of worktree config (out of scope; that's their bug).
- Not blocking Claude Code's legitimate use of worktrees mid-session. The `EnterWorktree` flow creates a *separate* repo directory with its own `.git`; the hook only touches the primary repo's config when the hook fires there.
- Not replacing the alias as a debugging tool. A one-liner `git config --unset extensions.worktreeConfig` remains available for manual use if the user ever needs it, but we're not installing it globally.

## Design

### Hook type: PreToolUse

Claude Code fires `PreToolUse` before every tool call. This is the earliest reliable point. SessionStart would also work but fires less often (once per session start); PreToolUse gives defense-in-depth — if a tool call mid-session mutates config, the next tool call catches it.

Cost: the hook runs a single `git config --unset` per tool call. When the flag is unset (the common case), git exits with code 5 ("tried to unset an option which does not exist") and produces no side effects. Latency is negligible (low milliseconds).

### Scope: user-level (`~/.claude/settings.json`)

Installed once, protects every repo opened with Claude Code on this machine. Project-level would require duplicating the config into every repo's `.claude/settings.json`.

### Command

```bash
git -C "$CLAUDE_PROJECT_DIR" config --local --unset extensions.worktreeConfig 2>/dev/null; exit 0
```

Key behaviors:

- `git -C "$CLAUDE_PROJECT_DIR"` — run against the project the hook fires for, not the shell's cwd.
- `--local` — only touch the repo's own config, never user/global/system.
- `--unset` on a missing key returns exit 5; `2>/dev/null` suppresses the stderr line; `exit 0` ensures the hook never blocks a tool call even if git is absent or the directory isn't a git repo.
- No matcher filter — runs on every tool call. A more selective matcher (e.g., only `Bash` or only `Edit`) saves nothing meaningful and adds a failure mode (a non-matched tool call could mutate config and we'd miss it).

### What the hook does NOT do

- Does not log. Silent success is the desired behavior; a log line on every tool call is noise.
- Does not touch `.git/config.worktree` if it exists. If git's worktree-config subsystem created one legitimately in a future worktree, we leave it alone; unsetting the extension flag is enough to restore default behavior.
- Does not run on non-git directories. The `git -C` call errors harmlessly and `exit 0` swallows it.

## Settings.json shape

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "git -C \"$CLAUDE_PROJECT_DIR\" config --local --unset extensions.worktreeConfig 2>/dev/null; exit 0"
          }
        ]
      }
    ]
  }
}
```

This merges into existing `hooks.PreToolUse` entries without clobbering them. If the user already has PreToolUse hooks, we append a new entry to the array.

## Verification plan

1. Install hook in `~/.claude/settings.json`.
2. Manually set the flag in agentsHQ: `git config --local extensions.worktreeConfig true`.
3. Confirm: `git config --local --get extensions.worktreeConfig` → `true`.
4. Trigger any Claude Code tool call (e.g., a Read).
5. Re-check: `git config --local --get extensions.worktreeConfig` → no output (git exits non-zero because the key is absent). Flag is gone.
6. Open agentsHQ in AntiGravity, confirm agent initializes normally.

## Risks

- **Hook fires on wrong directory.** `$CLAUDE_PROJECT_DIR` is set by Claude Code to the primary project root, not any sub-worktree. Mitigated by using `git -C` with that specific path.
- **Hook masks a legitimate future need for worktreeConfig.** If a future workflow deliberately wants per-worktree config, the hook will silently strip it. Mitigation: the hook is one line in user settings; it can be commented out in 10 seconds when that day comes. Low probability given current usage.
- **Hook not invoked on a different machine.** User-level settings live in this machine's `~/.claude/`. A second workstation needs the same hook added. Tracked as a follow-on memory note, not part of this spec.

## Follow-on (not in this spec)

- Save a feedback memory noting the hook exists, why, and where it lives, so future sessions don't "helpfully" remove it.
- If a second machine joins the workflow, replicate the hook there.
