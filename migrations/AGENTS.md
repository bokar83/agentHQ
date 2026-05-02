---
owner: production
status: active
---

# migrations/ - Database Migration Files

Forward-only DB migration scripts for the orchestrator's Postgres schema.

## What lives here

Numbered SQL or Python migration files that build on each other in order. The current orchestrator schema is the result of all migrations applied in sequence.

## What does NOT live here

- Schema snapshots (those go in `sql/` or `docs/database/`)
- One-time bootstrap scripts (those go in `scripts/` or `zzzArchive/_pre-cleanup-*/server-setup/`)
- Application code (`orchestrator/`)

## Rules

- Migrations are forward-only. Never edit a migration that has been applied to production. Add a new migration that corrects the prior one.
- Number migrations sequentially (`001_`, `002_`, etc.). The number IS the apply order.
- Reference the migration number in handoff docs and roadmap entries when shipping schema changes.

## Cross-references

- Constitution: [`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md)
- Folder Governance: [`docs/AGENT_SOP.md`](../docs/AGENT_SOP.md)
- Schema reference: `docs/database/schema_v2.sql`
