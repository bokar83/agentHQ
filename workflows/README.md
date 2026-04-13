# agentsHQ — Workflows Guidebook

The `workflows/` directory contains automated sequences and integration logic that connect agentsHQ to external triggers and archival systems.

## Current Infrastructure

This directory primarily houses our **n8n orchestration files**. n8n acts as the "connective tissue" for agentsHQ, handling:
- **Telegram Ingest:** Webhook listeners for the @agentsHQ_bot.
- **Archival:** The "Always-Save" workflow that syncs every output to GitHub, Google Drive, and Notion.
- **Reporting:** Daily scheduled jobs for News Briefs and Hunter leads.

## File Map

| File | Purpose |
| :--- | :--- |
| `workflow-daily-news-brief.json` | Schedule and formatting for the daily Telegram brief. |
| `workflow-SUB-always-save.json` | Persistent storage sub-process (GitHub, Drive, Notion). |

## Strategy: Toward a Unified Workflow Layer

While currently centered on n8n JSON exports for **Telegram** and **Archival**, the `workflows/` directory is being evolved to support:
1. **Python Workflows:** Native code-based sequences using `Task` and `Crew` definitions.
2. **Cron Jobs:** Scheduled scripts located in `orchestrator/scheduler.py`.
3. **Trigger Logic:** Real-time routing from Telegram and webhooks.

## Legacy & Archived

The `workflows/legacy/` directory contains older or experimental integrations:
- `workflow-whatsapp-v6.json`: Legacy Twilio/WhatsApp integration (obsolete).

## Deployment Note

To update a workflow, import the corresponding `.json` file into the n8n dashboard:
[https://n8n.srv1040886.hstgr.cloud](https://n8n.srv1040886.hstgr.cloud)
