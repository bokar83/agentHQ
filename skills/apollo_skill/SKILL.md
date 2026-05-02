# Apollo.io Lead Discovery Skill

**Description:** Agent-driven lead discovery for Catalyst Growth Engine.
**Goal:** Find 5+ message-ready Utah service SMB leads per day using the Apollo.io API.

## Capabilities
- `search_utah_leads`: Find leads matching the Utah ICP (Legal, Accounting, Agency, Home Services).
- `reveal_lead_email`: Consume a credit to reveal a specific lead's email (only on explicit trigger).
- `find_owner_by_company`: Look up an owner/decision-maker by company name (used by Signal Works after Google Maps detects no-website businesses).

## Configuration
Requires `APOLLO_API_KEY` environment variable.
The skill operates in a "Safe-Search" mode initially to preserve credits.

---

## HARD RULES

### 1. Company-name lookup: use mixed_people/api_search

For looking up a person by company name (no domain), use `POST mixed_people/api_search` with `q_organization_name`. **Do NOT use `organizations/enrich` + `people/match`**: both return 422 Unprocessable Entity for this use case and waste credits.

```python
# RIGHT
POST https://api.apollo.io/api/v1/mixed_people/api_search
{
  "q_organization_name": "Acme Plumbing",
  "person_titles": ["owner", "founder", "ceo"],
  "page": 1, "per_page": 5
}

# WRONG (returns 422 for company-name lookup)
POST organizations/enrich  # needs domain, not name
POST people/match          # needs email or LinkedIn URL
```

Implementation: `skills/apollo_skill/apollo_client.py:find_owner_by_company`. See `feedback_apollo_company_name_lookup.md` for full diagnosis (cost 30 credits to discover 2026-04-30).

### 2. Capture website_url at insert time

`reveal_emails()` MUST include `website_url` in its return dict (pulled from `match.organization.website_url`). Downstream callers (`signal_works/topup_cw_leads.py` and `signal_works/topup_leads.py`) MUST persist it in the leads table at INSERT time. Saves a Serper credit + ~1s latency per lead later in the pipeline.

### 3. psycopg2 LIKE + %s collision

Any SQL passed to psycopg2 with both `LIKE 'prefix%'` AND `%s` placeholders must escape the literal `%` as `%%`. See `feedback_psycopg2_like_escape.md`. Symptom: `IndexError: tuple index out of range` from `cursor.execute`.

Source filter convention used across pipelines:
- CW: `source LIKE 'apollo_catalyst_works%%'` (matches both `apollo_catalyst_works` and `apollo_catalyst_works_widened`)
- SW: `source LIKE 'signal_works%%'`

### 4. Coordination: never bare `docker compose build orchestrator`

Always use `scripts/orc_rebuild.sh`. Bare builds collide with morning_runner mid-flight if a parallel session is rebuilding. The wrapper checks `task:morning-runner` lock first. AGENT_SOP Hard Rule.

---

## Version History

- **v1.0:** Initial skill, Utah ICP, Safe-Search mode.
- **v1.1 (2026-05-01):** Added `find_owner_by_company` capability, HARD RULES block (Apollo endpoint correction, website_url at insert, psycopg2 escape, orc_rebuild mandate).
