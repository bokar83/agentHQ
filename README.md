# agentsHQ

**Owner:** Boubacar Barry — Catalyst Works Consulting  
**VPS:** 72.60.209.109 (Ubuntu 24.04, Docker)  
**n8n:** https://n8n.srv1040886.hstgr.cloud  
**Version:** 2.0

---

## What This Is

agentsHQ is a self-hosted multi-agent AI system that runs on a private VPS. It receives tasks via WhatsApp or HTTP, routes them to specialist AI agents, and returns real deliverables — websites, research reports, consulting documents, code, social content, and more.

It is not a chatbot. It is not an automation tool. It is an autonomous operating system for knowledge work.

---

## Quick Start

**Send a task via WhatsApp** → agent's number → your request in plain language  
**Send a task via HTTP:**
```bash
curl -X POST http://72.60.209.109:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Create a website for a West African restaurant in Atlanta", "from_number": "test"}'
```

**Check what the system can do:**
```bash
curl http://72.60.209.109:8000/capabilities
```

**Check system status:**
```bash
curl http://72.60.209.109:8000/health
```

---

## System Files

| File | Purpose |
|---|---|
| `AGENTS.md` | System soul file — identity, architecture, task registry |
| `CLAUDE.md` | Instructions for AI coding tools working on this codebase |
| `README.md` | You are here |
| `docker-compose.yml` | Container orchestration |
| `.env` | Secrets and configuration (never commit) |

## Orchestrator Files

| File | Purpose |
|---|---|
| `orchestrator/orchestrator.py` | FastAPI service, main entry point |
| `orchestrator/router.py` | Task classification engine |
| `orchestrator/crews.py` | Crew assembly by task type |
| `orchestrator/agents.py` | All agent definitions |
| `orchestrator/tools.py` | Tool registry and MCP adapters |
| `orchestrator/memory.py` | Qdrant + PostgreSQL memory interface |

---

## Current Capabilities

| Task Type | Example Request |
|---|---|
| Website build | "Create a website for Saveurs d'Afrique restaurant in Atlanta" |
| App build | "Build a ROI calculator for consulting engagements" |
| Research | "Research the top 5 AI agent frameworks in 2026" |
| Consulting | "Write a proposal for a 3-month diagnostic engagement" |
| Social content | "Write a LinkedIn post about the hidden cost of ignoring constraints" |
| Code | "Write a Python script to batch rename files by date" |
| Writing | "Draft an email to a prospect who went quiet after the discovery call" |

---

## Adding New Capabilities

The system can propose and create new agent types when it encounters tasks it can't handle. Simply send a request — if no agent fits, the system will propose a new one for your approval.

To manually add a capability:
1. Add task type to `orchestrator/router.py`
2. Add crew builder to `orchestrator/crews.py`
3. Add agent to `orchestrator/agents.py` (if needed)
4. Create `agents/[name]/AGENT.md` soul file
5. Update `AGENTS.md` registry
6. Restart: `docker compose restart orchestrator`

---

## Phase Roadmap

- **Phase 1 (current):** Core agent stack live, WhatsApp interface, basic task types
- **Phase 2:** leGriot social media agent, memory-informed outputs
- **Phase 3:** MCP integrations (Notion, Google Calendar, Gmail)
- **Phase 4:** Agent creator agent, self-expansion loop
- **Phase 5:** Always-save workflow (GitHub + Drive + Notion archival)
- **Phase 6:** Multi-client support, consulting delivery workflows

---

## Support

- VPS SSH: `ssh root@72.60.209.109`
- n8n dashboard: https://n8n.srv1040886.hstgr.cloud
- Logs: `docker compose logs orchestrator -f`
- Restart: `docker compose restart orchestrator`
