#!/usr/bin/env python3
"""
check_no_provider_redirect.py - Block commits that bake a non-Anthropic
ANTHROPIC_BASE_URL into ~/.claude/settings.json or any committed config.

Fires as a pre-commit hook on any staged JSON file that contains
ANTHROPIC_BASE_URL pointing at a non-Anthropic host (e.g. openrouter.ai).

Why: The 2026-05-02 incident burned $57 because a UserPromptSubmit hook
rewrote settings.json to redirect all Claude Code traffic to OpenRouter.
A committed redirect is even worse -- it survives reboots and new sessions.
"""
import json
import subprocess
import sys
from pathlib import Path

ALLOWED_HOSTS = ("anthropic.com", "api.anthropic.com")
BLOCKED_PATHS = (
    Path.home() / ".claude" / "settings.json",
    Path.home() / ".claude" / "settings.local.json",
)


def _staged_json_files() -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True
    )
    return [Path(p) for p in result.stdout.splitlines() if p.endswith(".json")]


def _check_file(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    violations = []
    base_url = ""

    # Top-level env block (settings.json pattern)
    if isinstance(data, dict):
        base_url = (data.get("env") or {}).get("ANTHROPIC_BASE_URL", "")

    if not base_url:
        return []

    if not any(host in base_url for host in ALLOWED_HOSTS):
        violations.append(
            f"  {path}: ANTHROPIC_BASE_URL={base_url!r}\n"
            f"  This routes ALL Claude Code traffic through a third-party provider.\n"
            f"  Remove it before committing. To clear: remove ANTHROPIC_BASE_URL from\n"
            f"  the env block in settings.json."
        )

    return violations


def main() -> int:
    violations = []

    # Check staged JSON files in the repo
    for path in _staged_json_files():
        if path.exists():
            violations.extend(_check_file(path))

    # Always check the global settings.json even if not staged
    for path in BLOCKED_PATHS:
        if path.exists():
            v = _check_file(path)
            if v:
                violations.extend([
                    f"  WARNING: {path} has a live provider redirect (not staged, but active):",
                ] + v)

    if violations:
        print("PROVIDER REDIRECT GUARD: Blocked.\n")
        for v in violations:
            print(v)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
