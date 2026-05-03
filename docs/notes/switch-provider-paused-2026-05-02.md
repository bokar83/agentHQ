# Switch-Provider / Smart Router: PAUSED 2026-05-02

## Status: PAUSED. Do not rebuild without explicit sign-off.

## What was built

A local provider-switching system for Claude Code and Codex CLI:

- `skills/switch-provider/switch_provider.py`: rewrites `~/.claude/settings.json` env block to redirect to OpenRouter, TheRouter, or Anthropic direct
- `skills/switch-provider/classify_task.py`: keyword classifier that runs as a `UserPromptSubmit` hook to auto-switch provider based on prompt content
- `skills/switch-provider/providers.json`: provider registry (openrouter, anthropic-official, therouter)
- `tests/test_classify_task.py`: 32+ tests for the classifier
- `tests/test_switch_provider.py`: tests for the switching script
- `~/.claude/settings.json`: was modified to wire `classify_task.py` as a `UserPromptSubmit` hook
- `docs/superpowers/specs/2026-05-02-multi-cli-provider-switching-design.md`: design spec (now deleted)

## Why it was paused

The `UserPromptSubmit` hook firing on every prompt caused OpenRouter to receive requests with context windows exceeding the 810k token limit. Result: "Prompt is too long" errors on every message. The session became unusable.

The auto-switching behavior (classify every prompt, switch provider silently) was too aggressive. The system needs a different approach before it can be re-enabled.

## What was NOT removed

The VPS-side Atlas circuit breaker (`orchestrator/provider_health.py`, `orchestrator/provider_probe.py`, changes to `orchestrator/llm_helpers.py`) was a separate layer and was NOT touched. That remains active on the VPS.

## If resuming this work

- Do NOT wire `UserPromptSubmit` hooks that auto-switch provider without explicit user action.
- Manual switching is safer than automatic keyword routing.
- Test with a fresh session context before enabling any hook-based switching.
- Token budget: OpenRouter has a 785k prompt token cap at current credit level.

## Git refs

All deleted files are preserved in git history. Last commits before removal:
- `e311312` fix(smart-router): returncode check + keyword fixes
- `3411bf0` feat(switch-provider): classify_task.py keyword router
- `2818eda` chore(sync): included switch-provider files
- `85d00a6` fix(switch-provider): exact TOML match
- `908662c` feat(switch-provider): initial switch_provider.py
- `b934781` feat(switch-provider): providers.json
