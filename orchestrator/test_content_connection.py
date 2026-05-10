"""Tests for content_connection_crew.py — Atlas M9d-C"""
import pytest
from unittest.mock import MagicMock


def test_fetch_recent_content_returns_list():
    mock_notion = MagicMock()
    mock_notion.query_database.return_value = [
        {"id": "abc", "properties": {
            "Name": {"title": [{"plain_text": "Post about AI agents"}]},
            "Platform": {"select": {"name": "LinkedIn"}},
            "Status": {"select": {"name": "Published"}},
        }},
    ]
    from orchestrator.content_connection_crew import fetch_recent_content
    results = fetch_recent_content(notion=mock_notion, db_id="test-db", days=30)
    assert isinstance(results, list)
    assert results[0]["title"] == "Post about AI agents"
    assert results[0]["platform"] == "LinkedIn"


def test_fetch_filters_non_published():
    mock_notion = MagicMock()
    mock_notion.query_database.return_value = [
        {"id": "abc", "properties": {
            "Name": {"title": [{"plain_text": "Draft post"}]},
            "Platform": {"select": {"name": "LinkedIn"}},
            "Status": {"select": {"name": "Draft"}},
        }},
    ]
    from orchestrator.content_connection_crew import fetch_recent_content
    results = fetch_recent_content(notion=mock_notion, db_id="test-db", days=30)
    assert len(results) == 0


def test_build_connection_prompt_requires_non_obvious():
    from orchestrator.content_connection_crew import build_connection_prompt
    prompt = build_connection_prompt(
        posts=[{"title": "Post A", "platform": "LinkedIn"}, {"title": "Post B", "platform": "X"}],
        today="2026-06-01"
    )
    assert "non-obvious" in prompt.lower() or "not obvious" in prompt.lower()
    assert "connection" in prompt.lower()


def test_parse_connections_returns_list():
    from orchestrator.content_connection_crew import parse_connections
    llm_output = """### Connection 1: AI agents and lead gen
Post A and Post B both address the same underlying problem...
Why it matters: combining them creates a stronger angle.

### Connection 2: Trust signals across platforms
Different but related angle.
"""
    results = parse_connections(llm_output)
    assert len(results) >= 1
    assert "title" in results[0]
    assert "body" in results[0]


def test_write_connections_to_notion_creates_records():
    mock_notion = MagicMock()
    from orchestrator.content_connection_crew import write_connections_to_notion
    write_connections_to_notion(
        notion=mock_notion,
        connections=[{"title": "Test Connection", "body": "Some body text"}],
        today="2026-06-01"
    )
    assert mock_notion.create_page.called
    call_args = mock_notion.create_page.call_args
    # Second positional arg = properties
    props = call_args[0][1]
    assert props["Type"]["select"]["name"] == "Connection Insight"
