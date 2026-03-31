"""
firecrawl_tools.py — Shared Firecrawl Tool Definitions
=======================================================
Defines FirecrawlScrapeTool, FirecrawlCrawlTool, FirecrawlSearchTool.
Imported by orchestrator/tools.py to avoid inline duplication.

The agent-brain/tools.py retains its own copies for now; this module
is the authoritative definition for the orchestrator side.
"""

import os
import json
import logging
from crewai.tools import BaseTool

try:
    from firecrawl import V1FirecrawlApp
except ImportError:
    V1FirecrawlApp = None

logger = logging.getLogger(__name__)


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

            api_key = os.environ.get("FIRECRAWL_API_KEY")
            client = V1FirecrawlApp(api_key=api_key)
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

            api_key = os.environ.get("FIRECRAWL_API_KEY")
            client = V1FirecrawlApp(api_key=api_key)
            response = client.crawl_url(url, limit=limit, max_depth=max_depth)

            if not response.success or not response.data:
                return f"Error crawling {url}: {getattr(response, 'error', None) or 'no pages returned'}"

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

            api_key = os.environ.get("FIRECRAWL_API_KEY")
            client = V1FirecrawlApp(api_key=api_key)
            response = client.search(query, limit=limit)

            if not response.success or not response.data:
                return f"Error searching for '{query}': {response.error or 'no results returned'}"

            sections = []
            for doc in response.data:
                # Real API returns dicts; mocked tests return attribute-style objects
                if isinstance(doc, dict):
                    url = doc.get("url", "")
                    markdown = doc.get("markdown", "") or ""
                    title = doc.get("title", "") or url
                else:
                    url = doc.url
                    markdown = doc.markdown or ""
                    title = doc.title or url
                if markdown:
                    header = f"\n\n---\n## {title}\nSource: {url}\n\n"
                    sections.append(header + markdown)
                elif url:
                    sections.append(f"\n\n---\nSource: {url} (no content extracted)")

            if not sections:
                return f"Search returned no content for '{query}'."

            return f"Search results for '{query}' ({len(sections)} results):" + "".join(sections)

        except Exception as e:
            logger.warning(f"FirecrawlSearchTool failed (non-fatal): {e}")
            return f"Error searching: {str(e)}"


__all__ = ['FirecrawlScrapeTool', 'FirecrawlCrawlTool', 'FirecrawlSearchTool']
