---
name: constraints_ai_capture
description: Constraints AI demo lead capture pipeline. Agent-internal Python module, not a Boubacar-invoked skill. runner.py drafts and (optionally) sends 3-touch warm-inbound sequence (Day 0/2/4) to leads who submit their email on catalystworks.consulting Constraints AI demo. Triggered via /constraints-capture endpoint. DO NOT archive.
---

# constraints_ai_capture (Agent-Internal)

Production code module. Not a Boubacar-invoked skill.

## Files
- runner.py -- 3-touch sequence runner for inbound constraints_ai leads. Templates at templates/email/constraints_ai_t{1,2,3}.py.
- __init__.py -- package marker.

## Trigger
POST to /constraints-capture (Traefik strips /api/orc prefix) writes Supabase leads row with sequence_pipeline='constraints_ai', sequence_touch=0. Morning runner picks up + drafts T1 same day, T2 Day 2, T3 Day 4.

## Auto-send
Gated by env AUTO_SEND_CONSTRAINTS_AI (default 'false' = drafts only, no send).
