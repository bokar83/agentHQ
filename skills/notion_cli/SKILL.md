---
name: notion-cli
description: Project-specific CLI for direct interaction with Notion databases in agentsHQ.
---

# Notion CLI Skill

**Name:** notion_cli-rs
**Description:** A dedicated project-specific CLI for direct interaction with Notion databases within the `agentsHQ` ecosystem. Use this for robust logging, task management, and structural updates to the Notion workspace without relying solely on MCP server adapters.

## Usage

```bash
python skills/notion_cli/notion_cli.py <command> [args]
```

### Commands

#### `log-action`
Logs a technical agent session or specific output to the **Agent Activity Log** database.

**Args:**
- `title` (required): Name of the action or task.
- `--status`: Selection from `Success`, `In Progress`, `Failed`, `Pending Review`.
- `--agent`: Name of the agent (e.g., `Code Agent`).
- `--transcript`: Detailed session log or summary.
- `--artifacts`: URL to generated files or outputs.

**Example:**
```bash
python skills/notion_cli/notion_cli.py log-action "Notion Organization Setup" --status Success --agent "Code Agent"
```

#### `search`
Searches the entire Notion workspace for pages, databases, or content.

**Args:**
- `query` (required): The search term.

**Example:**
```bash
python skills/notion_cli/notion_cli.py search "Execution"
```

## Configuration

- **Secret**: Uses `NOTION_SECRET` from `.env`.
- **Primary Database**: Uses `NOTION_DATABASE_ID` (Mapping: Agent Activity Log).
