---
owner: workspace
status: active
---

# projects/ - Per-Project Working Folders

Active project work that does NOT yet fit a client engagement (`workspace/clients/`), a skill (`skills/`), a website (`output/websites/`), or an app (`output/apps/`). Inputs and intermediate artifacts.

## What lives here

| Subfolder pattern | Purpose |
| --- | --- |
| `<project-slug>/` | One folder per active project. Free-form internal structure. |
| `<project>/_build/` | Build scripts, generators, page-generators tied to that project |
| `<project>/research/` | Research artifacts specific to that project |
| `<project>/_archive/` | Per-project archive of superseded versions (separate from top-level `zzzArchive/`) |

Current active projects:

- `elevate-built-oregon/` - Rod / Elevate Roofing & Construction first SW conversion attempt (R1)

## What does NOT live here

- Client engagement folders (those go in `workspace/clients/<slug>/`)
- Catalyst Works brand work (`workspace/catalyst-works/`)
- Long-completed work (`zzzArchive/`)
- Reusable skills (`skills/`)

## Rules

- Each project subfolder needs a `README.md` stating purpose and target trigger.
- When a project ships its outcome (signed contract, deployed site, etc.), the project folder becomes a candidate for graduation: move to `workspace/clients/<slug>/` if a client relationship started, or `zzzArchive/` if it ended.
- Sandbox-style monthly sweep applies: anything untouched 60+ days surfaces for graduate-or-archive review.

## Cross-references

- Constitution: [`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md)
- Folder Governance: [`docs/AGENT_SOP.md`](../docs/AGENT_SOP.md)
- Sandbox rule (parallel pattern): [`sandbox/README.md`](../sandbox/README.md)
