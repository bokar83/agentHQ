---
name: local-crm
description: Agent-driven pipeline management for tracking Catalyst Growth Engine leads in a local PostgreSQL CRM. Triggers on "local crm", "update pipeline", "add lead to CRM", "CRM record", "pipeline status".
---

# Local CRM Skill

**Description:** Agent-driven pipeline management for Catalyst Growth Engine.
**Goal:** Track leads from discovery to paid diagnostics in a local PostgreSQL database.

## Capabilities
- `add_lead`: Add a new prospect to the CRM.
- `log_interaction`: Record outreach, replies, and notes.
- `update_lead_status`: Advance leads through the pipeline (new -> messaged -> replied -> booked -> paid).
- `get_daily_scoreboard`: Report on sales velocity.

## Configuration
Requires `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` environment variables.
