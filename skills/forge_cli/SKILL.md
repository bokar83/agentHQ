---
name: forge-cli
description: Core Notion client + Forge KPI/page-builder. Agent-internal only -- not Boubacar-invoked. notion_client.py (NotionClient) imported by atlas_dashboard, crews, griot, content_board_reorder, handlers, auto_publisher. DO NOT archive.
---

# Forge CLI (Agent-Internal)

Production code module. Not a Boubacar-invoked skill.

- `notion_client.py` -- NotionClient class. Imported by 15+ orchestrator files (atlas_dashboard, crews, griot, content_board_reorder, handlers_approvals, handlers_commands, auto_publisher, griot_scheduler).
- `forge.py` -- KPI refresh. Imported by crews.py.
- `databases.py`, `page_builder.py`, `kpi.py` -- Forge/Notion database helpers.

**DO NOT archive.** These files are active production imports.
