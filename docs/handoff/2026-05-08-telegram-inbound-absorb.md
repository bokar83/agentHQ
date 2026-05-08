# Session Handoff - Telegram Inbound Router Absorb - 2026-05-08

## TL;DR

Absorbed Telegram's May 2026 Bot API update (11 features). Sankofa initially
returned ARCHIVE-AND-NOTE because agentsHQ had no inbound Telegram
infrastructure. Ran VPS diagnostic: both bot tokens support getUpdates
(inbound long-poll is live, no webhook conflict). Verdict flipped to PROCEED.
Karpathy HOLD: collapsed v1 scope to single routing branch (owner DM only).
No code written — absorb only. Next session builds the module.

---

## What was built / changed

- `docs/reviews/absorb-log.md` — appended 2026-05-08 PROCEED entry
- `docs/reviews/absorb-followups.md` — appended v1 build target (2026-05-12)

---

## Decisions made

**v1 scope = single branch only.** `orchestrator/telegram_inbound.py` polls
`getUpdates` every 5s on `ORCHESTRATOR_TELEGRAM_BOT_TOKEN`. Routes inbound DM
from `OWNER_TELEGRAM_CHAT_ID` only. No bot-to-bot, no lead-qual, no guest
@mention in v1. Those are v2+ branches, gated on v1 verification.

**Verification gate before any v2 branch:** send test DM to @agentsHQ4Bou_bot,
confirm orchestrator logs show message received + dispatched + action fired.

**Guest Queries NOT enabled yet.** Attempted 2026-05-08 — BotFather UI has no toggle and `/setguestqueries` returns "Unrecognized command". Feature announced but not rolled out. Check again ~2026-05-22.

**Bot facts confirmed:**
- ORCHESTRATOR bot: `@agentsHQ4Bou_bot` (id: 8777275362), token env var `ORCHESTRATOR_TELEGRAM_BOT_TOKEN`
- REMOAT bot: `@CatalystWorksRemoat_bot` (id: 8635131644), token env var `REMOAT_TELEGRAM_BOT_TOKEN`
- Both: `can_join_groups: True`, `supports_guest_queries: False`, no webhook registered
- Owner chat ID: `OWNER_TELEGRAM_CHAT_ID=7792432594`

---

## SUPERSEDED 2026-05-08 (same session)

**telegram_inbound.py was built, tested, and reverted.** Root cause: `handlers.py:247` already contains `telegram_polling_loop()` — a full production-grade inbound handler with `process_telegram_update()` 9-step dispatch (auth, slash commands, approvals, feedback, classify). Building a second poller on the same token would cause duplicate message consumption and missed updates.

**Actual outcome:** Inbound was already live. Built slash commands on top instead: `/sw`, `/digest`, `/publish` added to `handlers_commands.py` and verified working.

**Remaining open:**
- Guest Queries: not rolled out. Check scheduled 2026-05-10T21:27Z via routine `trig_01GfTDBcYQ3vA7T9phNwhjsE`.
- Bot-to-bot: `can_manage_bots: false` — not rolled out.
- `skills/atlas/SKILL.md` inbound surface docs: deferred, not needed since no new module shipped.

---

## Files changed this session

- `docs/reviews/absorb-log.md`
- `docs/reviews/absorb-followups.md`
- `docs/handoff/2026-05-08-telegram-inbound-absorb.md` (this file)
