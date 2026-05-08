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

## What is NOT done (explicit)

- `orchestrator/telegram_inbound.py` not written yet
- Poll tick not wired into main.py / scheduler
- Guest Queries not enabled on either bot
- Bot-to-bot coordination branch not built
- SW lead qualification branch not built
- `skills/atlas/SKILL.md` not updated (deferred until module ships)

---

## Open questions

- Where in orchestrator scheduler does the poll tick live? Check `orchestrator/main.py`
  and existing tick pattern (e.g., `griot_morning_tick`) before writing new module.
- What action fires on owner DM in v1? Simplest: log to container stdout + echo
  via notifier back to Boubacar (loopback confirm). Define before coding.

---

## Next session must start here

1. Read `orchestrator/main.py` and one existing tick (e.g., `griot_morning_tick`)
   to understand the scheduler pattern.
2. Write `orchestrator/telegram_inbound.py` — single branch: poll getUpdates,
   filter for `chat_id == OWNER_TELEGRAM_CHAT_ID`, log + echo back via notifier.
3. Register poll tick in scheduler (same pattern as existing ticks).
4. Deploy: `git pull && docker compose up -d orchestrator` on VPS.
5. Verify: DM @agentsHQ4Bou_bot → confirm logs + loopback message received.
6. If verified: update `skills/atlas/SKILL.md` with inbound surface docs.
7. Only after v1 verified: open BotFather and enable Guest Queries.

---

## Files changed this session

- `docs/reviews/absorb-log.md`
- `docs/reviews/absorb-followups.md`
- `docs/handoff/2026-05-08-telegram-inbound-absorb.md` (this file)
