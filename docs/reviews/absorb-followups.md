# Absorb Follow-ups (PROCEED tracker)

Schema: `YYYY-MM-DD | placement | leverage type | next action | target date`

PROCEED verdicts append here automatically. PROCEED without a follow-up entry is incomplete.

---
2026-05-02 | new tool (scripts/markitdown_helper.py) | continuous-improvement | pip install markitdown, write wrapper, validate on 3 real artifacts | 2026-05-09
2026-05-02 | enhance skills/ui-styling | continuous-improvement | (1) write scripts/refresh-shadcn-cache.sh that pulls https://ui.shadcn.com/llms.txt + apps/v4/registry.json into skills/ui-styling/cache/ date-stamped; (2) add references/shadcn-blocks.md with vercel-launch-grep-able starter tags for the 27 v4 blocks; (3) refresh + demote shadcn-components.md / shadcn-theming.md / shadcn-accessibility.md to point at cache as authoritative; (4) add canonical-home line to skills/ui-styling/SKILL.md | 2026-05-09
2026-05-02 | enhance skills/ui-styling + skills/design-audit + skills/seo-strategy | continuous-improvement | awesome-shadcn-ui curation (5 surgical picks): (1) tweakcn theme generator appended to ui-styling/references/shadcn-theming.md + pointer in clone-builder; (2) new ui-styling/references/shadcn-agent-ui.md (21st.dev Agent Elements) + pointer in frontend-design; (3) new ui-styling/references/shadcn-pdf.md (pdfx lane) + routing row in skills/design + pointer in frontend-design; (4) design-audit Mode 4 (memoire-backed token-drift extraction). Note: lives in ~/.claude/skills/design-audit/, OUTSIDE agentsHQ repo, won't sync via nsync; (5) seo-strategy Mode 2 revenue-weighted prioritization rule (auditzap framing). Verify by 2026-05-15: at least one citation across the 5 edits in a real build/audit; if zero citations, kill the unused refs. | 2026-05-15
