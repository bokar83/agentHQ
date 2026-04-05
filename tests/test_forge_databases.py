import pytest
from unittest.mock import MagicMock, patch
from skills.forge_cli.databases import ForgeDB


@pytest.fixture
def db():
    mock_client = MagicMock()
    mock_client.create_page.return_value = {"id": "new-id", "url": "https://notion.so/new-id"}
    mock_client.update_page.return_value = {"id": "existing-id"}
    return ForgeDB(client=mock_client)


def test_log_action(db):
    result = db.log_action("Built homepage", agent="Designer", status="Success")
    assert result["id"] == "new-id"
    call_props = db.client.create_page.call_args[1]["properties"]
    assert call_props["Action"]["title"][0]["text"]["content"] == "Built homepage"
    assert call_props["Agent"]["select"]["name"] == "Designer"
    assert call_props["Status"]["select"]["name"] == "Success"


def test_add_task(db):
    result = db.add_task("Wire Hunter", priority="P1", due="2026-04-12")
    assert result["id"] == "new-id"
    call_props = db.client.create_page.call_args[1]["properties"]
    assert call_props["Task"]["title"][0]["text"]["content"] == "Wire Hunter"
    assert call_props["Priority"]["select"]["name"] == "High"  # P1 maps to High
    assert call_props["Status"]["select"]["name"] == "Not Started"


def test_add_pipeline_lead(db):
    result = db.add_pipeline_lead("Acme Corp", contact="John", value=5000, status="New")
    call_props = db.client.create_page.call_args[1]["properties"]
    assert call_props["Lead/Company"]["title"][0]["text"]["content"] == "Acme Corp"
    assert call_props["Deal Value"]["number"] == 5000
    assert call_props["Status"]["select"]["name"] == "New"


def test_log_revenue(db):
    result = db.log_revenue(2500, source="Consulting", buyer="Acme Corp", description="AI Diagnostic")
    call_props = db.client.create_page.call_args[1]["properties"]
    assert call_props["Offer"]["title"][0]["text"]["content"] == "AI Diagnostic"
    assert call_props["Amount"]["number"] == 2500


def test_add_content_idea(db):
    result = db.add_content_idea("AI stalls at leadership", platforms=["LinkedIn"], topics=["AI", "Leadership"])
    call_props = db.client.create_page.call_args[1]["properties"]
    assert call_props["Title"]["title"][0]["text"]["content"] == "AI stalls at leadership"
    assert call_props["Status"]["select"]["name"] == "Idea"
    assert call_props["Platform"]["multi_select"] == [{"name": "LinkedIn"}]


def test_mark_task_done(db):
    db.mark_task_done("task-page-id")
    call_props = db.client.update_page.call_args[1]["properties"]
    assert call_props["Status"]["select"]["name"] == "Done"
