---
name: OpenRouter burn guard defense stack
description: What was built 2026-05-03 to prevent runaway OpenRouter spend from happening again
type: feedback
---

After the $57 burn incident (2026-05-03), a 6-layer defense stack was built and committed to main.

**Layer 1: PreToolUse hook (live, local)**
File: `C:/Users/HUAWEI/.claude/hooks/check-base-url.js`
Wired in: `~/.claude/settings.json` PreToolUse
What it does: exits 2 (blocks tool call) if `ANTHROPIC_BASE_URL` is set to a non-Anthropic host. Only layer that interrupts a live session mid-burn.

**Layer 2: 5-min balance spike probe (live, VPS)**
File: `orchestrator/provider_probe.py` (`_fetch_balance()` and `_check_spike()`)
What it does: polls `/api/v1/auth/key` every 5 min, Telegrams if balance drops >$2 in one window. Two module-level floats, no new table. Runs inside the existing provider heartbeat.

**Layer 3: Pre-commit provider redirect guard**
File: `scripts/check_no_provider_redirect.py`
What it does: blocks any commit that bakes a non-Anthropic `ANTHROPIC_BASE_URL` into any JSON config.

**Layer 4: Pre-commit hook registration guard**
File: `scripts/check_hook_registration.py`
What it does: blocks any new `UserPromptSubmit` or `PreToolUse` command in settings.json that lacks `HOOK_MODEL`, `HOOK_COST_PER_FIRE`, `HOOK_FIRING_RATE` annotations.

**Layer 5: AGENT_SOP hard rule**
File: `docs/AGENT_SOP.md` (hard rules section)
What it does: documents the 4 mandatory questions + $0.10/min threshold as a design-time gate.

**Layer 6: Crew contracts C6a canary gate**
File: `orchestrator/contracts/TEMPLATE.md` Gate 2 C6a
What it does: requires one supervised $0.50-cap run confirming actual cost/tick and firing rate before the 7-day dry-run window starts.

**How to apply:** If OpenRouter balance is draining unexpectedly, check in order: (1) is `ANTHROPIC_BASE_URL` set? (2) is the VPS probe firing? (3) which app_name in the OpenRouter activity CSV is driving spend? Claude Code local sessions show as app_name="Claude Code". VPS crews show as "agentsHQ".
