# Apollo.io Lead Discovery Skill

**Description:** Agent-driven lead discovery for Catalyst Growth Engine.
**Goal:** Find 5 message-ready Utah service SMB leads per day using the Apollo.io API.

## Capabilities
- `search_utah_leads`: Find leads matching the Utah ICP (Legal, Accounting, Agency, Home Services).
- `reveal_lead_email`: Consume a credit to reveal a specific lead's email (only on explicit trigger).

## Configuration
Requires `APOLLO_API_KEY` environment variable.
The skill operates in a "Safe-Search" mode initially to preserve credits.
