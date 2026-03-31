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


# ── Task 3: New specialist agents ─────────────────────────────

class TestNew3DAgents:

    def test_website_intelligence_agent_exists(self):
        from agents import build_website_intelligence_agent
        agent = build_website_intelligence_agent()
        assert agent.role is not None

    def test_website_intelligence_agent_has_scraping_tools(self):
        from agents import build_website_intelligence_agent
        from tools import FirecrawlScrapeTool, FirecrawlCrawlTool, FirecrawlSearchTool
        agent = build_website_intelligence_agent()
        tool_types = [type(t) for t in agent.tools]
        assert FirecrawlScrapeTool in tool_types
        assert FirecrawlCrawlTool in tool_types
        assert FirecrawlSearchTool in tool_types

    def test_asset_prompter_agent_exists(self):
        from agents import build_asset_prompter_agent
        agent = build_asset_prompter_agent()
        assert agent.role is not None

    def test_3d_web_builder_agent_exists(self):
        from agents import build_3d_web_builder_agent
        agent = build_3d_web_builder_agent()
        assert agent.role is not None

    def test_seo_auditor_agent_exists(self):
        from agents import build_seo_auditor_agent
        agent = build_seo_auditor_agent()
        assert agent.role is not None


# ── Task 4: 3D website crew structure ─────────────────────────

class Test3DWebsiteCrew:

    def test_3d_crew_exists(self):
        from crews import build_3d_website_crew
        crew = build_3d_website_crew("build a 3D website for a luxury watch brand")
        assert crew is not None

    def test_3d_crew_has_7_tasks(self):
        from crews import build_3d_website_crew
        crew = build_3d_website_crew("build a 3D website for a coffee brand")
        assert len(crew.tasks) == 7

    def test_3d_crew_is_sequential(self):
        from crews import build_3d_website_crew
        from crewai import Process
        crew = build_3d_website_crew("build a 3D website for a sneaker brand")
        assert crew.process == Process.sequential

    def test_3d_crew_has_intelligence_agent(self):
        from crews import build_3d_website_crew
        crew = build_3d_website_crew("build a 3D website for a tech product")
        agent_roles = [a.role for a in crew.agents]
        assert "Website Intelligence Researcher" in agent_roles

    def test_3d_crew_has_asset_prompter(self):
        from crews import build_3d_website_crew
        crew = build_3d_website_crew("build a 3D website for a skincare brand")
        agent_roles = [a.role for a in crew.agents]
        assert "3D Asset Prompt Engineer" in agent_roles


# ── Task 5: Router registration ────────────────────────────────

class TestRouter3DWebsite:

    def test_3d_website_build_in_task_types(self):
        from router import TASK_TYPES
        assert "3d_website_build" in TASK_TYPES

    def test_3d_website_build_has_correct_crew(self):
        from router import TASK_TYPES
        assert TASK_TYPES["3d_website_build"]["crew"] == "3d_website_crew"

    def test_3d_website_build_has_keywords(self):
        from router import TASK_TYPES
        keywords = TASK_TYPES["3d_website_build"]["keywords"]
        assert len(keywords) >= 3
        combined = " ".join(keywords)
        assert any(w in combined for w in ["3d", "animated", "scroll", "animation"])
