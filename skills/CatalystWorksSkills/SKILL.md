---
name: catalyst-works-skills
description: Index for Catalyst Works practice-specific skills — agent-teams, news, sheet-mint, and sheet-mint-workspace. Use when the user asks about CW-internal skill packs, sheet-mint operations, the news scraper, or agent-teams composition. Each child is a real skill with its own SKILL.md. Triggers on "catalyst works skills", "CW skills", "sheet-mint", "agent teams", "CW news", "list CW skills".
---

# Catalyst Works Skills Index

This is an index folder for Catalyst Works (CW) practice skills. Each child is a real, independently-invocable skill with its own SKILL.md.

## Sub-skills

| Path | Purpose |
|------|---------|
| `agent-teams/` | Composition patterns for spawning multi-agent teams in CrewAI for CW client engagements |
| `news/` | News-source scraping + summary skill for CW client briefings and content board sourcing |
| `sheet-mint/` | Spreadsheet generation skill — has its own `evals/` and `references/` |
| `sheet-mint-workspace/` | Workspace artifacts from sheet-mint runs (iteration-1, etc.) — NOT a skill, scratch space |

## Procedure

When asked about a CW-specific skill:

1. Identify the requested child by name (agent-teams, news, sheet-mint)
2. Open the child folder and read its SKILL.md
3. Follow the child's procedure
4. `sheet-mint-workspace/` is workspace, not a skill — do not invoke its contents directly

## Output Contract

This skill is a routing index. Returns the path to the requested child skill. The downstream skill produces the actual artifact.

## Failure Modes

- Treating `sheet-mint-workspace/` as a callable skill. It's the output sink for sheet-mint runs.
- Authoring a new top-level skill inside `CatalystWorksSkills/` when it should live as a top-level entry under `skills/`. CW-specific skills live here only when they are tightly coupled to CW practice flows; cross-practice skills go top-level.
