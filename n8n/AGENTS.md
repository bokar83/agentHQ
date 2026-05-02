---
owner: production
status: active
---

# n8n/ - Automation Workflows

n8n workflow definitions and imports.

## What lives here

| Subfolder | Purpose |
| --- | --- |
| `imported/` | All workflow JSONs (synced from live n8n + consolidated from former `workflows/` and `n8n-workflows/` root folders on Move Day 2026-05-02) |

## Rules for LLMs working here

- **NEVER run `docker stop`, `docker restart`, or `docker cp` on the n8n container.** Use n8n UI or REST API only.
- **NEVER edit SQLite directly.** All workflow changes go through the n8n UI or `mcp__claude_ai_n8n__*` tools.
- Workflow JSON files here are exports/backups only. The live source of truth is the running n8n instance.
- To create or update a workflow: use the n8n MCP tools, then export the result here for backup.
- Per `feedback_n8n_publish_after_update.md`: n8n update creates a draft; you must call publish_workflow after.

## n8n access

n8n runs as a separate Docker service. Access via the n8n UI or the `mcp__claude_ai_n8n__*` MCP tools available in Claude Code.

## Cross-references

- Constitution: [`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md)
- Folder Governance: [`docs/AGENT_SOP.md`](../docs/AGENT_SOP.md)
- Memory: `feedback_n8n_publish_after_update.md`, `feedback_n8n_code_node_no_fetch.md`, `feedback_n8n_vps_restrictions.md`
