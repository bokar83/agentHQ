---
name: memory
description: Memory helpers and references for retrieving and preserving agent operating context. Two layers: (1) flat-file auto-memory in ~/.claude/projects/.../memory/ for curated signal; (2) MemPalace semantic search over verbatim conversation history.
---

# Memory

Two-layer system. Use both.

## Layer 1  -  Curated flat-file memory (primary)

Files in `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/`. Typed entries: `user_*.md`, `feedback_*.md`, `project_*.md`, `reference_*.md`. Index: `MEMORY.md`. Always loaded at session start. Source of truth for stable facts.

Write with `Write` tool. Never delete  -  update or archive.

## Layer 2  -  MemPalace semantic search (verbatim recall)

Palace: `d:/Ai_Sandbox/agentsHQ/sandbox/.tmp/palace-agentshq`
Venv: `d:/Ai_Sandbox/agentsHQ/sandbox/.tmp/venv-mempalace/Scripts/`
MCP: `mempalace` (registered in `.claude.json`, 8 tools available)
Sweep: 5353 drawers from 71 Claude Code transcript files (indexed 2026-05-04)

Use when: need exact wording from a past session, troubleshooting a recurring error, verifying what was actually said vs. what was summarized.

**Search via MCP tool** (preferred  -  no terminal needed):
`mempalace_search` with query string, optional wing/room filter.

**Search via CLI**:

```powershell
$env:PYTHONIOENCODING = "utf-8"
& "d:/Ai_Sandbox/agentsHQ/sandbox/.tmp/venv-mempalace/Scripts/mempalace.exe" --palace "d:/Ai_Sandbox/agentsHQ/sandbox/.tmp/palace-agentshq" search "your query" --results 5
```

**Re-sweep after new sessions**:

```powershell
$env:PYTHONIOENCODING = "utf-8"
& "d:/Ai_Sandbox/agentsHQ/sandbox/.tmp/venv-mempalace/Scripts/mempalace.exe" --palace "d:/Ai_Sandbox/agentsHQ/sandbox/.tmp/palace-agentshq" sweep "C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ"
```

PreCompact hook auto-saves before context compression (wired 2026-05-04).
Stop hook: deliberately deferred  -  wire only after extended pilot.
