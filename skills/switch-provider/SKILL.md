---
name: switch-provider
description: Switch the active LLM provider for Claude Code and Codex CLI by rewriting env blocks in settings.json and config.toml.
---

# switch-provider

Switch the active LLM provider for Claude Code and Codex CLI.

## Trigger phrases
- "switch provider"
- "switch to openrouter"
- "switch to anthropic official"
- "switch claude code to X"
- "switch codex to X"
- "list providers"
- "what provider am I on"
- "use openrouter"
- "use anthropic direct"

## Usage

Manual (from agentsHQ repo root):
    python skills/switch-provider/switch_provider.py openrouter
    python skills/switch-provider/switch_provider.py anthropic-official
    python skills/switch-provider/switch_provider.py openrouter --cli codex
    python skills/switch-provider/switch_provider.py openrouter --cli all
    python skills/switch-provider/switch_provider.py --list

Agent/skill invocation:
    import subprocess
    subprocess.run(
        ["python", "skills/switch-provider/switch_provider.py", provider, "--cli", cli],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )

## Notes
- Claude Code picks up the change on the next tool call (no restart needed).
- Codex requires a terminal restart.
- providers.json lives alongside this script. Add new providers there.
- $VAR values in providers.json are resolved from environment variables at write time.
