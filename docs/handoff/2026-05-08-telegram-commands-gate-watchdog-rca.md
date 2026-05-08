# Session Handoff - Telegram Commands + Gate Watchdog RCA - 2026-05-08

## TL;DR

Long session: absorbed Telegram May 2026 update, built 3 Telegram slash commands (/sw, /digest, /publish), fixed baked-import precedence bug (3 RCA cycles), fixed gate watchdog deploying with orc_rebuild.sh unconditionally (now smart: docker compose up for code-only, rebuild for requirements.txt changes). Two Telegram features (bot-to-bot, Guest Queries) not yet rolled out — remote check scheduled 2026-05-10T21:27Z.

---

## What was built / changed

- `orchestrator/handlers_commands.py` — added `_cmd_sw`, `_cmd_digest`, `_cmd_publish`; registered in `_COMMANDS`
- `/app/handlers_commands.py` (baked) — synced via `docker exec cp`; was silently shadowing orchestrator/ copy
- `scripts/gate-deploy-watchdog.sh` — smart deploy: git diff requirements.txt → orc_rebuild.sh if changed, docker compose up -d if not; fetch-failure fallback
- `/usr/local/bin/gate-deploy-watchdog.sh` — synced (cron target, was stale old copy)
- `docs/roadmap/atlas.md` — session cheat block updated
- `docs/reviews/absorb-log.md` — Telegram blog PROCEED entry
- `docs/reviews/absorb-followups.md` — v1 build target 2026-05-12
- `docs/handoff/2026-05-08-telegram-inbound-absorb.md` — absorb session doc
- `docs/handoff/2026-05-08-telegram-sw-command-rca.md` — baked import RCA
- `docs/handoff/2026-05-08-orchestrator-restart-rca.md` — gate watchdog RCA
- `~/.claude/skills/rca/SKILL.md` — baked import subsystem added to triage table
- `~/.claude/skills/agentshq-absorb/SKILL.md` — implausible number check added to common mistakes

---

## Decisions made

- **Baked import rule:** After editing any handler file, always `docker exec orc-crewai cp /app/orchestrator/<file>.py /app/<file>.py` — volume mount alone is not enough. List in memory.
- **Gate watchdog:** Never call orc_rebuild.sh unconditionally. Always diff requirements.txt first.
- **Telegram bot-to-bot + Guest Queries:** Not rolled out as of 2026-05-08. `can_manage_bots: false`, `supports_guest_queries: false`. Remote check routine `trig_01GfTDBcYQ3vA7T9phNwhjsE` fires 2026-05-10T21:27Z.
- **Sankofa/Karpathy/RCA:** Invoke at first dead end, not after 3 solo attempts. Lesson reinforced this session.
- **Push back on implausible numbers:** 498h → 48h was a fat-finger. Rule: if number >10x reasonable range, confirm before acting.

---

## What is NOT done (explicit)

- `absorb-followups.md` target for telegram_inbound.py v1 = 2026-05-12 — not built yet; see prompt below
- Telegram bot-to-bot + Guest Queries pending Telegram rollout
- `skills/atlas/SKILL.md` inbound surface docs deferred until module ships

---

## Open questions

- Remote routine result 2026-05-10: will write to handoff doc, check next session
- `/digest` fires full email + Telegram output — confirm acceptable on next use

---

## Next session must start here

1. Check remote routine result at `docs/handoff/` for Telegram feature rollout (after 2026-05-10)
2. If M5 or other branches are ready for Gate — push with [READY]
3. Build `orchestrator/telegram_inbound.py` v1 (see `docs/handoff/2026-05-08-telegram-inbound-absorb.md` for full prompt)

---

## Files changed this session

- `orchestrator/handlers_commands.py`
- `scripts/gate-deploy-watchdog.sh`
- `/usr/local/bin/gate-deploy-watchdog.sh` (VPS only)
- `docs/roadmap/atlas.md`
- `docs/reviews/absorb-log.md`
- `docs/reviews/absorb-followups.md`
- `docs/handoff/2026-05-08-telegram-inbound-absorb.md`
- `docs/handoff/2026-05-08-telegram-sw-command-rca.md`
- `docs/handoff/2026-05-08-orchestrator-restart-rca.md`
- `~/.claude/skills/rca/SKILL.md`
- `~/.claude/skills/agentshq-absorb/SKILL.md`
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_baked_image_import_precedence.md`
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_invoke_skills_early_not_late.md`
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_gate_watchdog_and_schedule.md`
