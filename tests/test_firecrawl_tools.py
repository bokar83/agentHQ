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
        # This test targets agent-brain's tools module (inserted at sys.path[0] above).
        # In agent-brain, FirecrawlScrapeTool is part of RESEARCH_TOOLS.
        # In orchestrator, it lives in SCRAPING_TOOLS instead — see
        # test_orchestrator_research_tools_does_not_include_scrape below.
        from tools import RESEARCH_TOOLS, FirecrawlScrapeTool
        tool_types = [type(t) for t in RESEARCH_TOOLS]
        assert FirecrawlScrapeTool in tool_types

    def test_orchestrator_research_tools_does_not_include_scrape(self):
        """In orchestrator, FirecrawlScrapeTool is in SCRAPING_TOOLS, not RESEARCH_TOOLS."""
        import importlib
        import sys
        # Force orchestrator module
        orch_path = os.path.join(os.path.dirname(__file__), '..', 'orchestrator')
        saved = sys.path[:]
        sys.path.insert(0, orch_path)
        if 'tools' in sys.modules:
            del sys.modules['tools']
        try:
            from tools import RESEARCH_TOOLS, SCRAPING_TOOLS, FirecrawlScrapeTool
            research_types = [type(t) for t in RESEARCH_TOOLS]
            scraping_types = [type(t) for t in SCRAPING_TOOLS]
            assert FirecrawlScrapeTool not in research_types, "orchestrator RESEARCH_TOOLS should not include FirecrawlScrapeTool"
            assert FirecrawlScrapeTool in scraping_types, "orchestrator SCRAPING_TOOLS must include FirecrawlScrapeTool"
        finally:
            sys.path = saved
            if 'tools' in sys.modules:
                del sys.modules['tools']

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
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'infrastructure', '.env'))
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
