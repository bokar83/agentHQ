---
name: agentsHQ project context
description: Core architecture, status, and goals of the agentsHQ multi-agent system owned by Boubacar Barry
type: project
---

# agentsHQ Project Context

## System Identity

- **Owner:** Boubacar Barry (Catalyst Works Consulting)
- **VPS:** 72.60.209.109 (Hostinger)
- **GitHub:** <https://github.com/bokar83/agentHQ> (source of truth)
- **Local:** D:\Ai_Sandbox\agentsHQ

## Architecture

- **Orchestrator:** FastAPI + CrewAI, running in Docker on VPS port 8000
- **Router:** Claude Haiku classifies task type → routes to correct crew
- **11 agents:** Planner, Researcher, Copywriter, Web Builder, App Builder, Code, Consulting, Social Media (leGriot), QA, Orchestrator, Agent Creator
- **9 crews:** Website, Research, Consulting, Social, Code, Writing, App, AgentCreation, Unknown
- **Agent Teams:** Parallel crew execution pattern — `POST /run-team` endpoint, `run_parallel_team()` + `build_team_synthesis_crew()` in crews.py
- **Models:** All via OpenRouter — MODEL_REGISTRY in agents.py (see Pending Code Fixes below)
- **Memory:** Qdrant (vector, semantic search) + PostgreSQL (archive)

## Live Services

- Orchestrator: <http://72.60.209.109:8000>
- PostgreSQL: 72.60.209.109:5432
- Qdrant: internal only
- n8n: <https://n8n.srv1040886.hstgr.cloud>
- Telegram Bot: @agentsHQ4Bou_bot (Boubacar's ID: 7792432594)

## Verified Working Task Types (as of Day 3)

- website_build ✅
- social_content ✅ (leGriot voice)
- consulting_deliverable ✅ (Theory of Constraints approach)

## Built But Not Yet Tested

- research_report, code_task, general_writing, app_build, agent_creation

## Key Files

- orchestrator/orchestrator.py — main FastAPI service + /run-team endpoint
- orchestrator/agents.py — 11 agent definitions with dynamic model selection
- orchestrator/crews.py — 9 sequential crews + agent teams parallel functions
- orchestrator/router.py — task classification via Claude Haiku
- orchestrator/tools.py — 5 custom tools + MCP stubs
- orchestrator/memory.py — Qdrant + PostgreSQL memory system
- docker-compose.yml — 4 containers (postgres, qdrant, metaclaw, orchestrator)
- .env — all secrets (repo root: `d:\Ai_Sandbox\agentsHQ\.env` locally, `/root/agentsHQ/.env` on VPS)
- skills/CatalystWorksSkills/ — custom skills tracked in git (agent-teams, sheet-mint)
- docs/memory/ — session memory files (read at start of every session)

## Skills Directory

- skills/community — community skills (external git repo, NOT tracked here)
- skills/superpowers — methodology skills (external git repo, NOT tracked here)
- skills/CatalystWorksSkills/ — custom skills, TRACKED in git
  - agent-teams/SKILL.md — parallel crew execution pattern (VPS agent teams)
  - sheet-mint/SKILL.md — spreadsheet generation skill (v2, updated 2026-03-27)

## sheet-mint Skill Status (as of 2026-03-27)

The sheet-mint skill builds sellable Google Sheets templates via GWS CLI and posts them to Etsy.

**Current state:**

- SKILL.md: v2 — includes premium design rules (dark/light color systems, typography hierarchy, REPT progress bars, card structure rules)
- Phase 2 evals: 3/3 passing (100%)
- Phase 3 (GWS CLI build): NOT yet fully tested end-to-end — blocked by permission loop
- Phase 4 (listing/mockup): written, not tested

**Partially built spreadsheet in Drive:**

- Product: Smart 50/30/20 Monthly Budget Planner
- Spreadsheet ID: `1HpWewlOv4p1YCkzAs0iECWgWQvpLpr2TZbo5rKaNuCQ`
- URL: [Smart Budget Planner](https://docs.google.com/spreadsheets/d/1HpWewlOv4p1YCkzAs0iECWgWQvpLpr2TZbo5rKaNuCQ/edit)
- Status: 7 tabs created, _Ref!A1:A13 (months) written. Everything else pending.
- BUILD_PROMPT.md: `D:\Ai_Sandbox\agentsHQ\zzzArchive\testingSandbox\smart-budget-planner\BUILD_PROMPT.md`
- SESSION_SUMMARY.md: `D:\Ai_Sandbox\agentsHQ\zzzArchive\testingSandbox\smart-budget-planner\SESSION_SUMMARY.md`

**To resume the build:** Start Claude Code with `claude --dangerously-skip-permissions`, then reference the spreadsheet ID and BUILD_PROMPT.md. Skip Phases 1 and 2 — go straight to Phase 3 execution.

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

## Fixed in Day 7 (2026-04-01)

- ✅ Growth Hunter Engine fully built and deployed
  - 5-step discovery: Serper LinkedIn dork → Serper local business → Firecrawl → Hunter.io → Apollo fallback
  - Supabase CRM: leads + lead_interactions tables live; psycopg2 via Transaction Pooler (port 6543)
  - orchestrator/db.py — centralized DB connection utility (Supabase + VPS Postgres)
  - skills/serper_skill/hunter_tool.py — discover_leads() + reveal_email_for_lead()
  - skills/local_crm/crm_tool.py — rewritten: Supabase, phone field, update_lead_email(), get_lead_by_name()
  - CRMRevealEmailTool added to HUNTER_TOOLS; scoreboard_tool added to HUNTER_TOOLS
  - Hunter crew: 20 leads/run, memory=False, scoreboard task at end
  - Email report: send_hunter_report() in notifier.py — fires after every hunter_task run
  - Email recipients: bokar83@gmail.com + boubacarbusiness@gmail.com
  - SMTP via Gmail App Password — SMTP_USER + SMTP_PASS in .env + docker-compose.yml
  - Trigger: "find leads" or "prospect" to @agentsHQ4Bou_bot
- ✅ asyncio.to_thread() — crew.kickoff() no longer blocks uvicorn event loop
- ✅ All WhatsApp/WAHA references removed — Telegram only
- ✅ infrasctructure/ stale folder deleted — .env at repo root only
- ✅ gws_client.py deleted (Windows-only dead code, not importable in Docker)

## Known Bugs (as of Day 5 — 2026-03-28)

- PostgreSQL missing session_id column in conversation_archive table
- Qdrant client version compatibility (search attribute error, fails silently)
- Always Save Sub node in n8n is outdated — needs upgrade in n8n UI (delete old Execute Workflow node, add new one)
- No async job queue — long tasks block /run endpoint; implement job_id + /status/{job_id} pattern

## Fixed in Day 5 (2026-03-28)

- ✅ OpenRouter key replaced (old key was returning 401 "User not found")
- ✅ MODEL_REGISTRY corrected: `claude-sonnet-4.6`, `claude-haiku-4.5`, `claude-opus-4.6` (OpenRouter uses dot notation)
- ✅ Router confidence threshold raised from 0.6 → 0.75
- ✅ Telegram workflow: added `Has Files?` IF guard before `Send Files via Telegram` (prevents crash on empty files_created)
- ✅ Security hook emoji encoding fixed (Windows cp1252 crash on push)
- ✅ /run endpoint tested and confirmed working (20s, success:true)

## n8n API Access (for future programmatic fixes)

- API Key: stored in `/var/lib/docker/volumes/n8n_data/_data/database.sqlite` → `user_api_keys.apiKey`
- n8n REST API: `http://localhost:5678/api/v1` — use `X-N8N-API-KEY` header
- Workflow IDs: Telegram=`a6ciAzyqvnXIC9lw`
- CLI import (`n8n import:workflow`) fails while n8n is running due to SQLite lock — always use REST API instead

## Pending Code Improvements

✅ /run endpoint now uses asyncio.to_thread() — crew.kickoff() runs off the event loop so concurrent Telegram messages don't block.

## Deferred Agents

- Journal Agent (daily voice prompts, reflection, habit tracking)
- Idea Capture Agent (brain dump via Telegram, summarize/archive)
- Spend Monitor (OpenRouter credit tracking, threshold alerts via Telegram)

→ Use brainstorming skill before building any of these.

## Day 6 Priority List

1. Test Telegram bot end-to-end: send a real message to @agentsHQ4Bou_bot and confirm reply arrives
2. Upgrade Always Save Sub node in n8n UI (delete old Execute Workflow node, add fresh one pointing to `CW | SUB - Always Save`)
3. Test all 6 remaining task types via Telegram: research_report, code_task, general_writing, app_build, agent_creation, consulting_deliverable
4. Async job queue: implement job_id + /status/{job_id} to prevent timeout on long tasks
5. PostgreSQL schema fix: add session_id column to conversation_archive

## Day 4 Priority List (reference)

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
