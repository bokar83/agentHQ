import time
import pytest
from unittest.mock import patch, MagicMock
from skills.forge_cli.notion_client import NotionClient


def test_client_initializes_with_headers():
    client = NotionClient(secret="test-secret")
    assert client.headers["Authorization"] == "Bearer test-secret"
    assert client.headers["Notion-Version"] == "2022-06-28"


def test_create_page_sends_correct_payload():
    client = NotionClient(secret="test-secret")
    with patch("httpx.Client") as MockClient:
        mock = MockClient.return_value.__enter__.return_value
        mock.post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "new-page-id", "url": "https://notion.so/new-page-id"},
        )
        mock.post.return_value.raise_for_status = MagicMock()
        result = client.create_page(
            database_id="db-123",
            properties={
                "Name": {"title": [{"text": {"content": "Test"}}]},
            },
        )
        assert result["id"] == "new-page-id"
        call_payload = mock.post.call_args[1]["json"]
        assert call_payload["parent"]["database_id"] == "db-123"


def test_query_database_returns_results():
    client = NotionClient(secret="test-secret")
    with patch("httpx.Client") as MockClient:
        mock = MockClient.return_value.__enter__.return_value
        mock.post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"results": [{"id": "page-1"}], "has_more": False},
        )
        mock.post.return_value.raise_for_status = MagicMock()
        results = client.query_database("db-123")
        assert len(results) == 1
        assert results[0]["id"] == "page-1"
