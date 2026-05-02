---
name: linkedin-mvm
description: Operational tooling for the LinkedIn AI Governance motion, including personalized DMs, prospect ingestion, and morning nudges.
---

# LinkedIn MVM Skill

**Name:** LinkedIn MVM
**Description:** Operational tooling for the LinkedIn AI Governance flagship motion. Generates personalized DMs from a CSV, ingests prospects into the lead DB, and queues the morning Telegram nudge.

## Source of Truth

**Playbook V3 (positioning, pricing, targets):** `docs/ai-governance/Bou_CW-AI-Governance-Final-Playbook-2026-04-16.md`
**LinkedIn execution SOP:** `docs/playbooks/linkedin-mvm.md`
**DM template:** `templates/linkedin/dm_v1.py` (single source of truth)
**Profile copy:** `docs/playbooks/linkedin-profile-rewrite-2026-04-30.md`

## Files

- `generate_dms.py` - reads `workspace/linkedin-mvm/target_list.csv`, writes personalized DMs to a dated MD file, and ingests prospects into the lead DB.
- `morning_nudge.py` - pulls 5 next-up prospects (status=new), formats them with the DM template, sends to Telegram. Triggered daily at 8:55 AM MT by VPS cron.

## CSV format expected

`workspace/linkedin-mvm/target_list.csv` columns:
```
name,company,title,location,linkedin_url,industry,hook
```

The `hook` column is the personalization line that powers the DM. Should be one observation about the prospect (a recent post, the company's domain, a trigger event). 1-2 sentences max.

## Usage

```bash
# Generate today's DMs after dropping new names into target_list.csv:
python -m skills.linkedin_mvm.generate_dms

# Output: workspace/linkedin-mvm/dms_to_send_YYYY-MM-DD.md
# Each entry has the LinkedIn URL above the DM, copy-paste ready.
```

## Lead DB

Uses `skills.local_crm.crm_tool.add_lead()` which writes to:
1. Supabase `leads` table (primary)
2. Notion CRM Leads DB `619a842a-0e04-4cb3-8d17-19ec67c130f0` (auto-sync)

Source value: `LinkedIn`. Pipeline statuses: `new -> messaged -> replied -> booked -> paid`.

## Version

- v1.0 (2026-04-30): Initial. CSV ingest + DM generation + Telegram morning nudge.
