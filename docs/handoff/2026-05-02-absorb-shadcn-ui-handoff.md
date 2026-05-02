# Handoff: shadcn-ui/ui absorbed, next absorb is another design repo

**Date:** 2026-05-02
**From session:** /agentshq-absorb https://github.com/shadcn-ui/ui
**Verdict:** PROCEED. Placement: enhance skills/ui-styling. Leverage: continuous-improvement.
**Target follow-up date:** 2026-05-09
**Commit:** `56df740` on `main`. Pushed to GitHub. VPS `/root/agentsHQ` fast-forwarded. Three-way sync verified.

## What was decided in the prior session

shadcn-ui/ui (MIT, monorepo: apps/v4 docs+registry source with 1,056 components + 27 blocks; packages/shadcn v4.6.0 CLI; last commit 2026-04-30) is the canonical shadcn substrate. Placement: **enhance skills/ui-styling**. That skill already references shadcn and has three shadcn-specific reference files (`shadcn-components.md` 424 lines, `shadcn-theming.md` 373 lines, `shadcn-accessibility.md`). They are stale (v3-era).

Re-shaped integration plan (Sankofa flagged the original priority was inverted; Karpathy SHIP with one WARN):

1. `scripts/refresh-shadcn-cache.sh` (10 lines bash, no retention or diff logic). Pulls `https://ui.shadcn.com/llms.txt` + `https://ui.shadcn.com/schema/registry.json` into `skills/ui-styling/cache/` with date-stamped filenames. **The durable mechanism. Ships first.**
2. `references/shadcn-blocks.md`. Catalogs the 27 v4 blocks with `vercel-launch`-grep-able starter tags (one line each: name | category | starter tag | description | install command).
3. Refresh + demote the three existing reference files to "scaffolding". Top of each: `Authoritative source: cache/llms-DATE.txt. Refresh via scripts/refresh-shadcn-cache.sh.`
4. One-line addition to `skills/ui-styling/SKILL.md` declaring it the canonical shadcn home so `frontend-design` + `ui-ux-pro-max` defer to it without ambiguity.
5. Followup logged in `docs/reviews/absorb-followups.md` (target 2026-05-09).

Falsifiable metric: by 2026-05-15, `git log skills/ui-styling/` shows the cache script committed + at least one shadcn block named in a `vercel-launch` deploy log. Cache-script commit alone counts if no client build happens in window.

## What shipped in this session (committed `56df740`, pushed, VPS in sync)

11 files changed, 202 insertions, 4 deletions:

- New: `skills/ui-styling/scripts/refresh-shadcn-cache.sh` (10 lines bash, Karpathy WARN-compliant)
- New: `skills/ui-styling/references/shadcn-blocks.md` (27-block starter index)
- New: `skills/ui-styling/cache/.gitkeep` (cache contents gitignored, regenerable via script)
- New: `docs/handoff/2026-05-02-absorb-shadcn-ui-handoff.md` (this file)
- Modified: `skills/ui-styling/SKILL.md` (canonical-home line)
- Modified: `skills/ui-styling/references/shadcn-components.md` (scaffolding banner only; v4.6.0 content sweep still pending 2026-05-09)
- Modified: `skills/ui-styling/references/shadcn-theming.md` (scaffolding banner only; same)
- Modified: `skills/ui-styling/references/shadcn-accessibility.md` (scaffolding banner only; same)
- Modified: `docs/reviews/absorb-log.md` (verdict appended)
- Modified: `docs/reviews/absorb-followups.md` (followup appended)
- Modified: `.gitignore` (excludes `skills/ui-styling/cache/*` except `.gitkeep`)

Sync state at handoff:

| Surface | HEAD |
| --- | --- |
| Local | `56df740` |
| GitHub `origin/main` | `56df740` |
| VPS `/root/agentsHQ` | `56df740` |

## Skills now claimed in the design space (after this absorb)

| Skill | Role | What it owns |
| --- | --- | --- |
| `ui-styling` | **Canonical shadcn home** | shadcn/ui components, Radix primitives, Tailwind utility patterns, blocks-as-starters, theme tokens, dark mode, accessibility patterns specific to shadcn |
| `ui-ux-pro-max` | UI/UX intelligence library | 50+ styles, 161 color palettes, 57 font pairings, 161 product types, 99 UX guidelines, 25 chart types across 10 stacks. References shadcn at description-level only and defers to ui-styling for shadcn specifics. |
| `frontend-design` | Production-grade frontend craft | Volta cinematic standard, banned default skeleton, business-type matching. Renders sites; calls ui-styling for shadcn. |
| `design` | Brand identity + corporate identity program | Logos (55 styles), CIP (50 deliverables), HTML presentations, banners (22 styles), icons (15 styles), social photos. |
| `design-system` | Token architecture | Three-layer tokens (primitive, semantic, component), CSS variables, spacing/typography scales, slide generation. |
| `banner-design` | Banners | Social media, ads, web heroes, print. Uses ui-ux-pro-max + frontend-design + ai-artist. |
| `web-design-guidelines` | Compliance reviewer | Reviews UI code for Web Interface Guidelines compliance (accessibility, UX best practices). |
| `design-audit` | Quality scorer | Scores HTML/PDF/slides/banners against 5-dimension Impeccable rubric. Documents only, never fixes. |

## How the next absorb should orient

**Phase 1 registry check** in the next session will surface this entry automatically:

```text
2026-05-02 | https://github.com/shadcn-ui/ui | PROCEED | enhance skills/ui-styling | continuous-improvement
```

**Phase 3 routing decision tree for any design-area artifact:**

- shadcn / Radix / Tailwind component substrate -> already covered by `ui-styling`. Don't duplicate.
- Animation / motion patterns -> check `frontend-design`, `gsap`, `hyperframes`, `3d-animation-creator` first.
- Color / palette / typography systems -> `ui-ux-pro-max` (161 palettes, 57 font pairings already indexed).
- Tokens / design-system primitives -> `design-system`.
- Brand / logo / CIP -> `design`.
- Banner / social card / ad creative -> `banner-design`.
- UX rules / accessibility checklists -> `ui-ux-pro-max` (99 guidelines) + `web-design-guidelines` (compliance reviewer) + `design-audit` (scorer).

If the next repo is a **competing component library** (Material UI, Chakra, Park UI, HeroUI, Mantine, etc.):

- Default placement: **enhance ui-styling** with a "decision matrix: shadcn vs X" reference, not a separate skill.
- Only escalate to `extend ui-styling` if the library introduces a fundamentally different distribution model (e.g., runtime npm dependency vs copy-paste).
- Only escalate to `new skill` if it serves a different stack we don't currently target (e.g., SwiftUI-only, Flutter-only).

If the next repo is a **design-token / theming framework** (Style Dictionary, Theo, Tokens Studio):

- Default placement: **enhance design-system**.

If the next repo is an **animation / motion library** (Framer Motion variants, Lottie, GSAP plugins):

- Default placement: **enhance frontend-design** or **enhance gsap** depending on ecosystem.

If the next repo is **UX / accessibility / heuristics docs**:

- Default placement: **enhance ui-ux-pro-max** (99 guidelines already there) or **enhance web-design-guidelines**.

## Open WARN from this session

Karpathy logged one WARN: **keep `refresh-shadcn-cache.sh` under 10 lines of bash. No flags, no retention policy, no diff logic on the first cut.** If the next absorb proposes a similar fetch-and-cache script, this WARN applies again. Resist the urge to abstract. (Note: the shipped script has 10 lines including one OS-detection line for Windows schannel, which is the minimum viable and within the WARN budget.)

## Sandbox state

`D:\Ai_Sandbox\agentsHQ\sandbox\.tmp\absorb-shadcn-ui-ui\` is still on disk (rm permission was denied). 8,592 files. Read-only per absorb hard rule. Safe to delete manually when ready.
