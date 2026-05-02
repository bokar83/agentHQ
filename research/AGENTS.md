---
owner: workspace
status: active / gitignored
---

# research/ - Cross-Project Research Notes

Research artifacts that are not yet (or never will be) tied to a specific project, client, or skill. Gitignored.

## What lives here

Free-form research output: markdown notes, scraped data summaries, comparison studies, exploratory analysis. Single source of truth for "thinking about X" content.

## What does NOT live here

- Project-specific research (those go in `projects/<project>/research/`)
- Client-specific research (those go in `workspace/clients/<slug>/research/`)
- Reference docs that other agents need to read (those go in `docs/reference/`)
- Final deliverables (those go in `deliverables/`)

## Rules

- Gitignored. Local-only by design (per `.gitignore` line 121).
- If a research note becomes load-bearing for any active code or skill, graduate it to `docs/reference/` and update the relevant memory entry.
- Monthly sweep: untouched 60+ days = graduate or archive to `zzzArchive/`.

## Cross-references

- Constitution: [`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md)
- Folder Governance: [`docs/AGENT_SOP.md`](../docs/AGENT_SOP.md)
- Reference docs (the graduation target): [`docs/reference/`](../docs/reference/)
