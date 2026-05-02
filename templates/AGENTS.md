---
owner: production
status: active
---

# templates/ - Email + Document Templates

Templates used by orchestrator agents to produce consistent output. Distinct from `skills/<skill>/templates/` (per-skill templates) and from `signal_works/templates/` (legacy SW templates being phased out).

## What lives here

| Subfolder | Purpose |
| --- | --- |
| `email/` | Email body templates (cold_outreach, cw_t2-t5, sw_t1-t4) callable via `build_body(lead)` |
| Other doc templates as needed | |

## What does NOT live here

- Per-skill templates (those go in `skills/<skill>/templates/`)
- Skill definitions themselves (`skills/`)
- Legacy SW templates pending refactor (`signal_works/templates/`)

## Rules

- Email templates here are the canonical source. The 9 templates were refactored 2026-05-01 to a uniform `build_body(lead)` callable interface (see handoff `docs/handoff/2026-05-01-no-greeting-rule-and-cw-personalizer-fixes.md`).
- The no-greeting hard rule applies: when first_name confidence is LOW or unknown, drop the greeting entirely. Never use "Hi there." See `feedback_no_greeting_when_unknown.md`.
- Em-dash hard rule applies: scrub before commit (pre-commit hook enforces this).

## Cross-references

- Constitution: [`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md)
- Folder Governance: [`docs/AGENT_SOP.md`](../docs/AGENT_SOP.md)
- Memory: `feedback_no_greeting_when_unknown.md`
