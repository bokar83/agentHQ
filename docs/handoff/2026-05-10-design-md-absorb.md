# Session Handoff — Google DESIGN.md Absorb + dream.py Fix — 2026-05-10

## TL;DR

Full absorb of Google's open-source DESIGN.md format (google-labs-code/design.md, Apache 2.0). Three phases shipped: brand routing infrastructure (INDEX.md + 6 skill read-instructions), Studio channel DESIGN.md specs for all 3 channels (palettes approved by Boubacar after HTML preview), and YAML machine-readable tokens added to CW styleguides. dream.py first run also completed after fixing 3 Windows bugs (SSL, fence strip, token ceiling). Memory consolidation applied (13 changes).

---

## What was built / changed

**Phase 1 — Brand routing:**
- `docs/styleguides/INDEX.md` — brand-to-file routing table (cw / sw / utb / 1stgen / aic slugs)
- BRAND ROUTING block added to: `skills/brand/SKILL.md`, `skills/design/SKILL.md`, `skills/design-system/SKILL.md`, `skills/frontend-design/SKILL.md`, `skills/ui-styling/SKILL.md`, `~/.claude/skills/ui-ux-pro-max/SKILL.md`

**Phase 2 — Studio channel DESIGN.md specs (palettes LOCKED):**
- `docs/styleguides/studio/under-the-baobab.DESIGN.md` — Terracotta `#C4622D` + Gold `#D4A017` + Indigo `#1B1F4A`; Fraunces + Source Serif 4; region tags mandatory
- `docs/styleguides/studio/first-generation-money.DESIGN.md` — Deep Teal `#0A7C6E` + Amber `#C97B2A` + Highlight Yellow `#FFD166`; DM Sans + DM Mono; math-on-screen signature
- `docs/styleguides/studio/ai-catalyst.DESIGN.md` — Violet `#6C63FF` + Electric Cyan `#00E5FF` + Base `#0E0E1A`; Syne + JetBrains Mono; dark mode only for video

**Phase 3 — YAML tokens:**
- `docs/styleguides/CURRENT_TYPOGRAPHY.md` — YAML front-matter: full typography token stack, retired font list, HTML import string
- `docs/styleguides/styleguide_master.md` — YAML front-matter: CW colors, spacing, rounded, components
- All 6 skill routing instructions updated: "extract YAML between --- delimiters as authoritative"
- `docs/styleguides/design.md.template` — canonical template for future brand DESIGN.md files

**dream.py fixes (`scripts/dream.py`):**
- Windows SSL bypass: `httpx.Client(verify=False)` on `sys.platform == "win32"`
- Fence strip: `.strip()` after first-line removal handles ` ```json ` tag
- `MAX_TOKENS`: 16000 → 32000 (16k caused JSON truncation at token ceiling)
- Better parse error: truncation hint when `tokens_used >= MAX_TOKENS - 100`

**dream.py run — applied:**
- 3 memory merges (4 absorb files → 1 `feedback_absorb_protocol.md`, 2 FGM files → 1, precommit stash folded in)
- 9 stale project files archived
- Gate cron contradiction fixed in MEMORY.md (was showing wrong schedule)

**Commits:** `6ec027c` (DESIGN.md Phases 1-3), `9921e96` (dream.py fixes) — both pushed to main, VPS current

---

## Decisions made

- **Option A over Option B:** Extended `docs/styleguides/` with YAML tokens rather than creating separate `docs/brand/` dir. Existing styleguides are the canonical home; Option B would have duplicated purpose.
- **Palettes are Boubacar-approved and locked.** UTB, 1stGen, AIC color + font choices approved after HTML preview 2026-05-10. Do not re-derive or propose changes without explicit re-scope.
- **YAML tokens are authoritative over prose.** When both YAML block and prose table contain the same value, YAML wins. This is now in all 6 skill routing instructions.
- **Sankofa/Karpathy corrected placement:** YAML in `design-system` skill was wrong; correct home is `docs/styleguides/` with INDEX.md as universal router. Per-project `DESIGN.md` at project root (frontend-design protocol) still takes precedence for active multi-session builds.

---

## What is NOT done (explicit)

- **Phase 3b (2026-05-24):** Wire `orchestrator/studio_production_crew.py` to read `docs/styleguides/studio/<channel_slug>.DESIGN.md` before each render job and inject brand tokens into ffmpeg/image prompts. Logged in `absorb-followups.md`.
- **SW demo build validation (2026-05-17):** Verify agent loads `docs/styleguides/INDEX.md` + correct CW brand files unprompted on next SW demo build. Success criterion logged.
- **YT analytics regex (from prior session):** `orchestrator/studio_analytics_scraper.py` TikTok working, YT `"viewCount":"(\d+)"` regex not matching — needs investigation.
- **`docs/brand/design.md.template`** orphan was deleted — only the correct copy at `docs/styleguides/design.md.template` exists.

---

## Open questions

- None blocking. Phase 3b and SW validation are scheduled, not open questions.

---

## Next session must start here

1. Read `docs/roadmap/studio.md` session log (bottom) for Phase 3b context
2. Open `orchestrator/studio_production_crew.py` — find where channel brand_config is loaded per render job
3. Add DESIGN.md path resolution: `docs/styleguides/studio/{channel_slug}.DESIGN.md` — parse YAML front-matter, inject color/font tokens into image gen prompts and ffmpeg overlay params
4. Test on VPS: run one production tick manually, confirm render uses locked palette colors
5. If time: fix YT analytics regex in `orchestrator/studio_analytics_scraper.py`

---

## Files changed this session

```
docs/styleguides/
  INDEX.md                                  (new — brand routing table)
  CURRENT_TYPOGRAPHY.md                     (YAML front-matter added)
  styleguide_master.md                      (YAML front-matter added)
  design.md.template                        (new — canonical template)
  studio/
    under-the-baobab.DESIGN.md              (new — UTB brand spec)
    first-generation-money.DESIGN.md        (new — 1stGen brand spec)
    ai-catalyst.DESIGN.md                   (new — AIC brand spec)
docs/reviews/
  absorb-log.md                             (PROCEED logged)
  absorb-followups.md                       (Phase 1-3 done marked, Phase 3b + validation deferred)
docs/roadmap/
  studio.md                                 (session log appended)
skills/
  brand/SKILL.md                            (BRAND ROUTING + YAML extraction instruction)
  design/SKILL.md                           (same)
  design-system/SKILL.md                    (same)
  frontend-design/SKILL.md                  (same, with per-project DESIGN.md precedence note)
  ui-styling/SKILL.md                       (same)
~/.claude/skills/ui-ux-pro-max/SKILL.md     (same)
scripts/dream.py                            (SSL bypass, fence strip, 32k tokens, better error)
memory/
  feedback_design_html_preview_first.md     (new)
  feedback_dream_py_windows_ssl.md          (new)
  MEMORY.md                                 (2 entries added, gate cron contradiction fixed)
```
