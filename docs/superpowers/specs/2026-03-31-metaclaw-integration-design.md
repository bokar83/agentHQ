# MetaClaw Integration Design
**Date:** 2026-03-31  
**Project:** agentsHQ — Catalyst Works Consulting  
**Status:** Approved, ready for implementation planning

---

## Overview

MetaClaw is a meta-learning proxy that sits between CrewAI agents and the LLM API. It intercepts every LLM call, injects a skill bank (Markdown files), maintains cross-session memory (SQLite), and optionally fine-tunes models via RL — all transparently, without modifying agent logic.

This integration adds continuous self-improvement to agentsHQ's three highest-value agents, delivered in three phased layers with a master kill switch for safe rollback at every stage.

---

## Architecture

MetaClaw runs as a new Docker service (`metaclaw`) on VPS `72.60.209.109`, inside the existing Docker network alongside `orchestrator`, `qdrant`, and `postgres`. It exposes an OpenAI-compatible proxy on port `30000` (internal network only).

Three agents — `consulting`, `researcher`, `social_media` — use a new `get_llm_metaclaw()` factory in `agent-brain/agents.py` that routes through the MetaClaw proxy. All other agents continue using `get_llm()` (direct OpenRouter) unchanged.

```
Telegram → n8n → orchestrator:8000
                      │
          ┌───────────┼───────────────────┐
          │           │                   │
    consulting    researcher         social_media
    agent         agent              agent
          │           │                   │
          └───────────┴───────────────────┘
                      │
              metaclaw:30000 (Docker internal)
              ├── injects skill .md files into system prompt
              ├── collects conversation samples
              ├── [Phase 2] retrieves + injects memory
              ├── [Phase 3] feeds RL training loop
              └── forwards to OpenRouter → LLM
                      │
              all other agents: bypass MetaClaw
              └── OpenRouter directly (unchanged)
```

---

## Rollback Safety

Every layer has an independent kill switch. No destructive changes.

| Switch | How | Effect |
|--------|-----|--------|
| **Master kill switch** | Set `USE_METACLAW=false` in VPS `.env` | All three agents fall back to direct OpenRouter instantly |
| **Per-agent fallback** | `get_llm_metaclaw()` catches proxy connection errors and calls `get_llm()` | If MetaClaw is down, agents degrade gracefully — tasks still complete |
| **Phase 2 disable** | Set `memory.enabled: false` in `~/.metaclaw/config.yaml` | Memory injection off; Qdrant + PostgreSQL untouched |
| **Phase 3 rollback** | Change model in `get_llm_metaclaw()` back to Claude Sonnet | Reverts from Kimi K2.5 to Claude in one line; fine-tuned weights preserved on Tinker |

Qdrant and PostgreSQL are never modified by this integration. They run in parallel with MetaClaw's SQLite memory store throughout.

---

## Phase 1 — Skills Layer

**Goal:** Agents receive injected skill instructions on every LLM call. Samples are collected for future evolution.

### What MetaClaw does in Phase 1
1. Intercepts the LLM call from the CrewAI agent
2. Retrieves relevant skill `.md` files from `~/.metaclaw/skills/` (keyword or embedding match)
3. Injects matched skills into the system prompt
4. Forwards the augmented call to OpenRouter → Claude Sonnet
5. Stores the conversation sample with metadata for future RL use

### Seed skill files (pre-written, committed to repo)

| File | Content |
|------|---------|
| `consulting_voice.md` | Boubacar's 8 voice rules extracted from agent backstory — bold diagnosis, insight-first, three dimensions, counterintuitive observation, uncomfortable closing question |
| `researcher_synthesis.md` | Research brief structure, source prioritization, never fabricate data, always cite URLs |
| `social_voice.md` | leGriot rules — no fabricated stories, hypothetical framing (`"Imagine if..."`), no buzzwords, write from principles not anecdotes |
| `catalyst_works_context.md` | Who Boubacar is, what Catalyst Works does, Theory of Constraints expertise, target client profile |

Seed skills are extracted directly from existing agent backstories — current agent behavior is preserved and explicitly encoded. MetaClaw evolves these files automatically as interactions accumulate.

### Config (`~/.metaclaw/config.yaml` on VPS)
```yaml
mode: skills_only
proxy:
  host: 0.0.0.0
  port: 30000
  api_key: metaclaw-internal
upstream:
  base_url: https://openrouter.ai/api/v1
  api_key: ${OPENROUTER_API_KEY}
  model: openrouter/anthropic/claude-sonnet-4-5
skills:
  retrieval_mode: hybrid
  top_k: 3
  max_tokens: 600
memory:
  enabled: false
rl:
  enabled: false
```

### Code changes — `agent-brain/agents.py`

**New factory function** (alongside existing `get_llm()`):
```python
_METACLAW_TEMPS = {"consultant": 0.3, "researcher": 0.2, "social": 0.8}

def get_llm_metaclaw(agent_role: str, task_complexity: str = "moderate", temperature: float = None) -> LLM:
    """
    MetaClaw-proxied LLM for consulting, researcher, social_media agents.
    Falls back to direct OpenRouter if USE_METACLAW=false or proxy unreachable.
    """
    if os.environ.get("USE_METACLAW", "true").lower() != "true":
        return select_llm(agent_role, task_complexity, temperature)

    final_temp = temperature if temperature is not None else _METACLAW_TEMPS.get(agent_role, 0.3)

    try:
        return LLM(
            model=MODEL_REGISTRY.get("claude-sonnet"),
            api_key="metaclaw-internal",
            base_url="http://metaclaw:30000/v1",
            temperature=final_temp,
            extra_headers={
                "HTTP-Referer": "https://agentshq.catalystworks.com",
                "X-Title": "agentsHQ"
            }
        )
    except Exception:
        logger.warning("MetaClaw proxy unreachable — falling back to direct OpenRouter")
        return select_llm(agent_role, task_complexity, temperature)
```

**Agent function changes** — three one-line swaps:
- `build_consulting_agent()`: `llm=select_llm("consultant", "complex")` → `llm=get_llm_metaclaw("consultant", "complex")`
- `build_researcher_agent()`: `llm=select_llm("researcher", "moderate")` → `llm=get_llm_metaclaw("researcher", "moderate")`
- `build_social_media_agent()`: `llm=select_llm("social", "moderate")` → `llm=get_llm_metaclaw("social", "moderate")`

### Docker changes — `docker-compose.yml`

New service block:
```yaml
metaclaw:
  image: python:3.11-slim
  container_name: agentshq-metaclaw-1
  working_dir: /app
  volumes:
    - metaclaw_config:/root/.metaclaw
    - ./metaclaw:/app/metaclaw_seed
  environment:
    - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
  command: >
    bash -c "pip install aiming-metaclaw &&
             cp -n /app/metaclaw_seed/skills/* /root/.metaclaw/skills/ 2>/dev/null || true &&
             metaclaw start --mode skills_only"
  ports:
    - "127.0.0.1:30000:30000"
  restart: unless-stopped

volumes:
  metaclaw_config:
```

### New directory in repo: `metaclaw/`
```
metaclaw/
  skills/
    consulting_voice.md
    researcher_synthesis.md
    social_voice.md
    catalyst_works_context.md
  config_template.yaml     # reference config, not secrets
```

### VPS environment — `.env` additions
```
USE_METACLAW=true
```

---

## Phase 2 — Memory Layer

**Trigger:** Phase 1 stable for ~1 week. Skills injecting cleanly, no proxy errors in logs.

**Goal:** MetaClaw's SQLite memory store adds typed cross-session memory (episodic, semantic, preference, project_state, procedural_observation) on top of Qdrant + PostgreSQL. Agents remember past work, client context, and user preferences across sessions.

### What changes
- One config update on VPS: `mode: skills_only` → `mode: skills_and_memory`
- Add `memory.enabled: true` and `memory.scope_id: agentshq` to `~/.metaclaw/config.yaml`
- All three target agents share one memory namespace — consulting's client knowledge is available to researcher; social agent accumulates approved voice patterns over time

### What agents gain
- **Consulting:** Remembers past client engagements, prior diagnoses, what recommendations were accepted
- **Researcher:** Remembers what has already been researched, which sources were reliable, prior research briefs
- **Social:** Accumulates approved phrasings, rejected buzzwords, successful post structures

### No code changes to agentsHQ
MetaClaw handles memory retrieval and injection entirely in the proxy layer.

### Rollback
Set `memory.enabled: false` in config. SQLite store is preserved — no data loss.

---

## Phase 3 — RL Layer (MadMax Mode)

**Trigger:** Phase 2 stable. Meaningful sample volume accumulated (estimated 2-4 weeks of normal usage).

**Goal:** GRPO LoRA fine-tuning on Kimi K2.5 using collected samples. Fine-tuning runs during VPS idle windows via Tinker or MinT cloud (GPU provided by service). PRM judge uses Claude Haiku 4.5.

### Model selection rationale
- **Kimi K2.5** (Moonshot via OpenRouter): ~$0.15/M input tokens, MetaClaw's native recommended model, strong reasoning and instruction following. Most cost-efficient capable model available.
- **Claude Haiku 4.5** as PRM judge: already in MODEL_REGISTRY, fast, cheap, reliable scorer
- **Claude Sonnet** remains available for all non-MetaClaw agents throughout

### Important: agent model changes in Phase 3
The three target agents switch from Claude Sonnet to Kimi K2.5 as their base model. This is the model being fine-tuned. Claude continues serving all other agents.

### What changes
1. Register Tinker or MinT API key (user obtains from service)
2. Update MetaClaw config: `mode: madmax`, add RL backend config block
3. Update `get_llm_metaclaw()`: change `model_string` to Kimi K2.5 model ID
4. Add PRM config: `prm_model: openrouter/anthropic/claude-haiku-4-5`

### Config additions for Phase 3
```yaml
mode: madmax
rl:
  enabled: true
  backend: tinker        # or mint
  api_key: ${TINKER_API_KEY}
  base_url: https://api.tinker.ai/v1
  model: moonshotai/kimi-k2.5
  prm_model: openrouter/anthropic/claude-haiku-4-5
  scheduler:
    idle_only: true
    sleep_hours: "22:00-07:00"
```

### Rollback
Change `model_string` in `get_llm_metaclaw()` back to `MODEL_REGISTRY.get("claude-sonnet")`. Fine-tuned weights remain on Tinker — recoverable at any time.

---

## Implementation Sequence

| Phase | Prerequisites | Estimated effort | Risk |
|-------|--------------|-----------------|------|
| Phase 1 — Skills | None | ~3-4 hours | Low — isolated to 3 agents, fallback built in |
| Phase 2 — Memory | Phase 1 stable 1 week | ~30 min (config only) | Very low — no code changes |
| Phase 3 — RL | Phase 2 stable, sample volume, Tinker API key | ~2 hours | Medium — model switch for 3 agents |

---

## Files to Create/Modify

### Create (new)
- `metaclaw/skills/consulting_voice.md`
- `metaclaw/skills/researcher_synthesis.md`
- `metaclaw/skills/social_voice.md`
- `metaclaw/skills/catalyst_works_context.md`
- `metaclaw/config_template.yaml`

### Modify (existing)
- `agent-brain/agents.py` — add `get_llm_metaclaw()`, update 3 agent functions
- `docker-compose.yml` — add `metaclaw` service + volume
- `.env` (VPS) — add `USE_METACLAW=true`

### Not modified
- `agent-brain/orchestrator.py` — no changes
- `agent-brain/memory.py` — no changes (Qdrant + PostgreSQL untouched)
- `agent-brain/crews.py` — no changes
- `agent-brain/router.py` — no changes
- All other agent build functions — no changes
