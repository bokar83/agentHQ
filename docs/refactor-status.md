# Orchestrator Modular Refactor: Status

**Last updated:** 2026-04-22
**Live entrypoint:** `orchestrator.py` (the monolith)
**Shadow modules:** `app.py`, `engine.py`, `handlers.py`, `handlers_chat.py`, `handlers_doc.py`, `worker.py`, `state.py`, `constants.py`, `schemas.py`, `utils.py`, `health.py`

## What is this document

On 2026-04-17 a modular refactor shipped: `orchestrator.py` (2,748 lines) was decomposed into 11 focused modules. The modules exist alongside the monolith. They are not yet the live entrypoint.

The Dockerfile still runs `uvicorn orchestrator:app`, which means everything operates out of the monolith. The new modules are correct but dormant.

This document tracks what still needs to move from `orchestrator.py` into the new modules before the entrypoint can be flipped to `uvicorn app:app`.

## What IS complete in the shadow modules

- Port of routes: `/run`, `/run-sync`, `/run-team`, `/classify`, `/capabilities`, `/outputs`, `/outputs/{filename}`, `/memory/search`, `/history/{session_id}`, `/run-async`, `/status/{job_id}`, `/inbound-lead`, `/chat-token`, `/upload`, `/sync-session`, `/telegram`, `/health`, `/internal/health-report`, `/`
- `verify_api_key` with fail-closed behavior (as of 2026-04-22 monolith also fail-closed)
- Doc-routing emoji commands (confirm, edit, new-project, flag, approve-routing)
- `run_orchestrator`, `run_team_orchestrator`, `_build_summary`, `_save_overflow_if_needed`
- Constants `SAVE_REQUIRED_TASK_TYPES`, `MEMORY_GATED_TASK_TYPES`
- State dicts `_last_completed_job`, `_active_project`
- Pydantic models for all request/response shapes
- Health registry

## What is MISSING in the shadow modules

These are in `orchestrator.py` but not yet in the new modules. They must be ported before the entrypoint flip, or they will regress when the flip happens.

### 1. Rich `run_chat` with Simpsons persona + tool use
**Where:** `orchestrator.py:305-637` (330 lines)
**New module version:** `handlers.py:18-40` (20-line generic CrewAI wrapper)
**Why it matters:** current chat has a Bart Simpsons persona system prompt, 4 tools (`query_system`, `retrieve_output_file`, `save_memory`, `forward_to_crew`), conversation history loading from Postgres, and session memory injection. The `handlers.py` version has none of this.

### 2. Slash commands
**Where:** `orchestrator.py:1685-1853`
**New module version:** `handlers.py:84-105` (only /switch and /status)
**Missing commands:**
- `/scan-drive`. Triggers `scheduler._run_drive_watch(scan_all=True)`.
- `/lessons [task_type]`. Lists recent agent_learnings rows.
- `/purge-lesson [id]`. Soft-deletes a lesson.
- `/status [job_id]`. Current version only shows last job; the rich version queries `job_queue` by ID.
- `/projects`. Shows last 10 jobs for this chat.
- `/cost [days]`. LLM spend rollup from `llm_calls`.
- `/switch <name>`. The new-module version is simpler but functional.

### 3. Praise / critique detection
**Where:** `orchestrator.py:1280-1300, 1855-1879`
**New module version:** `handlers_chat.py:34-66` (similar structure but different regex patterns)
**Gap:** the two implementations match different word lists. Either align them or pick one.

### 4. `_run_background_job` compound workflows
**Where:** `orchestrator.py:1038-1196` (158 lines)
**New module version:** `worker.py:9-91` (82 lines, barebones)
**Missing:**
- Compound email follow-up (if classification has `has_email_followup`, spin a GWS crew after the main task to draft a summary email)
- Hunter task email delivery (calls `notifier.send_hunter_report`)
- `_trigger_evolution` after every successful job (OpenSpace)
- `extract_and_save_learnings` trigger on success + MEMORY_LEARNING_ENABLED
- Last-completed-job tracking for praise/critique pairing

### 5. `_query_system` with full introspection
**Where:** `orchestrator.py:231-302` (72 lines)
**New module version:** `utils.py:31-57` (27 lines)
**Gap:** new version lists agents but does not include descriptions, recent output files, or the infrastructure block.

### 6. `telegram_polling_loop` with webhook retry
**Where:** `orchestrator.py:1945-1992` (48 lines with deleteWebhook 3-attempt retry + 401 handling)
**New module version:** `handlers.py:135-160` (single attempt, no error branching)

### 7. `_shortcut_classify` / `_classify_obvious_chat` drift
**Where:** `orchestrator.py:1236-1259`
**New module version:** `handlers.py:162-173`
**Gap:** the two classifiers match different inputs. `orchestrator.py` version is richer (greeting-only for obvious-chat, keyword shortcut via `router._keyword_shortcut`). `handlers.py` version hard-codes `"find leads"` and `"research"` prefixes and matches broad chat triggers. These MUST be aligned to the orchestrator.py version, per `docs/routing-architecture.md` critical rules 3 and 4.

## Plan to complete the refactor

The safe order (no flipping until all of these are done):

1. **Port the full `run_chat` to `handlers.py`** (or a new `handlers_chat_rich.py`). Copy system prompt, tool definitions, tool handlers, history loading, embedding-based memory injection, session save on exchange. Largest individual port.
2. **Extract slash commands to a new `handlers_commands.py`** with one function per command. Call from the main dispatch in `handlers.py`.
3. **Align praise/critique regex** between `orchestrator.py` and `handlers_chat.py`. Pick one version (orchestrator.py has more signals, `handlers_chat.py` has emoji support). Recommend merging both lists.
4. **Expand `worker.py`** with compound email follow-up, hunter email, evolution trigger, learning extraction, and `_last_completed_job` bookkeeping. This file must also import `_active_project` / `_last_completed_job` from `state.py` so both old and new paths share state during the cutover.
5. **Harden `telegram_polling_loop`** in `handlers.py` with the 3-attempt deleteWebhook retry + 401 halt.
6. **Align classifiers** in `handlers.py` with the monolith per the routing-architecture rules.
7. **Rewrite `_query_system`** in `utils.py` to match the monolith's richer output.
8. **Smoke-test the entire shadow path** by running `uvicorn app:app` locally on port 8001 with a copy of the VPS env. Test: Telegram polling, chat, /cost, emoji handler, inbound-lead webhook, /run-sync, /run-async.
9. **Flip the Dockerfile entrypoint.** Keep `orchestrator.py` in the repo for one deploy cycle as a rollback path. Verify all integrations after restart.
10. **After 1 week of stable operation: delete `orchestrator.py`** and rename `app.py` → `orchestrator.py` (so the Dockerfile CMD doesn't need a second edit).

## Why we did not flip the entrypoint on 2026-04-22

A rushed flip at this stage would regress:
- The Simpsons-persona chat with tool use
- Six slash commands (`/cost`, `/projects`, `/lessons`, `/purge-lesson`, `/scan-drive`, rich `/status`)
- Compound email follow-up after crew tasks
- Hunter report email
- Post-task evolution trigger
- Post-task learning extraction

These were built deliberately in the monolith and have no equivalent in the shadow modules. The session that does the flip must port every one of them first.

## DB connection consolidation (piggyback on the flip)

The code-review scan on 2026-04-22 counted 17 inline `psycopg2.connect()`
call sites across 7 files, most of which are in `orchestrator.py` itself.
Rather than touch those in isolation (risky in the protected window, and
the same lines are about to be replaced by the refactor anyway), we will
consolidate on `memory._pg_conn()` (or `db.get_local_connection()`) AS
PART OF the port work. Every inline connect in the monolith becomes a
single helper call in the new module.

Net effect: fewer lines in the new modules than the equivalent lines in
`orchestrator.py`, and a single place to add pooling later if we ever
need it.

## Minimum subset for a "just works" flip

If a future session wants to flip with minimum porting, the ABSOLUTE minimum is:

1. Port the full `run_chat` (critical: chat is the primary browser UI entrypoint)
2. Port `/cost`, `/projects`, `/status <job_id>` slash commands (these are used regularly)
3. Port the `telegram_polling_loop` retry logic
4. Align `_classify_obvious_chat` with the monolith per routing-architecture.md

The rest (learning extraction, evolution, compound email) can be staged later because they are opt-in behind env flags that are currently off or rarely fired.
