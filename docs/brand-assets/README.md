# Brand Assets — agentsHQ Canonical Hub

All Boubacar brand visual assets live here. One folder per brand. Each folder gets logo files + README documenting design system.

## Status (2026-05-16)

| Brand | Folder | Logo state | Files | Notes |
|---|---|---|---|---|
| Human at Work | `humanatwork-ai/` | ✅ NEW SVG system v1 | 3 SVG + preview + README | Designed 2026-05-16 for LS store launch |
| Catalyst Works | `catalyst-works/` | ✅ Imported existing | `logo-original.jpg` (52K) + `logo-mark.svg` (CW symbol mark, 384B) | Source: `D:/Ai_Sandbox/CatalystWorks_logo.jpg` + `thepopebot/chat-ui/cw-mark.svg` |
| HR Exposed | `hrexposed-net/` | ✅ Imported existing | `logo-v1.png` (15K) + `logo-v2.png` (15K) | Source: LLM_Chat_Archive 2026-03-17 |
| Studio: AI Catalyst | `studio-ai-catalyst/` | ✅ Migrated | `logo.png` (765K) + `logo-nobg.png` (811K) | Migrated from `docs/roadmap/studio/brand/logos/` (2026-05-03) |
| Studio: 1stGen Money | `studio-1stgen-money/` | ✅ Migrated | `logo.png` (665K) + `logo-nobg.png` (685K) | Migrated from `docs/roadmap/studio/brand/logos/` |
| Studio: Under the Baobab | `studio-baobab/` | ✅ Migrated | `logo.png` (866K) + `logo-nobg.png` (943K) + `logo-original.jpg` | Migrated from `docs/roadmap/studio/brand/logos/` |
| Yatilocs | `yatilocs/` | ✅ Imported existing | `logo.svg` (310B) + `logo-large.png` (2.1M) | Boubacar client/personal site asset |
| Signal Works | (missing) | ❌ Not yet created | — | TODO: generate v1 when greenlit |
| 1stGen Money (primary brand, not Studio variant) | (missing) | ❌ Not yet created | — | TODO: generate v1 when greenlit. Studio variant is faceless-channel branding. |
| geolisted.co | (missing) | ❌ Not yet created | — | TODO: generate v1 when greenlit |
| agentsHQ (parent) | (missing) | ❌ Not yet created | — | TODO: generate v1 when greenlit |

## Brand-mark rules (universal, per `feedback_no_draft_or_letter_brand_marks`)

- **NEVER** use a single-letter brand-mark block (no `[H]` / `[CW]` / `[1G]` boxes next to wordmarks). Banned.
- **NEVER** ship pages with "DRAFT" / "PLACEHOLDER" / "WIP" badges on production.
- Wordmark + accent OR actual designed mark. Letter blocks signal amateur placeholder.

## File-naming convention (apply going forward)

| Filename | Purpose |
|---|---|
| `logo-horizontal.svg` | Primary wordmark, web nav + email signatures |
| `logo-square.svg` | Stacked, social profiles + store avatars |
| `logo-favicon.svg` | Symbol-only, 64×64 favicon |
| `logo-mark.svg` | Symbol-only without wordmark (alt to favicon for larger sizes) |
| `logo.png` (or `logo-original.jpg`) | Imported existing asset, source-of-truth backup |
| `logo-nobg.png` | Transparent-background variant for placement |
| `logo-preview.html` | Live preview of all variants |
| `README.md` | Brand spec: typography, palette, accent, rules |

## Brand-status legend

- ✅ **Imported existing** — file existed in another location, copied to canonical here
- ✅ **Migrated** — file existed in older agentsHQ subfolder pattern, moved to canonical here
- ✅ **NEW SVG system** — designed fresh in canonical Conakry-clay / brand-specific palette
- ❌ **Missing** — no logo exists yet, queued for generation

## Originals preserved

Per `feedback_no_delete_archive_instead` memory: originals NOT deleted from source locations. Files copied (not moved) to preserve them in case of corruption or rollback need:

- `D:/Ai_Sandbox/CatalystWorks_logo.jpg` — left in place
- `D:/Ai_Sandbox/agentsHQ/docs/roadmap/studio/brand/logos/*` — left in place
- `D:/Ai_Sandbox/yatilocs-site/*` — left in place
- `D:/Ai_Sandbox/LLM_Chat_Archive/...` — left in place

## Cross-references

- `feedback_no_draft_or_letter_brand_marks.md` — universal brand-mark rule
- `feedback_always_local_path_first.md` — always give local paths first
- `feedback_studio_brand_design_rules.md` — Studio-specific brand rules
- `docs/styleguides/` — brand voice + writing rules (separate from visual assets)
- `docs/styleguides/studio/*.DESIGN.md` — Studio per-channel design docs

## Next steps

1. Generate missing logos: Signal Works / 1stGen Money primary / geolisted.co / agentsHQ — pending Boubacar approval on brand direction per
2. Audit existing imported logos: do CW + hrExposed + Studio + Yatilocs still represent the current brand vision? Boubacar review pending.
3. Expand Conakry-clay system to other brands OR define brand-specific palettes for CW / SW / 1stGen / hrexposed / geolisted / agentsHQ.
