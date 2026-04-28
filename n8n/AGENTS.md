---
owner: production
status: active
---

# n8n/ - Automation Workflows

n8n workflow definitions and imports.

## What lives here

| Subfolder | Purpose |
| --- | --- |
| `imported/` | Workflows synced from the live n8n instance |
| `workflows/` | Workflow exports and drafts (consolidated from former `n8n-workflows/` root folder) |

## Rules for LLMs working here

- **NEVER run `docker stop`, `docker restart`, or `docker cp` on the n8n container.** Use n8n UI or REST API only.
- **NEVER edit SQLite directly.** All workflow changes go through the n8n UI or `mcp__claude_ai_n8n__*` tools.
- Workflow JSON files here are exports/backups only - the live source of truth is the running n8n instance.
- To create or update a workflow: use the n8n MCP tools, then export the result here for backup.

## n8n access

n8n runs as a separate Docker service. Access via the n8n UI or the `mcp__claude_ai_n8n__*` MCP tools available in Claude Code.
