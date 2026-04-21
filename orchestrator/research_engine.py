"""
research_engine.py: CrewAI bypass for research-type prompts.
============================================================
Runs a single Anthropic tool-use loop with Firecrawl search/scrape tools.
No CrewAI, no max_iter, no force-final-answer prefill. The loop terminates
when Claude emits stop_reason == "end_turn" or hits the hard cap below.

Rationale: CrewAI's max_iter fallback sends a conversation that ends on
an assistant turn ("assistant message prefill"). Anthropic's API rejects
that shape with 400. Three prior commits (3c5dfa6, 06b55d5, and the
researcher/planner crew) have patched individual agents. This module
replaces the research path entirely so the bug class cannot recur here.
"""

import os
import logging
from typing import Optional

import anthropic

logger = logging.getLogger("agentsHQ.research_engine")

MODEL = "claude-sonnet-4-5-20250929"
MAX_TURNS = 20


def _tool_definitions() -> list:
    """Anthropic tool-use schema for Firecrawl-backed web access."""
    return [
        {
            "name": "web_search",
            "description": (
                "Search the web and return the top results with full page content "
                "as clean markdown. Use this to find local businesses, compare "
                "options, pull current facts, or gather primary sources."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to fetch. Default 5, max 10.",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "web_scrape",
            "description": (
                "Scrape a specific URL and return the page content as clean markdown. "
                "Use after web_search when you need the full content of one page."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Absolute URL to fetch."},
                },
                "required": ["url"],
            },
        },
    ]


def _execute_tool(name: str, tool_input: dict, firecrawl_api_key: str) -> str:
    """Dispatch a tool call and return a string result."""
    try:
        from firecrawl import V1FirecrawlApp
    except ImportError:
        return "Error: firecrawl package not installed."

    client = V1FirecrawlApp(api_key=firecrawl_api_key)

    if name == "web_search":
        query = tool_input.get("query", "")
        limit = min(int(tool_input.get("limit", 5) or 5), 10)
        if not query:
            return "Error: query is required."
        try:
            response = client.search(query, limit=limit)
        except Exception as exc:
            logger.warning(f"Firecrawl search failed for '{query}': {exc}")
            return f"Tool error (web_search failed for '{query}'): {exc}. Try a different query or proceed with what you know."
        if not getattr(response, "success", False) or not getattr(response, "data", None):
            return f"No search results for '{query}'."

        sections = []
        for doc in response.data:
            if isinstance(doc, dict):
                url = doc.get("url", "")
                markdown = doc.get("markdown", "") or ""
                title = doc.get("title", "") or url
            else:
                url = getattr(doc, "url", "")
                markdown = getattr(doc, "markdown", "") or ""
                title = getattr(doc, "title", "") or url
            if markdown:
                sections.append(f"\n\n---\n## {title}\nSource: {url}\n\n{markdown}")
            elif url:
                sections.append(f"\n\n---\nSource: {url} (no content)")
        return f"Search results for '{query}':" + "".join(sections) if sections else f"No content found for '{query}'."

    if name == "web_scrape":
        url = tool_input.get("url", "")
        if not url:
            return "Error: url is required."
        try:
            response = client.scrape_url(url, formats=["markdown"])
        except Exception as exc:
            logger.warning(f"Firecrawl scrape failed for {url}: {exc}")
            return f"Tool error (web_scrape failed for {url}): {exc}. Try a different URL or summarize from search results."
        if not getattr(response, "success", False):
            return f"Error scraping {url}: {getattr(response, 'error', 'unknown')}"
        return getattr(response, "markdown", "") or f"No content returned for {url}."

    return f"Error: unknown tool '{name}'."


def run_research(
    user_prompt: str,
    anthropic_api_key: Optional[str] = None,
    firecrawl_api_key: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> dict:
    """
    Run one research task to completion.

    Returns:
        {
            "success": bool,
            "answer": str,
            "tool_calls": int,
            "turns": int,
            "error": Optional[str],
        }
    """
    anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
    firecrawl_api_key = firecrawl_api_key or os.environ.get("FIRECRAWL_API_KEY")
    if not anthropic_api_key:
        return {"success": False, "answer": "", "tool_calls": 0, "turns": 0, "error": "ANTHROPIC_API_KEY missing"}

    client = anthropic.Anthropic(api_key=anthropic_api_key)

    sys_text = system_prompt or (
        "You are agentsHQ's research engine. Answer the user's request by searching "
        "the web and scraping sources when needed. Cite URLs for every factual claim. "
        "Prefer primary sources. When asked for local businesses, return name, address, "
        "phone, hours, and a one-line summary of why you picked each one. When the user "
        "asks for a phone script, write the exact words they should say. Never fabricate "
        "phone numbers or addresses. If you cannot verify a fact, say so."
    )

    messages = [{"role": "user", "content": user_prompt}]
    tool_calls = 0

    for turn in range(1, MAX_TURNS + 1):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=sys_text,
            tools=_tool_definitions(),
            messages=messages,
        )

        try:
            from usage_logger import log_anthropic_call, merge_context
            log_anthropic_call(response, merge_context({
                "agent_name": "research_engine",
                "task_type": "research_report",
                "crew_name": "research_engine",
            }))
        except Exception as e:
            logger.debug("usage_logger failed on research turn: %s", e)

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            final_text = "".join(
                getattr(block, "text", "") for block in response.content if getattr(block, "type", "") == "text"
            ).strip()
            return {
                "success": True,
                "answer": final_text,
                "tool_calls": tool_calls,
                "turns": turn,
                "error": None,
            }

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if getattr(block, "type", "") != "tool_use":
                    continue
                tool_calls += 1
                result_text = _execute_tool(block.name, block.input, firecrawl_api_key or "")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                })
            messages.append({"role": "user", "content": tool_results})
            continue

        final_text = "".join(
            getattr(block, "text", "") for block in response.content if getattr(block, "type", "") == "text"
        ).strip()
        return {
            "success": True,
            "answer": final_text or f"(Stopped early: {response.stop_reason})",
            "tool_calls": tool_calls,
            "turns": turn,
            "error": None,
        }

    return {
        "success": False,
        "answer": "",
        "tool_calls": tool_calls,
        "turns": MAX_TURNS,
        "error": f"Hit MAX_TURNS cap of {MAX_TURNS} without end_turn",
    }
