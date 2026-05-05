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

**Geography (updated 2026-05-05 evening):** SW = full US, industry-agnostic, employees 1-50 (was Utah-only trades). CW = full US (Apollo CW_ICP_WIDENED). Studio outreach is MERGED INTO SW -- no separate Studio harvest. Studio codename now = faceless YouTube agency only (content production, no leads).

**Daily targets:** SW=50 drafts/day (35 + gap fill from CW shortfall), CW=15 drafts/day. Hormozi ramp: prove reply rate before scaling to 100/day.

**Hunter.io tier:** MUST be on paid Starter ($49/mo) or higher. Free tier (50/mo) was exhausted 2026-05-05 and produced 0 SW emails for ~24 hours. Check quota at session start when investigating "0 emails" reports: `curl -s "https://api.hunter.io/v2/account?api_key=$KEY"`.

**Apollo limitation:** `find_owner_by_company` has near-zero hit rate for local trades-SMBs (663 misses, 1 hit in one Phoenix/Vegas pass). Apollo people DB is corporate-biased. SW workhorse = Serper -> website domain extract -> Hunter domain_search.

**Calendly:** Use `calendly.com/boubacarbarry/signal-works-discovery-call`. Never `catalystworks` (404).

**Docker deploy:** Code dirs (signal_works/skills/templates/orchestrator) are volume-mounted as of 2026-05-05. Deploy = `git pull && docker compose up -d orchestrator` (~10 sec). Rebuild ONLY when `requirements.txt` changes.
