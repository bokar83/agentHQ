---
name: agentsHQ project context
description: Core architecture, status, and goals of the agentsHQ multi-agent system owned by Boubacar Diallo
type: project
---

# agentsHQ Project Context

## System Identity

- **Owner:** Boubacar Diallo (Catalyst Works Consulting)
- **VPS:** 72.60.209.109 (Hostinger)
- **GitHub:** <https://github.com/bokar83/agentHQ> (source of truth)
- **Local:** D:\Ai_Sandbox\agentsHQ

## Architecture

- **Orchestrator:** FastAPI + CrewAI, running in Docker on VPS port 8000
- **Router:** Claude Haiku classifies task type → routes to correct crew
- **11 agents:** Planner, Researcher, Copywriter, Web Builder, App Builder, Code, Consulting, Social Media (leGriot), QA, Orchestrator, Agent Creator
- **9 crews:** Website, Research, Consulting, Social, Code, Writing, App, AgentCreation, Unknown
- **Models:** All via OpenRouter — MODEL_REGISTRY in agents.py (see Pending Code Fixes below)
- **Memory:** Qdrant (vector, semantic search) + PostgreSQL (archive)

## Live Services

- Orchestrator: <http://72.60.209.109:8000>
- PostgreSQL: 72.60.209.109:5432
- Qdrant: internal only
- WAHA (WhatsApp, parked): <http://72.60.209.109:3000>
- n8n: <https://n8n.srv1040886.hstgr.cloud>
- Telegram Bot: @agentsHQ4Bou_bot (Boubacar's ID: 7792432594)

## Verified Working Task Types (as of Day 3)

- website_build ✅
- social_content ✅ (leGriot voice)
- consulting_deliverable ✅ (Theory of Constraints approach)

## Built But Not Yet Tested

- research_report, code_task, general_writing, app_build, agent_creation

## Key Files

- orchestrator/orchestrator.py — main FastAPI service (398 lines)
- orchestrator/agents.py — 11 agent definitions with dynamic model selection (366 lines)
- orchestrator/crews.py — 9 crew assemblies (692 lines)
- orchestrator/router.py — task classification via Claude Haiku (165 lines)
- orchestrator/tools.py — 5 custom tools + MCP stubs (284 lines)
- orchestrator/memory.py — Qdrant + PostgreSQL memory system (204 lines)
- docker-compose.yml — 4 containers (postgres, qdrant, waha, orchestrator)
- infrasctructure/.env — all secrets (note: typo in folder name "infrasctructure")

## Skills Directory

- skills/community — 1,264 community skills (NOT runtime agent tools)
- skills/superpowers — 14 methodology skills (workflow discipline FOR DEVELOPMENT)

**Important:** Superpowers skills are the methodology WE use when building new features/agents.
They are NOT loaded into agents at runtime.
Workflow: brainstorming → writing-plans → executing-plans (use this for every new agent/feature).

Agents use STATIC tools only (Serper, file ops, SaveOutput, QueryMemory, Escalate, ProposeNewAgent).

## MCP Integration (Not Yet Connected)

Stubs exist in tools.py for:

- get_notion_tools()
- get_google_calendar_tools()
- get_gmail_tools()
- get_airtable_tools()

All MCP servers are ACTIVE in Claude's environment — high-value next integration.
Suggested wiring: consulting_agent → Notion, planner_agent → Google Calendar, researcher_agent → Gmail.

## Known Bugs (as of Day 3)

- files_created empty array bug (10s buffer fix applied in orchestrator.py, needs verification)
- PostgreSQL missing session_id column in conversation_archive table
- Qdrant client version compatibility (search attribute error, fails silently)
- Close Webhook node in n8n needs deletion (causes workflow error)
- Always Save Sub node in n8n is outdated, needs upgrade

## Pending Code Fixes (from Day 4 review)

MODEL_REGISTRY in agents.py uses old model strings — update to:

- `"claude-sonnet": "openrouter/anthropic/claude-sonnet-4-6"`
- `"claude-haiku":  "openrouter/anthropic/claude-haiku-4-5-20251001"`
- `"claude-opus":   "openrouter/anthropic/claude-opus-4-6"`

Router confidence threshold at 0.6 is too permissive — raise to 0.75.

No async job queue — long tasks block /run endpoint; implement job_id + /status/{job_id} pattern.

## Deferred Agents

- Journal Agent (daily voice prompts, reflection, habit tracking)
- Idea Capture Agent (brain dump via Telegram, summarize/archive)
- Spend Monitor (OpenRouter credit tracking, threshold alerts via Telegram)

→ Use brainstorming skill before building any of these.

## Day 4 Priority List

1. Verify files_created fix: `grep -n "start_time.timestamp" /app/orchestrator.py` inside container
2. Fix Send Files via Telegram n8n node (Chat ID + Document URL expression)
3. Delete Close Webhook node in n8n
4. Fix Archive to DB node (retest, port open)
5. Upgrade Always Save Sub node (delete old, add new Execute Workflow node)
6. Test remaining 5 task types via Telegram
7. Technical debt: async job queue, spend monitoring, PostgreSQL schema fix

## Session Commands

```bash
# Health check
ssh root@72.60.209.109 "cd ~/agentsHQ && docker compose ps"

# Watch logs
ssh root@72.60.209.109 "docker logs orc-crewai -f"

# SSH into container
ssh root@72.60.209.109 "docker exec -it orc-crewai bash"

# Rebuild after code changes
ssh root@72.60.209.109 "cd ~/agentsHQ && docker compose build orchestrator && docker compose up -d orchestrator"

# End-of-session git sync (run BOTH every session)
cd D:\Ai_Sandbox\agentsHQ && git add . && git commit -m "SESSION: ..." && git push
ssh root@72.60.209.109 "cd ~/agentsHQ && git add . && git commit -m 'SESSION: ...' && git push"
```
