# agentsHQ — Skills Guidebook

The `skills/` directory contains modular capabilities that agents can use to interact with the world. Skills are our "superpowers."

## Directory Structure

```
skills/
└── [skill_name]/
    ├── SKILL.md           ← Detailed capability definition
    └── skill.py           ← Logic for the skill (tool functions)
```

## The Skill Definition (`SKILL.md`)

Each skill has a descriptor file that explains:
- **Capability:** What does this skill allow an agent to do?
- **Keywords:** Trigger words that help the router or agents identify the need for this skill.
- **Environment:** Any `.env` variables required (e.g., `GITHUB_TOKEN`, `NOTION_API_KEY`).
- **Standard Usage:** Code snippets or CLI examples of how to invoke the skill.

## Core Patterns

- **CLI-Anything:** Many skills are wrappers around powerful CLI tools (e.g., `vercel-cli`, `gh`, `notion-cli`).
- **MCP Adapters:** We use the Model Context Protocol to bridge agents to external data sources like Google Calendar, Gmail, and Notion.
- **Skill Evolution:** If an agent finds it needs a capability it doesn't have, it can use the `SkillBuilder` agent to propose and build a new skill directory.

## Registering a Skill

1. **Implement Logic:** Create the `skill.py` with one or more decorated `@tool` functions.
2. **Register Tool:** Add the tool factory or function to `orchestrator/tools.py`.
3. **Bind to Agents:** Assign the skill to specific agents in `orchestrator/agents.py`.
