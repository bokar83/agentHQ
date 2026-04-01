# AGENT_INSTRUCTIONS.md
# Instructions for AI Coding Assistants & Agentic IDEs
# Works with: Claude Code, Cursor, Antigravity, Windsurf, RooCode, Gemini CLI, Copilot, and any AGENTS.md-compatible tool

---

## What This Codebase Is

agentsHQ is a self-hosted multi-agent orchestration system for Boubacar Barry / Catalyst Works Consulting.
It runs on a private VPS (Ubuntu 24.04, Docker). It receives tasks via Telegram or HTTP, routes them to
specialist AI agents built with CrewAI, and returns real deliverables.

**This is not a demo. Every change ships to production.**

---

## LLM & Tool Philosophy

**No tool lock-in. No LLM lock-in.**

- The best tool for any job is chosen by the operator (Boubacar) at the time of the task
- LLM assignments live in each agent's `AGENT.md` soul file — not in shared code
- The `get_llm(model, temperature)` factory in `agents.py` accepts any model string from any provider
- MCP is the preferred integration protocol for external services
- If Boubacar specifies a model or tool for a specific agent or skill, that specification wins

Do not assume any specific AI assistant, IDE, or LLM when writing code or documentation.
Write tool-agnostic code that any capable AI assistant can read, understand, and extend.

---

## Critical Rules

1. **Never hardcode task logic** — all routing goes through `router.py`. No task-specific instructions in `orchestrator.py`.
2. **Never hardcode credentials** — all secrets come from environment variables. Never put API keys in code.
3. **Never break the FastAPI contract** — the `/run` endpoint signature must remain stable. n8n depends on it.
4. **Always update AGENTS.md** — when adding a new agent or task type, register it in `AGENTS.md`.
5. **Always create a SKILL.md** — when adding a new skill/tool, create the soul file in `skills/[skill-name]/SKILL.md`.
6. **Always create an AGENT.md** — when adding a new agent, create the soul file in `agents/[agent-name]/AGENT.md`.
7. **Silence means success** — Linux convention. No output from a command = it worked.
8. **Never guess at memory** — if you need to know what's in a file, read it before editing it.

---

## Architecture Principles

- **Router first** — `router.py` classifies intent before any crew is assembled
- **Dynamic crew assembly** — `crews.py` builds the right crew for each task type at runtime
- **Agents are stateless** — all memory goes through Qdrant or PostgreSQL, never in-process
- **Tools are registered** — all tools defined in `tools.py`, imported by agents that need them
- **MCP is preferred** — use MCPServerAdapter for external service integrations
- **Soul files are canonical** — `AGENTS.md`, `AGENT.md`, and `SKILL.md` files define system behavior. Code implements them.

---

## File Responsibilities

| File | Responsibility | Touch When |
|---|---|---|
| `orchestrator/orchestrator.py` | FastAPI app, main entry point | Adding new API endpoints |
| `orchestrator/router.py` | Task classification engine | Adding new task types |
| `orchestrator/crews.py` | Crew assembly by task type | Adding new crew configurations |
| `orchestrator/agents.py` | All Agent definitions | Adding/modifying agents |
| `orchestrator/tools.py` | All Tool definitions + MCP adapters | Adding tools or MCP servers |
| `orchestrator/memory.py` | Qdrant + PostgreSQL interface | Changing memory behavior |
| `AGENTS.md` | System soul file — identity + registry | Any structural change |
| `AGENT_INSTRUCTIONS.md` | Coding assistant instructions | Updating dev workflow |

---

## Adding a New Task Type — Checklist

- [ ] Add task type key and metadata to `TASK_TYPES` dict in `router.py`
- [ ] Add crew builder function in `crews.py`
- [ ] Add any new agent definitions needed in `agents.py`
- [ ] Create `agents/[agent-name]/AGENT.md` soul file
- [ ] Add any new tools to `tools.py`
- [ ] Map crew type to builder in `CREW_REGISTRY` in `crews.py`
- [ ] Register new task type in `AGENTS.md` Task Type Registry table
- [ ] Test: `curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d '{"task": "test request", "from_number": "test"}'`

---

## Adding a New Tool — Checklist

- [ ] Create `skills/[skill-name]/SKILL.md` soul file
- [ ] Implement tool as `BaseTool` subclass in `tools.py` OR as MCP adapter
- [ ] Add to appropriate tool bundle (RESEARCH_TOOLS, CODE_TOOLS, etc.)
- [ ] Import in `agents.py` for relevant agents
- [ ] Test in isolation before assigning to agents

---

## Adding a New Agent — Checklist

- [ ] Create `agents/[agent-name]/AGENT.md` soul file
- [ ] Define `build_[name]_agent()` function in `agents.py`
- [ ] Specify LLM in `AGENT.md` (if Boubacar has a preference) or use appropriate default
- [ ] Assign minimal tool set — only what the agent actually needs
- [ ] Add to relevant crews in `crews.py`
- [ ] Register in `AGENTS.md`

---

## LLM Configuration

LLM assignments are agent-specific. To change the model for an agent:
1. Update the agent's `AGENT.md` soul file with the preferred model
2. Update the `llm=` parameter in the agent's `build_*()` function in `agents.py`
3. The `get_llm(model, temperature)` factory accepts any OpenRouter model string

Current model strings (via OpenRouter):
```
anthropic/claude-sonnet-4-5       # balanced, most tasks
anthropic/claude-opus-4-5         # complex reasoning
google/gemini-flash-1.5           # fast, cheap, routing/planning
perplexity/llama-3.1-sonar-large-128k-online  # research with web access
openai/gpt-4o                     # alternative general purpose
```

To use a different provider directly (not via OpenRouter), update `openai_api_base` in `get_llm()`.

---

## Environment Variables

All in `~/agentsHQ/.env`. Required:
```
OPENROUTER_API_KEY=
SERPER_API_KEY=
POSTGRES_PASSWORD=
GITHUB_USERNAME=
GITHUB_REPO=
REPORT_EMAIL=
GENERIC_TIMEZONE=
N8N_ENCRYPTION_KEY=
VPS_IP=
```

Optional (Phase 5):
```
GOOGLE_DRIVE_FOLDER_ID=
NOTION_SECRET=
NOTION_DATABASE_ID=
PERSONAL_WHATSAPP=
N8N_ESCALATION_WEBHOOK=
```

---

## Running & Testing

```bash
# Health check
curl http://localhost:8000/health

# What can the system do?
curl http://localhost:8000/capabilities

# Classify a task without running it
curl "http://localhost:8000/classify?task=write+a+linkedin+post+about+constraints"

# Run a task
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Create a one-page website for a pizza restaurant", "from_number": "test"}'

# List outputs
curl http://localhost:8000/outputs

# Search memory
curl "http://localhost:8000/memory/search?query=restaurant+website"
```

---

## Deployment

```bash
# Upload a changed file
scp -i ~/.ssh/id_ed25519 [local-file] root@72.60.209.109:~/agentsHQ/[path]

# Restart orchestrator (no rebuild needed for .py changes)
ssh root@72.60.209.109 "cd ~/agentsHQ && docker compose restart orchestrator"

# Rebuild (needed when requirements.txt changes)
ssh root@72.60.209.109 "cd ~/agentsHQ && docker compose build orchestrator && docker compose up -d orchestrator"

# Watch logs
ssh root@72.60.209.109 "docker compose logs orchestrator -f"
```

---

## Code Style

- Python 3.11+
- Type hints on all function signatures
- Docstrings on all classes and public functions
- Use `logging` module — no `print()` statements in production code
- Agent descriptions written in second person ("You are...")
- Task descriptions written in imperative mood ("Research and summarize...")
- One responsibility per function
- Fail loudly on configuration errors, fail gracefully on runtime errors
