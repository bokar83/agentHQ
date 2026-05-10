# Session Handoff - openclaw absorb + arch patterns - 2026-05-09

## TL;DR

Absorbed `openclaw/openclaw` (370K stars, self-hosted AI assistant platform). Phase 0 all-no — full platform replacement, not a component. ARCHIVE-AND-NOTE. Deep-dive into their architecture surfaced 3 concrete patterns worth borrowing for Atlas infra. All three logged as Atlas backlog items 7/8/9. AGENT_SOP.md got a new Extension Ownership Boundary rule.

## What was built / changed

- `docs/reviews/absorb-log.md` — openclaw verdict appended
- `docs/roadmap/atlas.md` — items 7/8/9 added to default next moves; session log entry appended; cheat block updated to 2026-05-09
- `docs/AGENT_SOP.md` — Extension Ownership Boundary section added before Karpathy principles

## Decisions made

- **openclaw = ARCHIVE-AND-NOTE.** Not a component — a full competing runtime (Telegram + multi-channel + skills registry + cron). No Phase 0 leverage fires.
- **3 patterns extracted from openclaw architecture:**
  - Item 7: Prepared Runtime Facts — cache env vars/model refs/channel IDs at startup, not per-tick. Target: `orchestrator/runtime_cache.py` or extend `startup_check.py`.
  - Item 8: Docker Healthcheck Hardening — add `healthcheck`, `cap_drop: [ALL]`, `security_opt: no-new-privileges` to `orc-crewai` in `docker-compose.yml`.
  - Item 9: Manifest-First Skill Loader — pre-build skill manifest dict at startup, retire per-run `importlib` crawls in `engine.py`.
- **telegram:access dmPolicy pairing** already fully wired in plugin (`server.ts` supports `"pairing"` mode). Our `access.json` uses `"allowlist"` intentionally — correct for single-user setup.
- **AGENT_SOP Extension Ownership Boundary:** owner module fixes its own bugs; core gets generic seams. Pattern from openclaw AGENTS.md.

## What is NOT done (explicit)

- Items 7/8/9 are backlog — no trigger conditions block them but not scoped to this session. Next relevant maintenance window.
- Clawhip absorb still queued for 2026-05-15 (pre-condition for item 6 Gate context-burn fix).

## Open questions

None from this session.

## Next session must start here

1. Read `docs/roadmap/atlas.md` cheat block (updated to 2026-05-09 state).
2. Priority order unchanged from prior session: container entrypoint verify → /digest /publish test → M18 HALO instrumentation.
3. If doing any `docker-compose.yml` touch: wire Atlas item 8 (healthcheck + cap_drop) in the same commit — no standalone session needed.
4. Clawhip absorb due 2026-05-15 — run `/agentshq-absorb https://github.com/Yeachan-Heo/clawhip` when ready.

## Files changed this session

- `docs/reviews/absorb-log.md`
- `docs/roadmap/atlas.md`
- `docs/AGENT_SOP.md`
- `docs/handoff/2026-05-09-openclaw-absorb.md` (this file)
