# Firecrawl Integration Design
**Date:** 2026-03-31  
**Status:** Approved

---

## Overview

Integrate Firecrawl into agentsHQ across two tracks:

1. **Claude Code MCP** — Firecrawl tools available in local Claude Code sessions via `firecrawl-mcp` npx server
2. **VPS Orchestrator** — Two new CrewAI tools in `tools.py` using the `firecrawl-py` Python SDK, giving VPS agents the ability to scrape and crawl the web during task execution

---

## Track 1: Claude Code MCP Server

### What it does
Adds Firecrawl as an MCP server to Claude Code so it's available during planning, research, and agent-building sessions locally.

### Config
Merge the following into Claude Code MCP settings:

```json
{
  "mcpServers": {
    "firecrawl-mcp": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {
        "FIRECRAWL_API_KEY": "fc-YOUR_FIRECRAWL_API_KEY_HERE"
      }
    }
  }
}
```

### Target file
`C:\Users\HUAWEI\.claude\mcp.json` — this is the active MCP config (confirmed: currently contains github, context7, playwright servers). Add `firecrawl-mcp` as a new entry.

---

## Track 2: VPS Orchestrator — CrewAI Tools

### New tools in `agent-brain/tools.py`

#### `FirecrawlScrapeTool`
- **Purpose:** Scrape a single URL and return clean markdown content
- **Input:** JSON with `url` (required) and optional `formats` list (default: `["markdown"]`)
- **Output:** Markdown string of the page content, or error message on failure
- **Use case:** Research agents call this after Serper finds relevant URLs — turn search results into readable content
- **API call:** `firecrawl.scrape_url(url, params={"formats": formats})`

#### `FirecrawlCrawlTool`
- **Purpose:** Crawl an entire website up to a configurable depth and page limit
- **Input:** JSON with `url` (required), `limit` (default: 10 pages), `max_depth` (default: 2)
- **Output:** Combined markdown from all crawled pages, or error message on failure
- **Use case:** Deep research — ingest a competitor site, documentation, or knowledge base in full
- **API call:** `firecrawl.crawl_url(url, params={"limit": limit, "maxDepth": max_depth})`

### Error handling
Both tools:
- Fail gracefully — return a descriptive error string, never raise exceptions that crash the crew
- Log errors at WARNING level (non-fatal, consistent with `QueryMemoryTool` pattern)
- Return an actionable message so the agent can decide to skip or escalate

### Tool bundle changes

```python
# BEFORE
RESEARCH_TOOLS = [search_tool, file_reader, QueryMemoryTool()]

# AFTER
RESEARCH_TOOLS = [search_tool, file_reader, QueryMemoryTool(), FirecrawlScrapeTool()]
SCRAPING_TOOLS = [FirecrawlScrapeTool(), FirecrawlCrawlTool()]  # new opt-in bundle
```

`WRITING_TOOLS`, `CODE_TOOLS`, `ORCHESTRATION_TOOLS` — unchanged.

---

## Environment & Deployment

### `.env` addition
```
# ── WEB SCRAPING ──────────────────────────────────────────────
# Firecrawl — gives agents the ability to read full web pages and crawl sites
# Get from: firecrawl.dev > Dashboard > API Keys
FIRECRAWL_API_KEY=fc-YOUR_FIRECRAWL_API_KEY_HERE
```

File: `infrasctructure/.env`

### `docker-compose.yml` addition
Add to the `orchestrator` service `environment` block:
```yaml
- FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}
```

### `requirements.txt` addition
```
# ── Web Scraping ───────────────────────────────────────────────
firecrawl-py>=1.0.0
```

File: `orchestrator/requirements.txt`

---

## Files Changed

| File | Change |
|------|--------|
| `agent-brain/tools.py` | Add `FirecrawlScrapeTool`, `FirecrawlCrawlTool`; update `RESEARCH_TOOLS`; add `SCRAPING_TOOLS` |
| `orchestrator/requirements.txt` | Add `firecrawl-py>=1.0.0` |
| `docker-compose.yml` | Add `FIRECRAWL_API_KEY` env var to orchestrator service |
| `infrasctructure/.env` | Add `FIRECRAWL_API_KEY` value |
| Claude Code MCP config | Add `firecrawl-mcp` server entry |

---

## Out of Scope

- Assigning `SCRAPING_TOOLS` to specific agents — this is left for the next agent build that needs crawl capability (e.g., Competitor Research agent)
- Firecrawl's `/extract` structured data endpoint — add when a specific agent needs structured extraction
- Rate limiting / quota management — Firecrawl's API handles this; agents fail gracefully on 429s
