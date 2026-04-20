from unittest.mock import MagicMock, patch
from skills.forge_cli.notion_client import NotionClient


def test_get_database_schema_returns_properties():
    client = NotionClient(secret="fake")
    fake_response = {
        "object": "database",
        "id": "dbid",
        "properties": {
            "Lead/Company": {"id": "title", "type": "title"},
            "Status": {"id": "s", "type": "status"},
        },
    }
    with patch.object(client, "_request", return_value=fake_response) as req:
        props = client.get_database_schema("dbid")
    assert "Lead/Company" in props
    assert props["Status"]["type"] == "status"
    req.assert_called_once_with("get", "databases/dbid")


def test_get_database_schema_empty_when_no_properties():
    client = NotionClient(secret="fake")
    with patch.object(client, "_request", return_value={"object": "database", "id": "dbid"}):
        props = client.get_database_schema("dbid")
    assert props == {}
