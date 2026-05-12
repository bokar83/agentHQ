---
owner: production
status: active
---

# skills/ - The Skill Library

**Standing rules:** read `docs/RULES.md` before any task. Apply at every action boundary. (2026-05-11 — RCA fix Layer 2.)

71 skills. One folder per skill. Flat structure by design.

## What lives here

Every Claude Code skill available to Boubacar and to agents. Each skill folder contains a `SKILL.md` (required) and optional implementation files.

## What does NOT live here

- Python tools imported by orchestrator (those are in `orchestrator/tools.py`)
- Client work or deliverables
- Workflow definitions (those go in `n8n/`)

## Rules for LLMs working here

- **Create here first**, then copy to `~/.claude/skills/[name]/`. Never create skills only in the global folder.
- **Every skill folder requires `SKILL.md`** with frontmatter: `name`, `description`, `type` (or trigger).
- **After creating a skill**, add one row to `skills/_index.md`.
- **Naming convention**: kebab-case for multi-word skills (`cold-outreach`), snake_case for legacy skills (`apollo_skill`). New skills use kebab-case.
- **The `skills/` folder is invisible to the Python runtime.** Nothing here is auto-loaded. Skills are Claude Code tools only unless explicitly imported in `orchestrator/tools.py`.

## Finding the right skill fast

Read `skills/_index.md` first. It is a one-file routing table for all 71 skills. Do not read individual SKILL.md files until you have identified the target skill from the index.

## Categories (for _index.md routing)

`quality` | `council` | `revenue` | `media` | `research` | `ops` | `engineering` | `content` | `design` | `data`

## Cross-references

- Constitution: [`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md)
- Folder Governance: [`docs/AGENT_SOP.md`](../docs/AGENT_SOP.md)
