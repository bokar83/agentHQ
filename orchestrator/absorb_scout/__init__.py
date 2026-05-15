"""
absorb_scout -- Phase 2 source adapters.

Each adapter exposes one function:

    fetch(state: dict) -> list[dict]

where state is the row from scout_state for this source (cursor + counters)
and the return is a list of candidate dicts of shape::

    {"url": str, "kind": str, "source": str, "title": str, "ts": str}

The scout_dispatcher.scout_tick() in orchestrator/scout_dispatcher.py iterates
the registered adapters, de-dupes URLs against absorb_queue, enqueues new
ones via absorb_inbound.enqueue(), and updates scout_state per source.
"""
from . import reddit_rss, github_trending, hn_search  # noqa: F401

ADAPTERS = {
    # Reddit RSS feeds. Add subs by appending to this list.
    "scout-reddit-claude": ("scout-reddit", reddit_rss.fetch, "https://www.reddit.com/r/ClaudeAI/new/.rss"),
    "scout-reddit-localllama": ("scout-reddit", reddit_rss.fetch, "https://www.reddit.com/r/LocalLLaMA/new/.rss"),
    "scout-reddit-aiagents": ("scout-reddit", reddit_rss.fetch, "https://www.reddit.com/r/AI_Agents/new/.rss"),
    "scout-gh-ai-agents": ("scout-gh", github_trending.fetch, "ai-agents"),
    "scout-gh-mcp": ("scout-gh", github_trending.fetch, "mcp-server"),
    "scout-hn-agent": ("scout-hn", hn_search.fetch, "agent"),
}
