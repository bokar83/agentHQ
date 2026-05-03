# Multi-CLI Provider Switching: Design Spec

**Date:** 2026-05-02
**Author:** Boubacar Barry / Claude Code
**Status:** Approved for implementation
**Inspired by:** cc-switch (farion1231/cc-switch) absorb eval

---

## Problem Statement

agentsHQ currently locks every LLM call to a single provider:

- Claude Code CLI routes through Anthropic official or whatever `ANTHROPIC_BASE_URL` is set to in `~/.claude/settings.json`.
- Atlas (VPS orchestrator) routes all LLM calls through OpenRouter exclusively via `llm_helpers.py`.
- Codex CLI uses `~/.codex/config.toml` independently.
- Gemini CLI uses `~/.gemini/` OAuth independently.

There is no way to switch providers without hand-editing config files, and no failover when a provider goes down. This spec defines a three-layer solution.

---

## Scope

### In scope

- **Layer A:** Manual provider switching from the command line (one command, any supported CLI).
- **Layer B:** Agent/skill-driven provider switching (same script, called programmatically).
- **Layer C:** Atlas circuit breaker with Telegram alert on provider failure, auto-restore on recovery.

### Out of scope

- Gemini CLI switching (OAuth-based, not API-key-based; deferred).
- Automatic provider switching without human confirmation (degrade-and-alert is the chosen pattern).
- Installing or depending on cc-switch desktop app.
- Multi-provider load balancing or cost optimization routing.

---

## Architecture

Three independent layers. None depends on another. Build in order.

```
Layer A/B: skills/switch-provider/          (local dev machine)
Layer C:   orchestrator/llm_helpers.py      (VPS container)
```

---

## Layer A + B: `skills/switch-provider/`

### Purpose

A single Python script that reads a local `providers.json` and writes the selected provider's credentials into the target CLI's config file. Manual use (A) and agent/skill use (B) call the exact same script.

### File structure

```
skills/switch-provider/
  SKILL.md
  switch_provider.py
  providers.json
```

### `providers.json` shape

```json
{
  "openrouter": {
    "label": "OpenRouter (current default)",
    "claude": {
      "ANTHROPIC_BASE_URL": "https://openrouter.ai/api",
      "ANTHROPIC_AUTH_TOKEN": "$OPENROUTER_API_KEY"
    },
    "codex": {
      "model": "openai/gpt-4o"
    }
  },
  "anthropic-official": {
    "label": "Anthropic Official",
    "claude": {}
  },
  "therouter": {
    "label": "TheRouter relay",
    "claude": {
      "ANTHROPIC_BASE_URL": "https://api.therouter.ai",
      "ANTHROPIC_AUTH_TOKEN": "$THEROUTER_API_KEY"
    }
  }
}
```

Notes:
- `$VAR` values are resolved from environment variables at write time.
- An empty `claude: {}` block means remove `ANTHROPIC_BASE_URL` override (revert to official Anthropic).
- Only `claude` and `codex` targets are supported in v1. `gemini` key is reserved but not implemented.

### `switch_provider.py` behavior

```
usage: switch_provider.py <provider> [--cli claude|codex|all] [--list]
```

- `--list`: print all available providers and their labels, exit.
- `--cli claude`: write to `~/.claude/settings.json` env block only.
- `--cli codex`: write to `~/.codex/config.toml` only.
- `--cli all`: write to all supported CLIs that have a config block for this provider.
- Default `--cli` is `claude`.

**Atomic write pattern (required):**
1. Read current config file into memory.
2. Apply provider values into the relevant section.
3. Write to a temp file in the same directory (`settings.json.tmp`).
4. `os.replace(tmp, target)` (atomic on all platforms).
5. Print confirmation: `Switched claude to openrouter (https://openrouter.ai/api)`.

**Claude Code hot-switch behavior:** Writing to `~/.claude/settings.json` env block takes effect on the next tool call without restarting the session. Confirmed by cc-switch FAQ + cc-switch source.

**Codex restart note:** Codex requires a terminal restart after `config.toml` changes. The script prints a reminder.

### SKILL.md trigger phrases

- "switch provider"
- "switch to openrouter"
- "switch to anthropic official"
- "switch claude code to X"
- "switch codex to X"
- "list providers"
- "what provider am I on"

### Agent/skill invocation pattern (Layer B)

Any skill or agent that needs to switch providers calls:

```python
import subprocess
result = subprocess.run(
    ["python", "skills/switch-provider/switch_provider.py", provider, "--cli", cli],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
```

No direct import. Subprocess boundary keeps the skill isolated.

### Success criteria

- `python skills/switch-provider/switch_provider.py openrouter` writes the correct `ANTHROPIC_BASE_URL` to `~/.claude/settings.json` without corrupting existing keys.
- `python skills/switch-provider/switch_provider.py anthropic-official` removes the `ANTHROPIC_BASE_URL` override from the env block.
- `python skills/switch-provider/switch_provider.py openrouter --cli codex` writes the correct model to `~/.codex/config.toml`.
- `python skills/switch-provider/switch_provider.py --list` prints all providers without side effects.
- Running the script twice in a row produces identical output (idempotent).
- A corrupted or missing config file does not crash the script; it creates a minimal valid config.

---

## Layer C: Atlas Circuit Breaker + Telegram Alert

### Purpose

Atlas's `llm_helpers.py` currently has a single point of failure: OpenRouter. If OpenRouter is unreachable or returns errors, every Atlas crew call fails silently or crashes. This layer adds:

1. A failure counter per provider (in the existing `agent_config` Postgres DB).
2. A circuit breaker: after 3 failures in 5 minutes, mark the provider as tripped and pause LLM calls.
3. A Telegram alert fired once on trip, once on recovery.
4. A health probe cron (every 5 minutes via the existing heartbeat system) that tests the active provider and resets the circuit if it recovers.

### What does NOT change

- OpenRouter remains the only active provider. There is no automatic silent failover to a second provider. Degrade-and-alert is the pattern.
- `call_llm()` signature is unchanged.
- `get_openrouter_client()` is unchanged.

### New DB table: `provider_health`

```sql
CREATE TABLE IF NOT EXISTS provider_health (
    id          SERIAL PRIMARY KEY,
    provider    TEXT NOT NULL DEFAULT 'openrouter',
    status      TEXT NOT NULL DEFAULT 'healthy',  -- 'healthy' | 'tripped'
    fail_count  INT  NOT NULL DEFAULT 0,
    tripped_at  TIMESTAMPTZ,
    recovered_at TIMESTAMPTZ,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
INSERT INTO provider_health (provider, status) VALUES ('openrouter', 'healthy')
ON CONFLICT DO NOTHING;
```

One row per provider. Only `openrouter` in v1.

### Circuit breaker logic in `call_llm()`

```
on openai.APIError or httpx.TimeoutException:
    increment fail_count for active provider
    if fail_count >= 3 AND time_since_first_fail <= 5 min:
        set status = 'tripped', tripped_at = now()
        send Telegram alert: "OpenRouter tripped. 3 failures in 5 min. Manual switch: python skills/switch-provider/switch_provider.py <provider> --cli claude"
    re-raise the exception (caller handles as before)
```

The circuit breaker does NOT catch the exception for the caller. It only tracks and alerts. Existing error handling in crews is unchanged.

### Health probe: `orchestrator/provider_probe.py`

New file. Registered as a heartbeat wake on 5-minute interval (same pattern as existing heartbeats).

Behavior:
1. Read active provider status from `provider_health`.
2. If `tripped`: send a lightweight test call (1-token completion). If it succeeds: set `status = 'healthy'`, `fail_count = 0`, `recovered_at = now()`. Send Telegram: "OpenRouter recovered. Resume normal operations."
3. If `healthy`: run the same lightweight test. If it fails: increment fail_count (same circuit breaker logic as above).
4. Log result to `provider_health.updated_at`.

### Telegram alert format

Trip alert:
```
ATLAS ALERT: OpenRouter tripped
3 failures in the last 5 minutes.
Manual switch command:
  python skills/switch-provider/switch_provider.py therouter --cli claude
Resume when fixed:
  python skills/switch-provider/switch_provider.py openrouter --cli claude
```

Recovery alert:
```
ATLAS: OpenRouter recovered.
Health probe passed. Resuming normal operations.
```

### Files touched

- `orchestrator/llm_helpers.py`: add `_record_failure()` and `_check_circuit()` helpers, call from `call_llm()` exception handler.
- `orchestrator/provider_probe.py`: new file, registered as heartbeat.
- DB migration: `provider_health` table creation script.
- `orchestrator/heartbeat_registry.py` (or equivalent): register `provider_probe` wake.

### Success criteria

- Simulating 3 consecutive `openai.APIError` exceptions triggers a Telegram alert within the same minute.
- `provider_health` row updates correctly on each failure and on recovery.
- `call_llm()` still raises the exception to the caller after recording it (no silent swallowing).
- Health probe successfully detects recovery and sends the recovery Telegram message.
- `provider_health` table creation is idempotent (safe to run on an already-initialized DB).

---

## Build Order

| Step | Layer | What | Est. time |
|---|---|---|---|
| 1 | A+B | `switch_provider.py` + `providers.json` + `SKILL.md` | 3h |
| 2 | C | `provider_health` DB table + migration | 30m |
| 3 | C | `llm_helpers.py` circuit breaker + Telegram alert | 2h |
| 4 | C | `provider_probe.py` health probe + heartbeat registration | 1.5h |

Total: ~7 hours across two sessions. Layer A/B ships first and is independently useful.

---

## What This Enables After Build

- **Today (Layer A/B):** `python skills/switch-provider/switch_provider.py openrouter` from any terminal. Skills can call it programmatically. No GUI needed.
- **After Layer C:** Atlas trips, you get a Telegram ping with the exact command to run. You run it on your laptop. Atlas recovers on its own when OpenRouter comes back. Zero surprise bills, zero silent failures.

---

## Explicit Non-Decisions (Deferred)

- **Auto-failover without human confirmation:** Rejected. Risk of silent cost escalation on Anthropic direct. Revisit after 30 days of Layer C telemetry.
- **Gemini CLI switching:** Deferred. OAuth flow is not API-key-based; needs separate design.
- **Multi-provider load balancing:** Out of scope. OpenRouter already does this internally across its provider network.
- **cc-switch as a dependency:** Rejected. The script we build is simpler and has no GUI dependency.
