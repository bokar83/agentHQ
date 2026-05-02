# Adversarial Report : Level 2 Deep Audit (Skeptical Hostile Auditor)

Date: 2026-04-22  
Scope: Entire `agentsHQ` repository with heavy focus on orchestrator, memory, database connectivity, and agent/skill execution surfaces.

## Verdict
**FAIL**. The current setup contains exploitable security gaps and structural weaknesses.

- Critical findings: **3**
- Architectural findings: **2**

## Protocol Compliance (from `.agents/workflows/adversarial-review.md`)
1. Skeptical reading: Completed on `orchestrator/*.py`, `orchestrator/skills/*`, `skills/*` (non-community), `agents/*`, deployment files.
2. Assumption mapping: Completed (see section below).
3. Active stress-test: Completed with scratch script at `tmp/adversarial_stress_test.py`.
4. Revenue engine audit: Completed (voice + lead-gen pathways validated; risk impact documented).
5. Findings/verdict artifact: This file.

## Assumption Mapping (Trusted Inputs / Services)
- HTTP caller identity is trusted to be authenticated at the route level.
- Telegram webhook payload is trusted as source-of-truth input.
- Agent tool input payloads (`filename`, `app_name`, etc.) are trusted as safe.
- External callback targets (`callback_url`) are trusted as safe to POST to.
- Memory/storage layers (Postgres + Qdrant) are treated as optional and failure-tolerant.
- Service boundaries rely on env configuration (`ORCHESTRATOR_API_KEY`, `ALLOWED_USER_IDS`, tokens).

## Active Stress-Test (Protocol Step 3)
Script: `tmp/adversarial_stress_test.py`  
Execution: `python tmp/adversarial_stress_test.py`

Observed output highlights:
- Sensitive routes without auth dependencies detected: `/run-sync`, `/classify`, `/capabilities`, `/outputs`, `/outputs/{filename}`, `/memory/search`, `/status/{job_id}`.
- `subprocess.run(..., shell=True)` detected in `orchestrator/tools.py`.
- SaveOutput path escape simulation confirmed traversal outside `/app/outputs`.

## Critical Findings

### C1) Unauthenticated Execution and Data Exposure Surface
**Severity:** Critical  
**Why it matters:** External callers can run agent workflows and read internal outputs/status without API key checks on several high-impact routes.

**Evidence:**
- Unprotected sync execution endpoint:
  - `orchestrator/orchestrator.py:2139` (`@app.post("/run-sync", response_model=TaskResponse)` with no dependency)
- Additional unauthenticated sensitive read endpoints:
  - `orchestrator/orchestrator.py:2232` (`/classify`)
  - `orchestrator/orchestrator.py:2248` (`/capabilities`)
  - `orchestrator/orchestrator.py:2264` (`/outputs`)
  - `orchestrator/orchestrator.py:2287` (`/outputs/{filename}`)
  - `orchestrator/orchestrator.py:2308` (`/memory/search`)
  - `orchestrator/orchestrator.py:2488` (`/status/{job_id}`)
- Auth function allows full bypass if key missing:
  - `orchestrator/orchestrator.py:128-130` (`if not expected: return`)
- Service is published externally:
  - `docker-compose.yml:124` (`"8000:8000"`)
  - `docker-compose.yml:200` (Traefik router exposes API path)

**Attack path:**
1. Call `/run-sync` anonymously.
2. Trigger agent tasks that can write files, query memory, or perform external actions.
3. Pull artifacts via `/outputs` and `/outputs/{filename}`.

---

### C2) Command Injection in Vercel Launch Tool
**Severity:** Critical  
**Why it matters:** User-influenced text is interpolated into a shell command and executed with `shell=True`, enabling arbitrary command execution in the orchestrator runtime.

**Evidence:**
- Weak sanitization:
  - `orchestrator/tools.py:142` (`clean_name = app_name.replace("-app", "")`)
- Shell string construction with user-derived content:
  - `orchestrator/tools.py:151` (`cmd = f"bash \"{script_path}\" \"{clean_name}\" {prod_flag}"`)
- Shell execution enabled:
  - `orchestrator/tools.py:156` (`subprocess.run(cmd, shell=True, ...)`)
- Tool broadly exposed:
  - `orchestrator/tools.py:1835-1836` (`launch_vercel_tool` included in `CODE_TOOLS` and `ORCHESTRATION_TOOLS`)

**Attack path:**
1. Send crafted task that causes tool invocation with malicious `app_name` payload.
2. Shell metacharacters break command context.
3. Arbitrary OS command executes in container context.

---

### C3) Arbitrary File Write via SaveOutputTool Path Traversal
**Severity:** Critical  
**Why it matters:** Agent-invoked file writes accept attacker-controlled filenames without path confinement, allowing writes outside `/app/outputs`.

**Evidence:**
- Filename accepted directly:
  - `orchestrator/tools.py:901` (`filename = data.get("filename", ...)`)
- No traversal/absolute-path validation:
  - `orchestrator/tools.py:907` (`filepath = os.path.join(output_dir, filename)`)
- Direct write:
  - `orchestrator/tools.py:908` (`with open(filepath, "w", ...)`)
- Tool is pervasive:
  - `orchestrator/tools.py:1834-1835` (`SaveOutputTool()` in `WRITING_TOOLS` and `CODE_TOOLS`)

**Stress-test confirmation:**
- `tmp/adversarial_stress_test.py` resolved `../../secrets/owned.txt` outside base output directory.

**Attack path:**
1. Prompt agent to call `save_output` with traversal filename.
2. Overwrite/plant files outside intended output directory.
3. Persist malicious content or sabotage runtime artifacts.

## Architectural Findings

### A1) Security Policy Drift from Dual FastAPI Implementations
**Severity:** Architectural  
**Why it matters:** Two app modules define overlapping responsibilities with conflicting auth behavior, creating patch drift and false confidence.

**Evidence:**
- `orchestrator/app.py` is fail-closed when API key missing:
  - `orchestrator/app.py:50-54`
- `orchestrator/orchestrator.py` is fail-open when API key missing:
  - `orchestrator/orchestrator.py:128-130`
- Runtime entrypoint uses only one module:
  - `orchestrator/Dockerfile:52` (`uvicorn orchestrator:app`)

**Consequence:** Security fixes applied to the wrong file won’t protect production. Behavior differs by entrypoint and environment.

---

### A2) Memory/DB Reliability is Fail-Open and Non-Observable
**Severity:** Architectural  
**Why it matters:** Persistence failures are routinely downgraded to warnings while success is still reported; DB access uses repeated ad-hoc connections with no pooling.

**Evidence:**
- Save pipeline masks failures and still returns success:
  - `orchestrator/memory.py:105-106` (Qdrant save failure non-fatal)
  - `orchestrator/memory.py:134-135` (Postgres save failure non-fatal)
  - `orchestrator/memory.py:137` (`return True` regardless)
- Repeated direct `psycopg2.connect` patterns across hot paths:
  - `orchestrator/memory.py:111-117`, `188-194`, `222-228`, `251-257`
- Upstream orchestration also suppresses memory failures:
  - `orchestrator/engine.py:153-154`, `223-224`

**Consequence:** Silent data loss in memory/analytics/audit trails, weak SLO observability, and higher connection pressure under load.

## Revenue Engine Audit (Voice + Lead-Gen Integrity)
- Voice guardrails still present in review pipeline:
  - `orchestrator/crews.py:2483-2492` (explicit anti-generic voice rules)
  - `orchestrator/engine.py:184-186` (voice polisher post-processing)
- Lead metrics and CRM summary pipeline still present:
  - `orchestrator/tools.py:1579-1591` (CRM aggregate query)

**Risk note:** Due to C1, unauthorized callers can trigger workflows that alter lead pipeline state and distort revenue metrics integrity.

## Remediation Priorities
1. Enforce auth dependency on all non-public routes (`/run-sync`, `/outputs*`, `/memory/search`, `/status/*`, `/classify`, `/capabilities`); remove fail-open auth fallback.
2. Eliminate `shell=True` in `LaunchVercelAppTool`; use argument lists and strict allowlist validation for `app_name`.
3. Constrain `SaveOutputTool` writes to a canonical output root using normalized path checks and explicit filename allowlist.
4. Consolidate to one FastAPI app module to eliminate policy drift.
5. Introduce DB connection pooling + hard failure telemetry for memory/audit persistence.

## Appendix: Commands Run (abbrev)
- `Get-Content .agents/workflows/adversarial-review.md`
- Pattern sweeps with `Select-String` across orchestrator and skills
- Targeted file reads with numbered lines (`orchestrator.py`, `tools.py`, `memory.py`, `db.py`, `crews.py`, `agents.py`, `docker-compose.yml`, `Dockerfile`)
- Stress script creation/execution: `tmp/adversarial_stress_test.py`
