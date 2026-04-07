import os, pytest
os.environ["NOTION_SECRET"] = "fake_token_for_testing"  # pragma: allowlist secret

from unittest.mock import patch, MagicMock


def test_query_database_returns_results():
    from skills.notion_skill.notion_tool import query_database
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"results": [{"id": "abc", "properties": {"Name": {"title": [{"plain_text": "Test Idea"}]}}}]}
    mock_resp.raise_for_status = lambda: None
    with patch("httpx.post", return_value=mock_resp):
        results = query_database("fake-db-id")
    assert len(results) == 1
    assert results[0]["id"] == "abc"


def test_create_database_returns_id():
    from skills.notion_skill.notion_tool import create_database
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"id": "new-db-id-123", "url": "https://notion.so/new-db-id-123"}
    mock_resp.raise_for_status = lambda: None
    with patch("httpx.post", return_value=mock_resp):
        result = create_database("parent-page-id", "agentsHQ Ideas")
    assert result["id"] == "new-db-id-123"


def test_notion_create_idea_tool_requires_env():
    """NotionCreateIdeaTool returns error string if IDEAS_DB_ID not set."""
    import sys
    sys.path.insert(0, "d:/Ai_Sandbox/agentsHQ/orchestrator")
    os.environ.pop("IDEAS_DB_ID", None)
    from tools import NotionCreateIdeaTool
    tool = NotionCreateIdeaTool()
    result = tool._run('{"title": "Test", "content": "Hello"}')
    assert "IDEAS_DB_ID" in result or "Error" in result
