---
owner: production
status: active
---

# docs/ - Platform Documentation

All system documentation: SOPs, roadmaps, playbooks, reference, handoffs.

## What lives here

| Subfolder | Purpose |
| --- | --- |
| `AGENT_SOP.md` | Shared operating rules for ALL agents - read first every session |
| `roadmap/` | Living roadmaps for multi-session projects (atlas, harvest, studio) |
| `playbooks/` | Operational procedures (pipeline, outreach, discovery calls) |
| `reference/` | Reference documents (repo-structure, tools-access, PM library) |
| `handoff/` | Session handoff documents (superseded by roadmap system for active projects) |
| `engagements/` | Legacy location - active engagements now in `workspace/clients/` |
| `ai-governance/` | AI governance playbooks and audit reports |
| `design-references/` | Design inspiration and brand references |
| `prompts/` | Prompt templates (shared across sessions) |
| `research/` | Research findings and reports |

## What does NOT live here

- Client deliverables (those go in `workspace/clients/[slug]/deliverables/`)
- Code (that goes in `orchestrator/`)
- Skills (that go in `skills/`)

## Rules for LLMs working here

- **Read `AGENT_SOP.md` first every session** - it contains hard rules, session-start steps, and skill triggers.
- **Read the relevant roadmap** before working on any roadmapped project (atlas, harvest, studio).
- **Append session logs** to the roadmap at session end - do not create new handoff docs for roadmapped projects.
- **Never put client-specific content here** - docs/ is platform-level documentation only.
