---
owner: production
status: active
---

# sql/ - SQL Schema Snapshots and Queries

SQL files for inspection, schema reference, and ad-hoc queries. Distinct from `migrations/` (forward-only migration scripts) and from root `setup-database.sql` (the live docker-compose mount).

## What lives here

Reference SQL files. Query templates. Schema snapshots that document state without applying changes.

## What does NOT live here

- Forward-only DB migrations (those go in `migrations/`)
- The live Postgres init mount (that's `setup-database.sql` at repo root, mounted by `docker-compose.yml:32`)
- Application code that constructs SQL (`orchestrator/`)

## Rules

- Files here are reference only; they are not auto-applied to the live DB.
- If a SQL change needs to apply to production, it goes in `migrations/<NNN>_*.sql` and gets run by the migration runner.
- Per `feedback_db_split.md`: internal data lives in local Postgres (orc-postgres container); external/customer data lives in Supabase. Files here may target either; label clearly.

## Cross-references

- Constitution: [`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md)
- Folder Governance: [`docs/AGENT_SOP.md`](../docs/AGENT_SOP.md)
- Live mount: `setup-database.sql` (root) per `docker-compose.yml:32`
- Migrations: [`migrations/`](../migrations/)
- Memory: `feedback_db_split.md`
