---
name: hunter-skill
description: Automates discovery, logging, and reporting of high-intent Utah leads for Catalyst Works Consulting. Triggers on "hunter", "run hunter", "prospect Utah", "daily prospecting", "find contacts", "hunter leads".
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

**Apollo limitation:** `find_owner_by_company` had near-zero hit rate (663 misses, 1 hit) until 2026-05-07 fix. Root cause: was sending `q_organization_name` to `mixed_people/api_search` which Apollo silently ignores (param only valid on Organization Search endpoint). Fixed via two-step pattern: `mixed_companies/search` → `organization_ids[]` → `mixed_people/api_search`. Hit rate now 25-50% on Apollo-known orgs. Apollo people DB still corporate-biased — SW workhorse remains Serper Maps → website domain → Hunter domain_search.

**Hunter domain_search (rewritten 2026-05-07):** 3-tier server-side filter cascade is the right pattern. T1: `type=personal + seniority=executive + department=executive` (confidence ≥80). T2: senior fallback. T3: any deliverable ≥60. Each tier costs 1 credit but only fires on miss. Live test: 7/8 hit rate on real SMB domains (vs ~12% before). Filtering client-side after `limit=10` wastes credits and returns generic role mailboxes (info@, sales@) instead of owner emails.

**Wire paid tools to BOTH harvest + enrichment paths.** 2026-05-07 incident: Hunter Starter ($49/mo) was wired in `topup_leads.py` but never called from `enrich_missing_emails`. Result: 0/50 emails despite paid plan. Lesson: when adding any paid email finder, audit BOTH `signal_works/topup_leads.py:_resolve_email()` AND `skills/email_enrichment/enrichment_tool.py:enrich_missing_emails()`. If one is missing the tool, wire it.

**Daily target = 50 emails (locked 2026-05-07):** SW=35 + CW=15 = 50 verified emails/day floor. `signal_works/harvest_until_target.py` runs SW + CW topups in retry-until-target loop with stall detection. Phone-only / website-only leads still saved with `email_source` flag (`phone_only` / `website_only` / `phone_and_website`) but excluded from 50-count. Hunter daily cap raised 200 → 400 to support volume.

**topup_cw_leads.force_fresh (added 2026-05-08):** `topup_cw_leads` early-exits when `_count_ready_cw_leads(conn) >= minimum`. This starves daily CW injection when undrafted residue accumulates (e.g., 41 existing leads → CW skipped → harvest stalls at 31/50). Fix: `force_fresh=True` bypasses the short-circuit. `harvest_until_target._run_cw_until` passes `force_fresh=True`. Default `force_fresh=False` preserves existing callers. Merged commit `2efb37c`. Validated: CW 0/15 → 15/15 same day.

**Harvest run via docker exec -d (2026-05-08):** SW harvest takes 8-12 min. Running synchronously via `docker exec orc-crewai bash -c '...'` over SSH times out at ~3 min (exit 137 = exec session killed, NOT OOM). Use detached exec for any harvest run expected >2 min:
```bash
ssh root@72.60.209.109 "docker exec -d orc-crewai bash -c 'cd /app && python -m signal_works.harvest_until_target --target 50 --sw-target 35 --cw-target 15 >> /tmp/harvest.log 2>&1'"
# Monitor: docker exec orc-crewai tail -20 /tmp/harvest.log
# Or watch Telegram for ✅ Daily harvest complete
```

**Calendly:** Use `calendly.com/boubacarbarry/signal-works-discovery-call`. Never `catalystworks` (404).

**Docker deploy:** Code dirs (signal_works/skills/templates/orchestrator) are volume-mounted as of 2026-05-05. Deploy = `git pull && docker compose up -d orchestrator` (~10 sec). Rebuild ONLY when `requirements.txt` changes.
