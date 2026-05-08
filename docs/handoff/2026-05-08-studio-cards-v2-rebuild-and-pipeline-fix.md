# Session Handoff — Studio Cards v2 Rebuild + Pipeline Fix — 2026-05-08

## TL;DR

Two root-cause fixes. (1) All 6 studio intro/outro MP4s were mis-rendering: `<template>` wrapper on standalone comps hid content from renderer, wordmarks were positioned `bottom: 9-24%` (too low on 9:16 portrait), animation overran clip duration (tagline at 4.3s in a 4s clip), and `package.json` scripts were pinned to `hyperframes@0.4.44` while `node_modules/` had `0.5.0-alpha.15`. All 6 rebuilt as standalone comps, wordmarks vertically centered, timing compressed, re-rendered on VPS via scratch dir, deployed to `channel_cards/`. (2) Studio `production_tick` had been logging `0 qa-passed candidates queued` for days despite 11 existing in Notion — bare `from studio_production_crew import` in `scheduler.py` loaded the stale baked-image root copy instead of the volume-mounted `orchestrator/` copy. One-line fix. Both channels rendered and shipped within minutes of the fix merging.

## What was built / changed

### Studio cards v2 (VPS only — workspace/ gitignored)
- `workspace/studio-cards/compositions/*.html` — all 6 rewritten as standalone (no `<template>`, `data-composition-id` div directly in `<body>`)
- `workspace/studio-cards/channel_cards/*.mp4` — 6 v2 MP4s deployed (wordmark centered, timing fixed, HF v0.5.0-alpha.15)
- `workspace/studio-cards/channel_cards/_archive/*_v1_2026-05-07.mp4` — v1 archived
- `workspace/studio-cards/package.json` — scripts updated from `hyperframes@0.4.44` → `0.5.0-alpha.15`
- `workspace/studio-cards-test/` — scratch render dir created on VPS (HF installed, reusable)

### Code (git-tracked)
- `orchestrator/drive_publish.py` — committed (was orphan untracked since earlier session). `publish_public_file`, `update_public_file`, `ensure_public`, `audit_email_template_pdfs`. Branch `feat/drive-pdfs-public-helper` merged to main `99ab510` by Gate.
- `orchestrator/scheduler.py:613` — `from studio_production_crew import` → `from orchestrator.studio_production_crew import`. Branch `fix/studio-production-import` pushed [READY], pending Gate merge.

### Memory
- `reference_studio_cards_v2_pipeline.md` — updated with standalone render workflow, v2 composition rules, why 27s composite was abandoned
- `feedback_studio_bare_import_baked_shadow.md` — NEW: documents the bare-import shadow bug pattern, diagnosis method, fix

### Skills
- `~/.claude/skills/hyperframes/SKILL.md` — added "Studio Brand Cards" section with 6 pitfalls confirmed in production (template wrapper, bottom positioning, timing overrun, VPS-only render, exact alpha pin, per-comp standalone)

### Roadmap
- `docs/roadmap/studio.md` — session log appended

## Decisions made

- **Standalone comps forever** for Studio brand cards. Never `<template>` on a file that renders as the root index.html.
- **Vertical center, not bottom** — `top: 50%; transform: translateY(-50%)` for all wordmarks in 9:16.
- **Animation completes by clip-2s** — 4s clip → all in by 2.5s, 1.5s hold. Not negotiable.
- **Per-comp render** — one comp = one render = one MP4. The 27s composite pattern is dead.
- **`fix/studio-production-import` cherry-picked** off `feat/concierge-autonomous` to a clean branch — the M4 work on that branch wasn't ready to ship.

## What is NOT done (explicit)

- `fix/studio-production-import` not yet merged — Gate hasn't fired since push. Will merge on next Gate tick.
- Studio pipeline still starved on upstream content — 11 pre-existing candidates now draining, but trend scout + script generator need verification that new ideas are flowing post-drain.
- M4 Concierge `feat/concierge-autonomous` — missing `concierge_sweep()` tick function + `scheduler.py` heartbeat wiring. 9 commits, no [READY] yet.
- M5 Chairman `chairman_crew.py` untracked — needs `feat/chairman-learning-loop` branch.
- Stale handoff doc (>3 days) in `docs/handoff/` root — needs archive.
- `feat/concierge-autonomous` has parallel-session WIP (modified `griot.py`, `absorb-log.md`, `harvest.md`, `skills/outreach/SKILL.md`) — not mine, not committed.

## Open questions

- Does `fix/studio-production-import` merge cleanly? Gate will tell. Check `git log --oneline origin/main -3`.
- After 11 candidates drain: is trend scout producing new `idea` entries? Check Notion Studio Pipeline DB `Stage=idea` count.
- M4: ready for `concierge_sweep` + scheduler wiring? See note in conversation.

## Next session must start here

1. `git fetch origin && git log --oneline origin/main -3` — confirm `fix/studio-production-import` merged.
2. `ssh root@72.60.209.109 "docker logs orc-crewai --tail 50 2>&1 | grep -iE 'production_tick|renders done|ERROR.*production'"` — check how many of the 11 candidates processed and whether any errors hit.
3. Check Notion Studio Pipeline DB `Stage=idea` count — if 0, trend scout / script generator is starved and needs investigation.
4. M4 Concierge: add `concierge_sweep()` + `scheduler.py` heartbeat wiring to `feat/concierge-autonomous`, push [READY].
5. M5 Chairman: verify `aa56d2d` + `226b039` on main — run `python -m orchestrator.chairman_crew` dry-run on VPS.

## Files changed this session

```
orchestrator/
  drive_publish.py          (committed — was orphan untracked)
  scheduler.py              (line 613: bare import → qualified import)

workspace/studio-cards/     (gitignored — VPS only)
  package.json              (hyperframes@0.4.44 → 0.5.0-alpha.15 in scripts)
  compositions/*.html       (all 6 rewritten as standalone)
  channel_cards/*.mp4       (6 v2 MP4s, sizes 1.7-3.8MB)
  channel_cards/_archive/   (*_v1_2026-05-07.mp4 x6)

workspace/studio-cards-test/ (gitignored — scratch dir, stays on VPS)

memory/
  reference_studio_cards_v2_pipeline.md   (updated: render workflow, v2 rules)
  feedback_studio_bare_import_baked_shadow.md  (NEW)
  MEMORY.md                               (new entry added)

skills/ (global)
  ~/.claude/skills/hyperframes/SKILL.md   (Studio Brand Cards section added)

docs/
  roadmap/studio.md         (session log appended)
  handoff/2026-05-08-studio-cards-v2-rebuild-and-pipeline-fix.md  (this file)
```

## Git state at session close

| Location | Branch | HEAD |
|---|---|---|
| GitHub `main` | — | `2efb37c` (pre studio-import-fix) |
| Local | `fix/studio-production-import` | `f4bf0df` (pushed, Gate pending) |
| VPS | `main` | `2efb37c` |
| `feat/concierge-autonomous` | local+remote | `46bc7ec` (M4 in-flight, no [READY]) |
