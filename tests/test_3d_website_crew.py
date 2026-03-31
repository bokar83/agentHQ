"""
test_3d_website_crew.py — Tests for 3D website crew and related changes.

Run:
    cd D:/Ai_Sandbox/agentsHQ
    pytest tests/test_3d_website_crew.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent-brain'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'orchestrator'))

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


# ── Task 2: Upgraded website crew ─────────────────────────────

class TestUpgradedWebsiteCrew:

    def test_researcher_agent_has_scraping_tools(self):
        """Researcher agent must include all 3 Firecrawl tools."""
        from agents import build_researcher_agent
        from tools import FirecrawlScrapeTool, FirecrawlCrawlTool, FirecrawlSearchTool
        agent = build_researcher_agent()
        tool_types = [type(t) for t in agent.tools]
        assert FirecrawlScrapeTool in tool_types
        assert FirecrawlCrawlTool in tool_types
        assert FirecrawlSearchTool in tool_types

    def test_website_crew_has_seo_task(self):
        """Website crew must have a task with 'seo' or 'audit' in description."""
        from crews import build_website_crew
        crew = build_website_crew("build a website for a bakery in Austin")
        seo_tasks = [
            t for t in crew.tasks
            if "seo" in t.description.lower() or "audit" in t.description.lower()
        ]
        assert len(seo_tasks) >= 1

    def test_website_crew_task_count(self):
        """Website crew must have exactly 6 tasks (was 5, now +1 SEO audit)."""
        from crews import build_website_crew
        crew = build_website_crew("build a website for a dentist")
        assert len(crew.tasks) == 6
