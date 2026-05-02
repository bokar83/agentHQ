"""Tests for orchestrator/notion_state_poller.py."""
import json
import shutil
import sys
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "orchestrator"))


@pytest.fixture
def tmp_path():
    path = REPO_ROOT / "tests" / "_tmp" / str(uuid.uuid4())
    path.mkdir(parents=True, exist_ok=False)
    yield path
    shutil.rmtree(path, ignore_errors=True)


def test_load_cache_missing_returns_empty_dict(tmp_path):
    import notion_state_poller as p
    cache_path = tmp_path / "notion_state_cache.json"
    result = p.load_cache(cache_path)
    assert result == {"_meta": {"version": 1}, "rows": {}}


def test_save_cache_atomic_write(tmp_path):
    import notion_state_poller as p
    cache_path = tmp_path / "notion_state_cache.json"
    state = {
        "_meta": {"version": 1, "last_tick": "2026-05-02T14:30:00Z"},
        "rows": {
            "page-id-1": {
                "task_id": "T-26045",
                "title": "Foo",
                "status": "Not Started",
            }
        },
    }
    p.save_cache(cache_path, state)
    assert cache_path.exists()
    loaded = json.loads(cache_path.read_text(encoding="utf-8"))
    assert loaded == state
    assert not (tmp_path / "notion_state_cache.json.tmp").exists()


def test_load_cache_corrupted_renames_and_returns_empty(tmp_path):
    import notion_state_poller as p
    cache_path = tmp_path / "notion_state_cache.json"
    cache_path.write_text("{not valid json", encoding="utf-8")
    result = p.load_cache(cache_path)
    assert result == {"_meta": {"version": 1}, "rows": {}}
    broken_files = list(tmp_path.glob("notion_state_cache.json.broken-*"))
    assert len(broken_files) == 1


def test_extract_tracked_props_typical_row():
    import notion_state_poller as p
    row = {
        "id": "page-1",
        "properties": {
            "Task ID": {"rich_text": [{"plain_text": "T-26045"}]},
            "Task": {"title": [{"plain_text": "Follow up on inbox replies"}]},
            "Status": {"select": {"name": "Not Started"}},
            "P0": {"checkbox": True},
            "Sprint": {"multi_select": [{"name": "Week 3"}]},
            "Owner": {"multi_select": [{"name": "Boubacar"}]},
            "Due Date": {"date": {"start": "2026-05-08"}},
            "Blocked By": {"relation": [{"id": "page-blocker-1"}]},
            "Notes": {"rich_text": [{"plain_text": "some notes"}]},
            "Outcome": {"rich_text": []},
        },
    }
    result = p.extract_tracked_props(row)
    assert result == {
        "task_id": "T-26045",
        "title": "Follow up on inbox replies",
        "status": "Not Started",
        "p0": True,
        "sprint": ["Week 3"],
        "owner": ["Boubacar"],
        "due_date": "2026-05-08",
        "blocked_by": ["page-blocker-1"],
        "notes": "some notes",
        "outcome": "",
    }


def test_extract_tracked_props_handles_nulls():
    import notion_state_poller as p
    row = {
        "id": "page-2",
        "properties": {
            "Task ID": {"rich_text": []},
            "Task": {"title": []},
            "Status": {"select": None},
            "P0": {"checkbox": False},
            "Sprint": {"multi_select": []},
            "Owner": {"multi_select": []},
            "Due Date": {"date": None},
            "Blocked By": {"relation": []},
            "Notes": {"rich_text": []},
            "Outcome": {"rich_text": []},
        },
    }
    result = p.extract_tracked_props(row)
    assert result == {
        "task_id": "",
        "title": "",
        "status": "",
        "p0": False,
        "sprint": [],
        "owner": [],
        "due_date": None,
        "blocked_by": [],
        "notes": "",
        "outcome": "",
    }


def test_diff_no_changes_returns_empty():
    import notion_state_poller as p
    row = {
        "task_id": "T-26045", "title": "Foo", "status": "Not Started",
        "p0": False, "sprint": [], "owner": ["Boubacar"], "due_date": None,
        "blocked_by": [], "notes": "", "outcome": "",
    }
    cache = dict(row)
    events = p.diff_row(cache, row)
    assert events == []


def test_diff_status_change():
    import notion_state_poller as p
    cache = {"task_id": "T-26045", "title": "Foo", "status": "Not Started",
             "p0": False, "sprint": [], "owner": [], "due_date": None,
             "blocked_by": [], "notes": "", "outcome": ""}
    current = dict(cache, status="Done")
    events = p.diff_row(cache, current)
    assert len(events) == 1
    assert events[0] == {"verb": "status", "desc": "Not Started -> Done"}


def test_diff_multiple_changes_in_one_edit():
    import notion_state_poller as p
    cache = {"task_id": "T-26045", "title": "Foo", "status": "Not Started",
             "p0": False, "sprint": ["Week 3"], "owner": ["Boubacar"],
             "due_date": None, "blocked_by": [], "notes": "", "outcome": ""}
    current = dict(cache, status="Done", sprint=["Week 4"], p0=True)
    events = p.diff_row(cache, current)
    verbs = sorted(e["verb"] for e in events)
    assert verbs == ["p0", "sprint", "status"]


def test_diff_sprint_set_equality_ignores_order():
    import notion_state_poller as p
    cache = {"task_id": "T-26045", "title": "Foo", "status": "Not Started",
             "p0": False, "sprint": ["Week 3", "Week 5"], "owner": [],
             "due_date": None, "blocked_by": [], "notes": "", "outcome": ""}
    current = dict(cache, sprint=["Week 5", "Week 3"])
    events = p.diff_row(cache, current)
    assert events == []


def test_diff_archived_when_sprint_moves_to_archive():
    import notion_state_poller as p
    cache = {"task_id": "T-26045", "title": "Foo", "status": "Not Started",
             "p0": False, "sprint": ["Week 3"], "owner": [],
             "due_date": None, "blocked_by": [], "notes": "", "outcome": ""}
    current = dict(cache, sprint=["Archive"])
    events = p.diff_row(cache, current)
    assert any(e["verb"] == "archived" for e in events)


def test_diff_blocked_by_added_and_removed():
    import notion_state_poller as p
    cache = {"task_id": "T-26045", "title": "Foo", "status": "Not Started",
             "p0": False, "sprint": [], "owner": [], "due_date": None,
             "blocked_by": ["page-A", "page-B"], "notes": "", "outcome": ""}
    current = dict(cache, blocked_by=["page-A", "page-C"])
    events = p.diff_row(cache, current)
    verbs = sorted(e["verb"] for e in events)
    assert "blocked" in verbs
    assert "unblocked" in verbs


def test_diff_notes_golden_gem_prefix():
    import notion_state_poller as p
    cache = {"task_id": "T-26045", "title": "Foo", "status": "Not Started",
             "p0": False, "sprint": [], "owner": [], "due_date": None,
             "blocked_by": [], "notes": "", "outcome": ""}
    current = dict(cache, notes="Golden Gem: this matters")
    events = p.diff_row(cache, current)
    notes_events = [e for e in events if e["verb"] == "notes"]
    assert len(notes_events) == 1
    assert notes_events[0]["desc"].startswith("prefix: Golden Gem")


def test_diff_due_date_none_to_value():
    import notion_state_poller as p
    cache = {"task_id": "T-26045", "title": "Foo", "status": "Not Started",
             "p0": False, "sprint": [], "owner": [], "due_date": None,
             "blocked_by": [], "notes": "", "outcome": ""}
    current = dict(cache, due_date="2026-05-08")
    events = p.diff_row(cache, current)
    assert events == [{"verb": "due", "desc": "none -> 2026-05-08"}]


def test_format_changelog_line_basic():
    import notion_state_poller as p
    line = p.format_changelog_line(
        timestamp="2026-05-02T14:30:21Z",
        task_id="T-26045",
        verb="status",
        title="Follow up on inbox replies",
        desc="Not Started -> Done",
    )
    assert line == '2026-05-02T14:30:21Z | T-26045 | status | "Follow up on inbox replies" | Not Started -> Done'


def test_format_changelog_line_truncates_long_title():
    import notion_state_poller as p
    long_title = "x" * 80
    line = p.format_changelog_line(
        timestamp="2026-05-02T14:30:21Z",
        task_id="T-26045",
        verb="status",
        title=long_title,
        desc="a -> b",
    )
    assert '"' + "x" * 60 + '..."' in line


def test_format_changelog_line_replaces_pipes_in_title_and_desc():
    import notion_state_poller as p
    line = p.format_changelog_line(
        timestamp="2026-05-02T14:30:21Z",
        task_id="T-26045",
        verb="renamed",
        title="A | B",
        desc='"x | y" -> "p | q"',
    )
    assert " | " in line
    assert "A ┃ B" in line
    assert "x ┃ y" in line


def test_format_changelog_line_system_event():
    import notion_state_poller as p
    line = p.format_changelog_line(
        timestamp="2026-05-02T14:30:21Z",
        task_id="system",
        verb="backfill",
        title="",
        desc="n=638 active rows",
    )
    assert line == '2026-05-02T14:30:21Z | system | backfill | "" | n=638 active rows'


def test_query_recently_changed_paginates(monkeypatch):
    import notion_state_poller as p
    monkeypatch.setenv("NOTION_SECRET", "fake-token")

    page1 = {
        "results": [{"id": "page-A", "properties": {}}, {"id": "page-B", "properties": {}}],
        "has_more": True,
        "next_cursor": "cursor-2",
    }
    page2 = {
        "results": [{"id": "page-C", "properties": {}}],
        "has_more": False,
        "next_cursor": None,
    }

    call_count = {"n": 0}

    def fake_post(url, headers, json, timeout):
        call_count["n"] += 1
        m = MagicMock()
        m.json.return_value = page1 if call_count["n"] == 1 else page2
        m.raise_for_status = lambda: None
        m.status_code = 200
        return m

    with patch("notion_state_poller.httpx.post", side_effect=fake_post):
        rows = p.query_recently_changed("dbid", since_iso="2026-05-02T14:24:00.000Z")

    assert len(rows) == 3
    assert [r["id"] for r in rows] == ["page-A", "page-B", "page-C"]
    assert call_count["n"] == 2


def test_query_recently_changed_uses_correct_filter():
    import notion_state_poller as p

    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["json"] = json
        m = MagicMock()
        m.json.return_value = {"results": [], "has_more": False}
        m.raise_for_status = lambda: None
        return m

    with patch.dict("os.environ", {"NOTION_SECRET": "fake"}):  # pragma: allowlist secret
        with patch("notion_state_poller.httpx.post", side_effect=fake_post):
            p.query_recently_changed("dbid", since_iso="2026-05-02T14:24:00.000Z")

    assert "/query" in captured["url"]
    flt = captured["json"].get("filter", {})
    assert flt.get("timestamp") == "last_edited_time"
    assert flt.get("last_edited_time", {}).get("on_or_after") == "2026-05-02T14:24:00.000Z"


def test_tick_first_run_does_backfill(tmp_path, monkeypatch):
    import notion_state_poller as p
    monkeypatch.setenv("NOTION_SECRET", "fake")
    monkeypatch.setattr(p, "DEFAULT_CACHE_PATH", tmp_path / "cache.json")
    monkeypatch.setattr(p, "DEFAULT_CHANGELOG_PATH", tmp_path / "changelog.md")

    sample_rows = [
        {
            "id": f"page-{i}",
            "properties": {
                "Task ID": {"rich_text": [{"plain_text": f"T-2604{i}"}]},
                "Task": {"title": [{"plain_text": f"Task {i}"}]},
                "Status": {"select": {"name": "Not Started"}},
                "P0": {"checkbox": False},
                "Sprint": {"multi_select": []},
                "Owner": {"multi_select": [{"name": "Boubacar"}]},
                "Due Date": {"date": None},
                "Blocked By": {"relation": []},
                "Notes": {"rich_text": []},
                "Outcome": {"rich_text": []},
            },
        }
        for i in range(3)
    ]

    monkeypatch.setattr(p, "query_all_active", lambda db_id: sample_rows)
    monkeypatch.setattr(p, "query_recently_changed", lambda db_id, since_iso: [])
    monkeypatch.setattr(p, "_with_lock", lambda fn: fn())

    result = p.tick(database_id="dbid")
    assert result["mode"] == "backfill"
    assert result["rows_indexed"] == 3
    cache = json.loads((tmp_path / "cache.json").read_text(encoding="utf-8"))
    assert len(cache["rows"]) == 3
    log = (tmp_path / "changelog.md").read_text(encoding="utf-8")
    assert "system | backfill" in log
    assert log.count("\n") == 1


def test_tick_normal_emits_event_per_change(tmp_path, monkeypatch):
    import notion_state_poller as p
    monkeypatch.setenv("NOTION_SECRET", "fake")
    monkeypatch.setattr(p, "DEFAULT_CACHE_PATH", tmp_path / "cache.json")
    monkeypatch.setattr(p, "DEFAULT_CHANGELOG_PATH", tmp_path / "changelog.md")

    cache = {
        "_meta": {"version": 1, "last_tick": "2026-05-02T14:00:00Z"},
        "rows": {
            "page-A": {
                "task_id": "T-26045", "title": "Foo", "status": "Not Started",
                "p0": False, "sprint": [], "owner": ["Boubacar"],
                "due_date": None, "blocked_by": [], "notes": "", "outcome": "",
            }
        },
    }
    p.save_cache(tmp_path / "cache.json", cache)

    notion_row = {
        "id": "page-A",
        "properties": {
            "Task ID": {"rich_text": [{"plain_text": "T-26045"}]},
            "Task": {"title": [{"plain_text": "Foo"}]},
            "Status": {"select": {"name": "Done"}},
            "P0": {"checkbox": False},
            "Sprint": {"multi_select": []},
            "Owner": {"multi_select": [{"name": "Boubacar"}]},
            "Due Date": {"date": None},
            "Blocked By": {"relation": []},
            "Notes": {"rich_text": []},
            "Outcome": {"rich_text": []},
        },
    }
    monkeypatch.setattr(p, "query_recently_changed", lambda db_id, since_iso: [notion_row])
    monkeypatch.setattr(p, "_with_lock", lambda fn: fn())

    result = p.tick(database_id="dbid")
    assert result["mode"] == "normal"
    assert result["events_emitted"] == 1

    log = (tmp_path / "changelog.md").read_text(encoding="utf-8")
    assert "T-26045 | status" in log
    assert "Not Started -> Done" in log

    cache_after = json.loads((tmp_path / "cache.json").read_text(encoding="utf-8"))
    assert cache_after["rows"]["page-A"]["status"] == "Done"


def test_tick_handles_new_row_as_created(tmp_path, monkeypatch):
    import notion_state_poller as p
    monkeypatch.setenv("NOTION_SECRET", "fake")
    monkeypatch.setattr(p, "DEFAULT_CACHE_PATH", tmp_path / "cache.json")
    monkeypatch.setattr(p, "DEFAULT_CHANGELOG_PATH", tmp_path / "changelog.md")

    p.save_cache(tmp_path / "cache.json", {"_meta": {"version": 1}, "rows": {}})

    new_row = {
        "id": "page-new",
        "properties": {
            "Task ID": {"rich_text": [{"plain_text": "T-26618"}]},
            "Task": {"title": [{"plain_text": "Reply to Adam"}]},
            "Status": {"select": {"name": "Not Started"}},
            "P0": {"checkbox": False},
            "Sprint": {"multi_select": [{"name": "Backlog"}]},
            "Owner": {"multi_select": [{"name": "Boubacar"}]},
            "Due Date": {"date": None},
            "Blocked By": {"relation": []},
            "Notes": {"rich_text": []},
            "Outcome": {"rich_text": []},
        },
    }
    monkeypatch.setattr(p, "query_recently_changed", lambda db_id, since_iso: [new_row])
    monkeypatch.setattr(p, "_with_lock", lambda fn: fn())

    result = p.tick(database_id="dbid")
    log = (tmp_path / "changelog.md").read_text(encoding="utf-8")
    assert "T-26618 | created" in log
    assert "Owner=Boubacar" in log
    assert "Sprint=Backlog" in log
