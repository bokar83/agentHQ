---
owner: production
status: active - future satellite
---

# signal_works/ - Signal Works Outreach Pipeline

**Standing rules:** read `docs/RULES.md` before any task. Apply at every action boundary. (2026-05-11 — RCA fix Layer 2.)

Daily cold outreach pipeline: 20 drafts/day (10 Signal Works + 10 Catalyst Works).

## Current status

Lives at repo root because `orchestrator/` imports from it. This is technical debt.
Future plan: extract to its own repo (`bokar83/signal-works`) once import boundaries are clean.

## What lives here

- `morning_runner.py` - entry point for daily outreach run
- `gmail_draft.py` - HTML email drafting via Gmail API
- `templates/` - email templates per niche
- Supporting modules for outreach logic

## Rules for LLMs working here

- Entry point is `morning_runner.py` - run this to trigger the daily pipeline.
- **Use `signal_works/gmail_draft.py` for HTML email drafts**, not the `gws` CLI (hits 8191-char limit on Windows).
- Email sends from `boubacar@catalystworks.consulting`.
- Week 1: human review mode. Week 2+: auto-send mode.
- Do not move this folder until orchestrator imports are refactored - it will break the container build.

## Cross-references

- Constitution: [`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md)
- Folder Governance: [`docs/AGENT_SOP.md`](../docs/AGENT_SOP.md)
