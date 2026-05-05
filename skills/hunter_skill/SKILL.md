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

## HARD RULES (added 2026-05-05)

**Niche resolution:** Never use `lead.get("niche", "small business")` in email templates.
Apollo leads have `industry` not `niche`. Use `_resolve_niche(lead)` from
`templates/email/sw_t1.py` which maps industry -> human label via `_INDUSTRY_TO_NICHE`.
Fallback to generic hook (no ChatGPT prompt) when niche cannot be resolved.

**Geography:** SW = Utah-only trades (Serper+Firecrawl). CW = full US (Apollo CW_ICP_WIDENED).
Studio = full US+Canada (STUDIO_ICP + STUDIO_ICP_TARGETED alternating daily).

**Daily targets (2026-05-05):** SW=35 drafts, CW=15 drafts, gap fill to 50 total, Studio=15 bonus.

**Calendly:** Use `calendly.com/boubacarbarry/signal-works-discovery-call`. Never `catalystworks` (404).

**Docker deploy:** Code dirs (signal_works/skills/templates/orchestrator) are volume-mounted as of 2026-05-05. Deploy = `git pull && docker compose up -d orchestrator` (~10 sec). Rebuild ONLY when `requirements.txt` changes.
