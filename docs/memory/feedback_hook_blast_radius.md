---
name: Hook blast radius rule
description: Never wire UserPromptSubmit or PreToolUse hook that calls LLM or rewrites global config without answering 4 canary questions first
type: feedback
---

Before registering any Claude Code hook on `UserPromptSubmit`, `PreToolUse`, or any per-message/per-tool event that makes an LLM call or writes to `~/.claude/settings.json` or any global config, answer all four questions in writing:

1. Which model, and what is the max context size it will see at realistic session length (not toy session)?
2. What is the cost per firing at that context (prompt_tokens x model_rate_per_token)?
3. What is the worst-case firing rate (calls/min if it loops or fires every message)?
4. Does a kill switch exist that stops it without restarting the process?

If (answer 2) x (answer 3) exceeds $0.10/min, do NOT register the hook.

**Why:** 2026-05-03 incident: a `UserPromptSubmit` hook (`classify_task.py`) rewrote `ANTHROPIC_BASE_URL` on every message, routing all Claude Code traffic to OpenRouter. Session context snowballed from 16k to 344k tokens. 363 calls at Sonnet 4.6 pricing = $57.45 in 3 hours. No kill switch existed. Topping up the balance mid-session made it worse. The hook had answer 2 = ~$0.09/call at 300k tokens, answer 3 = every message. Product of those two numbers is catastrophic.

**How to apply:** When asked to build any hook: stop, write out the 4 answers, do the math, refuse to wire if rate exceeds $0.10/min. Offer a manual slash command or shell alias as the safe alternative. Pre-commit hook `scripts/check_hook_registration.py` now enforces annotation at commit time. VPS crew version lives in `orchestrator/contracts/TEMPLATE.md` C6a.
