# RCA: enrichment pipeline — 2026-05-07

**Root cause:** Hunter.io `domain_search` (paid, 2000/mo) was never called from `enrich_missing_emails`. Pipeline stopped at Prospeo (low SMB coverage). Separately, `discover_leads` Step 4 extracted domain from `linkedin_url` field, producing garbage emails (thom@google.com, jefferynelson@instagram.com) when the field contained non-LinkedIn URLs.

**Fix applied:**
- `skills/email_enrichment/enrichment_tool.py:542` — added Hunter `domain_search` as step 2b (after scrape, before Prospeo). Uses website domain from step 1.
- `skills/email_enrichment/enrichment_tool.py:571` — removed priority gate on Prospeo phone capture; now always tries `want_phone=True`
- `skills/serper_skill/hunter_tool.py:591` — replaced bad `elif` that extracted domain from `linkedin_url` with `_serper_find_company_domain(lead["company"])` to get actual business domain
- `orchestrator/scheduler.py:218` — updated task_request from "Utah" to full US ICP (ICP was widened 2026-05-05, prompt never updated)

**Success criterion verified:**
`docker exec orc-crewai python3 -c "from skills.email_enrichment.enrichment_tool import enrich_missing_emails; r=enrich_missing_emails(limit=10); print(r['emails_found'])"` → `4` (was 0/50 before fix)

**Never-again rule:** Any paid email tool (Hunter, Apollo, Prospeo) added to the stack MUST be wired into BOTH the harvest path (`topup_leads._resolve_email`) AND the enrichment path (`enrich_missing_emails._enrich_one`). Audit both paths when investigating 0-email reports.

**Memory update:** yes — feedback_enrichment_hunter_not_wired.md
