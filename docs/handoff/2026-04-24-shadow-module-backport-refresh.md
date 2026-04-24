# Session Handoff: Shadow Module Backport (REFRESH)

**Supersedes:** `docs/handoff/2026-04-23-shadow-module-backport-handoff.md` (written 2026-04-22, now stale)
**Date refreshed:** 2026-04-24
**Target execution date:** current session
**Estimated time:** 5 to 7 hours focused, or three 2-hour halves
**Risk:** High. Flips the Dockerfile entrypoint in production. Must not break browser chat, Telegram polling, Claude Code, n8n, OR the approval queue / heartbeat / autonomy surfaces that shipped AFTER the original handoff was written.

---

## Why this refresh exists

The 2026-04-23 handoff was written at the close of the 2026-04-22 security-cleanup session. Between then and now, five PRs merged that expanded the monolith:

```
64dd319 Phase 0: autonomy safety rails (spend cap, kill switch, feature flags) (#9)
39ee56f Phase 1: episodic memory + approval queue (#10)
2f85ed7 fix(phase1): address Codex review findings on PR #10 (#11)
25213f0 fix(phase1): address Codex review round 2 on PR #11 (#13)
bdb8401 Phase 2: heartbeat scheduler (#12)
```

These added roughly 500 lines of new logic inside `process_telegram_update` and 11 new slash commands. The original handoff does not account for any of it. A naive execution of the 2026-04-23 plan would silently regress freshly-shipped, Codex-reviewed work.

The monolith is now **3,200 lines**, not 2,748. All line-number references in the original handoff are stale.

---

## Current state (verified 2026-04-24)

**Dockerfile CMD:** `uvicorn orchestrator:app --host 0.0.0.0 --port 8000 --log-level info`
**Live module:** `orchestrator/orchestrator.py` (3,200 lines)
**Shadow modules:** same 11 files, but the shadow `app.py` now has broken imports against the current codebase (see gap #1 below).

**Verified blocking bugs in current shadow code (would prevent `uvicorn app:app` from starting):**

1. `app.py:13` imports `_git_lock` from `state`: `state.py` does not export it. Will `ImportError` on boot.
2. `app.py:14-18` imports `HealthReportRequest`, `SyncSessionRequest`, `ChatTokenRequest` from `schemas`: `schemas.py` does not define them. Will `ImportError` on boot.

So even without the feature gaps, the shadow entrypoint cannot start today.

---

## Full gap inventory (monolith has, shadow is missing)

Seven gaps from the original handoff, still valid but with corrected line numbers, plus six new gaps from Phases 0/1/2.

### A. Original seven gaps (still accurate, line numbers updated)

| # | Gap | Monolith | Shadow |
|---|---|---|---|
| A1 | Rich `run_chat` (Simpsons persona + 4 tools + history) | `orchestrator.py:329-661` (330 lines) | `handlers.py:18-40` (20-line CrewAI stub) |
| A2 | `_query_system` with agent descriptions + output files + infra block | `orchestrator.py:253-326` | `utils.py:31-57` (no descriptions, no outputs, no infra) |
| A3 | `_shortcut_classify` / `_classify_obvious_chat` correct logic | `orchestrator.py:1281-1298` (uses `router._keyword_shortcut`, tight greeting set) | `handlers.py:162-173` (hardcodes `"find leads"` / `"research"`, broad chat triggers, violates routing-architecture rule 4) |
| A4 | Praise/critique regex richness | `orchestrator.py:1305-1339` (word lists) | `handlers_chat.py:9-32` (regex with emojis), align / union |
| A5 | `_run_background_job` compound email + hunter email + evolution + learning + `_last_completed_job` | `orchestrator.py:1062-1220` (158 lines) | `worker.py:9-91` (91 lines, none of the above) |
| A6 | `telegram_polling_loop` 3-attempt deleteWebhook + 401 halt + `callback_query` in `allowed_updates` | `orchestrator.py:2347-2398` | `handlers.py:135-160` (single-attempt, no 401 halt, **no callback_query in allowed_updates, approval buttons broken**) |
| A7 | Original six slash commands (`/cost /projects /status-by-id /lessons /purge-lesson /scan-drive`) | `orchestrator.py:1887-2041` | `handlers.py:84-105` (only `/switch` and minimal `/status`) |

### B. New gaps from Phases 0/1/2 (NOT in original handoff)

| # | Gap | Where to port from | Notes |
|---|---|---|---|
| B1 | `callback_query` branch (inline-button feedback tag) at start of `process_telegram_update` | `orchestrator.py:1350-1377` | Phase 1. Handles `feedback_tag:<id>:<value>` button taps from rejections. |
| B2 | Approval-queue reply handling + `_PENDING_FEEDBACK_WINDOWS` eviction + reply-to-message approvals + fallback `yes confirm` / `no confirm` + doc-routing precedence | `orchestrator.py:1402-1531` (~130 lines) | Phase 1. `_PENDING_FEEDBACK_WINDOWS` dict lives at `orchestrator.py:84`: must move to `state.py`. |
| B3 | Nine new slash commands: `/autonomy_status /pause_autonomy /resume_autonomy /spend /queue /approve /reject /outcomes /heartbeat_status /trigger_heartbeat` | `orchestrator.py:2057-2254` | Phases 0/1/2. Grouped with the original six in a new `handlers_commands.py`. |
| B4 | `/run-team`, `/capabilities`, `/outputs`, `/outputs/{filename}`, `/memory/search`, `/history/{session_id}`, `/run-async`, `/chat-token`, `/autonomy/approve/{queue_id}`, `/internal/health-report` route set | `orchestrator.py:2596-3168` | Shadow `app.py` has none of these. |
| B5 | `startup_event` must call `install_litellm_callback()` (token ledger) | `orchestrator.py:180-184` | Shadow startup skips it, would silently break the /cost ledger after the flip. |
| B6 | `run_task_async` `_run_in_background` logic (file injection, friendly error shaping, callback_url POST) | `orchestrator.py:2803-2925` | Used by the browser chat UI via `/run-async`. Non-trivial (~130 lines). |

### C. Module-level state that must move to `state.py`

| Symbol | Currently in | Needed by |
|---|---|---|
| `_PENDING_FEEDBACK_WINDOWS` | `orchestrator.py:84` | B2 (approval queue reply) |
| `_git_lock` | `orchestrator.py:246` | shadow `app.py:13` already tries to import it |
| `_PRAISE_SIGNALS`, `_CRITIQUE_SIGNALS` | `orchestrator.py:1305-1316` | A4 |
| `_TASK_KEYWORDS`, `_CHAT_PREFIXES` | `orchestrator.py:1266-1279` | A3 / A7 helpers |

### D. Schema and constant gaps

- `schemas.py` must gain `HealthReportRequest`, `SyncSessionRequest`, `ChatTokenRequest` (for B4).
- `constants.py` already has `SAVE_REQUIRED_TASK_TYPES` and `MEMORY_GATED_TASK_TYPES`: verified.

### E. Doc-routing precedence + connection hygiene (Codex round 2 findings)

- `_doc_routing_pending()` in the monolith uses try/finally to close conn in all paths (PR #11 Codex P2 fix).
- Must be preserved when porting B2.

---

## Files touched by this work

| File | Type | Scope |
|---|---|---|
| `orchestrator/state.py` | modify | add `_PENDING_FEEDBACK_WINDOWS`, `_git_lock`, `_PRAISE_SIGNALS`, `_CRITIQUE_SIGNALS`, `_TASK_KEYWORDS`, `_CHAT_PREFIXES` |
| `orchestrator/schemas.py` | modify | add 3 missing models |
| `orchestrator/handlers.py` | major rewrite | replace classifiers, rewrite `process_telegram_update` in full, harden polling loop, delete generic `run_chat` stub (moves to `handlers_chat.py`) |
| `orchestrator/handlers_chat.py` | modify | port rich `run_chat` + tool handlers; align praise/critique word lists (union) |
| `orchestrator/handlers_commands.py` | **NEW** | all 15 slash commands, one function per command, single dispatcher |
| `orchestrator/handlers_approvals.py` | **NEW** | Phase 1 reply/approval logic (B1, B2), too big to live inline in handlers.py |
| `orchestrator/worker.py` | major expand | add compound email, hunter email, `_trigger_evolution`, `extract_and_save_learnings`, `_last_completed_job` writes |
| `orchestrator/utils.py` | modify | richer `_query_system` |
| `orchestrator/app.py` | major expand | add `install_litellm_callback()` to startup, add B4 routes, fix imports |
| `orchestrator/Dockerfile` | 1 line | CMD `orchestrator:app` -> `app:app`: **LAST** |

**Files NOT touched (protected):**
- `orchestrator/orchestrator.py`: stays as rollback reference for one week post-flip
- `orchestrator/router.py`: routing-architecture.md critical rules
- `orchestrator/council.py`: llm_ranking_review.md protected voices/models
- `orchestrator/research_engine.py`, `kie_media.py`, `usage_logger.py`, `content_board_reorder.py`, `scrub_titles.py`
- `orchestrator/autonomy_guard.py`, `approval_queue.py`, `episodic_memory.py`, `heartbeat.py`: Phase 0/1/2 code, just import from it
- `docs/AGENT_SOP.md`, `docs/routing-architecture.md`, `docs/llm_ranking_review.md`

---

## Execution order (refreshed plan)

Each step has a verification gate. No step moves to the next until the prior step's gate passes.

### Step 0, Save point (5 min)

```bash
git tag savepoint-pre-shadow-backport-2026-04-24
git push origin savepoint-pre-shadow-backport-2026-04-24
```

**Gate:** tag visible in `git ls-remote --tags origin | grep shadow-backport`.

### Step 1, Fix shadow import blockers + state migration (20 min)

Touch `state.py` and `schemas.py` only. Make the dormant shadow importable before touching behavior.

1. `state.py`: add `_PENDING_FEEDBACK_WINDOWS: dict = {}`, `_git_lock = threading.Lock()`, praise/critique word lists, task keywords / chat prefixes.
2. `schemas.py`: add `HealthReportRequest`, `SyncSessionRequest`, `ChatTokenRequest`.

**Gate:** `python -c "import orchestrator.app"` from repo root completes without `ImportError` (may still fail at runtime, but import resolves).

### Step 2, Align classifiers (15 min)

Per routing-architecture.md rules 3 and 4. Touch `handlers.py` only.

- Delete `_shortcut_classify` and `_classify_obvious_chat` in handlers.py.
- Replace with the monolith versions from orchestrator.py:1281-1298. Must use `from router import _keyword_shortcut` and the tight greeting set (`hi`, `hey`, `hello`, `thanks`, `thank you`, `morning`, `good morning`, `good evening`).

**Gate:** `_classify_obvious_chat("find me dentists in 84095")` returns `False`. `_classify_obvious_chat("hello")` returns `True`.

### Step 3, Port rich run_chat to handlers_chat.py (45 min)

- Move `run_chat` out of `handlers.py` and put the rich version in `handlers_chat.py`.
- Port the Simpsons persona system prompt, 4 tool definitions (`query_system`, `retrieve_output_file`, `save_memory`, `forward_to_crew`), `_retrieve_output_file` helper, tool-call dispatch, conversation-history loading with trailing-assistant strip.
- Update `handlers.py` dispatcher to import `run_chat` from `handlers_chat`.

**Gate:** `run_chat("hi")` returns a dict with `success`, `result`, `task_type="chat"`. The result contains a Simpsons quote (we can verify with a test env `OPENROUTER_API_KEY`).

### Step 4, Create handlers_commands.py with all 15 slash commands (60 min)

One function per command, all return `True` if handled or `False` if not applicable. Single `dispatch_command(text, chat_id)` entry point used by `handlers.py`.

- Original 6 from A7: `/cost`, `/projects`, `/status [job_id]`, `/lessons`, `/purge-lesson`, `/scan-drive`
- Phase 0/1/2 9 from B3: `/autonomy_status`, `/pause_autonomy`, `/resume_autonomy`, `/spend`, `/queue`, `/approve`, `/reject`, `/outcomes`, `/heartbeat_status`, `/trigger_heartbeat`, `/switch`

**Gate:** unit test that each command function returns a tuple (handled: bool, reply: str) and that `dispatch_command("/queue", chat_id)` returns `(True, ...)`.

### Step 5, Create handlers_approvals.py with Phase 1 reply logic (45 min)

Port B1 (callback_query) and B2 (approval-queue reply handling). This is the most subtle piece because of the doc-routing precedence rule.

- `handle_callback_query(update)`: Phase 1 inline-button feedback tag
- `handle_approval_reply(text, chat_id, reply_to_msg_id)`: reply-to-message approvals + alias parsing
- `handle_pending_feedback_tag(text, chat_id, reply_to_msg_id)`: the 5-minute free-text window
- `handle_naked_approval(text, chat_id)`: `yes confirm` / `no confirm` + doc-routing-pending check
- `_doc_routing_pending()`: the connection-hygiene helper (preserves Codex PR #11 P2 fix)

**Gate:** unit test each handler returns a tuple `(handled, reply)` and honors the eviction + doc-routing precedence rules from the commit history.

### Step 6, Rewrite process_telegram_update in handlers.py (60 min)

Now glue Steps 2-5 together. The new `process_telegram_update` becomes a thin orchestrator (~80 lines) that calls into the dispatchers in order:

1. `handle_callback_query(update)`: Phase 1
2. Extract message/text/chat_id/sender_id, auth check
3. `handle_approval_reply(...)`: Phase 1
4. `handle_pending_feedback_tag(...)`: Phase 1
5. `handle_naked_approval(...)`: Phase 1
6. `handle_doc_emoji(emoji, text, chat_id, reply_id)`: existing handlers_doc.py (unchanged)
7. `dispatch_command(text, chat_id)`: 15 slash commands
8. `handle_feedback(text, chat_id)`: praise/critique (Step 3 union)
9. Classify -> chat (via run_chat) or crew (via `_run_background_job`)

Must match the exact ordering in `orchestrator.py:1346-2345`. Any reordering risks regressing the feedback-window precedence rules added by PRs #10/#11/#13.

**Gate:** harness test that sends a synthetic `update` dict for each path (callback_query, reply-to approve, 5-min tag, slash command, emoji, praise, crew task, chat) and asserts the right handler fires.

### Step 7, Harden telegram_polling_loop in handlers.py (10 min)

- 3-attempt `deleteWebhook` with 2s sleep between attempts + warning log after 3 failures.
- `allowed_updates` must include `callback_query` (Phase 1 requirement, PR #10 commit `b5439a2`).
- 401 response stops the loop (invalid token).
- Non-401 errors sleep 5s.
- 30s timeout on the long-poll.

**Gate:** code inspection, must be byte-identical to `orchestrator.py:2347-2398` except for module/import names.

### Step 8, Expand worker.py (45 min)

- Compound email follow-up (`has_email_followup=True` + task_type filter).
- Hunter report email on `task_type == "hunter_task"`.
- `_last_completed_job[chat_id]` write in success path.
- `_trigger_evolution` in finally block (as daemon thread).
- `extract_and_save_learnings` in finally block (gated by `MEMORY_LEARNING_ENABLED` + `MEMORY_GATED_TASK_TYPES`).
- Keep the existing ping/watchdog timer intact.

**Gate:** run `_run_background_job` against a stub classification with `has_email_followup=True` and confirm the email crew builder is called (mock `build_gws_crew`).

### Step 9, Rewrite _query_system in utils.py (10 min)

Byte-port from `orchestrator.py:253-326`. Agent descriptions dict, task types with trigger keywords, recent output files (last 10 by mtime), infrastructure block with `VPS_IP` env var.

**Gate:** `_query_system()` output contains "INFRASTRUCTURE:" and "RECENT OUTPUT FILES" sections.

### Step 10, Expand app.py to full route set + startup (60 min)

- Fix imports (already done in Step 1).
- Add `install_litellm_callback()` to startup (B5).
- Add routes from B4: `/run-team`, `/capabilities`, `/outputs`, `/outputs/{filename}`, `/memory/search`, `/history/{session_id}`, `/run-async`, `/chat-token`, `/autonomy/approve/{queue_id}`, `/internal/health-report`.
- `/run-async` gets the full `_run_in_background` logic with file injection, friendly error shaping, callback_url POST (B6).
- `/chat-token` + `verify_chat_token` JWT helper.
- Align `verify_api_key` with the 2026-04-22 fail-closed version (already closer in app.py than it was in the pre-cleanup monolith, check for parity).

**Gate:** `uvicorn app:app --port 8001` boots. `curl http://127.0.0.1:8001/health` returns 200. `curl http://127.0.0.1:8001/capabilities` returns 401 without API key, 200 with.

### Step 11, Local smoke test on port 8001 (30 min)

With `.env.test` copied from VPS:

```bash
cd orchestrator
python -m uvicorn app:app --host 127.0.0.1 --port 8001
```

Tests (separate terminal, KEY from .env):

```bash
# Core
curl -sS http://127.0.0.1:8001/health | jq .
curl -sS -H "X-Api-Key: $KEY" http://127.0.0.1:8001/capabilities | jq . | head -5
curl -sS -H "X-Api-Key: $KEY" "http://127.0.0.1:8001/classify?task=find+me+dentists+in+84095" | jq .

# Chat + rich tool use (sync, slow but catches persona regression)
curl -sS -H "X-Api-Key: $KEY" -H "Content-Type: application/json" \
  -X POST http://127.0.0.1:8001/run-sync \
  -d '{"task":"hi"}'  # Expect a Simpsons-ish response

# Auth fail-closed
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8001/run-sync -X POST -d '{"task":"x"}'
# Expect: 401
```

**Do NOT test Telegram polling locally**, it would race with the VPS polling loop. Manual verification deferred to Step 13.

**Gate:** all four curls return expected output. No exceptions in the uvicorn log.

### Step 12, Flip Dockerfile entrypoint (1 line) (2 min)

```diff
- CMD ["uvicorn", "orchestrator:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
+ CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
```

**Gate:** diff shows exactly one line changed.

### Step 13, Deploy + 14-point verification (30 min)

Deploy protocol (per `feedback_container_file_sync`):

```bash
scp orchestrator/*.py root@agentshq.boubacarbarry.com:/root/agentsHQ/orchestrator/
scp orchestrator/Dockerfile root@agentshq.boubacarbarry.com:/root/agentsHQ/orchestrator/Dockerfile
ssh root@agentshq.boubacarbarry.com "cd /root/agentsHQ && docker compose up -d --build orchestrator"
```

**Verification checklist (14 checks, not 12):**

| # | Check | Expected |
|---|---|---|
| 1 | `GET /health` | 200 |
| 2 | `GET /api/orc/health` via Traefik | 200 |
| 3 | `POST /run-sync` unauth | 401 |
| 4 | `POST /run-sync` authed with `{"task":"hi"}` | 200, Simpsons-ish chat |
| 5 | Send a real Telegram message | Bot replies |
| 6 | `/cost` via Telegram | Ledger data |
| 7 | `/projects` via Telegram | Recent jobs list |
| 8 | `/queue` via Telegram | Empty or real proposals (Phase 1) |
| 9 | `/autonomy_status` via Telegram | Autonomy live, all crews off/dry-run |
| 10 | `/heartbeat_status` via Telegram | 3 registered wakes with next fire times (Phase 2) |
| 11 | Emoji command (filing/edit/new/flag/approve) | Full cycle completes |
| 12 | `POST /inbound-lead` synthetic payload | Accepted, Notion row created |
| 13 | `POST /chat-token` with valid PIN | Returns JWT |
| 14 | llm_calls table keeps growing after flip (token ledger alive) | Row count increases after a task |

**If check 10 fails**: the Phase 2 heartbeat did not re-register, `start_scheduler()` was not called or scheduler.py:425 `_heartbeat.start()` was skipped. Inspect logs first, do not redeploy.

**Rollback on any failure:**
```bash
git reset --hard savepoint-pre-shadow-backport-2026-04-24
ssh root@agentshq.boubacarbarry.com "cd /root/agentsHQ && docker compose up -d --build orchestrator"
```

### Step 14, Housekeeping (5 min)

- Keep `orchestrator/orchestrator.py` in the repo as the rollback reference for >= 7 days (do NOT delete).
- Update memory `project_shadow_module_backport.md` to COMPLETE with commit hash + rollback tag.
- Set a reminder for 2026-05-01 to delete `orchestrator.py` if all checks still green.

---

## Protected work cross-check

Nothing in this plan touches:
- `router.py` (routing-architecture critical rules 1-5)
- council voice models (`llm_ranking_review.md`)
- `research_engine.py`, `kie_media.py`, `usage_logger.py` (only imported, not modified)
- `content_board_reorder.py`, `scrub_titles.py`
- `docs/AGENT_SOP.md`

Phase 0/1/2 modules (`autonomy_guard.py`, `approval_queue.py`, `episodic_memory.py`, `heartbeat.py`) are imported but not modified, all their callers in the monolith get ported verbatim.

---

## Success criteria

1. Dockerfile CMD: `uvicorn app:app`
2. All 14 verification checks pass
3. A real Telegram round-trip gets a Simpsons-persona chat response
4. `/cost`, `/queue`, `/autonomy_status`, `/heartbeat_status` all work over Telegram
5. An emoji command succeeds end-to-end
6. Approval queue reply-to-message flow still works (reply "yes confirm" to a pending proposal)
7. `orchestrator.py` still in repo, not deleted
8. Rollback tag exists on origin
9. Memory entries updated: `project_shadow_module_backport.md` -> COMPLETE

Rollback is one command if any check fails.
