# Handoff: 2026-05-03 Burn Guard RCA

**Date:** 2026-05-03
**Session type:** Incident investigation + hardening
**Branch:** main (all shipped)

---

## What burned and why

The night before this session, a `UserPromptSubmit` hook (`classify_task.py`) was still live
from the switch-provider experiment (reverted 2026-05-02). The hook rewrote
`ANTHROPIC_BASE_URL` in `~/.claude/settings.json` on every user message, silently routing every
Claude Code API call through OpenRouter. Boubacar topped up his OpenRouter balance while the
redirect was still live. Over roughly 3 hours, 363 API calls at Sonnet 4.6 pricing accumulated
across a session whose context had snowballed from 16k to 344k tokens, producing a $57.45
charge on that account ($62.12 total on 2026-05-03 UTC across 914 calls per the second CSV).
Every call completed with a valid stop or tool_calls finish reason, so there is no refund case.
Root cause: the hook had no kill switch, no firing-rate annotation, no context-size guard, and
no balance alerting layer to catch it mid-run.

---

## What was built

**Commit 6002ff8: feat(burn-guard): spike detection + provider redirect guards**

- `orchestrator/provider_probe.py`: extended the existing 5-min heartbeat with `_fetch_balance()` and `_check_spike()`. Fires a Telegram alert if the OpenRouter balance drops more than $2 in one probe window. No new table or new heartbeat.
- `C:/Users/HUAWEI/.claude/hooks/check-base-url.js`: PreToolUse hook that blocks every tool call when `ANTHROPIC_BASE_URL` is set to a non-Anthropic host. The only layer that can interrupt a live Claude Code session.
- `scripts/check_no_provider_redirect.py`: pre-commit script that fails any commit baking a non-Anthropic `ANTHROPIC_BASE_URL` into a JSON config file.
- `.pre-commit-config.yaml`: wired the above script into the pre-commit hook chain.

**Commit 7592575: feat(burn-guard): hook registration guard + canary gate + SOP checklist**

- `scripts/check_hook_registration.py`: pre-commit that blocks any new `UserPromptSubmit` or `PreToolUse` command entry in `settings.json` that lacks the three mandatory annotations: `HOOK_MODEL`, `HOOK_COST_PER_FIRE`, `HOOK_FIRING_RATE`.
- `.pre-commit-config.yaml`: wired the above.
- `orchestrator/contracts/TEMPLATE.md`: added C6a canary gate (supervised $0.50-cap run before the 7-day dry-run window).
- `docs/AGENT_SOP.md`: new hard rule with four mandatory questions that must be answered in writing before any LLM-calling hook is registered.

**Plugins installed this session (token reduction):**

- caveman plugin: UserPromptSubmit hook (`caveman-mode-tracker.js`) active.
- context-mode plugin: SessionStart hook (`context-mode-cache-heal.mjs`) active.

---

## Defense stack summary

| Layer | When fires | What it catches |
|---|---|---|
| `check-base-url.js` PreToolUse hook | Every tool call, live session | Blocks all tool use if `ANTHROPIC_BASE_URL` points to a non-Anthropic host |
| `provider_probe.py` spike check | Every 5-min heartbeat | Fires Telegram if OpenRouter balance drops more than $2 in one probe window |
| `_probe_openrouter_credits` health sweep | Daily sweep | Fires Telegram if OpenRouter balance falls below $5 |
| `check_no_provider_redirect.py` pre-commit | Every `git commit` | Blocks commits that bake a non-Anthropic `ANTHROPIC_BASE_URL` into JSON config |
| `check_hook_registration.py` pre-commit | Every `git commit` | Blocks new per-message hooks that lack cost and firing-rate annotations |
| AGENT_SOP hard rule (4-question checklist) | Session-start enforcement | Forces (a) context size, (b) cost per firing, (c) worst-case firing rate, (d) kill switch check before any hook is wired |
| C6a canary gate (contracts/TEMPLATE.md) | Crew onboarding | Requires supervised $0.50-cap test run before 7-day dry-run for any new crew |

---

## What is NOT done yet

The Atlas live spend card on the Mission Control dashboard currently shows only the `llm_calls`
ledger (Anthropic SDK calls, lower bound) with a stale-indicator tooltip. A real-time OpenRouter
balance sparkline that makes the burn rate visible without opening a browser tab has not been
built. Spike detection via `provider_probe.py` is the interim solution: it alerts within 5
minutes of a large drawdown but does not provide a visual trend or running daily total on the
dashboard surface.

---

## Next session

Wire the OpenRouter balance feed from `GET https://openrouter.ai/api/v1/credits` into the Atlas
dashboard frontend. The backend polling already exists in `health_sweep.py`
(`_probe_openrouter_credits`). The work is:

1. Expose the latest credit balance as a `/atlas/openrouter-balance` JSON endpoint in `app.py`.
2. Add a balance tile (current balance + 7-day sparkline from `provider_billing` table, M13
   scope) to the hero strip on `atlas.html` / `atlas.js`.
3. This is the M13 milestone already logged in `docs/roadmap/atlas.md`. Target: 2026-05-07.
