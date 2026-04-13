# agentsHQ — Agents Guidebook

The `agents/` directory contains the definition of every specialist agent in the system. Each agent project follows a strict "Identity First" pattern.

## Directory Structure

```
agents/
└── [agent_name]/
    ├── AGENT.md           ← The "Soul" file
    └── agent.py           ← The technical implementation (optional)
```

## The Soul File (`AGENT.md`)

Every agent MUST have a `AGENT.md` file. This is the source of truth for the agent's identity. It contains:
- **Role:** The official title (e.g., "Strategic Planner").
- **Goal:** What the agent is trying to accomplish.
- **Backstory:** The personality, tone, and experience that informs their reasoning.
- **Standard Tools:** The list of capabilities assigned to this specific agent.

## Adding a New Agent

1. **Create Directory:** Use `snake_case` for the folder name.
2. **Draft Soul File:** Write the `AGENT.md`. Be specific about personality and constraints.
3. **Register in Orchestrator:**
   - Add the agent builder function to `orchestrator/agents.py`.
   - Update the `AGENT_REGISTRY` in `orchestrator/agents.py`.
4. **Update Identity:** Add the new agent to the system-wide `AGENTS.md` file.

## Best Practices

- **Naming:** Folders must be `snake_case` to ensure they are valid Python package names.
- **Isolation:** Agents should stay within their "backstory" lane. Avoid making agents that are "general assistants."
- **Evolution:** Agent instructions can be optimized automatically by the `OpenSpace` evolution engine based on past performance.
