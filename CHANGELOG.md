# agentsHQ — Change Log

This file tracks every significant change to the agentsHQ project: features added, code removed, bugs fixed, and structural decisions made. It is the historical record. Use it to understand why something was done, find when something was removed, or roll back a decision.

---

## Format

Each entry follows this structure:
```
### [DATE] — [TYPE] — [Short title]
- **What:** What changed
- **Why:** Why it was changed
- **Files:** Which files were affected
- **Risk:** LOW / MED / HIGH
- **Rollback:** How to undo if needed (commit hash or manual steps)
```

Types: `FEATURE` | `FIX` | `REFACTOR` | `DELETE` | `STRUCTURE` | `CONFIG` | `SECURITY`

---

## 2026-04-02 — Deep Audit Session

Full technical PM review of the codebase. Two specialized agents ran in parallel: code logic audit + structural audit. All findings documented. The changes below were applied as a result.

---

### 2026-04-02 — FIX — HTML email template for Growth Hunter daily report
- **What:** Replaced plain-text hunter report email with styled HTML using Catalyst Works brand tokens. Added multipart alternative encoding (plain-text fallback + HTML per RFC 2046).
- **Why:** Better readability and brand consistency for daily lead emails.
- **Files:** `orchestrator/notifier.py` — added `_parse_hunter_report_to_html()`, updated `send_hunter_report()` and `send_email()`
- **Risk:** LOW — email only, no impact on Telegram or crew execution
- **Rollback:** `git revert 9dd5b56`

---

### 2026-04-02 — FIX — result={} init before try/finally in _run_background_job
- **What:** Added `result = {}` before the `try` block in `_run_background_job()`.
- **Why:** If any exception fired before the `result = run_orchestrator(...)` assignment, the `finally` block would throw `UnboundLocalError: local variable 'result' referenced before assignment`. This was masked by an outer try/except but caused the evolution trigger to silently never fire.
- **Files:** `orchestrator/orchestrator.py:735`
- **Risk:** LOW — purely defensive
- **Rollback:** Remove the `result = {}` line

---

### 2026-04-02 — FIX — asyncio.get_event_loop() → get_running_loop() in async functions
- **What:** Replaced two `asyncio.get_event_loop()` calls with `asyncio.get_running_loop()` inside async functions.
- **Why:** `get_event_loop()` is deprecated in Python 3.10+ inside coroutines and raises `DeprecationWarning`; in Python 3.12+ it raises `RuntimeError` when no current event loop is set.
- **Files:** `orchestrator/orchestrator.py:860, 1014`
- **Risk:** LOW
- **Rollback:** Revert both lines to `asyncio.get_event_loop()`

---

### 2026-04-02 — FIX — openspace_tool None guard before execute_async
- **What:** Added `if openspace_tool is not None` check before calling `openspace_tool.execute_async()` in `_trigger_evolution()`.
- **Why:** When the OpenSpace package is not installed, `openspace_tool` is set to `None`. The call would throw `AttributeError: 'NoneType' has no attribute 'execute_async'`, caught by a broad except but causing misleading error logs.
- **Files:** `orchestrator/orchestrator.py:802`
- **Risk:** LOW
- **Rollback:** Remove the None check

---

### 2026-04-02 — FIX — Remove duplicate import os and redundant typing imports
- **What:** Removed duplicate `import os` (appeared twice at lines 25 and 30). Consolidated `from typing import Optional` (appeared twice at lines 32 and 44). Removed unused `List`, `Dict`, `Any` from typing imports.
- **Why:** Dead imports, copy-paste artifact.
- **Files:** `orchestrator/orchestrator.py:25-44`
- **Risk:** LOW
- **Rollback:** No functional change — not needed

---

### 2026-04-02 — FIX — Postgres hostname default: agentshq-postgres-1 → orc-postgres
- **What:** Replaced all 4 occurrences of the stale `"agentshq-postgres-1"` hostname default with `"orc-postgres"` in memory.py.
- **Why:** The actual running Docker container is named `orc-postgres` (confirmed via `docker ps` on VPS). The stale default `agentshq-postgres-1` was from the initial Docker Compose setup and would cause all Postgres operations in memory.py to silently fail on a fresh container start if `POSTGRES_HOST` was not explicitly set in `.env`.
- **Files:** `orchestrator/memory.py:111, 175, 209, 238`
- **Risk:** LOW — overridden by env var in production anyway; this fixes the fallback
- **Rollback:** Replace `orc-postgres` back to `agentshq-postgres-1` in those 4 lines

---

### 2026-04-02 — FIX — requirements.txt: add pytz + requests, remove langchain-openai
- **What:** Added `pytz>=2024.1` and `requests>=2.31.0` to requirements.txt. Removed `langchain-openai>=0.1.20`.
- **Why:** `pytz` is imported by `scheduler.py` but was missing — fresh Docker build would silently break the daily cron. `requests` is imported by `notifier.py` and `orchestrator.py` but was missing — worked only as a transitive dependency of PyGithub. `langchain-openai` was listed but never imported anywhere in the codebase (all LLM calls go through CrewAI's LLM class via OpenRouter).
- **Files:** `orchestrator/requirements.txt`
- **Risk:** LOW
- **Rollback:** Revert requirements.txt changes

---

### 2026-04-02 — FIX — .env line 89 corruption: split concatenated variables
- **What:** Fixed corrupted `.env` line 89 where `NOTION_DATABASE_ID` and `WHATSAPP_PHONE` were concatenated on one line as `NOTION_DATABASE_ID=YOUR_DATABASE_ID_HEREWHATSAPP_PHONE=18016041983`.
- **Why:** Python's `dotenv` silently treated this as one variable, making `NOTION_DATABASE_ID` have a garbage value and `WHATSAPP_PHONE` invisible to any code that tried to read it.
- **Files:** `.env:89` (gitignored — must be applied manually on VPS too)
- **Risk:** LOW
- **Rollback:** Re-concatenate the two lines (not recommended)

---

### 2026-04-02 — DELETE — agent-brain/ directory removed
- **What:** Deleted the entire `agent-brain/` directory (6 files: orchestrator.py 403 lines, agents.py 486 lines, crews.py 997 lines, router.py 169 lines, memory.py 203 lines, tools.py 440 lines + Dockerfile, requirements.txt, tests/).
- **Why:** `agent-brain/` was a stale snapshot of `orchestrator/` from an earlier stage of development. `orchestrator/` is 40-60% larger and is the production version. `agent-brain/` was imported by nothing, built by nothing (docker-compose only references `orchestrator/Dockerfile`). Keeping both caused maintenance confusion and code drift risk.
- **Files:** Entire `agent-brain/` directory
- **Risk:** LOW — confirmed zero live references before deletion
- **Rollback:** `git checkout c939a5d -- agent-brain/` (last commit before deletion)

---

### 2026-04-02 — STRUCTURE — Rename agents/ subdirs from kebab-case to snake_case
- **What:** Renamed `agents/boub-ai-voice` → `boub_ai_voice`, `agents/outfit-stylist` → `outfit_stylist`, `agents/security-agent` → `security_agent`. Updated all references in AGENTS.md, README.md, and AGENT_INSTRUCTIONS.md.
- **Why:** Python convention is snake_case for directory names that may become importable modules. Kebab-case names with hyphens cannot be imported as Python modules. `skill_builder` was already correctly named — only the three hyphenated directories needed changing.
- **Files:** `agents/` directory, AGENTS.md, README.md, AGENT_INSTRUCTIONS.md
- **Risk:** LOW — these are spec/doc directories, not imported as Python modules
- **Rollback:** Rename directories back and revert doc files

---

### 2026-04-02 — STRUCTURE — Created sandbox/ directory
- **What:** Created `sandbox/` at project root with a README.md explaining its purpose as the testing and experimentation workspace.
- **Why:** There was no designated place to experiment with tools, products, and ideas before promoting them to `outputs/`. Dashboards4Sale/tmp/ was being used as an ad-hoc sandbox but had no clear purpose signal.
- **Files:** `sandbox/README.md`
- **Risk:** NONE
- **Rollback:** Delete `sandbox/` directory

---

### 2026-04-02 — FEATURE — news_brief crew: agent, crew, router registration
- **What:** Built the complete `news_brief` pipeline: `build_news_brief_agent()` in agents.py, `build_news_brief_crew()` in crews.py, registered in `CREW_REGISTRY`. The task type already existed in router.py.
- **Why:** `news_brief` was registered as a valid task type in router.py but had no backing crew — any news request silently fell through to `build_unknown_crew`. Now fully functional.
- **Files:** `orchestrator/agents.py`, `orchestrator/crews.py`
- **Risk:** LOW — additive only
- **Rollback:** Remove `build_news_brief_agent()`, `build_news_brief_crew()`, and the CREW_REGISTRY entry

---

### 2026-04-02 — SECURITY — Telegram sender authentication using ALLOWED_USER_IDS
- **What:** Added sender ID check in `process_telegram_update()`. Messages from users not in `ALLOWED_USER_IDS` receive a polite rejection and are not processed.
- **Why:** `ALLOWED_USER_IDS` was set in `.env` but never enforced. Any Telegram user who discovered the bot could send tasks to the full orchestrator.
- **Files:** `orchestrator/orchestrator.py` — `process_telegram_update()`
- **Risk:** LOW — only affects unauthorized users; your chat ID is pre-authorized
- **Rollback:** Remove the sender check block

---

### 2026-04-02 — DELETE — Dead code cleanup (remoat_approval.py, db.py, schema_v2.sql, tools.py, crews.py)
- **What:** Removed the following dead code:
  - `orchestrator/remoat_approval.py` — imported by nothing, superseded by `notifier.log_for_remoat()`
  - `orchestrator/db.py` — imported by nothing; memory.py and council.py bypass it with inline psycopg2
  - `orchestrator/schema_v2.sql` — SQL migration with no runner; moved to `docs/database/`
  - `tools.py`: removed `openspace_evolver` alias, `ALL_TOOLS` constant, 4 dead MCP tool factories
  - `crews.py`: removed `build_hierarchical_crew()` (not in CREW_REGISTRY, unreachable)
  - `agents.py`: removed `build_skill_builder_agent()` (no crew, no task type, unreachable)
  - `router.py`: removed `register_new_task_type()` (no callers anywhere)
  - `skills/local_crm/reply_logic.py` and `scoreboard.py` — never imported
- **Why:** Dead code that is imported by nothing and called by nothing creates maintenance confusion and obscures the real architecture.
- **Files:** Multiple — see above
- **Risk:** LOW — all confirmed unreferenced before deletion
- **Rollback:** `git checkout <commit-before> -- <file>` for any specific file

---

### 2026-04-02 — REFACTOR — _is_obvious_chat extracted to single shared function
- **What:** Replaced 3 diverging copies of the obvious-chat keyword check with a single `_classify_obvious_chat(msg: str) -> bool` function. Unified keyword list includes hunter keywords (`find`, `hunt`, `leads`, `prospect`) that were missing from the `/run-async` path.
- **Why:** The three copies had diverged — `/run-async` was missing hunter keywords, meaning a "find leads" request via that endpoint could be wrongly classified as chat and never dispatched to the hunter crew.
- **Files:** `orchestrator/orchestrator.py`
- **Risk:** LOW — behaviour-preserving; adds missing hunter keywords to the async path
- **Rollback:** Re-inline the three keyword checks

---

### 2026-04-02 — FIX — CLIHubSearchTool async deadlock
- **What:** Replaced `asyncio.get_event_loop().run_until_complete()` inside `CLIHubSearchTool._run()` with a thread-safe async executor pattern using `concurrent.futures.ThreadPoolExecutor`.
- **Why:** `BaseTool._run()` is synchronous. Calling `run_until_complete()` inside a sync method from an already-running event loop raises `RuntimeError: This event loop is already running`, which is the normal execution path for all crew tools called from FastAPI background tasks.
- **Files:** `orchestrator/tools.py:318`
- **Risk:** LOW — CLIHub tool was not functional before this fix; now it is
- **Rollback:** Revert to `loop.run_until_complete()` pattern

---

## Future / Backlog

Items identified during the 2026-04-02 audit that are deferred to a future session:

- **Organize agents/ into subcategories** (content/, technical/, research/, consulting/) — before 20+ agents
- **Organize skills/ into _core/, _integrations/, _third_party/** — before 30+ skills
- **Date-partition outputs/** into `outputs/YYYY-MM/` subdirs — before daily volume exceeds ~100/day
- **Reorganize tests/** into unit/, integration/, e2e/ — before 20+ test files
- **Wire db.py into memory.py and council.py** as the single DB connection source, or delete db.py permanently
- **Add README.md to orchestrator/, agents/, skills/, workflows/** — "how to add X" guides
- **Move n8n-workflows/ → workflows/** for clarity
- **Move Dashboards4Sale/tmp/ → projects/dashboards_builder/** with README
- **Add `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER` to .env explicitly** (currently relying on defaults)
- **Add `N8N_ESCALATION_WEBHOOK` to .env** so EscalateTool and ProposeNewAgentTool actually fire
- **MCP tool factories** (Notion/GCal/Gmail/Airtable in tools.py) — wire to agents when MCP is ready, or remove
