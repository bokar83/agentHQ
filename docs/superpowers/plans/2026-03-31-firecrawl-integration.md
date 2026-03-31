# Firecrawl Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Firecrawl web scraping/crawling to agentsHQ — both as a Claude Code MCP server and as three new CrewAI tools available to VPS agents.

**Architecture:** Three new tools (`FirecrawlScrapeTool`, `FirecrawlCrawlTool`, `FirecrawlSearchTool`) are added to `agent-brain/tools.py` using the `firecrawl-py` v4 SDK (`V1FirecrawlApp` class). `RESEARCH_TOOLS` gets `FirecrawlScrapeTool` automatically; a new `SCRAPING_TOOLS` bundle exposes all three for opt-in use. The MCP server is added to `~/.claude/mcp.json` for local Claude Code sessions.

**Tech Stack:** `firecrawl-py>=4.21.0`, `V1FirecrawlApp` from `firecrawl`, CrewAI `BaseTool`, Pydantic v2, Docker Compose environment injection.

**Virtual Test Results (pre-plan):** Confirmed against live SDK — correct class is `V1FirecrawlApp` (not `FirecrawlApp`); `scrape_url` returns a Pydantic model, access markdown via `response.markdown`; `crawl_url` returns `V1CrawlStatusResponse` with `.data: List[V1FirecrawlDocument]`, each with `.markdown`, `.url`, `.title`; `search` method also available — added as third tool for future-proofing.

---

## File Map

| File | Action | What changes |
|------|--------|-------------|
| `agent-brain/tools.py` | Modify | Add 3 new tool classes + update `RESEARCH_TOOLS` + add `SCRAPING_TOOLS` |
| `orchestrator/requirements.txt` | Modify | Add `firecrawl-py>=4.21.0` |
| `docker-compose.yml` | Modify | Add `FIRECRAWL_API_KEY` env var to orchestrator service |
| `infrasctructure/.env` | Modify | Add `FIRECRAWL_API_KEY` value |
| `~/.claude/mcp.json` | Modify | Add `firecrawl-mcp` server entry |
| `tests/test_firecrawl_tools.py` | Create | Unit tests for all three tools (mock + real API) |

---

## Task 1: Add `firecrawl-py` to requirements and `.env`

**Files:**
- Modify: `orchestrator/requirements.txt`
- Modify: `infrasctructure/.env`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add firecrawl-py to requirements.txt**

Open `orchestrator/requirements.txt`. Add after the `# ── MCP Support` block:

```
# ── Web Scraping ───────────────────────────────────────────────
firecrawl-py>=4.21.0
```

- [ ] **Step 2: Add FIRECRAWL_API_KEY to .env**

Open `infrasctructure/.env`. Add after the `SERPER_API_KEY` line:

```
# ── WEB SCRAPING ──────────────────────────────────────────────
# Firecrawl — gives agents the ability to read full web pages and crawl sites
FIRECRAWL_API_KEY=fc-YOUR_FIRECRAWL_API_KEY_HERE
```

- [ ] **Step 3: Add FIRECRAWL_API_KEY to docker-compose.yml**

Open `docker-compose.yml`. In the `orchestrator` service `environment` block, add after `- SERPER_API_KEY=${SERPER_API_KEY}`:

```yaml
      - FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}
```

- [ ] **Step 4: Verify env var loads correctly (local)**

```bash
cd d:/Ai_Sandbox/agentsHQ
.venv/Scripts/python -c "
from dotenv import load_dotenv
import os
load_dotenv('infrasctructure/.env')
key = os.environ.get('FIRECRAWL_API_KEY', 'MISSING')
print('Key loaded:', key[:10] + '...' if key != 'MISSING' else 'MISSING')
"
```

Expected output: `Key loaded: fc-479eab4...`

- [ ] **Step 5: Commit**

```bash
git add orchestrator/requirements.txt infrasctructure/.env docker-compose.yml
git commit -m "feat: add firecrawl-py dependency and env config"
```

---

## Task 2: Write failing tests for the three new tools

**Files:**
- Create: `tests/test_firecrawl_tools.py`

- [ ] **Step 1: Create the test file**

Create `tests/test_firecrawl_tools.py` with the full content below:

```python
"""
test_firecrawl_tools.py — Firecrawl Tool Tests
===============================================
Tests for FirecrawlScrapeTool, FirecrawlCrawlTool, FirecrawlSearchTool.

Run:
    pytest tests/test_firecrawl_tools.py -v                    # all tests (mocked)
    pytest tests/test_firecrawl_tools.py -v -m real_api        # hits real Firecrawl API

The real_api tests are skipped by default (require FIRECRAWL_API_KEY in env).
"""

import os
import sys
import json
import pytest
from unittest.mock import MagicMock, patch

# Ensure agent-brain is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent-brain'))


# ── Mocked response helpers ─────────────────────────────────────

def make_scrape_response(markdown="# Test Page\nContent here.", success=True, error=None):
    r = MagicMock()
    r.success = success
    r.markdown = markdown
    r.error = error
    return r


def make_crawl_doc(url="https://example.com/page", markdown="# Page\nBody.", title="Page"):
    d = MagicMock()
    d.url = url
    d.markdown = markdown
    d.title = title
    return d


def make_crawl_response(pages=None, success=True):
    r = MagicMock()
    r.success = success
    r.data = pages or [make_crawl_doc()]
    return r


def make_search_result(url="https://example.com", markdown="# Result\nContent.", title="Result"):
    d = MagicMock()
    d.url = url
    d.markdown = markdown
    d.title = title
    return d


def make_search_response(results=None, success=True, error=None):
    r = MagicMock()
    r.success = success
    r.data = results or [make_search_result()]
    r.error = error
    return r


# ── FirecrawlScrapeTool ─────────────────────────────────────────

class TestFirecrawlScrapeTool:

    @patch('tools.V1FirecrawlApp')
    def test_scrape_returns_markdown(self, MockApp):
        from tools import FirecrawlScrapeTool
        mock_client = MagicMock()
        mock_client.scrape_url.return_value = make_scrape_response("# Hello\nWorld")
        MockApp.return_value = mock_client

        tool = FirecrawlScrapeTool()
        result = tool._run(json.dumps({"url": "https://example.com"}))

        assert "# Hello" in result
        assert "World" in result
        mock_client.scrape_url.assert_called_once_with(
            "https://example.com", formats=["markdown"]
        )

    @patch('tools.V1FirecrawlApp')
    def test_scrape_missing_url_returns_error(self, MockApp):
        from tools import FirecrawlScrapeTool
        tool = FirecrawlScrapeTool()
        result = tool._run(json.dumps({}))
        assert "Error" in result or "url" in result.lower()

    @patch('tools.V1FirecrawlApp')
    def test_scrape_api_exception_returns_error_string(self, MockApp):
        from tools import FirecrawlScrapeTool
        mock_client = MagicMock()
        mock_client.scrape_url.side_effect = Exception("Connection refused")
        MockApp.return_value = mock_client

        tool = FirecrawlScrapeTool()
        result = tool._run(json.dumps({"url": "https://example.com"}))
        assert "Error" in result
        # Must not raise — crew should keep running
        assert isinstance(result, str)

    @patch('tools.V1FirecrawlApp')
    def test_scrape_no_markdown_in_response(self, MockApp):
        from tools import FirecrawlScrapeTool
        mock_client = MagicMock()
        mock_client.scrape_url.return_value = make_scrape_response(markdown=None)
        MockApp.return_value = mock_client

        tool = FirecrawlScrapeTool()
        result = tool._run(json.dumps({"url": "https://example.com"}))
        # Should return something usable, not crash
        assert isinstance(result, str)


# ── FirecrawlCrawlTool ──────────────────────────────────────────

class TestFirecrawlCrawlTool:

    @patch('tools.V1FirecrawlApp')
    def test_crawl_returns_combined_markdown(self, MockApp):
        from tools import FirecrawlCrawlTool
        mock_client = MagicMock()
        pages = [
            make_crawl_doc("https://example.com/", "# Home\nHome content."),
            make_crawl_doc("https://example.com/about", "# About\nAbout content."),
        ]
        mock_client.crawl_url.return_value = make_crawl_response(pages=pages)
        MockApp.return_value = mock_client

        tool = FirecrawlCrawlTool()
        result = tool._run(json.dumps({"url": "https://example.com"}))

        assert "# Home" in result
        assert "# About" in result
        mock_client.crawl_url.assert_called_once_with(
            "https://example.com", limit=10, max_depth=2
        )

    @patch('tools.V1FirecrawlApp')
    def test_crawl_respects_limit_and_depth_params(self, MockApp):
        from tools import FirecrawlCrawlTool
        mock_client = MagicMock()
        mock_client.crawl_url.return_value = make_crawl_response()
        MockApp.return_value = mock_client

        tool = FirecrawlCrawlTool()
        tool._run(json.dumps({"url": "https://example.com", "limit": 5, "max_depth": 3}))

        mock_client.crawl_url.assert_called_once_with(
            "https://example.com", limit=5, max_depth=3
        )

    @patch('tools.V1FirecrawlApp')
    def test_crawl_missing_url_returns_error(self, MockApp):
        from tools import FirecrawlCrawlTool
        tool = FirecrawlCrawlTool()
        result = tool._run(json.dumps({}))
        assert "Error" in result or "url" in result.lower()

    @patch('tools.V1FirecrawlApp')
    def test_crawl_api_exception_returns_error_string(self, MockApp):
        from tools import FirecrawlCrawlTool
        mock_client = MagicMock()
        mock_client.crawl_url.side_effect = Exception("Timeout")
        MockApp.return_value = mock_client

        tool = FirecrawlCrawlTool()
        result = tool._run(json.dumps({"url": "https://example.com"}))
        assert "Error" in result
        assert isinstance(result, str)


# ── FirecrawlSearchTool ─────────────────────────────────────────

class TestFirecrawlSearchTool:

    @patch('tools.V1FirecrawlApp')
    def test_search_returns_results_with_content(self, MockApp):
        from tools import FirecrawlSearchTool
        mock_client = MagicMock()
        results = [
            make_search_result("https://a.com", "# A\nContent A", "A"),
            make_search_result("https://b.com", "# B\nContent B", "B"),
        ]
        mock_client.search.return_value = make_search_response(results=results)
        MockApp.return_value = mock_client

        tool = FirecrawlSearchTool()
        result = tool._run(json.dumps({"query": "HVAC software pricing"}))

        assert "https://a.com" in result
        assert "Content A" in result
        mock_client.search.assert_called_once_with("HVAC software pricing", limit=5)

    @patch('tools.V1FirecrawlApp')
    def test_search_missing_query_returns_error(self, MockApp):
        from tools import FirecrawlSearchTool
        tool = FirecrawlSearchTool()
        result = tool._run(json.dumps({}))
        assert "Error" in result or "query" in result.lower()

    @patch('tools.V1FirecrawlApp')
    def test_search_api_exception_returns_error_string(self, MockApp):
        from tools import FirecrawlSearchTool
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("API error")
        MockApp.return_value = mock_client

        tool = FirecrawlSearchTool()
        result = tool._run(json.dumps({"query": "test query"}))
        assert "Error" in result
        assert isinstance(result, str)

    @patch('tools.V1FirecrawlApp')
    def test_search_respects_limit_param(self, MockApp):
        from tools import FirecrawlSearchTool
        mock_client = MagicMock()
        mock_client.search.return_value = make_search_response()
        MockApp.return_value = mock_client

        tool = FirecrawlSearchTool()
        tool._run(json.dumps({"query": "test", "limit": 10}))
        mock_client.search.assert_called_once_with("test", limit=10)


# ── Tool bundle membership ──────────────────────────────────────

class TestToolBundles:

    def test_firecrawl_scrape_in_research_tools(self):
        from tools import RESEARCH_TOOLS, FirecrawlScrapeTool
        tool_types = [type(t) for t in RESEARCH_TOOLS]
        assert FirecrawlScrapeTool in tool_types

    def test_scraping_tools_bundle_has_all_three(self):
        from tools import SCRAPING_TOOLS, FirecrawlScrapeTool, FirecrawlCrawlTool, FirecrawlSearchTool
        tool_types = [type(t) for t in SCRAPING_TOOLS]
        assert FirecrawlScrapeTool in tool_types
        assert FirecrawlCrawlTool in tool_types
        assert FirecrawlSearchTool in tool_types

    def test_writing_tools_unchanged(self):
        from tools import WRITING_TOOLS, FirecrawlScrapeTool
        tool_types = [type(t) for t in WRITING_TOOLS]
        assert FirecrawlScrapeTool not in tool_types

    def test_code_tools_unchanged(self):
        from tools import CODE_TOOLS, FirecrawlScrapeTool
        tool_types = [type(t) for t in CODE_TOOLS]
        assert FirecrawlScrapeTool not in tool_types


# ── Real API tests (skipped by default) ────────────────────────

@pytest.mark.real_api
class TestFirecrawlRealAPI:
    """
    These tests hit the real Firecrawl API. Only run when FIRECRAWL_API_KEY is set.
    Run with: pytest tests/test_firecrawl_tools.py -v -m real_api
    """

    @pytest.fixture(autouse=True)
    def require_api_key(self):
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'infrasctructure', '.env'))
        if not os.environ.get('FIRECRAWL_API_KEY'):
            pytest.skip("FIRECRAWL_API_KEY not set")

    def test_real_scrape(self):
        from tools import FirecrawlScrapeTool
        tool = FirecrawlScrapeTool()
        result = tool._run(json.dumps({"url": "https://example.com"}))
        assert "Example Domain" in result or len(result) > 50

    def test_real_search(self):
        from tools import FirecrawlSearchTool
        tool = FirecrawlSearchTool()
        result = tool._run(json.dumps({"query": "firecrawl web scraping", "limit": 2}))
        assert "http" in result
        assert len(result) > 100
```

- [ ] **Step 2: Run the tests — expect ImportError (tools don't exist yet)**

```bash
cd d:/Ai_Sandbox/agentsHQ
.venv/Scripts/pytest tests/test_firecrawl_tools.py -v 2>&1 | head -30
```

Expected: `ImportError: cannot import name 'FirecrawlScrapeTool' from 'tools'`

This confirms the tests are wired to the right module and will fail for the right reason.

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/test_firecrawl_tools.py
git commit -m "test: add failing tests for FirecrawlScrapeTool, CrawlTool, SearchTool"
```

---

## Task 3: Implement the three Firecrawl tools in tools.py

**Files:**
- Modify: `agent-brain/tools.py`

The implementation goes in two places: (1) a new `# FIRECRAWL TOOLS` section after the existing `CUSTOM TOOLS` section, and (2) updated bundle definitions at the bottom.

- [ ] **Step 1: Add the import at the top of tools.py**

In `agent-brain/tools.py`, add to the imports block (after the existing `import httpx` line):

```python
from firecrawl import V1FirecrawlApp
```

- [ ] **Step 2: Add the three tool classes**

After the `ProposeNewAgentTool` class (around line 228) and before the `# MCP SERVER ADAPTERS` section, add:

```python
# ══════════════════════════════════════════════════════════════
# FIRECRAWL TOOLS
# Web scraping and crawling via Firecrawl API (v4, V1FirecrawlApp)
# Docs: https://github.com/firecrawl/firecrawl
# Key: FIRECRAWL_API_KEY environment variable
# ══════════════════════════════════════════════════════════════

class FirecrawlScrapeTool(BaseTool):
    """
    Scrapes a single URL and returns clean markdown content.
    Use after Serper finds a relevant URL to read the full page.
    Input: JSON with 'url' (required) and optional 'formats' list.
    """
    name: str = "firecrawl_scrape"
    description: str = (
        "Scrape a single web page and return its full content as clean markdown. "
        "Use this after finding a relevant URL via search to read the actual page content. "
        "Input: JSON with 'url' (required) and optional 'formats' list "
        "(default: ['markdown']). Supports 'markdown', 'html', 'links'."
    )

    def _run(self, input_data: str) -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            url = data.get("url")
            if not url:
                return "Error: 'url' is required."
            formats = data.get("formats", ["markdown"])

            client = V1FirecrawlApp(api_key=os.environ.get("FIRECRAWL_API_KEY"))
            response = client.scrape_url(url, formats=formats)

            if not response.success:
                return f"Error scraping {url}: {response.error or 'unknown error'}"

            content = response.markdown or ""
            if not content:
                return f"No markdown content returned for {url}. Try formats=['html']."

            return content

        except Exception as e:
            logger.warning(f"FirecrawlScrapeTool failed (non-fatal): {e}")
            return f"Error scraping URL: {str(e)}"


class FirecrawlCrawlTool(BaseTool):
    """
    Crawls an entire website up to a configurable depth and page limit.
    Returns combined markdown from all crawled pages.
    Use for deep research — ingesting a competitor site, docs, or knowledge base.
    Input: JSON with 'url' (required), optional 'limit' (default 10), 'max_depth' (default 2).
    """
    name: str = "firecrawl_crawl"
    description: str = (
        "Crawl an entire website and return content from multiple pages as combined markdown. "
        "Use for deep research tasks: competitor analysis, reading full documentation, "
        "or ingesting a knowledge base. "
        "Input: JSON with 'url' (required), optional 'limit' (max pages, default 10), "
        "'max_depth' (link depth, default 2). Higher limits use more API credits."
    )

    def _run(self, input_data: str) -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            url = data.get("url")
            if not url:
                return "Error: 'url' is required."
            limit = data.get("limit", 10)
            max_depth = data.get("max_depth", 2)

            client = V1FirecrawlApp(api_key=os.environ.get("FIRECRAWL_API_KEY"))
            response = client.crawl_url(url, limit=limit, max_depth=max_depth)

            if not response.success or not response.data:
                return f"Error crawling {url}: no pages returned."

            sections = []
            for doc in response.data:
                if doc.markdown:
                    header = f"\n\n---\n## {doc.title or doc.url}\nSource: {doc.url}\n\n"
                    sections.append(header + doc.markdown)

            if not sections:
                return f"Crawled {url} but no markdown content was extracted."

            return f"Crawled {len(sections)} pages from {url}:" + "".join(sections)

        except Exception as e:
            logger.warning(f"FirecrawlCrawlTool failed (non-fatal): {e}")
            return f"Error crawling site: {str(e)}"


class FirecrawlSearchTool(BaseTool):
    """
    Searches the web AND returns full page content for each result.
    More powerful than Serper alone — combines search + scrape in one call.
    Use when you need both discovery AND content (not just snippets).
    Input: JSON with 'query' (required) and optional 'limit' (default 5).
    """
    name: str = "firecrawl_search"
    description: str = (
        "Search the web and return full page content (not just snippets) for each result. "
        "More powerful than standard web search — use when you need to read and analyze "
        "the actual content of search results, not just their titles and descriptions. "
        "Input: JSON with 'query' (required) and optional 'limit' (results count, default 5)."
    )

    def _run(self, input_data: str) -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            query = data.get("query")
            if not query:
                return "Error: 'query' is required."
            limit = data.get("limit", 5)

            client = V1FirecrawlApp(api_key=os.environ.get("FIRECRAWL_API_KEY"))
            response = client.search(query, limit=limit)

            if not response.success or not response.data:
                return f"Error searching for '{query}': {response.error or 'no results returned'}"

            sections = []
            for doc in response.data:
                if doc.markdown:
                    header = f"\n\n---\n## {doc.title or doc.url}\nSource: {doc.url}\n\n"
                    sections.append(header + doc.markdown)
                elif doc.url:
                    sections.append(f"\n\n---\nSource: {doc.url} (no content extracted)")

            if not sections:
                return f"Search returned no content for '{query}'."

            return f"Search results for '{query}' ({len(sections)} results):" + "".join(sections)

        except Exception as e:
            logger.warning(f"FirecrawlSearchTool failed (non-fatal): {e}")
            return f"Error searching: {str(e)}"
```

- [ ] **Step 3: Update the tool bundles at the bottom of tools.py**

Find the `# ── Tool sets by category ─────────────────────────────────────` section and replace it with:

```python
# ── Tool sets by category ─────────────────────────────────────
# These are convenience bundles used in agents.py

RESEARCH_TOOLS = [search_tool, file_reader, QueryMemoryTool(), FirecrawlScrapeTool()]
WRITING_TOOLS = [file_writer, SaveOutputTool()]
CODE_TOOLS = [code_interpreter, file_writer, file_reader, SaveOutputTool()]
ORCHESTRATION_TOOLS = [EscalateTool(), ProposeNewAgentTool(), QueryMemoryTool()]
SCRAPING_TOOLS = [FirecrawlScrapeTool(), FirecrawlCrawlTool(), FirecrawlSearchTool()]
ALL_TOOLS = RESEARCH_TOOLS + WRITING_TOOLS + CODE_TOOLS + ORCHESTRATION_TOOLS + SCRAPING_TOOLS
```

- [ ] **Step 4: Verify the module imports cleanly**

```bash
cd d:/Ai_Sandbox/agentsHQ
.venv/Scripts/pip install firecrawl-py -q
.venv/Scripts/python -c "
import sys
sys.path.insert(0, 'agent-brain')
from dotenv import load_dotenv
load_dotenv('infrasctructure/.env')
from tools import FirecrawlScrapeTool, FirecrawlCrawlTool, FirecrawlSearchTool, RESEARCH_TOOLS, SCRAPING_TOOLS
print('Import OK')
print('RESEARCH_TOOLS count:', len(RESEARCH_TOOLS))
print('SCRAPING_TOOLS count:', len(SCRAPING_TOOLS))
tool_names = [t.name for t in SCRAPING_TOOLS]
print('SCRAPING_TOOLS names:', tool_names)
"
```

Expected:
```
Import OK
RESEARCH_TOOLS count: 4
SCRAPING_TOOLS count: 3
SCRAPING_TOOLS names: ['firecrawl_scrape', 'firecrawl_crawl', 'firecrawl_search']
```

- [ ] **Step 5: Commit**

```bash
git add agent-brain/tools.py
git commit -m "feat: add FirecrawlScrapeTool, FirecrawlCrawlTool, FirecrawlSearchTool to tools.py"
```

---

## Task 4: Run the tests — expect them to pass

**Files:**
- Test: `tests/test_firecrawl_tools.py`

- [ ] **Step 1: Run all mocked tests**

```bash
cd d:/Ai_Sandbox/agentsHQ
.venv/Scripts/pytest tests/test_firecrawl_tools.py -v -k "not real_api"
```

Expected output:
```
PASSED tests/test_firecrawl_tools.py::TestFirecrawlScrapeTool::test_scrape_returns_markdown
PASSED tests/test_firecrawl_tools.py::TestFirecrawlScrapeTool::test_scrape_missing_url_returns_error
PASSED tests/test_firecrawl_tools.py::TestFirecrawlScrapeTool::test_scrape_api_exception_returns_error_string
PASSED tests/test_firecrawl_tools.py::TestFirecrawlScrapeTool::test_scrape_no_markdown_in_response
PASSED tests/test_firecrawl_tools.py::TestFirecrawlCrawlTool::test_crawl_returns_combined_markdown
PASSED tests/test_firecrawl_tools.py::TestFirecrawlCrawlTool::test_crawl_respects_limit_and_depth_params
PASSED tests/test_firecrawl_tools.py::TestFirecrawlCrawlTool::test_crawl_missing_url_returns_error
PASSED tests/test_firecrawl_tools.py::TestFirecrawlCrawlTool::test_crawl_api_exception_returns_error_string
PASSED tests/test_firecrawl_tools.py::TestFirecrawlSearchTool::test_search_returns_results_with_content
PASSED tests/test_firecrawl_tools.py::TestFirecrawlSearchTool::test_search_missing_query_returns_error
PASSED tests/test_firecrawl_tools.py::TestFirecrawlSearchTool::test_search_api_exception_returns_error_string
PASSED tests/test_firecrawl_tools.py::TestFirecrawlSearchTool::test_search_respects_limit_param
PASSED tests/test_firecrawl_tools.py::TestToolBundles::test_firecrawl_scrape_in_research_tools
PASSED tests/test_firecrawl_tools.py::TestToolBundles::test_scraping_tools_bundle_has_all_three
PASSED tests/test_firecrawl_tools.py::TestToolBundles::test_writing_tools_unchanged
PASSED tests/test_firecrawl_tools.py::TestToolBundles::test_code_tools_unchanged
16 passed
```

If any test fails, fix the implementation (not the tests) until all pass.

- [ ] **Step 2: Run real API smoke test**

```bash
cd d:/Ai_Sandbox/agentsHQ
.venv/Scripts/pytest tests/test_firecrawl_tools.py -v -m real_api
```

Expected: 2 tests pass, confirming live API connectivity with your key.

- [ ] **Step 3: Commit**

```bash
git add tests/test_firecrawl_tools.py
git commit -m "test: all firecrawl tool tests passing (mocked + real API)"
```

---

## Task 5: Add firecrawl-mcp to Claude Code MCP config

**Files:**
- Modify: `C:\Users\HUAWEI\.claude\mcp.json`

- [ ] **Step 1: Add firecrawl-mcp entry to mcp.json**

Open `C:\Users\HUAWEI\.claude\mcp.json`. Add `firecrawl-mcp` to the `mcpServers` object:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_REDACTED"
      }
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp"]
    },
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

- [ ] **Step 2: Verify npx can resolve the package**

```bash
npx -y firecrawl-mcp --help 2>&1 | head -10
```

Expected: Help text or version output (not "not found").

- [ ] **Step 3: Restart Claude Code**

Close and reopen Claude Code. The `firecrawl-mcp` server will appear in the MCP tools list at session start.

- [ ] **Step 4: Commit the MCP config note**

The `mcp.json` file is outside the git repo — note the change in the session handoff doc instead:

```bash
cd d:/Ai_Sandbox/agentsHQ
cat >> docs/session-handoff.md << 'EOF'

## 2026-03-31 — Firecrawl MCP Added
- `~/.claude/mcp.json` updated to include `firecrawl-mcp` server
- API key: fc-479eab4... (stored in mcp.json env block)
- Restart Claude Code to activate
EOF
git add docs/session-handoff.md
git commit -m "docs: note firecrawl-mcp added to Claude Code MCP config"
```

---

## Task 6: Final verification and push

- [ ] **Step 1: Run full test suite to confirm nothing broken**

```bash
cd d:/Ai_Sandbox/agentsHQ
.venv/Scripts/pytest tests/ -v -k "not real_api" 2>&1 | tail -20
```

Expected: All tests pass. (Note: `test_growth_engine.py` may fail if Postgres/Serper not running locally — that's pre-existing, not a regression.)

- [ ] **Step 2: Check that the docker-compose env var is wired**

```bash
cd d:/Ai_Sandbox/agentsHQ
grep FIRECRAWL docker-compose.yml
grep FIRECRAWL infrasctructure/.env
grep firecrawl orchestrator/requirements.txt
```

Expected:
```
      - FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}
FIRECRAWL_API_KEY=fc-YOUR_FIRECRAWL_API_KEY_HERE
firecrawl-py>=4.21.0
```

- [ ] **Step 3: Push to GitHub**

```bash
cd d:/Ai_Sandbox/agentsHQ
git push origin main
```

- [ ] **Step 4: Deploy to VPS**

```bash
ssh root@72.60.209.109 "cd /root/agentsHQ && git pull origin main && docker compose build orchestrator && docker compose up -d orchestrator"
```

Expected: Build completes, orchestrator restarts with Firecrawl available to agents.

- [ ] **Step 5: Smoke test via Telegram**

Send this message to `@agentsHQ4Bou_bot`:

> Research the homepage of firecrawl.dev and summarize what Firecrawl does in 3 bullet points.

Expected: Agent uses `firecrawl_scrape` tool, returns a markdown summary with 3 bullets — not just a Serper snippet.

---

## Self-Review Against Spec

| Spec requirement | Task that covers it |
|-----------------|-------------------|
| `firecrawl-py` added to requirements | Task 1 |
| `FIRECRAWL_API_KEY` in `.env` | Task 1 |
| `FIRECRAWL_API_KEY` in `docker-compose.yml` | Task 1 |
| `FirecrawlScrapeTool` — scrape single URL | Task 3 |
| `FirecrawlCrawlTool` — crawl entire site | Task 3 |
| `FirecrawlSearchTool` — search + content (future-proof addition) | Task 3 |
| `RESEARCH_TOOLS` updated with `FirecrawlScrapeTool` | Task 3 |
| `SCRAPING_TOOLS` bundle created | Task 3 |
| `WRITING_TOOLS`/`CODE_TOOLS` unchanged | Task 3 (verified in tests) |
| Graceful error handling (no crew crashes) | Task 3 + Task 4 tests |
| MCP server added to Claude Code | Task 5 |
| VPS deployment | Task 6 |
