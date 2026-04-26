# M9: Atlas Chat: Full Command Center

**Status:** Design locked (v4), ready to build
**Priority:** HIGH
**Save point:** `savepoint-pre-atlas-m9-design-2026-04-26` (rewind: `git checkout savepoint-pre-atlas-m9-design-2026-04-26`)
**Spec revision:** 2026-04-26 v4: post model research + blue/red team + code reviewer + Sankofa Council

---

## Vision (precise statement)

The chat interface is a **command center and execution surface**. Claude Code handles agentsHQ infrastructure changes only (editing orchestrator code, docker ops, git, file system). Everything else: approving content, drafting posts, building websites, iterating on artifacts, monitoring system state: happens through the chat interface on Telegram or the Atlas web panel.

The web chat must eventually match Claude Code for non-infrastructure work: back-and-forth conversation, tool execution, artifact rendering, iteration. Not "similar to": equivalent for that scope.

**The escape hatch that makes this possible:** `forward_to_crew` routes any task to the orchestrator's full crew engine. The chat does not need to replicate every Claude Code capability directly: it needs to be a capable dispatcher that can delegate to crews that have those capabilities.

**Explicit gap to close over time:** "build a website" requires a `build_site` crew that can generate, save, and serve HTML. That crew does not exist today. It is a tracked gap, not a design flaw. M9 ships the command surface; the crews that power it grow over time.

---

## Save points and sandboxing protocol

### Save point before every milestone

Before any M9a, M9b, M9c code starts:
```bash
git tag savepoint-pre-atlas-m9a-$(date +%Y%m%d)
# rewind: git checkout savepoint-pre-atlas-m9a-YYYYMMDD
```

Current save point already created: `savepoint-pre-atlas-m9-design-2026-04-26`

### Sandbox / test mode for M9

The red team identified a critical gap: every write action (approve, reject, queue) hits production directly. There is no staging lane. This is fixed with a `CHAT_SANDBOX=true` env var:

- When `CHAT_SANDBOX=true`: all write tools (approve_item, reject_item, queue_post) log the would-be action and return `"[SANDBOX] Would have approved item X: not executed"` instead of actually writing.
- Read tools (get_content_board, get_spend, get_heartbeats) still hit real data: sandboxing write actions is sufficient.
- The sandbox flag is added to the system prompt so the model tells the user "sandbox mode is active."
- Add `CHAT_SANDBOX` to docker-compose.yml allowlist. Default: `false`.

### Local smoke test before VPS deploy

Every M9 sub-milestone includes a local smoke test script at `scripts/test_m9{a,b,c}_smoke.py` that:
1. Calls the relevant new endpoints with mock data
2. Asserts the response schema matches `{"reply": "...", "actions": [...]}`
3. Asserts no Postgres connections are leaked (checks `pg_stat_activity` count before and after)
4. Can be run without a running container using mocked dependencies

Run before every deploy: `python scripts/test_m9a_smoke.py`

---

## Model strategy: three-tier routing, quality-first

### Research findings (verified 2026-04-26)

| Model | Slug | Input $/M | Output $/M | Context | Tool calling | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Gemini 2.5 Flash | `google/gemini-2.5-flash` | $0.30 | $2.50 | 1M | Confirmed (Google native) | Fastest at 1M context; built-in thinking mode; configurable |
| Claude Haiku 4.5 | `anthropic/claude-haiku-4.5` | $1.00 | $5.00 | 200K | Confirmed (bash, web search, computer-use, coding explicitly named) | Only model with computer-use confirmed; Anthropic agent pedigree |
| Claude Sonnet 4.5 | `anthropic/claude-sonnet-4.5` | $3.00 | $15.00 | 1M | Confirmed (parallel tool execution, extended autonomy, token-aware) | SOTA SWE-bench; speculative parallel tool calls; best for deep work |
| DeepSeek V3 0324 | `deepseek/deepseek-chat-v3-0324` | $0.20 | $0.77 | 163K | Works in practice, not confirmed on page | Very cheap; strong coder; latency can be high |
| Grok 3 Mini | `x-ai/grok-3-mini` | $0.30 | $0.50 | 131K | Not confirmed | Fast; weak on domain knowledge; risky for content work |
| DeepSeek R1 | `deepseek/deepseek-r1` | $0.70 | $2.50 | 64K | Not confirmed | Reasoning/thinking model; slow by design; wrong fit |
| Mistral Small 3.1 | `mistralai/mistral-small-3.1-24b-instruct` | $0.35 | $0.56 | 128K | Confirmed (function calling) | Oct 2023 knowledge cutoff is a real gap for agentic tasks |

### Decision: quality-first, three-tier routing

The user's priority is quality and speed, not cost savings. A few extra dollars per month for faster, more reliable results is explicitly preferred over cutting corners.

**Tier 1: Fast turns (status checks, quick approvals, conversational replies):**
`CHAT_MODEL` env var, default `anthropic/claude-haiku-4.5`
- Confirmed tool calling including computer-use
- Fastest Anthropic model, sub-second time-to-first-token
- 200K context covers any normal conversation history

**Tier 2: Tool-heavy and agentic tasks (drafting, multi-step crew chains, complex queries):**
`ATLAS_CHAT_MODEL` env var, default `anthropic/claude-haiku-4.5`
- Same model by default; the env var separation allows independent tuning
- Upgrade path: set `ATLAS_CHAT_MODEL=anthropic/claude-sonnet-4-5` for a session when doing deep drafting work

**Tier 3: Deep work ceiling (long artifact sessions, complex reasoning, website builds):**
Available via `ATLAS_CHAT_MODEL=anthropic/claude-sonnet-4-5` override
- Parallel tool execution, 1M context, extended autonomous operation
- Pay-per-deep-session: a heavy 30-min build session costs $2-5: worth it

**Why not Gemini 2.5 Flash as default despite lower cost:**
The command center is not a high-volume endpoint. Cost delta is ~$30/month for personal use. Gemini through OpenRouter has had intermittent tool-use failures (returns JSON in `content` instead of `tool_calls` field). A silent tool-use miss in a command center context is a broken workflow, not a UI glitch. Haiku 4.5 has explicit confirmation of the exact tool categories this system needs. Gemini stays available via env var for experimentation.

**Why not DeepSeek R1:** Deliberately slow (thinking model). Wrong fit for interactive use.

### Weekly model review (automated)

Models evolve faster than specs. Add a scheduled agent (CronCreate) to run weekly:
- Fetch https://openrouter.ai/models
- Compare current prices/capabilities for the 3 configured models
- Flag any new models that beat the current tier on quality or speed
- Write findings to `docs/reference/model-review-{date}.md`
- Notify via Telegram

This replaces manual spec updates. The recommendation in this doc is the starting point; the weekly agent keeps it current.

Env vars for model configuration (all three tiers):
```yaml
# docker-compose.yml orc-crewai environment section
- CHAT_MODEL=${CHAT_MODEL}
- ATLAS_CHAT_MODEL=${ATLAS_CHAT_MODEL}
- CHAT_TEMPERATURE=${CHAT_TEMPERATURE}
- CHAT_SANDBOX=${CHAT_SANDBOX}
```

VPS `.env` defaults:
```
CHAT_MODEL=anthropic/claude-haiku-4.5
ATLAS_CHAT_MODEL=anthropic/claude-haiku-4.5
CHAT_TEMPERATURE=0.7
CHAT_SANDBOX=false
```

Temperature lowered to 0.7 (from 0.85) for more consistent structured JSON output.

---

## Architecture decisions (all locked)

### Decision 1: Structured JSON response schema

The model always returns a JSON object with a defined schema:

```python
{
    "reply": "Here are three framings. Pick one to queue:",
    "actions": [
        {"label": "Option A: ...", "callback_data": "queue_post:notion_id_A"},
        {"label": "Option B: ...", "callback_data": "queue_post:notion_id_B"}
    ],
    "artifact": {
        "type": "html",
        "content": "...",
        "artifact_id": "art_abc123"
    }
}
```

- `reply`: always present, plain text or markdown
- `actions`: optional, array of `{label, callback_data}` objects
- `artifact`: optional, `{type, content, artifact_id}`: see artifact storage below

Error handling: `json.loads()` in try/except. On failure, return raw content as plain text reply, no actions. Never raise. Log the parse failure.

`response_format: {"type": "json_object"}` passed to the OpenRouter call where supported. Where not supported, the system prompt instructs the model to return JSON.

### Decision 2: Async task execution with job polling

**Red team finding:** `forward_to_crew` blocks the HTTP connection for 60-180 seconds. Nginx times out at 60s. Browser shows a spinner and gets nothing back.

**Fix:** Long-running tasks use the existing job queue pattern already in `app.py`:

1. `forward_to_crew` tool call in `run_chat()` kicks the task off via the background worker: `job_id = _run_background_job(task_request, session_key)`: returns immediately.
2. `run_chat()` returns: `{"reply": "On it: I've queued that task. I'll ping you when it's done.", "job_id": "job_abc123", "actions": [{"label": "Check status", "callback_data": "job_status:job_abc123"}]}`
3. `atlas.js` polls `GET /api/orc/status/{job_id}` every 3 seconds (same pattern as `index.html` already uses).
4. When the job completes, the result is injected as a new agent message in the chat.
5. On Telegram, the result is sent as a follow-up message automatically (the existing Telegram notify path already does this).

Short-running tool calls (get_content_board, get_spend, etc.) remain synchronous: they complete in under 2 seconds and do not need the job queue.

The distinction: `run_chat()` uses direct `atlas_dashboard` function calls for read tools (fast, synchronous), and job queue for `forward_to_crew` (slow, async).

### Decision 3: Artifact storage table

**Red team finding:** Multi-turn artifact iteration breaks because: (a) HTML content is truncated at 2000 chars in `agent_conversation_history`, (b) passing full HTML in every message eats context window.

**Fix:** New Postgres table `chat_artifacts`:

```sql
CREATE TABLE chat_artifacts (
    artifact_id   TEXT PRIMARY KEY,          -- e.g. "art_abc123"
    session_id    TEXT NOT NULL,
    turn_number   INTEGER NOT NULL,
    artifact_type TEXT NOT NULL,             -- "html", "svg", "markdown", "pdf"
    content       TEXT NOT NULL,             -- full content, no size cap
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON chat_artifacts (session_id, turn_number);
```

Workflow:
- Model generates an artifact; `run_atlas_chat()` stores it in `chat_artifacts` before returning.
- `artifact_id` is included in the response JSON, not the full content.
- On the next turn, the client sends the `artifact_id` in a special context message: `{"role": "user", "content": "[artifact:art_abc123] Make the headline bigger."}`.
- `run_atlas_chat()` resolves the `artifact_id` to the full content from Postgres before calling the model, injects it as a system context block.
- The model sees the full prior artifact without it passing through the `messages[]` array.

This is the same pattern Claude Code uses with files: the file is on disk; the conversation references it. The chat references the artifact by ID; the server resolves it.

### Decision 4: Write-action confirmation (not just for publish)

Any tool call that modifies production data requires an explicit confirmation turn:

Write-action tools: `approve_item`, `reject_item`, `queue_post`, `forward_to_crew` (when classified as a write task).

Confirmation pattern:
1. Model calls `approve_item({item_id: "123", title: "One constraint nobody has named yet"})`.
2. Tool handler checks `CHAT_SANDBOX`. If sandbox: log and return mock. If live: returns `{"status": "pending_confirm", "message": "About to approve: 'One constraint nobody has named yet'. Tap Confirm to proceed.", "confirm_token": "conf_abc"}`.
3. `run_chat()` returns this as an action block: `{"reply": "...", "actions": [{"label": "Confirm approve", "callback_data": "confirm:conf_abc"}, {"label": "Cancel", "callback_data": "cancel:conf_abc"}]}`.
4. Confirm tap executes the actual write. Cancel discards.
5. `publish_now` (Blotato) always requires confirmation, as already specified.

One confirmation turn. Not multiple. Fast enough for daily ops, safe enough to prevent misfires.

### Decision 5: Shared tool set, format-aware serializer

The tool set is identical for Telegram and web. The serializer is format-aware:

- `channel="telegram"`: reply truncated to 4000 chars. Tables converted to padded plain text. Actions converted to inline keyboard via `send_message_with_buttons`.
- `channel="web"`: full markdown. Tables as HTML tables. Actions as button row below bubble.

One system prompt, one tool set, one model call. The `channel` param is passed into `run_chat()` and `run_atlas_chat()`.

### Decision 6: Tracked gaps (not design flaws)

These are explicitly out of scope for M9 but documented so they do not get relitigated:

| Gap | What it means | When to close |
| --- | --- | --- |
| `build_site` crew | Chat can draft a single-file HTML page; cannot scaffold a full Next.js project | When website building is a primary use case (Studio M4+) |
| Telegram artifact rendering | Telegram cannot render HTML inline; build results are plain-text summaries | Not closable on Telegram; web chat is the right surface |
| Responsive preview | srcdoc iframe does not allow Playwright testing at 375px | Claude Code remains the tool for QA after building |
| Cross-session artifact retrieval | 3-sentence session summaries lose specific code decisions | M9c; `retrieve_file` bridges some of this today |

---

## Milestone split (final)

### M9a: Infrastructure correctness + Telegram proactive push with action buttons

**Correctness fixes (run before any feature code):**

1. `atlas_dashboard.py`: Add `conn.close()` in `finally` block to every fetcher using `_pg_conn()`. Affected: `_spend_aggregates`, `_spend_7d_by_day`, `_last_autonomous_action`, `_router_log_fallbacks`, `_error_log_tail`, `get_cost_ledger`.

2. `handlers_chat.py`: Add at module level:
```python
CHAT_MODEL = os.environ.get("CHAT_MODEL", "anthropic/claude-haiku-4.5")
ATLAS_CHAT_MODEL = os.environ.get("ATLAS_CHAT_MODEL", "anthropic/claude-haiku-4.5")
CHAT_TEMPERATURE = float(os.environ.get("CHAT_TEMPERATURE", "0.7"))
CHAT_SANDBOX = os.environ.get("CHAT_SANDBOX", "false").lower() == "true"
```
Replace both hardcoded model strings and temperature floats.

3. `handlers_chat.py`: Change `run_chat()` return to structured JSON schema. Parse with try/except. Strip actions from reply before saving to Postgres.

4. `handlers.py`: Replace lines 210-214 (the run_chat call + send_message) with `run_chat_with_buttons(message, session_key, chat_id, channel="telegram")`. This function calls `run_chat()`, reads `result["actions"]`, calls either `send_message_with_buttons` or `send_message`: never both.

5. `docker-compose.yml`: Add 4 env vars with `KEY=${KEY}` syntax.

6. `scripts/test_m9a_smoke.py`: Create smoke test. Run before deploy.

**Telegram proactive push upgrades:**

7. `notifier.py` / `publish_brief.py` / approval flow: Upgrade approval queue notification to include `[Approve] [Reject]` inline keyboard buttons on the notification message itself.

8. `handlers_approvals.py`: Add `_build_button(label, callback_data)` helper with 64-byte assert. Add callback dispatch cases for new button prefixes.

9. System prompt upgrade: direct operator persona, JSON schema instructions, tool-aware, sandbox-aware.

**M9a done when:**
- Approval queue notification arrives in Telegram with working action buttons
- `CHAT_MODEL` env var controls model (verify via container logs)
- `CHAT_SANDBOX=true` mode returns mock responses without writing to Notion
- Postgres connection count stable before and after a chat session (smoke test passes)
- No double-send (one message per turn in Telegram)

**Build budget:** 3-4 hours
**Branch:** `feat/atlas-m9a-telegram-push`
**Save point:** `git tag savepoint-pre-atlas-m9a-$(date +%Y%m%d)` before starting

---

### M9b: Web chat command center + async task execution

**Backend:**

1. `orchestrator/db.py` (new or add to memory.py): `CREATE TABLE chat_artifacts (...)`. Migration runs on startup.

2. `app.py`: Add `POST /api/orc/chat` (synchronous, calls `run_chat()` via `run_in_executor`, returns result). Auth: `verify_chat_token`.

3. `handlers_chat.py`: Add `run_atlas_chat(messages, session_key, channel="web")`:
   - Uses `ATLAS_CHAT_MODEL`
   - Accepts client-supplied messages array
   - Resolves any `[artifact:art_id]` references in messages before calling model
   - Stores artifacts in `chat_artifacts` table
   - Saves only text turns to `agent_conversation_history`
   - `forward_to_crew` uses background job queue, returns job_id immediately

4. `app.py`: Add `POST /api/orc/atlas/chat` calling `run_atlas_chat()` via `run_in_executor`. Auth: `verify_chat_token`.

5. `app.py`: Add `GET /api/orc/atlas/job/{job_id}`: polls the existing job status table, returns `{status, result}`.

**Frontend:**

6. `atlas.html`: Remove iframe. Add native chat panel in card slot 7 with Atlas design system markup.

7. `atlas.js`: Add `atlasChat` module:
   - `sessionKey`: read from `localStorage`, generate once as `"atlas:browser:" + crypto.randomUUID()`, persist
   - `messages: []`: client-side array, inject Postgres history on init (text-only, last 10 turns)
   - `sendMessage(text)`: append to messages, POST full array to `/api/orc/atlas/chat`, append reply
   - `renderMessage(role, text, actions, artifact)`: markdown renderer (inline, no deps), button row for actions, artifact renderer
   - `renderArtifact(artifact)`: `<iframe srcdoc>` for HTML, inline SVG for SVG
   - `pollJob(jobId)`: polls `/api/orc/atlas/job/{jobId}` every 3s, injects result as agent message when complete

8. `atlas.js`: Inline markdown renderer (~80 lines): bold, italic, code blocks, tables, numbered/bullet lists. No external lib.

**Confirmation layer:**

9. Write-tool handlers return `pending_confirm` status on first call. Confirm action triggers second call that actually executes. `_confirm_store` in `state.py` (matching the `_PUBLISH_BRIEF_WINDOWS` pattern) holds pending confirmations with 5-minute TTL.

**M9b done when:**
- Atlas panel has native chat, no iframe
- "Show me my content board" returns formatted inline table
- "Draft three framings for [idea]" returns three options with Queue buttons (which trigger a confirmation before writing)
- Long-running crew tasks show a job-in-progress message and inject result when complete (no spinner timeout)
- Artifact generation (even just a simple HTML snippet) stores in `chat_artifacts`, renders in iframe
- Session survives page refresh (stable localStorage session key)

**Build budget:** 4-5 hours (larger than previous estimate; async job polling and artifact table add scope)
**Branch:** `feat/atlas-m9b-web-chat`
**Save point:** `git tag savepoint-pre-atlas-m9b-$(date +%Y%m%d)` before starting
**Depends on:** M9a live on VPS

---

### M9c: Artifact iteration + cross-session memory + weekly model review agent

**Artifact iteration:**

Multi-turn HTML iteration works because M9b already stores artifacts by ID. M9c adds:
- Resize handle on the artifact iframe (drag to change height, 300-900px range)
- "Fullscreen" button that opens the artifact in a new tab (uses `blob:` URL from srcdoc content)
- `save_to_drive` action button on any artifact
- `push_to_github` action button (routes to `forward_to_crew` with a deploy task)

**Cross-session memory:**

After 30 minutes of inactivity (checked by heartbeat comparing `last_message_at` timestamp):
1. Fetch the session's turns from `agent_conversation_history`
2. Call cheapest available model (`CHAT_MODEL` default or `google/gemini-2.0-flash-001` if explicitly cheaper) to compress to a 3-5 sentence summary
3. Store as `(session_id="atlas:summary:{date}", role="session_summary", content=summary)` in `agent_conversation_history`
4. On next session init, fetch last 3 `session_summary` rows, inject as system context

For artifact-heavy sessions: the summary includes the `artifact_id` references (e.g., "Built a landing page for Catalyst Works: artifact art_abc123"). On next session, `retrieve_file` or `[artifact:art_abc123]` reference resolves to the full content.

**Weekly model review agent:**

CronCreate a weekly routine that:
1. Fetches current OpenRouter model pricing for the 3 configured models
2. Searches for new models that beat current tiers on throughput or quality
3. Writes a 1-page summary to `docs/reference/model-review-{date}.md`
4. Sends Telegram notification with top finding and any recommended change
5. Never auto-changes the env var: always surfaces the recommendation to Boubacar

This ensures the model choice evolves with the market without requiring a manual spec update.

**M9c done when:**
- Boubacar can iterate on a generated HTML page across 3+ turns without losing context
- Artifact opens fullscreen in new tab
- Agent references prior session work naturally ("last time we were building the Catalyst Works landing page...")
- Weekly model review is running and has fired at least once

**Build budget:** 2-3 hours
**Branch:** `feat/atlas-m9c-artifacts`
**Depends on:** M9b live

---

## System prompt (M9a and beyond)

```
You are Boubacar's agentsHQ command center.

You are a dispatcher and execution surface. You have direct access to the agentsHQ
system: content board, approval queue, spend, heartbeats, crew execution, Notion, and publishing.

RESPONSE FORMAT (required):
Always return a valid JSON object:
  {"reply": "...", "actions": [...optional...], "artifact": {...optional...}}

"reply": your response. Plain text or markdown.
"actions": optional array of {"label": "Button text", "callback_data": "action:id"}.
  Include only when offering a one-tap action. Omit otherwise.
"artifact": optional {"type": "html"|"svg"|"markdown", "content": "...", "artifact_id": "..."}.
  Include when generating a visual or document artifact.

SANDBOX MODE: {sandbox_status}
When sandbox is active, write actions are simulated. Tell the user.

BEHAVIOR:
When asked to do something, do it with your tools. Do not explain what you are about to do.
For write actions (approve, reject, queue): confirm once before executing.
For publish to a live platform: confirm once with exact text and platform, then execute.
For drafting: produce a first draft immediately. Ask for feedback after.
For tasks beyond your tool set: call forward_to_crew immediately. Never explain limitations.
  The orchestrator has many capabilities. Always assume it can handle the task.

Long-running tasks return a job ID. Tell the user the task is running and you will ping them with the result.

RESPONSE FORMAT FOR TELEGRAM: Keep reply under 3000 characters. Format data as plain text tables.
RESPONSE FORMAT FOR WEB: Full markdown is rendered. Tables, code blocks, bullet lists all work.

You remember recent sessions. Reference prior work naturally when relevant.
Short and direct. Get to the point.
```

---

## What does NOT change

- `/chat` and `index.html`: unchanged
- Telegram polling infrastructure: unchanged
- All existing `/atlas/*` data endpoints: tool dispatch calls fetcher functions directly
- Auth: same JWT-PIN, same `verify_chat_token`
- Spend cap and kill switch: unaffected
- `autonomy_state.json` dry_run: unaffected

---

## Hard rules

- Save point created before every milestone start
- `CHAT_SANDBOX=true` mode must be verified before any M9 milestone is considered production-ready
- All docker-compose env vars use `KEY=${KEY}` syntax
- `conn.close()` in `finally` block on every Postgres connection in `atlas_dashboard.py`
- Tool call messages (role=tool) are NOT saved to `agent_conversation_history`: text turns only
- One confirmation turn before any write action executes
- `callback_data` bytes checked at build time via `_build_button()` helper, max 64 bytes
- No em dashes anywhere

---

## Build session checklist (M9a: start here)

Before any code:
- [ ] `git tag savepoint-pre-atlas-m9a-$(date +%Y%m%d)`
- [ ] Read `orchestrator/atlas_dashboard.py`: find every `_pg_conn()` call, map which functions need `conn.close()`
- [ ] Read `orchestrator/handlers.py` lines 193-220: understand exact lines to replace for double-send fix
- [ ] Read `orchestrator/handlers_approvals.py`: understand existing callback_data patterns and ALLOWED_USER_IDS check location
- [ ] Read `orchestrator/notifier.py` lines 854-913: confirm `send_message_with_buttons` signature
- [ ] Add 4 env vars to VPS `.env` + `docker-compose.yml` before deploy (use `KEY=${KEY}` syntax)

Build order for M9a:
1. `atlas_dashboard.py`: `conn.close()` in finally blocks (correctness, no behavior change)
2. `handlers_chat.py`: env var reads, replace hardcoded strings, structured JSON return schema with try/except
3. `handlers_chat.py`: upgrade system prompt
4. `handlers_chat.py`: add `run_chat_with_buttons(message, session_key, chat_id, channel)` wrapper
5. `handlers.py`: replace lines 210-214 with single `run_chat_with_buttons` call
6. `handlers_approvals.py`: add `_build_button()` helper + new callback cases
7. `notifier.py` / `publish_brief.py`: upgrade approval notification to include action buttons
8. `docker-compose.yml`: add 4 env vars
9. `scripts/test_m9a_smoke.py`: write and run smoke test
10. Deploy: `docker compose up -d --build orchestrator`
11. Set `CHAT_SANDBOX=true` on VPS, verify mock responses work
12. Set `CHAT_SANDBOX=false`, verify real approval button fires exactly once
