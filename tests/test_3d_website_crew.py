"""
test_3d_website_crew.py — Tests for 3D website crew and related changes.

Run:
    cd D:/Ai_Sandbox/agentsHQ
    pytest tests/test_3d_website_crew.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'orchestrator'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent-brain'))

# ── Task 1: SCRAPING_TOOLS export ──────────────────────────────

class TestScrapingToolsBundle:

    def test_scraping_tools_exported_from_tools(self):
        """SCRAPING_TOOLS must be importable from tools module."""
        from tools import SCRAPING_TOOLS
        assert isinstance(SCRAPING_TOOLS, list)
        assert len(SCRAPING_TOOLS) == 3

    def test_scraping_tools_has_all_three_firecrawl_tools(self):
        """SCRAPING_TOOLS contains scrape, crawl, and search tools."""
        from tools import SCRAPING_TOOLS, FirecrawlScrapeTool, FirecrawlCrawlTool, FirecrawlSearchTool
        tool_types = [type(t) for t in SCRAPING_TOOLS]
        assert FirecrawlScrapeTool in tool_types
        assert FirecrawlCrawlTool in tool_types
        assert FirecrawlSearchTool in tool_types
