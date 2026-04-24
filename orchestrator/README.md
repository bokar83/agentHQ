# agentsHQ Orchestrator Guidebook

The `orchestrator/` directory is the heart of the agentsHQ system. It handles the lifecycle of a task from classification to delivery.

## Key Components

| Module | Purpose |
| :--- | :--- |
| `orchestrator.py` | The main FastAPI service and entry point. Manages background tasks and Telegram/HTTP interfaces. |
| `router.py` | Classification engine. Uses LLMs to map raw user requests to defined `TaskTypes`. |
| `crews.py` | The assembly line. Defines how `Specialist Agents` are grouped into `Crews` for specific tasks. |
| `agents.py` | Agent factory. Handles the initialization of agents with their specific roles and tools. |
| `tools.py` | The tool registry. All external capabilities (Search, Notion, GitHub) are registered and exposed here. |
| `memory.py` | State preservation. Orchestrates the connection between Qdrant (vector) and PostgreSQL (structured). |
| `notifier.py` | Feedback loop. Handles communication back to the user via Telegram or Email. |
| `council.py` | The Sankofa Council. A strategic review layer for multi-perspective adversarial analysis. |

## The Execution Pipeline

1. **Ingest:** A message arrives via Telegram or HTTP.
2. **Route:** The `Router` classifies the intent into a `task_type`.
3. **Assemble:** The `Orchestrator` fetches the corresponding `Crew` from the registry.
4. **Execute:** The CrewAI process runs. Specialist agents collaborate using tools.
5. **Finalize:** The output is saved to `outputs/`, memory is updated, and the user is notified.

## Design Patterns

- **Asynchronous by Default:** All long-running crew executions are dispatched as background tasks.
- **Defensive Error Handling:** Every major step is wrapped in try/except with escalation to the `EscalateTool`.
- **Identity-Driven:** Agents are defined using "Soul" files (`AGENT.md`) to maintain consistent personas.

## Autonomy Layer (Phase 0+)

The autonomy layer lets crews originate work on their own cadence, with hard safety rails. Nothing runs autonomously until a crew's flag is flipped live.

### Env vars

| Var | Default | Purpose |
| :--- | :--- | :--- |
| `AUTONOMY_ENABLED` | `true` | Master switch. Not enforced in Phase 0 (rails only); later phases gate crew execution on this. |
| `AUTONOMY_DAILY_USD_CAP` | `1.00` | Hard cap on autonomous LLM spend per calendar day (MT). Hitting the cap auto-kills the guard. |
| `AUTONOMY_STATE_FILE` | `data/autonomy_state.json` | Kill switch + per-crew flags. Survives restarts. Gitignored. |

### Owner-only Telegram commands

| Command | What it does |
| :--- | :--- |
| `/autonomy_status` | Show kill state, today's spend, per-crew enabled/dry-run flags |
| `/pause_autonomy` | Flip the kill switch. All autonomous crews blocked until resumed. |
| `/resume_autonomy` | Clear the kill switch |
| `/spend` | Today's autonomous spend vs cap, broken down per crew |

### Per-call ledger columns

`llm_calls.autonomous` (bool) and `llm_calls.guard_decision` (text) are populated by `usage_logger` for every autonomous-crew call. User-initiated calls leave them at default (`false`, `NULL`). See `orchestrator/autonomy_guard.py` and migration `004_autonomous_flag.sql`.
