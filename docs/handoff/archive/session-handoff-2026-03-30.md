# agentsHQ — Session Handoff 2026-03-30

## What this is
Context file for the next Claude Code session. Read this before touching anything.

---

## System Overview

- **Orchestrator**: FastAPI + CrewAI, running in Docker container `orc-crewai` on VPS `72.60.209.109:8000`
- **n8n**: Telegram bot `@agentsHQ4Bou_bot` → n8n workflow → POST `/run` → Telegram reply
- **GitHub**: `https://github.com/bokar83/agentHQ`
- **VPS project path**: `/root/agentsHQ` (NOT /opt/agentshq — that doesn't exist)
- **Local project path**: `d:\Ai_Sandbox\agentsHQ`

## All 3 environments are in sync as of this session
- Local = GitHub = VPS on commit `09e545b`

---

## What Was Fixed This Session

### 1. Voice polisher outputting monologue instead of deliverables (FIXED, DEPLOYED)
**Problem**: The voice polisher agent's first line is "I'll start by checking memory for any relevant context, then run the deliverable through the voice polisher tool." This was being returned as the task output instead of the actual deliverable, on ALL crews including code tasks.

**Root cause**: `build_humanization_task` was added to every crew when the voice polisher was built.

**Fix applied** (`orchestrator/crews.py`):
- Removed `build_humanization_task` from `build_code_crew()` (line ~502)
- Removed `build_humanization_task` from `build_writing_crew()` (line ~561)
- Removed `build_humanization_task` from `build_app_crew()` (line ~630)

**Voice polisher intentionally KEPT on**: `research_report`, `consulting_deliverable`, `social_content`, `website_build` — text/content outputs where humanization is appropriate.

**Status**: Deployed to VPS. NOT yet verified with a clean end-to-end test because concurrent request issue interrupted testing.

### 2. VPS deploy sequence confirmed
The correct commands (run on VPS from `/root/agentsHQ`):
```bash
cd /root/agentsHQ
git pull origin main
docker compose build orchestrator
docker compose up -d orchestrator
```
`docker restart` alone does NOT work — code is baked into the image, not volume-mounted.

---

## Known Issues to Fix Next Session

### ISSUE 1 — Verify voice polisher fix (5 min)
**What to do**: Send a single code task via Telegram:
> "Write a Python function that takes a list of dictionaries and returns them sorted by any key, with error handling for missing keys"

**Expected**: Actual Python code returned. If you still get "I'll start by checking memory..." — the old image is cached and needs a hard rebuild (`docker compose build --no-cache orchestrator`).

### ISSUE 2 — Concurrent requests cause "Check Agent is Running" timeout (MUST FIX)
**Problem**: When two Telegram messages are sent simultaneously, the "Check Agent is Running" node in n8n sends a GET to `/health` with a 5-second timeout. The orchestrator is busy running a crew (single-threaded) so it doesn't respond in time → ECONNABORTED error on ALL subsequent messages until the first finishes.

**Fix options** (choose one):
- **(a) Remove the "Check Agent is Running" node entirely** — simplest. Just let it go straight to "Run Agent Crew". Risk: if orchestrator is down, user gets a worse error message.
- **(b) Increase timeout to 30s in the n8n HTTP node** — keeps the health check but gives busy crews time to free up.
- **(c) Return "Bot is busy" gracefully** — modify orchestrator to queue requests and respond immediately with a "working on it" message.

**Recommended**: Option (b) — increase the timeout to 30s. Lowest risk, no code changes needed, just an n8n UI change.

**How to do it in n8n UI**: Open "Check Agent is Running" node → Options → Timeout → change 5000 to 30000.

### ISSUE 3 — Always Save Sub credential expired
**Problem**: The "Always Save Sub" node in n8n has an expired GitHub credential after the n8n update.
**Fix**: Manual re-auth in n8n UI → Credentials → find the GitHub credential → reconnect OAuth. Non-blocking, agents still work without it.

---

## Hard Rules (do not violate)

1. **NEVER touch n8n Docker containers** — no `docker stop/restart/cp` on n8n, no SQLite edits, no n8n CLI commands. This has caused two outages. Only modify n8n via the UI or REST API.
2. **All files go in `D:\Ai_Sandbox\agentsHQ` or `D:\Ai_Sandbox\`** — never on C: drive.
3. **Always deploy with build, not restart**: `docker compose build orchestrator && docker compose up -d orchestrator`
4. **End every session with sync**: local → GitHub → VPS all on same commit.

---

## n8n Workflow Architecture (current, working)

```
Telegram Trigger
  → Parse Message (extracts text, chat_id, from_number as String)
  → Check Agent is Running (GET /health, 5s timeout ← INCREASE THIS)
  → Run Agent Crew (POST /run, 300s timeout, body: {task, from_number, task_type})
  → Format Result (extracts result text, truncates to 3700 chars)
  → Has File? (boolean check)
    → [false] → Send Result to Telegram
    → [true] → Send Result + File to Telegram
```

The async polling approach (Wait → Poll → Is Done?) was **abandoned**. Sync `/run` with 300s timeout is the working solution.

---

## Orchestrator File Map

| File | Purpose |
|------|---------|
| `orchestrator/orchestrator.py` | FastAPI app, `/run` endpoint, job queue |
| `orchestrator/crews.py` | All 9 CrewAI crews — this is where voice polisher was fixed |
| `orchestrator/agents.py` | All 11 agent builders incl. `build_boub_ai_voice_agent()` |
| `orchestrator/router.py` | Task type → crew mapping |
| `orchestrator/tools.py` | Tools incl. `voice_polisher_tool` |
| `orchestrator/memory.py` | PostgreSQL conversation history |

---

## Sprint Priorities (in order)

1. Verify voice polisher fix with clean code task test
2. Fix "Check Agent is Running" timeout (increase to 30s in n8n UI)
3. Test all 4 agent types one at a time: research, consulting, code, writing
4. Fix Always Save Sub GitHub credential (n8n UI)
5. Google Drive integration
6. Usage dashboard (HTML on VPS)

---

## Useful Commands

**Check orchestrator logs on VPS:**
```bash
ssh root@72.60.209.109 "docker logs orc-crewai --tail 50 2>&1"
```

**Check running containers:**
```bash
ssh root@72.60.209.109 "docker ps --format 'table {{.Names}}\t{{.Status}}'"
```

**Hard rebuild (if image is cached):**
```bash
ssh root@72.60.209.109 "cd /root/agentsHQ && docker compose build --no-cache orchestrator && docker compose up -d orchestrator"
```

**Test orchestrator directly:**
```bash
curl -X POST http://72.60.209.109:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Write hello world in Python", "from_number": "test", "task_type": "code_task"}'
```
