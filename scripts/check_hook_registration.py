#!/usr/bin/env python3
"""
check_hook_registration.py - Block commits that register high-risk Claude Code
hooks without a cost/rate annotation in the same commit.

High-risk hook events: UserPromptSubmit, PreToolUse (when not a simple guard).
These fire on every message or tool call. A hook that makes an LLM call or
rewrites global config in these slots can drain a balance in minutes.

Rule: any staged change that adds a NEW command to UserPromptSubmit or adds
a non-trivial PreToolUse command must be accompanied by a comment block in
the same diff containing the four canary answers:
  # HOOK_MODEL: <model or N/A>
  # HOOK_MAX_CONTEXT: <tokens or N/A>
  # HOOK_COST_PER_FIRE: <$USD or N/A>
  # HOOK_FIRING_RATE: <per-message|per-tool|scheduled:Xmin>

If the annotation is missing, the commit is blocked with instructions.

Why: 2026-05-02 switch-provider hook cost $57 in 3 hours. No one asked
"what does this cost at 200k tokens?" before wiring it. This hook forces
the question at commit time.
"""
from __future__ import annotations

import re
import subprocess
import sys

HIGH_RISK_EVENTS = {"UserPromptSubmit", "PreToolUse"}

ANNOTATION_KEYS = {
    "HOOK_MODEL",
    "HOOK_MAX_CONTEXT",
    "HOOK_COST_PER_FIRE",
    "HOOK_FIRING_RATE",
}

# PreToolUse commands that are pure guards (no LLM, no config write) are exempt.
EXEMPT_PATTERNS = [
    r"git\s+-C.*worktreeConfig",   # existing worktree unset guard
    r"check-base-url\.js",          # our own burn guard
    r"exit\s+0",                    # trivial pass-through
]


def _get_staged_diff() -> str:
    result = subprocess.run(
        ["git", "diff", "--cached", "-U5"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return result.stdout


def _is_exempt(command: str) -> bool:
    return any(re.search(p, command) for p in EXEMPT_PATTERNS)


def _find_new_hook_commands(diff: str) -> list[tuple[str, str]]:
    """Return list of (event, command) for newly added hook commands in the diff."""
    found = []
    current_event = ""
    in_added_block = False

    for line in diff.splitlines():
        # Track which file/section we are in
        if line.startswith("+++"):
            in_added_block = True
            continue

        if not in_added_block:
            continue

        # Only look at added lines
        if not line.startswith("+"):
            continue

        stripped = line[1:]  # remove leading +

        # Detect event name from JSON key pattern: "UserPromptSubmit" or "PreToolUse"
        for event in HIGH_RISK_EVENTS:
            if f'"{event}"' in stripped:
                current_event = event

        # Detect a "command": "..." line
        cmd_match = re.search(r'"command"\s*:\s*"([^"]+)"', stripped)
        if cmd_match and current_event:
            command = cmd_match.group(1)
            if not _is_exempt(command):
                found.append((current_event, command))

    return found


def _diff_has_annotations(diff: str) -> bool:
    """Check that all four annotation keys appear somewhere in the staged diff."""
    found = set()
    for line in diff.splitlines():
        if not line.startswith("+"):
            continue
        for key in ANNOTATION_KEYS:
            if f"# {key}:" in line or f"// {key}:" in line:
                found.add(key)
    return ANNOTATION_KEYS.issubset(found)


def main() -> int:
    diff = _get_staged_diff()
    new_hooks = _find_new_hook_commands(diff)

    if not new_hooks:
        return 0

    if _diff_has_annotations(diff):
        return 0

    print("HOOK REGISTRATION GUARD: Blocked.\n")
    print("New high-risk hook command(s) detected in this commit:")
    for event, cmd in new_hooks:
        print(f"  Event: {event}")
        print(f"  Command: {cmd[:100]}")
        print()

    print("Before registering a hook that fires on every message or tool call,")
    print("add a comment block in the same file (or a nearby config) with:")
    print()
    print("  # HOOK_MODEL: <model name, or N/A if no LLM call>")
    print("  # HOOK_MAX_CONTEXT: <max tokens this hook will see at real session length>")
    print("  # HOOK_COST_PER_FIRE: <$USD per firing at that context, or N/A>")
    print("  # HOOK_FIRING_RATE: <per-message | per-tool | scheduled:Xmin>")
    print()
    print("If cost/fire x firing_rate exceeds $0.10/min, do NOT register the hook.")
    print("See docs/notes/switch-provider-paused-2026-05-02.md for the $57 incident.")

    return 1


if __name__ == "__main__":
    sys.exit(main())
