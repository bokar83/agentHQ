---
name: hunter-skill
description: Automates discovery, logging, and reporting of high-intent Utah leads for Catalyst Works Consulting.
---

# Hunter Skill — Catalyst Daily Prospecting

**Name:** Hunter Skill
**Description:** Automates the discovery, logging, and reporting of high-intent Utah leads for Catalyst Works Consulting.

## Capabilities

- Search across multiple niches (Law, Accounting, Creative, Trades).
- Cross-reference with PostgreSQL CRM to avoid duplicate outreach.
- Format detailed morning reports for email delivery.
- ROI-first strategic lead scoring.

## Usage (Internal for Agents)

- `harvest_daily_leads()`: Triggers the full 20-lead harvest and returns the report.
- `search_utah_leads(query)`: Finds targeted prospects in Salt Lake/Utah County.

## Deployment Target

- Runs daily on VPS at 06:00 AM MT.
- Delivers reports to `bokar83@gmail.com`, `boubacarbusiness@gmail.com`, and `catalystworks.ai@gmail.com`.
