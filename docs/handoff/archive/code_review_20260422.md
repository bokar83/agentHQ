# agentsHQ : Deep Code Review

**Date:** 2026-04-22
**Scope:** Full repo (not just orchestrator). Review only, no code changes.
**Method:** 8-phase deep pass : intake, static map, live correlation against VPS + Postgres, dead-code sweep, Karpathy compliance, hijacking sweep, missing pieces.
**Measured against:** Karpathy's 4 coding principles (docs/AGENT_SOP.md:22-27).
**Protected window:** Any file modified after 2026-04-15 is flagged, never proposed for deletion.

---

## Executive Verdict

**PASS with two structural issues and clean security posture for internal code; one real external attack surface.**

The codebase is lean, intentional, and well-designed in most places. The recent 7 days of work (token economy ledger, inbound_lead skill, research_engine bypass, LLM-backed router) are high-quality additions that follow Karpathy principles closely. Usage data confirms the token ledger, job queue, and conversation history are all working.

Three things need attention, in this order:

1. **Port 8000 is publicly exposed on the VPS IP.** docker-compose binds `0.0.0.0:8000`, UFW is inactive. 142 scanner probes in the last 24 hours hit the orchestrator directly, bypassing Traefik. This is the real `/run-sync` unauth risk Codex flagged. Fix: firewall, rebind to 127.0.0.1, or enforce fail-closed auth.
2. **Half-shipped modular refactor.** `orchestrator.py` (2,748 lines) is the live entrypoint. `app.py` + `engine.py` + `handlers.py` + 7 other new modules were created 2026-04-17 as a modular replacement but were never wired in. 19 symbols are duplicated with drift. `handlers_doc.py` is a stub. The refactor must be completed (flip the entrypoint) or intentionally shelved.
3. **Hardcoded JWT fallback secret** at orchestrator.py:2582. Low probability (requires `ORCHESTRATOR_API_KEY` to be unset at runtime) but a real vulnerability class.

Everything else is Karpathy cleanup: file-size discipline, connection pooling, silent-fail reduction, orphan removal.

---

## VPS vs Local Parity

**Status: CLEAN.** Verified by md5 comparison of every `orchestrator/*.py` file after LF normalization. Same git HEAD (`35b6db2`). Git working trees clean on both sides.

Single source of truth: the git repo. Local Windows files + VPS files are byte-identical.

---

## Recent Work : Do Not Touch (7-day protected window)

I read every commit from 2026-04-15 to 2026-04-22 (172 commits, 8 days). Summary of what was intentionally built or fixed in that window. These are off-limits for deletion proposals. I propose improvements inside this set only if something is broken.

| Area | Commits | What was built |
|---|---|---|
| Token Economy Ledger (Phases 1-3.5) | 9a074d3, a13859c, cbd1444, 57a1a2e, 91d951c | `usage_logger.py`, `llm_calls` table, per-call ledger, cache_control wiring, right-sized chairman + reviews, /cost Telegram command, x-ai grok-4-fast routing (15x/30x cheaper) |
| Inbound Lead Routine | 3e20337, 02c7762, d0e40fe, 37ccef9 | Full `skills/inbound_lead/` (7 modules + 9 tests), `/inbound-lead` route, Calendly/Formspree webhook pipeline, Notion Pipeline logging, idempotency, Telegram notify |
| Research Engine Bypass | 33e09bb, 52b07df, 7f04644, ef5dd11, c7451fc | `research_engine.py`, direct Anthropic tool-use loop, Firecrawl web_search + web_scrape, bypasses CrewAI max_iter prefill 400 |
| LLM-backed Router | 5c39dfb, 2f5b00d, 413e680, 48a4f82, 37ccef9, f7d5c59 | `_llm_classify()` + `_classify_raw()`, LLM fallback with Haiku, chat keyword removed, read-intent shortcut, P1 guard, bounded telemetry queue |
| Kie Media Skill | ab17603 | `kie_media.py`, `KieGenerateImageTool`, `KieGenerateVideoTool`, Kling/seedream model registry, media_generations migration |
| Content Board Reorder | c6fb08d | `content_board_reorder.py`, `scrub_titles.py`, 10-day schedule rewrite with Gate 0 + facilitator register |
| Modular Refactor (in-progress) | a84b450, 5b70462, 1b7f404, 302df23 | `app.py`, `engine.py`, `handlers.py`, `handlers_chat.py`, `handlers_doc.py`, `worker.py`, `state.py`, `constants.py`, `utils.py`, `schemas.py`, `health.py` : created but entrypoint never flipped |
| Karpathy Principles | 33e09bb, f48f1c3 | `docs/AGENT_SOP.md` rewrite, `.pre-commit-config.yaml` em-dash hook, `scripts/check_no_em_dashes.py` |
| Design Layer | 011adf8, 57823f2, 7d61b15, c46b3e3 | `design_context.py`, design_agent, design_review crew, DESIGN REQUIREMENTS blocks, frontend-design skill |
| Council Tightening | 91d951c, cbd1444, a13859c, ceb4e78 | grok-4-fast for peer reviews, prefix resolver, temperature decoupling, ranking ritual (bi-weekly Mondays) |
| nsync rules | ceb4e78 | Empty Source Control panel enforcement, 4-bucket triage |
| Cleanup (recent) | 35b6db2, d2bb835, 0010d19 | Deregister external/ gitlinks, drop .bak backups + mermaid probe, harden .gitignore |

**Protected files:** all `orchestrator/*.py` modified after 2026-04-17, all `skills/inbound_lead/*`, `orchestrator/research_engine.py`, `orchestrator/kie_media.py`, `orchestrator/usage_logger.py`, `orchestrator/content_board_reorder.py`, `orchestrator/scrub_titles.py`, `docs/AGENT_SOP.md`, `docs/routing-architecture.md`, `docs/llm_ranking_review.md`, `docs/kai_model_registry.md`.

---

## Findings : Priority Ordered

Every finding has: severity, Karpathy principle violated, evidence, proposed patch, and (if applicable) a note on whether it touches protected work.

---

### P0 : Critical

#### P0-1. Port 8000 publicly reachable on VPS IP, bypassing Traefik

**Severity:** Critical (only active hijacking surface).
**Karpathy:** #4 (Goal-driven execution : the goal "only chat access is public" is silently violated by double-exposure).

**Evidence:**
- `docker-compose.yml:123-124`: `ports: - "8000:8000"` binds to `0.0.0.0:8000`
- VPS `ss -tlnp`: `LISTEN 0 4096 0.0.0.0:8000 ... docker-proxy`
- VPS `ufw status`: inactive (no firewall at OS level)
- Docker logs (24h): 142 scanner probes to `/webui`, `/owa/`, `/inicio`, `/admin`, `/login`, etc. All returned 404 because the routes don't exist, but `/run-sync`, `/outputs`, `/memory/search` DO exist and are ungated.
- Traefik route for `agentshq.boubacarbarry.com/api/orc/*` received 0 hits in 24h, confirming your chat UI is not the one being scanned.

**Attack path:**
1. Attacker scans VPS IP range on port 8000.
2. Lands on agentsHQ orchestrator directly (bypasses Traefik, bypasses hostname routing).
3. Hits `/run-sync` or `/outputs`. These routes have no `Depends(verify_api_key)`.
4. If `ORCHESTRATOR_API_KEY` env var is ever unset, the `verify_api_key` function at orchestrator.py:128-130 fails open (`if not expected: return`), even for gated routes.

**Proposed patch:**

Option A (minimum change, recommended): bind port to localhost only.
```yaml
# docker-compose.yml:123-124 BEFORE
ports:
  - "8000:8000"

# AFTER
ports:
  - "127.0.0.1:8000:8000"   # Traefik routes public traffic; direct access local-only
```
Result: scanner probes dead, `agentshq.boubacarbarry.com/chat` still works via Traefik.

Option B (defense-in-depth): enable UFW.
```bash
ufw default deny incoming
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

Option C (belt and suspenders): add `Depends(verify_api_key)` to all sensitive routes in orchestrator.py + fix fail-closed.

My recommendation: A + B together. 5-minute change, kills the whole attack surface. Option C is orthogonal and should also be done, but for the drift problem in P1 not for this one.

**Touches protected work?** `docker-compose.yml` last modified 2026-04-20 (inbound_lead SUPABASE_DB_URL pipe). In the protected window. But this is a 2-character fix on an exposure line, not a deletion of recent work. Safe.

---

#### P0-2. `verify_api_key` fails open when env var is unset + hardcoded JWT fallback

**Severity:** Critical latent vulnerability.
**Karpathy:** #1 (Think before coding : assumption "env var is always set" is untested). #4 (Goal-driven : fail-closed default is the safe choice).

**Evidence:**
- `orchestrator/orchestrator.py:128-130`: `if not expected: return` allows all requests when env var is empty
- `orchestrator/orchestrator.py:2582`: `secret = os.environ.get("ORCHESTRATOR_API_KEY", "fallback-secret")`. If env var is unset, JWTs get signed with the literal string `"fallback-secret"` which is in the public codebase.
- 7 of 14 non-public routes are ungated entirely: `/run-sync`, `/classify`, `/capabilities`, `/outputs`, `/outputs/{filename}`, `/memory/search`, `/status/{job_id}`
- `orchestrator/app.py` (orphaned) has the correct fail-closed implementation at lines 45-61. The correct code exists, just not in the live module.

**Proposed patch:** Change `orchestrator.py:128-130` from:
```python
expected = os.environ.get("ORCHESTRATOR_API_KEY", "")
if not expected:
    return  # No key configured - allow all (dev/backwards compat)
```
to:
```python
expected = os.environ.get("ORCHESTRATOR_API_KEY", "")
if not expected:
    if os.environ.get("DEBUG_NO_AUTH", "false").lower() == "true":
        return  # explicit dev opt-in
    raise HTTPException(status_code=500, detail="Server auth misconfigured")
```

Change `orchestrator.py:2582`. Remove the default string:
```python
secret = os.environ.get("ORCHESTRATOR_API_KEY")
if not secret:
    raise HTTPException(status_code=503, detail="Chat token issuer not configured")
```

Add `dependencies=[Depends(verify_api_key)]` to 7 ungated routes. See `orchestrator/app.py:112-258` for the target pattern. Same route list, already correct there.

**Touches protected work?** orchestrator.py has been touched 6x in the last 7 days but lines 128-130 and 2582 have been stable longer than the window. Inline fix to existing lines, not removal of new code.

---

### P1 : High

#### P1-1. Half-shipped modular refactor: orchestrator.py and 11 new modules both live, 19 symbols duplicated

**Severity:** High architectural.
**Karpathy:** #3 violated catastrophically (refactor was purely additive, never subtractive).

**Evidence:**

The live entrypoint is `orchestrator.py` (2,748 lines), via Dockerfile:52 `CMD ["uvicorn", "orchestrator:app", ...]`.

A modular split shipped 2026-04-17 (commit `a84b450`) creating:

| Module | Lines | Imported By | Status |
|---|---|---|---|
| `orchestrator/app.py` | 276 | : | orphan (better auth than live) |
| `orchestrator/engine.py` | 350 | app.py, handlers.py, worker.py | orphan chain |
| `orchestrator/handlers.py` | 173 | app.py | orphan |
| `orchestrator/handlers_chat.py` | 66 | handlers.py | orphan chain |
| `orchestrator/handlers_doc.py` | 101 | handlers.py | orphan + STUB (only the filing emoji is implemented; edit/new/flag/approve missing) |
| `orchestrator/worker.py` | 91 | app.py, handlers.py | orphan chain |
| `orchestrator/state.py` | 11 | app.py, handlers.py, handlers_chat.py | orphan chain |
| `orchestrator/constants.py` | 32 | app.py, engine.py, handlers.py, worker.py | orphan chain |
| `orchestrator/schemas.py` | 45 | app.py | orphan chain |
| `orchestrator/utils.py` | 101 | app.py (orphan), notifier.py (LIVE) | partially live (only `sanitize_text`) |
| `orchestrator/health.py` | 32 | app.py (orphan), tools.py (LIVE) | live via tools.py |

Total approximately 1,445 live-dead lines awaiting entrypoint flip.

**19 duplicated symbols with drift:**

| Symbol | In orchestrator.py | In new module | Drift? |
|---|---|---|---|
| `run_orchestrator` | yes | engine.py | Yes. New version has cleaner memory save, fewer branches |
| `run_team_orchestrator` | yes | engine.py | Minor |
| `_build_summary` | yes | engine.py, utils.py | Yes. `design_review` label only in engine.py version |
| `_save_overflow_if_needed` | yes | engine.py, utils.py | Same |
| `run_chat` | yes | handlers.py | Yes. handlers.py version is a 20-line Agent wrapper; orchestrator.py is 330 lines with Simpsons persona |
| `_shortcut_classify`, `_classify_obvious_chat` | yes | handlers.py | Different logic. handlers.py version matches `"find leads"`/`"research"`, orchestrator.py version matches greetings |
| `_query_system`, `_extract_file_text` | yes | utils.py | Logic drift |
| `verify_api_key` | yes (fail-open) | app.py (fail-closed) | Security-critical drift |
| TaskRequest, TaskResponse, AsyncTaskResponse, JobStatusResponse, TeamTaskRequest, StatusResponse | yes | schemas.py | Minor. schemas.py missing `title`/`deliverable` fields |
| SAVE_REQUIRED_TASK_TYPES, MEMORY_GATED_TASK_TYPES | yes | constants.py | Same |

**Proposed patch (no delete on recent work : instead, complete the refactor):**

Phase A: Make the new modules first-class citizens.
1. Align `app.py` to match current orchestrator.py feature set (port any drift fixes from orchestrator.py that aren't in app.py yet).
2. Port 2026-04-20 inbound_lead route changes forward. Confirm app.py:171 matches orchestrator.py:2519.
3. Fill in `handlers_doc.py` edit/new/flag/approve handlers by extracting the inline blocks from orchestrator.py:1436-1682.

Phase B: Flip the entrypoint. Dockerfile:52 from `CMD ["uvicorn", "orchestrator:app", ...]` to `CMD ["uvicorn", "app:app", ...]`. Keep orchestrator.py in repo as fallback for one deploy cycle.

Phase C: Verify in production.
1. Telegram polling still fires.
2. `/chat-token` + `/run-async` path (browser chat UI).
3. `/inbound-lead` webhook.
4. `/run-sync` via Claude Code.

Phase D (after confirmed stable for 1 week): delete orchestrator.py and move app.py → orchestrator.py so Dockerfile can stay the same. Or leave as is, that is a cosmetic choice.

**Touches protected work?** Yes, the new modules ARE protected work. Proposal is to make them production-active, not to remove them. This completes your intent, doesn't reverse it.

---

#### P1-2. 17 inline `psycopg2.connect()` calls across 7 files; no connection pool

**Severity:** High (reliability).
**Karpathy:** #2 (Simplicity: duplicated boilerplate). #4 (Goal-driven: no telemetry on connection health).

**Evidence:**
- `orchestrator/memory.py`: 4 inline + 1 via `_pg_conn()` helper (lines 111, 188, 222, 251)
- `orchestrator/orchestrator.py`: 1 inline at 1364, plus 2 via `memory._pg_conn()`
- `orchestrator/scheduler.py`: 2 at 508, 846
- `orchestrator/council.py`: 1 at 670
- `orchestrator/handlers_doc.py`: 1 at 11
- `orchestrator/db.py`: 2 for Supabase + local (these ARE the pool centralizers but aren't used everywhere)
- Every call opens, uses, closes. Under load this will starve Postgres `max_connections`.

**Proposed patch:** Centralize on `memory._pg_conn()` or move to `orchestrator/db.py::get_local_connection()`. Wrap in a context manager or light pool. Do not require all callers to change at once, accept either helper. Low-risk cleanup.

**Touches protected work?** Most inline calls are older than the window. `handlers_doc.py:11` is in-window (stub file) but can be left alone during the P1-1 refactor completion.

---

#### P1-3. CORS wildcard on a public auth'd API

**Severity:** High (latent XSRF surface).
**Karpathy:** #2 (simplicity default for dev that wasn't tightened for prod).

**Evidence:** `orchestrator.py:114-119`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```
With `/chat-token` issuing JWTs that protect `/run-async`, a malicious site could trigger agent runs from any user session.

**Proposed patch:**
```python
_CORS_ALLOWED = [
    "https://agentshq.boubacarbarry.com",
    "http://localhost:3000", "http://localhost:5173", "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ALLOWED,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-Api-Key", "X-Internal-Token"],
    allow_credentials=True,
)
```

**Touches protected work?** Lines predate the window. Safe.

---

#### P1-4. Emoji command handlers (200+ lines) embedded inline in `process_telegram_update`

**Severity:** High (maintainability).
**Karpathy:** #2 (simplicity: `process_telegram_update` alone is 400+ lines with 5 inline emoji blocks).

**Evidence:** `orchestrator.py:1332-1683`. Filing, edit, new project, flag, approve routing matrix. Each with 60-90 lines of inline Postgres + gws_cli_tools calls.

The EXTRACTED module `handlers_doc.py` already exists but is a stub. It has the structure for filing but the other 4 are marked "for brevity in this turn, I am establishing the structure". This is exactly the incomplete refactor from P1-1.

**Proposed patch:** Fold this into P1-1 Phase A. Extract the 5 emoji blocks to `handlers_doc.py` properly, then use the modular entrypoint.

**Touches protected work?** handlers_doc.py IS in the protected window. Proposal completes it, doesn't delete it.

---

### P2 : Medium

#### P2-1. Silent telemetry loss: `router_log` table doesn't exist

**Severity:** Medium (observability).
**Karpathy:** #4 (Goal-driven: writes to non-existent table are fire-and-forget by design, but the table was never created).

**Evidence:**
- `orchestrator/router.py:467-474`: `INSERT INTO router_log (...)` fires for every classify call
- Postgres: `SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='router_log')` returns `f` (false)
- The bounded queue at `router.py:447-502` gracefully handles the error, but you're losing every routing decision to a silent drop.

**Proposed patch:** Create a migration `orchestrator/migrations/003_router_log.sql`:
```sql
CREATE TABLE IF NOT EXISTS router_log (
    id             bigserial PRIMARY KEY,
    ts             timestamptz NOT NULL DEFAULT now(),
    message        text NOT NULL,
    task_type      text,
    crew           text,
    used_llm       boolean,
    router_version text
);
CREATE INDEX idx_router_log_ts ON router_log (ts DESC);
CREATE INDEX idx_router_log_task_type ON router_log (task_type);
```
Apply via `docker exec orc-postgres psql -U postgres -f /tmp/003_router_log.sql`. No code changes needed, the inserts will start succeeding.

**Touches protected work?** The bounded queue was added 2026-04-20 (commit `37ccef9`). The table creation is completing intent, not changing recent work.

---

#### P2-2. Metaclaw container runs idle, zero API calls in 7 days, 177MB RAM wasted

**Severity:** Medium (dead infra). OUTSIDE protected window, built 2026-03-31.
**Karpathy:** #2 (speculative feature that never landed).

**Evidence:**
- Docker stats: `orc-metaclaw  0.24% CPU  177.4MiB RAM`
- `docker logs orc-metaclaw` (7 days): only healthz hits from Docker healthcheck, zero external API traffic
- `grep -rn "metaclaw" orchestrator/*.py`: 0 matches. No Python code references metaclaw.
- Integration plan at `docs/superpowers/plans/2026-03-31-metaclaw-integration.md` specified `get_llm_metaclaw()` factory in `agents.py`. Never implemented.
- `USE_METACLAW=true` env var exists but is not read anywhere in Python code
- Container builds from local `./metaclaw/` directory, depends on postgres, qdrant via `depends_on: service_started`

**Proposed patch (no touch on protected work, purely removal of unused infra):**

Option A (recommended): Decommission Metaclaw in docker-compose.yml.
1. Comment out the `metaclaw:` service block (docker-compose.yml:80-111)
2. Remove `metaclaw: condition: service_started` from orchestrator `depends_on`
3. Remove `USE_METACLAW` env var from orchestrator service
4. `docker compose up -d`. The orchestrator boots faster, 177MB RAM freed.
5. Archive the `metaclaw/` directory to `_archive_20260423/metaclaw/` with a `WHY.md` per your sunset pattern (memory: `project_vps_orphan_archive_20260421`)

Option B: Complete Phase 1 integration (wire `get_llm_metaclaw()` into 3 agents per the spec). This is a build, not a cleanup. Would be a separate session.

My recommendation: Option A. The integration plan hasn't been touched in 22 days. If/when you want it, rebuild from scratch. The codebase has evolved since the spec.

---

#### P2-3. `sync_artifact_to_notion` opens a new Qdrant client + embedding + HTTP request per task, with zero observability

**Severity:** Medium (cost + reliability).
**Karpathy:** #4 (no telemetry on whether syncs succeed).

**Evidence:** `memory.py:685-764`. Every save_to_memory triggers a daemon thread that calls Notion. No metric counts successes vs failures. If Notion is down or the DB ID is wrong, every sync silently drops with a log line.

**Proposed patch:** Add a simple counter table `notion_sync_events (id, task_type, ts, status, error)` and increment on every call. Review weekly via /cost-style Telegram command.

**Touches protected work?** memory.py last modified 2026-04-20 (`9a074d3` token-economy phases 1-2). In-window. Proposal is additive instrumentation, not removal.

---

#### P2-4. `_trigger_evolution` hook fires OpenSpace on every successful background job, zero activity in logs

**Severity:** Medium (dead feature gating).
**Karpathy:** #2 (speculative: fires but no evidence it does anything).

**Evidence:**
- `orchestrator.py:1198-1225` spawns a thread for `openspace_tool.execute_async(...)` after every job
- `docker logs orc-crewai --since 7d | grep -iE 'openspace|evolution'` returns empty
- `DISABLE_EVOLUTION` env var default false, so this code IS firing

**Proposed patch:** Either (a) add a log line when it starts/completes so we can see it working, or (b) flip the default to disabled until someone verifies OpenSpace is actually doing something. Cheapest fix is (a): add `logger.info` at entry and after execute_async completes. Cost if currently broken: LLM calls with no benefit.

**Touches protected work?** Lines are older than window. Safe.

---

### P3 : Low

#### P3-1. Hardcoded VPS IP in debug string

**Evidence:** `orchestrator.py:296`: `lines.append("  VPS: 72.60.209.109 : orchestrator on port 8000")`

**Fix:** Read from `os.environ.get("VPS_IP", "…")`. (env var already exists in docker-compose.yml:138.)

---

#### P3-2. Dockerfile ships `tests/` and `docs/` into production image

**Evidence:** `Dockerfile:39, 40`. `COPY tests/ tests/` and `COPY docs/ docs/`. Tests and docs increase image size and expose implementation details.

**Fix:** Remove `COPY tests/` line. Docs are needed for quote bank, so scope to only what's needed.

---

#### P3-3. `task_queue` table is empty and schema-incompatible with current code

**Evidence:** Postgres schema shows `task_queue` exists with `task_id`, `from_number` columns, but code (orchestrator.py:1764) uses `job_queue` with different schema. Rows: 0. Legacy table.

**Fix:** Drop `task_queue`. Verify no callers first.

Outside protected window.

---

#### P3-4. Shell=True in LaunchVercelAppTool (Vercel deploys)

**Evidence:** `tools.py:156`. `subprocess.run(cmd, shell=True, ...)` with user-derived `app_name` interpolated.

User confirmed: Vercel is used for app testing, this tool is active.

**Proposed patch:** Replace `shell=True` with argument list:
```python
# BEFORE
cmd = f"bash \"{script_path}\" \"{clean_name}\" {prod_flag}"
result = subprocess.run(cmd, shell=True, ...)

# AFTER
# Validate app_name against allowlist
import re
if not re.match(r"^[a-zA-Z0-9_-]+$", clean_name):
    return f"Invalid app_name: {clean_name!r}. Alphanumeric, dash, underscore only."
args = ["bash", script_path, clean_name]
if is_prod:
    args.append("--prod")
result = subprocess.run(args, shell=False, capture_output=True, text=True, cwd=base_dir)
```
Same behavior, no shell injection surface.

---

#### P3-5. One orphan root file: `send_diagram_email.py` (2026-04-07)

**Evidence:** Never imported from anywhere in the repo. No callers.

Outside protected window. Safe to delete.

---

#### P3-6. Misplaced documentation

**Evidence:** `agentsHQ-hyperframes-knowledge-update.md` lives at repo root. Would belong in `docs/` with other knowledge notes.

Touches protected work (2026-04-17). Propose relocation, not deletion. `git mv` to `docs/`.

---

### P4 : Nice-to-have / missing production essentials

#### P4-1. No Postgres backup cron

Production data (780 conversation history rows, 270 jobs, 122 LLM calls, 15 council runs) lives in `postgres_data` Docker volume with no scheduled dump. A `pg_dump` cron running nightly to `/root/backups/agentshq_YYYY-MM-DD.sql.gz` would solve this.

#### P4-2. No rate limiting on `/chat-token`

PIN-protected but not rate-limited. A 4-digit PIN could be brute-forced. Add simple IP-based rate limiting: 10 attempts per hour per IP.

#### P4-3. No pytest CI on commits

`tests/` has 28 files. `orchestrator/tests/` has 4. No GitHub Actions workflow runs them. `deploy-agentshq.yml` only triggers on orchestrator/ changes without running tests first. Add a `pytest.yml` workflow that runs on PRs.

#### P4-4. No `/metrics` endpoint for Prometheus/Grafana

Token ledger in DB is rich but requires SQL queries. A `/metrics` endpoint exposing cost-per-day, route hit counts, auth failures, job queue depth would let you wire Grafana dashboards in an afternoon. Optional but high leverage.

#### P4-5. `agent_learnings` table has 8 rows despite live infrastructure

MEMORY_LEARNING_ENABLED gate is everywhere. Is it set to true anywhere? If false in prod env, the whole learning loop is dormant code. Worth confirming.

---

## Orphan Inventory (final consolidated list)

**Hard orphans (zero importers, zero callers, outside protected window):**
- `send_diagram_email.py`. Propose delete (P3-5).
- `agents/security_agent/security_agent.py`. Verify no cron uses it; VPS crontab references it, keep.
- `agents/outfit_stylist/app.py`. Separate microservice with its own systemd unit, not part of orchestrator; keep.
- `test_sankofa.py` (root, untracked). Local-only; ignore.
- `LESSONS-LEARNED.md` (Mar 31, pre-Karpathy). Propose archive to `docs/archive/`.

**Soft orphans (zero live callers but newly added, PROTECTED):**
- `orchestrator/app.py`, `engine.py`, `handlers.py`, `handlers_chat.py`, `handlers_doc.py`, `worker.py`, `state.py`, `schemas.py`, `constants.py`, `utils.py` (partial). Complete P1-1 refactor.

**Stale but wired:**
- `orchestrator/handlers_doc.py`. Stub; complete as part of P1-1.

**Dead infra (outside window):**
- `metaclaw/` container + directory. P2-2 decommission or reseed.

**Misplaced:**
- `agentsHQ-hyperframes-knowledge-update.md` at root. Should be in docs/.

**Missing infrastructure:**
- `router_log` Postgres table
- `notion_sync_events` Postgres table (recommended)

---

## Hijacking Surface Audit (4 categories you requested)

| Category | Status | Notes |
|---|---|---|
| (a) Security backdoors, hardcoded secrets | 1 finding | `"fallback-secret"` JWT fallback (P0-2) |
| (b) Dependencies phoning home | CLEAN | All pinned, all legitimate, requirements.txt at orchestrator/requirements.txt |
| (c) Agents making unexpected outbound calls | CLEAN | All destinations catalogued: OpenRouter, Anthropic, Notion, Google, Telegram, GitHub, Firecrawl, Kie.ai, your n8n |
| (d) External exposure | 1 finding | Port 8000 on 0.0.0.0 bypasses Traefik (P0-1) |

Zero eval/exec, zero unsafe deserialization, zero unsafe yaml loads in your code. Matches for those patterns exist only in the `skills/community/` submodule (external code, out of scope).

---

## Karpathy Compliance Scorecard

| # | Principle | Score | Top Violation |
|---|---|---|---|
| 1 | Think before coding | PASS | Every major file has intent/architecture header. Drift section in routing-architecture.md is exemplary. |
| 2 | Simplicity first | FAIL | Three files over 1,800 lines. 200+ line inline handlers. 52 tool classes in one file. |
| 3 | Surgical changes | FAIL structurally | Refactor was purely additive. 19 symbols duplicated across modules. |
| 4 | Goal-driven execution | MIXED | Good: token ledger, job_queue, health registry. Bad: 10+ broad except blocks, missing router_log table, no explicit success criteria on background jobs. |

---

## Proposed Execution Plan : Priority Order

Single session recommended. Approximately 2 hours of work. One save point tag before starting.

### Step 0. Save point (5 min)
```bash
git tag savepoint-pre-code-review-cleanup-20260423
git push origin savepoint-pre-code-review-cleanup-20260423
```

### Step 1. P0 security fixes (20 min)
1. `docker-compose.yml:124` bind `127.0.0.1:8000:8000` instead of `0.0.0.0:8000`
2. `ssh root@agentshq.boubacarbarry.com` then `ufw default deny incoming; ufw allow 22,80,443/tcp; ufw enable`
3. Edit `orchestrator.py:128-130`. Fail-closed with `DEBUG_NO_AUTH` opt-in.
4. Edit `orchestrator.py:2582`. Remove the hardcoded fallback default.
5. Add `Depends(verify_api_key)` to 7 ungated routes. Before/after diff attached to each.
6. Narrow CORS to `agentshq.boubacarbarry.com` + localhost
7. Deploy, verify chat login + Telegram + Claude Code `/run-sync` all still work

Commit: `fix(security): close all public exposure + fail-closed auth + CORS lock`

### Step 2. P1-1 refactor completion (45 min)
1. Port any orchestrator.py drift into app.py + engine.py + handlers.py (diff in detail)
2. Fill `handlers_doc.py` with edit/new/flag/approve handlers (extract from orchestrator.py:1436-1682)
3. Dockerfile:52 flip `orchestrator:app` → `app:app`
4. Deploy, test: Telegram, browser chat, /inbound-lead, /run-sync, emoji commands
5. Keep orchestrator.py in repo as reference for 1 cycle

Commit: `refactor(orchestrator): complete modular split : app.py is live entrypoint`

### Step 3. P1-2/P1-3 cleanups (20 min)
1. Centralize DB connects on `memory._pg_conn()` or `db.get_local_connection()`
2. Narrow CORS (if not already done in Step 1)

Commit: `chore(cleanup): centralize DB connects, finalize CORS scope`

### Step 4. P2 telemetry + infra (30 min)
1. Apply migration `003_router_log.sql`
2. Decommission Metaclaw (comment out in docker-compose.yml, archive dir)
3. Add log lines to `_trigger_evolution` entry/exit
4. `shell=True` → argument list in LaunchVercelAppTool

Commit: `chore(infra): router_log migration, decommission metaclaw, shell hardening`

### Step 5. P3/P4 housekeeping (20 min)
1. Delete `send_diagram_email.py`
2. Move `agentsHQ-hyperframes-knowledge-update.md` → `docs/`
3. Archive `LESSONS-LEARNED.md` → `docs/archive/`
4. Drop legacy `task_queue` table
5. Remove hardcoded VPS IP
6. Remove `COPY tests/` from Dockerfile

Commit: `chore(cleanup): orphan files, misplaced docs, image slim-down`

### Step 6. Verification pass (10 min)
1. `/status` endpoint returns valid state
2. Send Telegram test message. Round trip works.
3. Browser chat login + send message. Works.
4. n8n webhook test. `/inbound-lead` works.
5. `/cost` Telegram command. Shows ledger data.
6. `docker stats`. Memory down (Metaclaw removed).

---

## What NOT to do

Per your protection rule, I am NOT proposing:
- Deletion of any file in `orchestrator/` modified after 2026-04-17 (the refactor island)
- Removal of `skills/inbound_lead/*`
- Changes to `research_engine.py`, `kie_media.py`, `usage_logger.py`, `content_board_reorder.py`, `scrub_titles.py`
- Changes to the LLM router architecture (protected per `docs/routing-architecture.md`)
- Changes to `council.py` voice + model selections (protected per `docs/llm_ranking_review.md`)
- Changes to the token economy ledger (protected per `project_token_economy`)
- Changes to `design_context.py` or design agent wiring (protected, Apr 17)
- Any touch to `docs/AGENT_SOP.md`, `docs/routing-architecture.md`, `docs/llm_ranking_review.md`

---

## Summary Numbers

| Metric | Value |
|---|---|
| Total commits in review window (2026-04-15 → 2026-04-22) | 172 |
| Python files in scope (excluding submodules) | 171 |
| Core orchestrator files | 30 |
| Top 3 files by line count | crews.py (2,884), orchestrator.py (2,748), tools.py (1,839) |
| Duplicated symbols between orchestrator.py and new modules | 19 |
| Live-dead lines (new module orphan island) | approximately 1,445 |
| External scanner probes in last 24h | 142 |
| Real 401 auth failures | 0 |
| LLM ledger rows (7 days) | 122 |
| Total LLM spend (7 days) | $0.66 |
| Chairman + Expansionist share of cost | 66% |
| `psycopg2.connect` inline call sites | 17 |
| Broad except-pass patterns | 10+ |
| Tables with zero rows (orphan candidates) | 7 (leads, n8n_chat_histories, lead_interactions, sop_changelog, security_events, task_queue, routing_matrix_proposals) |
| Tables with data (live) | 8 (agent_conversation_history 780, job_queue 270, conversation_archive 246, llm_calls 122, council_runs 15, pending_overflow 15, agent_learnings 8, notebooklm_pending_docs 6) |
| Qdrant collections | 2 (agentshq_memory, agentshq_learnings) |
| Unauthenticated sensitive routes | 7 (/run-sync, /classify, /capabilities, /outputs, /outputs/{filename}, /memory/search, /status/{job_id}) |
| Hardcoded secrets in live code | 1 (`"fallback-secret"`) |
| Unused containers | 1 (Metaclaw, 177MB RAM, 0 API calls in 7d) |
| Missing Postgres tables referenced by code | 1 (`router_log`) |

---

## Final Recommendation

Pull the trigger on Steps 0-3 this week. They are tight, reversible, and directly address the biggest risks (external exposure, auth drift) while completing your in-flight refactor.

Steps 4-5 can run in a second session when you want a cleanup day.

P4 items (Postgres backup, pytest CI, /metrics) are genuine gaps but can live on the backlog. They're not gate-keepers to anything on the revenue path.

Touch nothing else. The recent 7 days of work is high-quality. The problem is not missing features, it's that the intentional refactor never finished crossing the finish line.
