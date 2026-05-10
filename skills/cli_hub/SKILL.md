---
name: "cli_hub"
description: "Search the community CLI-Hub for pre-built agent-native CLIs (GIMP, Blender, OBS, etc.) and install them. Triggers on \"cli hub\", \"find a CLI\", \"agent CLI\", \"install CLI tool\", \"pre-built CLI\", \"CLI for\"."
---

# CLI-Hub Explorer Skill

**Purpose**: This skill allows you to discover and install community-contributed CLIs that wrap popular open-source software. Use this to expand your capabilities without manual configuration.

---

## 🛠️ Usage Examples

### 🔍 Search for a tool

Find if a tool like "Blender" or an "image editor" exists in the hub.

- `search_cli(query="blender")`
- `search_cli(query="image editor")`

### 📋 List all tools

See everything available.

- `list_clis()`
- `list_clis(category="video")`

### 🚀 Install a tool

Install the tool to the system PATH.

- `install_cli(name="blender")`
- `install_cli(name="shotcut")`

---

## ⛓️ Agent Guidance

1. **Before Building**: Always check the Hub before attempting to build a new skill from scratch using the `SkillBuilder`.
2. **Post-Installation**: After `install_cli` returns "success", search for the new tool's command (usually `cli-anything-<name>`) in the system PATH.
3. **Environment**: Many tools require the base software to be installed (e.g., GIMP needs `apt install gimp`). Read the `requires` field in the search results.
