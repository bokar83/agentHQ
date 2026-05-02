"""Tests for /task add parser in orchestrator/handlers_commands.py."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "orchestrator"))


def test_parse_minimal_title():
    import handlers_commands as h
    parsed = h.parse_task_add('/task add "Reply to Adam"')
    assert parsed.ok is True
    assert parsed.title == "Reply to Adam"
    assert parsed.owner == "Boubacar"
    assert parsed.sprint == "Backlog"
    assert parsed.p0 is False


def test_parse_with_all_flags():
    import handlers_commands as h
    parsed = h.parse_task_add('/task add "Audit Hunter" --owner=Decision --sprint=Week 2 --p0')
    assert parsed.ok is True
    assert parsed.title == "Audit Hunter"
    assert parsed.owner == "Decision"
    assert parsed.sprint == "Week 2"
    assert parsed.p0 is True


def test_parse_quoted_sprint_with_space():
    import handlers_commands as h
    parsed = h.parse_task_add('/task add "Foo" --sprint="Week 12"')
    assert parsed.ok is True
    assert parsed.sprint == "Week 12"


def test_parse_missing_title_returns_error():
    import handlers_commands as h
    parsed = h.parse_task_add('/task add')
    assert parsed.ok is False
    assert "title" in parsed.error.lower()


def test_parse_unquoted_title_returns_error():
    import handlers_commands as h
    parsed = h.parse_task_add('/task add Reply to Adam')
    assert parsed.ok is False
    assert "title" in parsed.error.lower() or "quote" in parsed.error.lower()


def test_parse_invalid_owner_returns_suggestion():
    import handlers_commands as h
    parsed = h.parse_task_add('/task add "Foo" --owner=boubcar')
    assert parsed.ok is False
    assert "Boubacar" in parsed.error


def test_parse_invalid_sprint_returns_error():
    import handlers_commands as h
    parsed = h.parse_task_add('/task add "Foo" --sprint=Week 99')
    assert parsed.ok is False
    assert "sprint" in parsed.error.lower()


def test_parse_unknown_flag_returns_error():
    import handlers_commands as h
    parsed = h.parse_task_add('/task add "Foo" --due=2026-05-08')
    assert parsed.ok is False
    assert "--due" in parsed.error or "unknown" in parsed.error.lower()


def test_handle_task_add_creates_row(monkeypatch):
    import handlers_commands as h
    monkeypatch.setenv("NOTION_SECRET", "fake")

    def fake_query(db_id, filter_body=None, sorts=None):
        return [{
            "id": "page-x",
            "properties": {
                "Task ID": {"rich_text": [{"plain_text": "T-26617"}]},
                "Task": {"title": [{"plain_text": "..."}]},
            },
        }]

    posted = {}

    def fake_post(url, headers, json, timeout):
        posted["url"] = url
        posted["json"] = json
        m = MagicMock()
        m.json.return_value = {"id": "new-page-id"}
        m.raise_for_status = lambda: None
        return m

    with patch("handlers_commands._query_database", side_effect=fake_query), \
         patch("handlers_commands.httpx.post", side_effect=fake_post), \
         patch("handlers_commands._top_3_boubacar", return_value=[
             {"task_id": "T-26045", "title": "Foo", "p0": True},
             {"task_id": "T-26200", "title": "Bar", "p0": False},
             {"task_id": "T-26101", "title": "Baz", "p0": False},
         ]):
        reply = h.handle_task_add('/task add "Reply to Adam"')

    assert "T-26618" in reply
    assert "Reply to Adam" in reply
    assert "Top 3" in reply
    assert posted["json"]["properties"]["Task"]["title"][0]["text"]["content"] == "Reply to Adam"
    assert posted["json"]["properties"]["Owner"]["multi_select"][0]["name"] == "Boubacar"
    assert posted["json"]["properties"]["Sprint"]["multi_select"][0]["name"] == "Backlog"


def test_handle_task_add_p0_clears_existing_p0(monkeypatch):
    import handlers_commands as h
    monkeypatch.setenv("NOTION_SECRET", "fake")

    def fake_query(db_id, filter_body=None, sorts=None):
        flt = filter_body or {}
        if isinstance(flt, dict) and flt.get("property") == "P0":
            return [{"id": "page-old-p0",
                     "properties": {
                         "Task ID": {"rich_text": [{"plain_text": "T-26045"}]},
                         "Task": {"title": [{"plain_text": "Old P0"}]}}}]
        return [{"id": "page-x",
                 "properties": {
                     "Task ID": {"rich_text": [{"plain_text": "T-26617"}]},
                     "Task": {"title": [{"plain_text": "..."}]}}}]

    patches = []

    def fake_patch(url, headers, json, timeout):
        patches.append((url, json))
        m = MagicMock()
        m.raise_for_status = lambda: None
        return m

    def fake_post(url, headers, json, timeout):
        m = MagicMock()
        m.json.return_value = {"id": "new-page-id"}
        m.raise_for_status = lambda: None
        return m

    with patch("handlers_commands._query_database", side_effect=fake_query), \
         patch("handlers_commands.httpx.post", side_effect=fake_post), \
         patch("handlers_commands.httpx.patch", side_effect=fake_patch), \
         patch("handlers_commands._top_3_boubacar", return_value=[]):
        reply = h.handle_task_add('/task add "New P0" --p0')

    cleared_calls = [(u, j) for u, j in patches if "P0" in str(j)]
    assert len(cleared_calls) >= 1
    assert cleared_calls[0][1]["properties"]["P0"]["checkbox"] is False


def test_handle_task_add_returns_error_on_parse_fail():
    import handlers_commands as h
    reply = h.handle_task_add('/task add')
    assert "title" in reply.lower() or "usage" in reply.lower()
