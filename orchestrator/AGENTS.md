---
owner: production
status: active
---

# orchestrator/ - The Python Brain

**Standing rules:** read `docs/RULES.md` before any task. Apply at every action boundary. (2026-05-11 — RCA fix Layer 2.)

This is the core runtime. Every AI request flows through here.

## What lives here

All Python application code: FastAPI app, router, crews, agents, tools, handlers, engine, memory, scheduler, saver, and all feature modules (griot, council, beehiiv, etc.).

## What does NOT live here

- Skills (those go in `skills/`)
- Client work (that goes in `workspace/clients/`)
- Documentation (that goes in `docs/`)
- UI code (that goes in `ui/`)

## Rules for LLMs working here

- **Never recreate `orchestrator.py`** - it was deleted 2026-04-25 (commit 4d1aeb3). The monolith was split into modular files.
- **All changes via Codex**, not Claude Code direct edits, unless it is a one-line fix or config change.
- **Run `python -m py_compile [file]`** after every edit.
- **Never hardcode task logic** - routing goes through `router.py`.
- **Never hardcode credentials** - all from environment variables.
- **New env vars must be added to both `.env` AND `docker-compose.yml` environment block** or they silently don't reach the container.

## Context scoping (load only what you need)

| Task | Files to read |
| --- | --- |
| Chat behavior | `handlers_chat.py`, `constants.py`, `llm_helpers.py` |
| Task routing | `router.py`, `constants.py` |
| New crew/agent | `crews.py`, `agents.py`, `tools.py` |
| Deploy / container | `Dockerfile`, `docker-compose.yml` (root) |
| Memory / history | `memory.py`, `session_store.py`, `episodic_memory.py` |
| Approval queue | `approval_queue.py`, `handlers_approvals.py` |
| Publishing / Griot | `griot.py`, `griot_scheduler.py`, `auto_publisher.py` |
| Council | `council.py`, `prompts/` |
| Cost tracking | `usage_logger.py` |

## Entrypoint

`app.py` is the sole entrypoint. `uvicorn app:app` starts the service.

## Cross-references

- Constitution: [`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md)
- Folder Governance: [`docs/AGENT_SOP.md`](../docs/AGENT_SOP.md)
