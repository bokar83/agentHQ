# agentsHQ — Lessons Learned
**Project:** agentsHQ — Self-hosted multi-agent orchestration system  
**Owner:** Boubacar Barry — Catalyst Works Consulting  
**Last Updated:** March 21, 2026 (end of Day 2)

---

## DAY 1 — March 20, 2026

### L1: CrewAI + OpenRouter — THE Critical Fix

**Problem:** CrewAI detects model name prefixes (`anthropic/`, `google/`) and tries to load native provider SDKs. Crashes with "native provider not available" errors.

**Correct solution:**
```python
from crewai import LLM
# requirements.txt must include: litellm>=1.0.0

llm = LLM(
    model="openrouter/anthropic/claude-sonnet-4-5",  # openrouter/ prefix mandatory
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0.3,
    extra_headers={
        "HTTP-Referer": "https://agentshq.catalystworks.com",
        "X-Title": "agentsHQ"
    }
)
```

**Rules:**
- Always use `from crewai import LLM` — NOT `langchain_openai.ChatOpenAI`
- Always prefix model strings with `openrouter/`
- Always add `litellm>=1.0.0` to `requirements.txt`

---

### L2: Verified OpenRouter Model IDs (March 2026)

```python
MODEL_REGISTRY = {
    "claude-sonnet": "openrouter/anthropic/claude-sonnet-4-5",
    "claude-haiku":  "openrouter/anthropic/claude-haiku-4.5",   # dot not dash
    "claude-opus":   "openrouter/anthropic/claude-opus-4-5",
}
```

---

### L3: Docker Compose — n8n Conflict
Remove n8n from our compose file. Use Hostinger's existing n8n at `https://n8n.srv1040886.hstgr.cloud`.

---

### L4: Docker Compose — Obsolete Version Warning
Remove `version: '3.8'` from `docker-compose.yml`.

---

### L5: PostgreSQL — Auto-Schema Loading
Mount SQL to `/docker-entrypoint-initdb.d/` — auto-runs on first start.

---

### L6: CrewAI Memory — Disable Until Tested
Set `memory=False` in all Crew definitions until embedder confirmed working.

---

### L7: Python Import Syntax
```python
# WRONG
from agents import (select_llm(),)
# CORRECT  
from agents import (select_llm,)
```

---

### L8: Test Sequence — Always Follow This Order
1. `/health` — service alive?
2. `/capabilities` — task types registered?
3. `/classify?task=...` — router working?
4. `POST /run` — only then run full task

---

### L9: Verify Model IDs Before Writing Code
Always verify at openrouter.ai/models. One wrong character = failed build cycle.

---

### L10: Docker Layer Caching
Put `requirements.txt` install BEFORE copying source files. Saves 80+ seconds per rebuild.

---

## DAY 2 — March 21, 2026

### L11: Always Publish After Save in n8n
**Save** stores locally. **Publish** activates production. Always Publish after every change.
**Cost of ignoring:** 20+ minutes debugging the wrong thing.

---

### L12: Check Wire Direction on IF Nodes
When importing n8n workflows from templates, always verify IF node branch connections first.
True Branch → correct path. False Branch → correct path.
**Cost of ignoring:** 90 minutes.

---

### L13: All Ports Default to Localhost Only
`"127.0.0.1:8000:8000"` = localhost only. `"8000:8000"` = externally accessible.

```bash
sed -i 's/- "127.0.0.1:8000:8000"/- "8000:8000"/' ~/agentsHQ/docker-compose.yml
```

Apply to ALL services needing external access: 8000, 3000, 5432.

---

### L14: n8n Cannot Reach Docker Containers by Name
n8n is outside our Docker network. Always use VPS IP:
- `http://orc-crewai:8000` → `http://72.60.209.109:8000`
- `http://orc-waha:3000` → `http://72.60.209.109:3000`

---

### L15: WAHA Requires API Key
Set a real key value — empty value still enforces auth:
```yaml
# docker-compose.yml
- WHATSAPP_API_KEY=agentshq123
```
```
# n8n nodes calling WAHA
Header: X-Api-Key: agentshq123
```

---

### L16: n8n Long-Running Task Timeout
Quick fix: Set Run Agent Crew node timeout to `900000` (15 min).
Proper fix (planned): Async job queue — return job_id immediately, poll `/status/{job_id}`.

---

### L17: PowerShell JSON Encoding
Always use UTF-8 without BOM:
```powershell
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText("path\file.json", '{"json":"content"}', $utf8NoBom)
```

---

### L18: SSH One-Liners Save Time
```powershell
ssh root@72.60.209.109 "command"           # run without logging in
ssh root@72.60.209.109 "cmd1 && cmd2"      # chain commands
ssh root@72.60.209.109 "docker logs orc-crewai -f"  # watch logs
```

---

### L19: n8n Execute Workflow Node — Outdated Version
Delete old node. Add new `Execute Workflow` node. Source = **Database**. Select from dropdown.

---

### L20: Agent Voice — No Fabrication Rule (leGriot)
- Never invent first-person stories or experiences
- Use "Imagine if..." for hypothetical scenarios
- Arguments from principles, not fabricated anecdotes

---

### L21: Consulting Agent — Voice Calibration
- One bold diagnosis — no menus of options
- Lead with the insight, not the problem statement
- Connect to financial + human + organizational outcomes
- One counterintuitive observation
- One uncomfortable closing question
- Use Claude Opus: `select_llm("consultant", "complex")`

---

## PROCESS LESSONS

### Fix Everything Before Starting
Before first build, audit ALL files:
1. Import statements — all names exist?
2. Model strings — verified against OpenRouter?
3. Required packages — requirements.txt complete?
4. Environment variables — match .env exactly?
5. Port bindings — all needed ports exposed?

### Read Error Messages Fully
Several errors contained the exact fix. Read completely before making changes.

### Give Full Files, Not Partial Fixes
Always provide complete functions or files. Partial fixes cause new errors.

### One-Liner Commands First
If it can be done in one command, do it in one command. Never use 3 steps when 1 works.

---

## QUICK REFERENCE

### Working Stack
```
VPS:           72.60.209.109 (Ubuntu 24.04.4)
n8n:           https://n8n.srv1040886.hstgr.cloud
Orchestrator:  http://72.60.209.109:8000
WAHA:          http://72.60.209.109:3000
PostgreSQL:    72.60.209.109:5432
WAHA API Key:  agentshq123
```

### Essential Commands
```powershell
# Health check
ssh root@72.60.209.109 "curl http://localhost:8000/health"

# Rebuild after code changes
ssh root@72.60.209.109 "cd ~/agentsHQ && docker compose build orchestrator && docker compose up -d"

# List recent outputs
ssh root@72.60.209.109 "ls -lt ~/agentsHQ/agent_outputs/ | head -10"

# Download output
scp -i C:\Users\HUAWEI\.ssh\id_ed25519 root@72.60.209.109:~/agentsHQ/agent_outputs/FILE D:\Ai_Sandbox\agentsHQ\outputs\FILE

# Test workflow
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText("C:\Users\HUAWEI\Desktop\test.json", '{"from":"15551234567","body":"YOUR TASK"}', $utf8NoBom)
Invoke-RestMethod -Uri "https://n8n.srv1040886.hstgr.cloud/webhook/whatsapp-incoming" -Method POST -ContentType "application/json" -InFile "C:\Users\HUAWEI\Desktop\test.json"
```
