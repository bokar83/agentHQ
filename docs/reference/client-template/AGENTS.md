---
owner: workspace
status: [active | paused | closed]
---

# Client: [Client Name]

**Slug:** [client-slug]
**Added:** YYYY-MM-DD
**Industry:** [industry]
**Primary contact:** [name, email]
**Engagement type:** [consulting | product | retainer]

## What lives here

- `engagements/` - all session notes, trackers, closeout docs
- `deliverables/` - all files produced for this client

## What does NOT live here

- Code changes to `orchestrator/` or `signal_works/` (those go in their folders)
- Skills built for this client (those go in `skills/` with client context in SKILL.md)

## Rules

- Never hardcode client data in orchestrator code
- All deliverables go in `deliverables/` immediately after creation
- Run `engagement-ops` skill for any new engagement
- Client is considered closed when `status: closed` is set in this file
