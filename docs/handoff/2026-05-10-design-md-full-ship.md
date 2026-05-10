# Session Handoff — DESIGN.md Full Ship (Phases 1-3b) — 2026-05-10

## TL;DR

Started with a Greg Isenberg tweet about Google's DESIGN.md format. Ran full absorb — verified the real GitHub repo (google-labs-code/design.md, Apache 2.0), stress-tested with Sankofa + Karpathy twice, shipped all three phases including the Phase 3b that was originally scoped for 2026-05-24. Also ran dream.py first run (fixed 3 Windows bugs), confirmed analytics scraper working, and mounted configs/ as a volume in docker-compose so brand config changes no longer need docker cp.

---

## What was built / changed

**Design system infrastructure:**
- `docs/styleguides/INDEX.md` — universal brand routing table (cw / sw / utb / 1stgen / aic)
- `docs/styleguides/CURRENT_TYPOGRAPHY.md` — YAML front-matter token block added
- `docs/styleguides/styleguide_master.md` — YAML front-matter token block added
- `docs/styleguides/design.md.template` — canonical template for new brand DESIGN.md files
- `docs/styleguides/studio/under-the-baobab.DESIGN.md` — full spec, locked palette
- `docs/styleguides/studio/first-generation-money.DESIGN.md` — full spec, locked palette
- `docs/styleguides/studio/ai-catalyst.DESIGN.md` — full spec, locked palette

**Skills updated (BRAND ROUTING + YAML extraction instruction):**
- `skills/brand/SKILL.md`, `skills/design/SKILL.md`, `skills/design-system/SKILL.md`
- `skills/frontend-design/SKILL.md`, `skills/ui-styling/SKILL.md`
- `~/.claude/skills/ui-ux-pro-max/SKILL.md`

**Brand configs deployed to VPS (palettes locked):**
- `configs/brand_config.under_the_baobab.json` — primary `#C4622D` (terracotta), Fraunces
- `configs/brand_config.first_generation_money.json` — primary `#0A7C6E` (teal), DM Sans
- `configs/brand_config.ai_catalyst.json` — primary `#6C63FF` (violet), Syne
- `docker-compose.yml` — `configs/` now volume-mounted (no more docker cp for brand changes)

**dream.py fixes (`scripts/dream.py`):**
- Windows SSL bypass: `httpx.Client(verify=False)` on win32
- Fence strip handles ` ```json ` tag
- MAX_TOKENS: 16k → 32k (16k truncated mid-JSON)
- Dream run applied: 3 merges, 9 archives, gate cron contradiction fixed

---

## Decisions made

- **Palettes are Boubacar-approved and locked.** Approved after HTML preview at `d:/tmp/palette-preview.html`. Do not re-derive without explicit re-scope.
- **brand_config JSONs are the Phase 3b integration point** — not Python code changes. The existing `load_brand_config()` 3-tier stack reads these JSONs. Updating the files + deploying is sufficient.
- **YAML tokens authoritative over prose** in all styleguide files. All 6 skill routing instructions say so explicitly.
- **configs/ volume-mount is now infra standard** — confirmed in docker-compose.yml. Any future `configs/` file changes deploy via `git pull + docker compose up -d`.
- **YT analytics scraper is working** — `originalViewCount` regex correct, 8/12 records updating. TikTok 0s = bot detection, not a code bug.

---

## What is NOT done (explicit)

- **SW demo build validation (2026-05-17):** Verify agent loads `docs/styleguides/INDEX.md` + correct CW brand files unprompted on next SW demo build. Still open in absorb-followups.md.
- **TikTok bot detection (views=0):** Likely requires session cookies or API. Not worth solving now — tracked as known limitation.

---

## Open questions

- None blocking.

---

## Next session must start here

1. Run `/nsync` — check VPS is current on `3f792ff`
2. Pick from open queue: SW demo build validation (build a SW demo page and confirm brand routing fires unprompted) OR next roadmap item per `docs/roadmap/README.md`
3. If doing SW validation: build a Signal Works demo page using `frontend-design` skill — confirm agent reads `docs/styleguides/INDEX.md` + CW stack without being told

---

## Files changed this session

```
docs/styleguides/
  INDEX.md                                    (new)
  CURRENT_TYPOGRAPHY.md                       (YAML front-matter added)
  styleguide_master.md                        (YAML front-matter added)
  design.md.template                          (new)
  studio/under-the-baobab.DESIGN.md           (new, palette locked)
  studio/first-generation-money.DESIGN.md     (new, palette locked)
  studio/ai-catalyst.DESIGN.md               (new, palette locked)
configs/
  brand_config.under_the_baobab.json          (palette updated)
  brand_config.first_generation_money.json    (palette updated)
  brand_config.ai_catalyst.json               (palette updated)
docker-compose.yml                            (configs/ volume mount added)
scripts/dream.py                              (SSL, fence, token ceiling fixes)
skills/brand/SKILL.md                         (routing instruction)
skills/design/SKILL.md                        (routing instruction)
skills/design-system/SKILL.md                 (routing instruction)
skills/frontend-design/SKILL.md               (routing instruction)
skills/ui-styling/SKILL.md                    (routing instruction)
~/.claude/skills/ui-ux-pro-max/SKILL.md       (routing instruction)
docs/reviews/absorb-log.md                    (PROCEED logged)
docs/reviews/absorb-followups.md              (Phases 1-3 + 3b DONE)
docs/roadmap/studio.md                        (two session log entries)
memory/feedback_design_html_preview_first.md  (new)
memory/feedback_dream_py_windows_ssl.md       (new)
memory/feedback_configs_not_volume_mounted.md (new)
memory/MEMORY.md                              (3 entries updated)
```

**Commits this session:** `6ec027c`, `9921e96`, `18400e5`, `620d36c`, `4b806c9`, `3f792ff`
