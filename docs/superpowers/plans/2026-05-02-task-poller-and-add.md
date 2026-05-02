# Notion State Poller + /task add Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 5-minute Notion poller that catches operator clicks and writes them to a permanent changelog, plus one Telegram verb (`/task add`) for fast phone capture. Notion stays the editing surface; agentsHQ catches up automatically.

**Architecture:** Two components. (1) `orchestrator/notion_state_poller.py` runs every 5 minutes via the existing heartbeat scheduler, queries Notion for rows changed in last 6 minutes, diffs against a JSON cache, appends one line per detected change to `docs/audits/changelog.md`. (2) `handle_task_add()` in `orchestrator/handlers_commands.py` parses `/task add "<title>"` Telegram commands, creates Notion rows with sensible defaults, returns echo + top 3 next tasks.

**Tech Stack:** Python 3.11, `httpx` (already in deps), `pytest`, Notion API v2022-06-28, OpenRouter (existing for orchestrator). Reuses existing `skills/notion_skill/notion_tool.py` helpers, `skills/coordination/__init__.py` locks, and `orchestrator/scheduler.py` heartbeat registration.

**Spec:** `docs/superpowers/specs/2026-05-02-task-poller-and-add-design.md`

---

## File Structure

| File | Responsibility | Status |
|---|---|---|
| `orchestrator/notion_state_poller.py` | Poller tick: query Notion, diff cache, write changelog, update cache | Create |
| `tests/test_notion_state_poller.py` | Unit tests for diff logic, format, edge cases | Create |
| `orchestrator/scheduler.py` | Register `notion-state-poller` wake | Modify (add ~10 lines) |
| `orchestrator/handlers_commands.py` | Add `handle_task_add()` + dispatch | Modify (add ~80 lines) |
| `tests/test_handle_task_add.py` | Unit tests for /task add parser | Create |
| `data/notion_state_cache.json` | State mirror (gitignored, runtime-created) | Created at runtime |
| `docs/audits/changelog.md` | Event log, append-only, committed | Created at runtime |

**Decomposition rationale:** Poller and `/task add` are independent. Poller has pure functions (diff, format, parse) wrapped by an impure `tick()` glue. `/task add` is a single function with parser + Notion writer. Each has its own test file. No new skill module, no new package. Single-file scripts are the pattern in `scripts/` and `orchestrator/`.

---

## Required reads before coding

- `docs/superpowers/specs/2026-05-02-task-poller-and-add-design.md` (the full spec)
- `orchestrator/scheduler.py:540-570` (wake registration pattern, see `auto-publisher` and `studio-trend-scout` examples)
- `orchestrator/handlers_commands.py` (existing dispatch pattern: `if text.lower().startswith("/cmd"):` returns string reply)
- `skills/notion_skill/notion_tool.py:108-123` (existing `query_database` helper; env var is `NOTION_SECRET`)
- `skills/coordination/__init__.py:82-119` (claim/complete API)
- `scripts/notion_task_audit.py:84-159` (existing pattern for Notion polling + paginated query)

---

## Pre-flight

### Task 0: Confirm environment

**Files:**
- Read: `d:/Ai_Sandbox/agentsHQ/.env`

- [ ] **Step 0.1: Confirm required env vars exist on local + VPS**

Run locally:
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('NOTION_SECRET ok' if os.environ.get('NOTION_SECRET') else 'MISSING'); print('NOTION_TASK_DB_ID', os.environ.get('NOTION_TASK_DB_ID', '249bcf1a302980739c26c61cad212477'))"
```

Run on VPS:
```bash
ssh root@72.60.209.109 "cd /root/agentsHQ && grep -c '^NOTION_SECRET=' .env"
```

Expected: `NOTION_SECRET ok` locally and `1` on VPS (one matching line).

- [ ] **Step 0.2: Verify branch state**

Run:
```bash
git branch --show-current
```
Expected: `feature/task-poller`. If not, `git checkout feature/task-poller`.

- [ ] **Step 0.3: Verify scheduler.py is importable + heartbeat available**

Run:
```bash
python -c "import sys; sys.path.insert(0, 'orchestrator'); import scheduler; print('ok')"
```
Expected: `ok` (scheduler module loads cleanly).

---

## Task 1: Poller skeleton + cache helpers

**Files:**
- Create: `orchestrator/notion_state_poller.py`
- Create: `tests/test_notion_state_poller.py`

### Task 1: Module skeleton with cache I/O

- [ ] **Step 1.1: Write the failing test for cache load/save round-trip**

Create `tests/test_notion_state_poller.py`:
```python
"""Tests for orchestrator/notion_state_poller.py."""
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "orchestrator"))


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
    # tmp file must not exist after save
    assert not (tmp_path / "notion_state_cache.json.tmp").exists()


def test_load_cache_corrupted_renames_and_returns_empty(tmp_path):
    import notion_state_poller as p
    cache_path = tmp_path / "notion_state_cache.json"
    cache_path.write_text("{not valid json", encoding="utf-8")
    result = p.load_cache(cache_path)
    assert result == {"_meta": {"version": 1}, "rows": {}}
    # Original corrupted file got renamed
    broken_files = list(tmp_path.glob("notion_state_cache.json.broken-*"))
    assert len(broken_files) == 1
```

- [ ] **Step 1.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_state_poller.py -v`
Expected: 3 failures with `ImportError: No module named 'notion_state_poller'`.

- [ ] **Step 1.3: Write the skeleton**

Create `orchestrator/notion_state_poller.py`:
```python
"""Notion State Poller.

Heartbeat-driven 5-minute tick. Queries Notion Tasks DB for rows changed in
last 6 minutes, diffs against cached state, writes one changelog line per
detected change. Single writer of docs/audits/changelog.md.

Spec: docs/superpowers/specs/2026-05-02-task-poller-and-add-design.md
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CACHE_PATH = REPO_ROOT / "data" / "notion_state_cache.json"
DEFAULT_CHANGELOG_PATH = REPO_ROOT / "docs" / "audits" / "changelog.md"
DEFAULT_NOTION_TASK_DB_ID = "249bcf1a302980739c26c61cad212477"

WINDOW_MIN = 6  # query window for "rows changed in last N min"
HARD_ROW_CAP = 200
HARD_TICK_SECONDS = 10
MAX_CHANGELOG_BYTES = 5 * 1024 * 1024  # 5 MB

NOTION_VERSION = "2022-06-28"


def load_cache(path: Path) -> dict:
    """Load the state cache. Returns {'_meta': ..., 'rows': {...}}.

    If the file is missing or corrupted, returns empty cache and renames
    the corrupted file out of the way for forensics.
    """
    if not path.exists():
        return {"_meta": {"version": 1}, "rows": {}}
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict) or "rows" not in data:
            raise ValueError("cache missing 'rows' key")
        return data
    except (json.JSONDecodeError, ValueError) as e:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        broken = path.with_suffix(f".json.broken-{ts}")
        path.rename(broken)
        logger.warning(f"notion_state_poller: corrupted cache renamed to {broken.name}; reason: {e}")
        return {"_meta": {"version": 1}, "rows": {}}


def save_cache(path: Path, state: dict) -> None:
    """Atomically save cache: write tmp, fsync, rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    raw = json.dumps(state, indent=2, ensure_ascii=False)
    tmp.write_text(raw, encoding="utf-8")
    # Best-effort fsync (Windows: rename is atomic without explicit fsync)
    try:
        with open(tmp, "rb") as f:
            os.fsync(f.fileno())
    except (OSError, AttributeError):
        pass
    tmp.replace(path)


def main():
    """CLI entry: run one tick. Used by heartbeat callback."""
    raise NotImplementedError("main() implemented in Task 6")


if __name__ == "__main__":
    main()
```

- [ ] **Step 1.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_state_poller.py -v`
Expected: 3 passed.

- [ ] **Step 1.5: Commit**

```bash
git add orchestrator/notion_state_poller.py tests/test_notion_state_poller.py
git commit -m "feat(poller): notion state poller skeleton + cache I/O"
```

---

## Task 2: Property extraction (Notion row -> tracked dict)

**Files:**
- Modify: `orchestrator/notion_state_poller.py`
- Modify: `tests/test_notion_state_poller.py`

### Task 2: Extract tracked properties from a Notion row payload

- [ ] **Step 2.1: Append failing test**

Append to `tests/test_notion_state_poller.py`:
```python
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
```

- [ ] **Step 2.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_state_poller.py -v -k extract_tracked`
Expected: 2 fail with `AttributeError: module 'notion_state_poller' has no attribute 'extract_tracked_props'`.

- [ ] **Step 2.3: Add `extract_tracked_props`**

Append to `orchestrator/notion_state_poller.py` (before `def main()`):
```python
TRACKED_PROPS = (
    "task_id", "title", "status", "p0",
    "sprint", "owner", "due_date", "blocked_by",
    "notes", "outcome",
)


def _rich_text_plain(rich_text_list: list) -> str:
    if not rich_text_list:
        return ""
    return rich_text_list[0].get("plain_text", "")


def _multi_select_names(items: list) -> list:
    return [item.get("name", "") for item in items]


def extract_tracked_props(row: dict) -> dict:
    """Extract just the properties we track from a Notion row payload.

    Returns a flat dict keyed by snake_case property name.
    Missing/null Notion values become empty string, empty list, or None.
    """
    props = row.get("properties", {})

    title_arr = props.get("Task", {}).get("title", []) or []
    task_id_arr = props.get("Task ID", {}).get("rich_text", []) or []
    notes_arr = props.get("Notes", {}).get("rich_text", []) or []
    outcome_arr = props.get("Outcome", {}).get("rich_text", []) or []

    status_sel = props.get("Status", {}).get("select")
    status = status_sel.get("name", "") if status_sel else ""

    p0 = bool(props.get("P0", {}).get("checkbox", False))

    sprint_items = props.get("Sprint", {}).get("multi_select", []) or []
    owner_items = props.get("Owner", {}).get("multi_select", []) or []

    due_obj = props.get("Due Date", {}).get("date")
    due_date = due_obj.get("start") if due_obj else None

    blocked_items = props.get("Blocked By", {}).get("relation", []) or []
    blocked_by = [r.get("id", "") for r in blocked_items if r.get("id")]

    return {
        "task_id": _rich_text_plain(task_id_arr),
        "title": _rich_text_plain(title_arr),
        "status": status,
        "p0": p0,
        "sprint": _multi_select_names(sprint_items),
        "owner": _multi_select_names(owner_items),
        "due_date": due_date,
        "blocked_by": blocked_by,
        "notes": _rich_text_plain(notes_arr),
        "outcome": _rich_text_plain(outcome_arr),
    }
```

- [ ] **Step 2.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_state_poller.py -v -k extract_tracked`
Expected: 2 passed.

- [ ] **Step 2.5: Commit**

```bash
git add orchestrator/notion_state_poller.py tests/test_notion_state_poller.py
git commit -m "feat(poller): extract_tracked_props pulls 10 fields from Notion row"
```

---

## Task 3: Diff function (cache row -> current row -> verb events)

**Files:**
- Modify: `orchestrator/notion_state_poller.py`
- Modify: `tests/test_notion_state_poller.py`

### Task 3: Per-property diff producing verb events

- [ ] **Step 3.1: Append failing tests**

Append to `tests/test_notion_state_poller.py`:
```python
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
```

- [ ] **Step 3.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_state_poller.py -v -k diff_`
Expected: 8 fail with `AttributeError: ... diff_row`.

- [ ] **Step 3.3: Add `diff_row`**

Append to `orchestrator/notion_state_poller.py` (after `extract_tracked_props`):
```python
def _csv(items: list) -> str:
    return ", ".join(items)


def diff_row(cache: dict, current: dict) -> list:
    """Compare cached state vs current state. Return list of verb events.

    Each event is a dict {"verb": <str>, "desc": <str>}. Empty list = no change.
    A single edit can produce multiple events (one per changed property).
    """
    events: list = []

    if cache.get("status") != current.get("status"):
        old = cache.get("status") or ""
        new = current.get("status") or ""
        events.append({"verb": "status", "desc": f"{old or '(empty)'} -> {new or '(empty)'}"})

    if cache.get("p0") != current.get("p0"):
        old = "true" if cache.get("p0") else "false"
        new = "true" if current.get("p0") else "false"
        events.append({"verb": "p0", "desc": f"{old} -> {new}"})

    cache_sprint = set(cache.get("sprint") or [])
    cur_sprint = set(current.get("sprint") or [])
    if cache_sprint != cur_sprint:
        old_csv = _csv(sorted(cache_sprint))
        new_csv = _csv(sorted(cur_sprint))
        events.append({"verb": "sprint", "desc": f"[{old_csv}] -> [{new_csv}]"})
        if "Archive" in cur_sprint and "Archive" not in cache_sprint:
            events.append({"verb": "archived", "desc": "Sprint moved to Archive"})

    cache_owner = set(cache.get("owner") or [])
    cur_owner = set(current.get("owner") or [])
    if cache_owner != cur_owner:
        old_csv = _csv(sorted(cache_owner))
        new_csv = _csv(sorted(cur_owner))
        events.append({"verb": "owner", "desc": f"[{old_csv}] -> [{new_csv}]"})

    if cache.get("due_date") != current.get("due_date"):
        old = cache.get("due_date") or "none"
        new = current.get("due_date") or "none"
        events.append({"verb": "due", "desc": f"{old} -> {new}"})

    cache_blocked = set(cache.get("blocked_by") or [])
    cur_blocked = set(current.get("blocked_by") or [])
    added = cur_blocked - cache_blocked
    removed = cache_blocked - cur_blocked
    if added:
        events.append({"verb": "blocked", "desc": f"added: {', '.join(sorted(added))}"})
    if removed:
        events.append({"verb": "unblocked", "desc": f"removed: {', '.join(sorted(removed))}"})

    if cache.get("title") != current.get("title"):
        old = cache.get("title") or ""
        new = current.get("title") or ""
        events.append({"verb": "renamed", "desc": f'"{old}" -> "{new}"'})

    if cache.get("notes", "") != current.get("notes", ""):
        new_notes = current.get("notes", "") or ""
        # If new notes have an emoji-prefix pattern (text up to first colon, max 30 chars), capture it
        if ":" in new_notes[:60]:
            prefix = new_notes.split(":", 1)[0].strip()
            if 1 <= len(prefix) <= 30:
                events.append({"verb": "notes", "desc": f"prefix: {prefix}"})
            else:
                events.append({"verb": "notes", "desc": "notes changed (no detail)"})
        elif not new_notes:
            events.append({"verb": "notes", "desc": "notes cleared"})
        else:
            events.append({"verb": "notes", "desc": "notes changed (no detail)"})

    if cache.get("outcome", "") != current.get("outcome", ""):
        new_outcome = current.get("outcome", "") or ""
        truncated = new_outcome if len(new_outcome) <= 60 else new_outcome[:57] + "..."
        events.append({"verb": "outcome", "desc": f'set: "{truncated}"'})

    return events
```

- [ ] **Step 3.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_state_poller.py -v`
Expected: all tests passed (3 from Task 1 + 2 from Task 2 + 8 from Task 3 = 13).

- [ ] **Step 3.5: Commit**

```bash
git add orchestrator/notion_state_poller.py tests/test_notion_state_poller.py
git commit -m "feat(poller): diff_row produces verb events per changed property"
```

---

## Task 4: Changelog line formatter

**Files:**
- Modify: `orchestrator/notion_state_poller.py`
- Modify: `tests/test_notion_state_poller.py`

### Task 4: Format a changelog line per the locked contract

- [ ] **Step 4.1: Append failing tests**

Append to `tests/test_notion_state_poller.py`:
```python
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
    # Title should be truncated to 60 chars + ellipsis (3 chars = 63 total inside quotes)
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
    assert " | " in line  # field separators preserved
    # Pipes inside title and desc replaced with U+2503
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
```

- [ ] **Step 4.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_state_poller.py -v -k format_changelog`
Expected: 4 fail with `AttributeError: ... format_changelog_line`.

- [ ] **Step 4.3: Add `format_changelog_line`**

Append to `orchestrator/notion_state_poller.py`:
```python
HEAVY_VBAR = "┃"
TITLE_MAX = 60


def format_changelog_line(
    timestamp: str,
    task_id: str,
    verb: str,
    title: str,
    desc: str,
) -> str:
    """Format one changelog line per the spec contract.

    Pipe characters in title and desc are replaced with U+2503 to keep the
    field separator unambiguous. Title is truncated to TITLE_MAX chars + "..."
    if longer.
    """
    title_safe = (title or "").replace("|", HEAVY_VBAR)
    desc_safe = (desc or "").replace("|", HEAVY_VBAR)
    if len(title_safe) > TITLE_MAX:
        title_safe = title_safe[:TITLE_MAX] + "..."
    return f'{timestamp} | {task_id} | {verb} | "{title_safe}" | {desc_safe}'


def append_changelog(path: Path, line: str) -> None:
    """Append a single line to the changelog file. Creates parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
```

- [ ] **Step 4.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_state_poller.py -v -k format_changelog`
Expected: 4 passed.

- [ ] **Step 4.5: Commit**

```bash
git add orchestrator/notion_state_poller.py tests/test_notion_state_poller.py
git commit -m "feat(poller): format_changelog_line + append_changelog"
```

---

## Task 5: Notion query helper (paginated, windowed)

**Files:**
- Modify: `orchestrator/notion_state_poller.py`
- Modify: `tests/test_notion_state_poller.py`

### Task 5: Query Notion for rows in time window

- [ ] **Step 5.1: Append failing test**

Append to `tests/test_notion_state_poller.py`:
```python
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
```

- [ ] **Step 5.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_state_poller.py -v -k query_recently`
Expected: 2 fail.

- [ ] **Step 5.3: Add `query_recently_changed`**

Append to `orchestrator/notion_state_poller.py`:
```python
import httpx


def _notion_headers() -> dict:
    token = os.environ.get("NOTION_SECRET")
    if not token:
        raise RuntimeError("NOTION_SECRET not in environment.")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def query_recently_changed(database_id: str, since_iso: str) -> list:
    """Query Notion DB for rows last_edited_time >= since_iso. Paginates.

    Returns list of raw row payloads (caller calls extract_tracked_props).
    """
    headers = _notion_headers()
    rows: list = []
    cursor = None
    while True:
        body = {
            "filter": {
                "timestamp": "last_edited_time",
                "last_edited_time": {"on_or_after": since_iso},
            },
            "page_size": 100,
        }
        if cursor:
            body["start_cursor"] = cursor
        r = httpx.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            headers=headers,
            json=body,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        rows.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        if len(rows) > HARD_ROW_CAP:
            logger.warning(
                f"notion_state_poller: row count {len(rows)} exceeds HARD_ROW_CAP={HARD_ROW_CAP}; truncating"
            )
            rows = rows[:HARD_ROW_CAP]
            break
    return rows


def query_all_active(database_id: str) -> list:
    """Backfill helper: query ALL rows where Status != Done. Paginates.

    Returns list of raw row payloads.
    """
    headers = _notion_headers()
    rows: list = []
    cursor = None
    while True:
        body = {
            "filter": {"property": "Status", "select": {"does_not_equal": "Done"}},
            "page_size": 100,
        }
        if cursor:
            body["start_cursor"] = cursor
        r = httpx.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            headers=headers,
            json=body,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        rows.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return rows
```

- [ ] **Step 5.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_state_poller.py -v`
Expected: all tests passed (now 19 total).

- [ ] **Step 5.5: Commit**

```bash
git add orchestrator/notion_state_poller.py tests/test_notion_state_poller.py
git commit -m "feat(poller): query_recently_changed + query_all_active with pagination"
```

---

## Task 6: Tick orchestrator + backfill mode + lock

**Files:**
- Modify: `orchestrator/notion_state_poller.py`
- Modify: `tests/test_notion_state_poller.py`

### Task 6: Wire it all together with the lock + backfill

- [ ] **Step 6.1: Append failing test**

Append to `tests/test_notion_state_poller.py`:
```python
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
    # Bypass coordination lock in tests
    monkeypatch.setattr(p, "_with_lock", lambda fn: fn())

    result = p.tick(database_id="dbid")
    assert result["mode"] == "backfill"
    assert result["rows_indexed"] == 3
    # Cache populated
    cache = json.loads((tmp_path / "cache.json").read_text(encoding="utf-8"))
    assert len(cache["rows"]) == 3
    # Changelog has exactly one backfill line
    log = (tmp_path / "changelog.md").read_text(encoding="utf-8")
    assert "system | backfill" in log
    assert log.count("\n") == 1


def test_tick_normal_emits_event_per_change(tmp_path, monkeypatch):
    import notion_state_poller as p
    monkeypatch.setenv("NOTION_SECRET", "fake")
    monkeypatch.setattr(p, "DEFAULT_CACHE_PATH", tmp_path / "cache.json")
    monkeypatch.setattr(p, "DEFAULT_CHANGELOG_PATH", tmp_path / "changelog.md")

    # Pre-existing cache with one row, status=Not Started
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

    # Notion now reports the row with status=Done
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

    # Cache updated
    cache_after = json.loads((tmp_path / "cache.json").read_text(encoding="utf-8"))
    assert cache_after["rows"]["page-A"]["status"] == "Done"


def test_tick_handles_new_row_as_created(tmp_path, monkeypatch):
    import notion_state_poller as p
    monkeypatch.setenv("NOTION_SECRET", "fake")
    monkeypatch.setattr(p, "DEFAULT_CACHE_PATH", tmp_path / "cache.json")
    monkeypatch.setattr(p, "DEFAULT_CHANGELOG_PATH", tmp_path / "changelog.md")

    # Empty-but-existing cache
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
```

- [ ] **Step 6.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_state_poller.py -v -k tick`
Expected: 3 fail with `AttributeError: ... tick`.

- [ ] **Step 6.3: Add `tick` and helpers**

Append to `orchestrator/notion_state_poller.py`:
```python
from datetime import timedelta


def _now_utc_iso() -> str:
    """ISO 8601 UTC with Z suffix, no fractional seconds."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _with_lock(fn):
    """Run `fn` inside the coordination lock. Returns fn's value, or None on conflict.

    Made a module-level function so tests can monkeypatch it cleanly.
    """
    try:
        from skills.coordination import lock as coord_lock
    except ImportError:
        return fn()  # tests / dev environments without coordination layer
    holder = "notion-state-poller"
    ttl = 60
    try:
        with coord_lock("task:notion-state-poller", holder=holder, ttl_seconds=ttl):
            return fn()
    except Exception as e:
        logger.warning(f"notion_state_poller: lock conflict or error ({e}); skipping tick")
        return {"mode": "skipped", "reason": "lock"}


def tick(database_id: str | None = None) -> dict:
    """Run one poller tick. Returns a dict summary.

    Modes:
      - "backfill" on first run (cache missing), populates cache from all
        active rows, emits one `system | backfill` line, no per-row events.
      - "normal" on subsequent runs, queries time-windowed changes, emits
        one event per (row, changed_property).
      - "skipped" if the coordination lock is held by another tick.
    """
    return _with_lock(lambda: _tick_inner(database_id))


def _tick_inner(database_id: str | None) -> dict:
    db_id = database_id or os.environ.get("NOTION_TASK_DB_ID", DEFAULT_NOTION_TASK_DB_ID)
    cache_path = DEFAULT_CACHE_PATH
    log_path = DEFAULT_CHANGELOG_PATH

    cache = load_cache(cache_path)
    rows_in_cache = bool(cache.get("rows"))

    now_iso = _now_utc_iso()

    if not rows_in_cache and not (cache_path.exists() and cache.get("_meta", {}).get("last_tick")):
        # Backfill mode
        all_rows = query_all_active(db_id)
        new_rows: dict = {}
        for r in all_rows:
            page_id = r["id"]
            new_rows[page_id] = extract_tracked_props(r)
        cache["rows"] = new_rows
        cache["_meta"] = {
            "version": 1,
            "last_tick": now_iso,
            "last_full_scan": now_iso,
        }
        save_cache(cache_path, cache)
        line = format_changelog_line(
            timestamp=now_iso,
            task_id="system",
            verb="backfill",
            title="",
            desc=f"n={len(new_rows)} active rows",
        )
        append_changelog(log_path, line)
        return {"mode": "backfill", "rows_indexed": len(new_rows)}

    # Normal mode: query window
    last_tick = cache.get("_meta", {}).get("last_tick", _now_utc_iso())
    # Window is WINDOW_MIN minutes; use last_tick minus 1 min as overlap
    try:
        last_tick_dt = datetime.fromisoformat(last_tick.replace("Z", "+00:00"))
    except ValueError:
        last_tick_dt = datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MIN)
    since_dt = max(last_tick_dt - timedelta(minutes=1), datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MIN))
    since_iso = since_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    rows = query_recently_changed(db_id, since_iso)

    events_emitted = 0
    for row in rows:
        page_id = row["id"]
        current = extract_tracked_props(row)
        cached = cache["rows"].get(page_id)
        if cached is None:
            # New row -> emit `created` event
            owner_csv = ", ".join(current.get("owner") or [])
            sprint_csv = ", ".join(current.get("sprint") or [])
            # Source not in tracked props; pull from row directly
            src_arr = row.get("properties", {}).get("Source", {}).get("rich_text", []) or []
            src_text = src_arr[0].get("plain_text", "") if src_arr else ""
            line = format_changelog_line(
                timestamp=now_iso,
                task_id=current.get("task_id") or "T-?????",
                verb="created",
                title=current.get("title") or "",
                desc=f'Owner={owner_csv} Sprint={sprint_csv} Source="{src_text}"',
            )
            append_changelog(log_path, line)
            events_emitted += 1
        else:
            for evt in diff_row(cached, current):
                line = format_changelog_line(
                    timestamp=now_iso,
                    task_id=current.get("task_id") or "T-?????",
                    verb=evt["verb"],
                    title=current.get("title") or "",
                    desc=evt["desc"],
                )
                append_changelog(log_path, line)
                events_emitted += 1
        cache["rows"][page_id] = current

    cache["_meta"]["last_tick"] = now_iso
    save_cache(cache_path, cache)
    return {"mode": "normal", "events_emitted": events_emitted}


def main():
    """CLI entry: run one tick. Used by heartbeat callback."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    result = tick()
    print(f"notion_state_poller: {result}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_state_poller.py -v`
Expected: all 22 tests passed.

- [ ] **Step 6.5: py_compile sanity check**

Run: `python -m py_compile orchestrator/notion_state_poller.py`
Expected: no output, exit 0.

- [ ] **Step 6.6: Commit**

```bash
git add orchestrator/notion_state_poller.py tests/test_notion_state_poller.py
git commit -m "feat(poller): tick orchestrator with backfill + lock + diff loop"
```

---

## Task 7: Heartbeat wake registration

**Files:**
- Modify: `orchestrator/scheduler.py`

### Task 7: Register the wake

- [ ] **Step 7.1: Read existing wake patterns**

Read `orchestrator/scheduler.py:540-571` (the auto-publisher and studio-trend-scout registrations) to confirm the exact pattern.

- [ ] **Step 7.2: Add wake registration**

Append to `orchestrator/scheduler.py` (after the studio-trend-scout block around line 571, before the M9c memory compressor block):

```python
    # Atlas: Notion State Poller. Runs every 5 minutes. Queries Tasks DB for
    # rows changed in last 6 minutes, diffs against cache, writes changelog.
    # Single source of truth for "what changed in the Tasks DB" event log.
    # Spec: docs/superpowers/specs/2026-05-02-task-poller-and-add-design.md
    try:
        import heartbeat as _heartbeat
        from notion_state_poller import tick as _notion_state_poller_tick
        _heartbeat.register_wake(
            "notion-state-poller",
            crew_name="atlas",
            callback=_notion_state_poller_tick,
            every="5m",
        )
    except Exception as e:
        logger.error(f"NOTION_STATE_POLLER: wake registration failed ({e}); continuing without poller", exc_info=True)
```

- [ ] **Step 7.3: Verify scheduler still imports cleanly**

Run:
```bash
python -c "import sys; sys.path.insert(0, 'orchestrator'); import scheduler; print('ok')"
```
Expected: `ok`.

- [ ] **Step 7.4: Commit**

```bash
git add orchestrator/scheduler.py
git commit -m "feat(scheduler): register notion-state-poller wake every 5m"
```

---

## Task 8: /task add parser

**Files:**
- Create: `tests/test_handle_task_add.py`
- Modify: `orchestrator/handlers_commands.py`

### Task 8: Parse the command surface

- [ ] **Step 8.1: Write failing tests for the parser**

Create `tests/test_handle_task_add.py`:
```python
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
    assert "Boubacar" in parsed.error  # suggestion of closest match


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
```

- [ ] **Step 8.2: Run tests to verify they fail**

Run: `pytest tests/test_handle_task_add.py -v`
Expected: 8 fail with `AttributeError: ... parse_task_add`.

- [ ] **Step 8.3: Add `parse_task_add` to `handlers_commands.py`**

Append to `orchestrator/handlers_commands.py` (near the end, before any dispatch hook):
```python
import re
from dataclasses import dataclass


VALID_OWNERS = ("Boubacar", "Coding", "agentsHQ", "Decision")
VALID_SPRINTS = (
    "Backlog",
    "Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6",
    "Week 7", "Week 8", "Week 9", "Week 10", "Week 11", "Week 12",
    "Archive",
)


@dataclass
class TaskAddParse:
    ok: bool
    title: str = ""
    owner: str = "Boubacar"
    sprint: str = "Backlog"
    p0: bool = False
    error: str = ""


def _closest_owner(name: str) -> str | None:
    """Case-insensitive prefix or substring match. Returns the canonical owner if 1 match."""
    needle = name.lower()
    matches = [o for o in VALID_OWNERS if needle in o.lower() or o.lower().startswith(needle)]
    if len(matches) == 1:
        return matches[0]
    return None


def parse_task_add(text: str) -> TaskAddParse:
    """Parse `/task add "<title>" [--owner=X] [--sprint=Y] [--p0]`.

    Returns TaskAddParse with ok=True or ok=False+error.
    """
    body = text.strip()
    # Strip leading "/task add"
    if body.lower().startswith("/task add"):
        body = body[len("/task add"):].strip()
    else:
        return TaskAddParse(ok=False, error='Expected "/task add" prefix.')

    if not body:
        return TaskAddParse(ok=False, error='Missing title. Usage: /task add "<title>" [--owner=X] [--sprint=Y] [--p0]')

    # Match the title: must be the first quoted string
    m = re.match(r'"([^"]*)"\s*(.*)$', body)
    if not m:
        return TaskAddParse(
            ok=False,
            error='Title must be in quotes. Usage: /task add "<title>" [--owner=X] [--sprint=Y] [--p0]',
        )
    title = m.group(1).strip()
    rest = m.group(2).strip()

    if not title:
        return TaskAddParse(ok=False, error="Title cannot be empty.")

    owner = "Boubacar"
    sprint = "Backlog"
    p0 = False

    # Tokenize the flag tail. Flags: --p0 (bool), --owner=X (single token), --sprint=X or --sprint="X Y"
    # Strategy: regex over rest
    flag_re = re.compile(r'--(\w+)(?:=("[^"]+"|\S+))?')
    pos = 0
    rest_lower = rest.lower()
    while pos < len(rest):
        m2 = flag_re.search(rest, pos)
        if not m2:
            break
        key = m2.group(1).lower()
        val = m2.group(2)
        if val is not None and val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        if key == "p0":
            p0 = True
        elif key == "owner":
            if val is None:
                return TaskAddParse(ok=False, error="--owner requires a value")
            cand = _closest_owner(val)
            if cand is None:
                return TaskAddParse(
                    ok=False,
                    error=f'Owner "{val}" not found. Valid: {", ".join(VALID_OWNERS)}.',
                )
            owner = cand
        elif key == "sprint":
            if val is None:
                return TaskAddParse(ok=False, error="--sprint requires a value")
            # Allow "Week N" without quotes by also pulling next token
            tail_after = rest[m2.end():]
            tail_match = re.match(r'\s+(\d+)', tail_after)
            if val.lower() == "week" and tail_match:
                val = f"Week {tail_match.group(1)}"
                pos = m2.end() + tail_match.end()
            else:
                pos = m2.end()
            if val not in VALID_SPRINTS:
                return TaskAddParse(
                    ok=False,
                    error=f'Sprint "{val}" not found. Valid: Backlog, Week 1-12, Archive.',
                )
            sprint = val
            continue  # we set pos manually
        else:
            return TaskAddParse(ok=False, error=f'Unknown flag --{key}. Valid: --owner, --sprint, --p0')
        pos = m2.end()

    return TaskAddParse(ok=True, title=title, owner=owner, sprint=sprint, p0=p0)
```

- [ ] **Step 8.4: Run tests to verify they pass**

Run: `pytest tests/test_handle_task_add.py -v`
Expected: 8 passed.

- [ ] **Step 8.5: Commit**

```bash
git add orchestrator/handlers_commands.py tests/test_handle_task_add.py
git commit -m "feat(handlers): parse_task_add for /task add command surface"
```

---

## Task 9: /task add Notion writer + dispatch

**Files:**
- Modify: `orchestrator/handlers_commands.py`
- Modify: `tests/test_handle_task_add.py`

### Task 9: Wire parser to Notion + reply formatter + dispatch hook

- [ ] **Step 9.1: Write failing tests for the writer**

Append to `tests/test_handle_task_add.py`:
```python
def test_handle_task_add_creates_row(monkeypatch):
    import handlers_commands as h
    monkeypatch.setenv("NOTION_SECRET", "fake")

    # Mock max-id query (returns one existing T-26617)
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

    # Existing P0 row
    def fake_query(db_id, filter_body=None, sorts=None):
        flt = (filter_body or {})
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

    # Existing P0 was cleared
    cleared_calls = [(u, j) for u, j in patches if "P0" in str(j)]
    assert len(cleared_calls) >= 1
    assert cleared_calls[0][1]["properties"]["P0"]["checkbox"] is False


def test_handle_task_add_returns_error_on_parse_fail():
    import handlers_commands as h
    reply = h.handle_task_add('/task add')
    assert "title" in reply.lower() or "usage" in reply.lower()
```

- [ ] **Step 9.2: Run tests to verify they fail**

Run: `pytest tests/test_handle_task_add.py -v -k handle_task_add`
Expected: 3 fail with `AttributeError: ... handle_task_add`.

- [ ] **Step 9.3: Add `handle_task_add` and helpers**

Append to `orchestrator/handlers_commands.py`:
```python
NOTION_TASK_DB_ID = os.environ.get("NOTION_TASK_DB_ID", "249bcf1a302980739c26c61cad212477")
NOTION_VERSION = "2022-06-28"


def _notion_headers_for_tasks() -> dict:
    token = os.environ.get("NOTION_SECRET")
    if not token:
        raise RuntimeError("NOTION_SECRET not in environment.")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _query_database(database_id: str, filter_body=None, sorts=None) -> list:
    """Thin wrapper to the existing skills.notion_skill helper, importable here for monkeypatching."""
    from skills.notion_skill.notion_tool import query_database
    return query_database(database_id, filter_body=filter_body, sorts=sorts)


def _next_task_id(database_id: str) -> str:
    """Find max T-YYxxxx, increment by 1. Year prefix from current UTC year."""
    today_year = datetime.now(timezone.utc).strftime("%y")
    rows = _query_database(
        database_id,
        sorts=[{"timestamp": "created_time", "direction": "descending"}],
    )
    max_n = 0
    prefix = f"T-{today_year}"
    for r in rows[:200]:  # bound the scan
        rt = r.get("properties", {}).get("Task ID", {}).get("rich_text", [])
        if not rt:
            continue
        tid = rt[0].get("plain_text", "")
        if tid.startswith(prefix):
            try:
                n = int(tid[len(prefix):])
                if n > max_n:
                    max_n = n
            except ValueError:
                continue
    return f"{prefix}{max_n + 1:04d}"


def _clear_existing_p0(database_id: str) -> None:
    """Patch every P0=true row to P0=false. Single-P0 invariant."""
    rows = _query_database(
        database_id,
        filter_body={"property": "P0", "checkbox": {"equals": True}},
    )
    headers = _notion_headers_for_tasks()
    for r in rows:
        body = {"properties": {"P0": {"checkbox": False}}}
        httpx.patch(
            f"https://api.notion.com/v1/pages/{r['id']}",
            headers=headers,
            json=body,
            timeout=30,
        )


def _top_3_boubacar() -> list:
    """Top 3 active Boubacar tasks for echo. Returns list of dicts {task_id, title, p0}."""
    rows = _query_database(
        NOTION_TASK_DB_ID,
        filter_body={
            "and": [
                {"property": "Owner", "multi_select": {"contains": "Boubacar"}},
                {"property": "Status", "select": {"does_not_equal": "Done"}},
            ]
        },
        sorts=[
            {"property": "P0", "direction": "descending"},
            {"property": "Priority", "direction": "ascending"},
            {"property": "Task ID", "direction": "ascending"},
        ],
    )
    out = []
    for r in rows[:3]:
        props = r.get("properties", {})
        title_arr = props.get("Task", {}).get("title", [])
        title = title_arr[0].get("plain_text", "") if title_arr else ""
        tid_arr = props.get("Task ID", {}).get("rich_text", [])
        task_id = tid_arr[0].get("plain_text", "") if tid_arr else ""
        p0 = bool(props.get("P0", {}).get("checkbox", False))
        out.append({"task_id": task_id, "title": title, "p0": p0})
    return out


def _format_top_3_lines(items: list) -> str:
    if not items:
        return ""
    lines = ["Top 3:"]
    for it in items:
        flag = "P0" if it.get("p0") else "  "
        lines.append(f"  {it.get('task_id', '?')}  {flag}  {it.get('title', '')[:50]}")
    return "\n".join(lines)


def handle_task_add(text: str) -> str:
    """Handle /task add command. Returns Telegram-friendly reply string."""
    parsed = parse_task_add(text)
    if not parsed.ok:
        return parsed.error

    db_id = NOTION_TASK_DB_ID
    try:
        new_id = _next_task_id(db_id)
        if parsed.p0:
            _clear_existing_p0(db_id)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        props = {
            "Task": {"title": [{"text": {"content": parsed.title}}]},
            "Status": {"select": {"name": "Not Started"}},
            "Owner": {"multi_select": [{"name": parsed.owner}]},
            "Sprint": {"multi_select": [{"name": parsed.sprint}]},
            "Task ID": {"rich_text": [{"text": {"content": new_id}}]},
            "Source": {"rich_text": [{"text": {"content": f"Manual: {today}"}}]},
            "P0": {"checkbox": parsed.p0},
        }
        body = {"parent": {"database_id": db_id}, "properties": props}
        httpx.post(
            "https://api.notion.com/v1/pages",
            headers=_notion_headers_for_tasks(),
            json=body,
            timeout=30,
        ).raise_for_status()
    except httpx.HTTPError as e:
        logger.warning(f"handle_task_add: Notion API error ({e})")
        return "Notion API error. Try again in 1 min."

    top3 = _top_3_boubacar()
    reply_lines = [f'Added {new_id}: "{parsed.title}"']
    top3_block = _format_top_3_lines(top3)
    if top3_block:
        reply_lines.append("")
        reply_lines.append(top3_block)
    return "\n".join(reply_lines)
```

Add at the top of `handlers_commands.py` if not already imported:
```python
import os
from datetime import datetime, timezone

import httpx
```

(Most of these are already imported; only add what is missing.)

- [ ] **Step 9.4: Wire dispatch into the existing handler**

Find the existing dispatch chain in `handlers_commands.py` (search for `if text.lower().startswith("/cost"):` or similar). Add a check for `/task add` BEFORE the catch-all fallback:

```python
    if text.lower().startswith("/task add"):
        return handle_task_add(text)
```

Place this near the other `/...` handlers in the same dispatch function.

- [ ] **Step 9.5: Run tests to verify they pass**

Run: `pytest tests/test_handle_task_add.py -v`
Expected: 11 tests passed.

- [ ] **Step 9.6: py_compile sanity check**

Run: `python -m py_compile orchestrator/handlers_commands.py`
Expected: no output, exit 0.

- [ ] **Step 9.7: Commit**

```bash
git add orchestrator/handlers_commands.py tests/test_handle_task_add.py
git commit -m "feat(handlers): handle_task_add wired to Notion + dispatch"
```

---

## Task 10: Deploy + verify C1-C4 on VPS

**Files:** none (deployment + smoke test only)

### Task 10: Deploy and verify

- [ ] **Step 10.1: Push branch + open PR**

Run:
```bash
git push origin feature/task-poller
gh pr create --base main --head feature/task-poller --title "Notion state poller + /task add" --body "Implements docs/superpowers/specs/2026-05-02-task-poller-and-add-design.md. See spec for context."
```
Expected: PR URL printed.

- [ ] **Step 10.2: Wait for review approval, then merge**

Boubacar reviews the PR. After approval:
```bash
gh pr merge --merge
```

- [ ] **Step 10.3: Sync local main + VPS**

Run:
```bash
git checkout main
git pull origin main
ssh root@72.60.209.109 "cd /root/agentsHQ && git stash push -m pre-poller-pull 2>/dev/null; git pull origin main"
```

- [ ] **Step 10.4: Rebuild orc-crewai with the new code**

Run:
```bash
ssh root@72.60.209.109 "cd /root/agentsHQ && bash scripts/orc_rebuild.sh"
```
Expected: build completes, container restarts, `orc-crewai` reports healthy within 30s.

- [ ] **Step 10.5: Verify C1 (poller catches Notion clicks)**

In Notion, change any active task's Status from `Not Started` to `In Progress`. Wait up to 5 minutes (one heartbeat tick).

Then run:
```bash
ssh root@72.60.209.109 "cd /root/agentsHQ && tail -3 docs/audits/changelog.md"
```
Expected: at least one line of the form:
```
2026-05-XX...Z | T-XXXXX | status | "..." | Not Started -> In Progress
```

If the file doesn't exist or no line appears, check:
```bash
ssh root@72.60.209.109 "docker logs orc-crewai --since 10m | grep -i 'notion_state_poller\|notion-state-poller'"
```

- [ ] **Step 10.6: Verify C2 (poller catches /task add)**

From Telegram, send: `/task add "Spec verification test"`.

Expected within 30 seconds: Telegram reply containing `Added T-26XXX: "Spec verification test"` and a `Top 3:` block.

Then within 5 minutes:
```bash
ssh root@72.60.209.109 "cd /root/agentsHQ && grep 'Spec verification test' docs/audits/changelog.md"
```
Expected: one line of the form:
```
2026-05-XX...Z | T-26XXX | created | "Spec verification test" | Owner=Boubacar Sprint=Backlog Source="Manual: 2026-05-XX"
```

- [ ] **Step 10.7: Verify C3 (failure modes)**

Three subtests from Telegram:

a) Send: `/task add` (no title)
Expected reply: contains `Missing title. Usage: ...`

b) Send: `/task add "Foo" --owner=NotARealOwner`
Expected reply: contains `Owner "NotARealOwner" not found. Valid: Boubacar, Coding, agentsHQ, Decision.`

c) In Notion, edit the `Source` field of any task (NOT tracked by poller). Wait 6 minutes.
Then run:
```bash
ssh root@72.60.209.109 "tail -10 /root/agentsHQ/docs/audits/changelog.md | grep -c '| source |'"
```
Expected: `0` (no line emitted because Source is not in TRACKED_PROPS).

- [ ] **Step 10.8: Verify C4 (lock works)**

Run two ticks back-to-back on VPS:
```bash
ssh root@72.60.209.109 "cd /root/agentsHQ && (docker exec orc-crewai python -m notion_state_poller &) && (docker exec orc-crewai python -m notion_state_poller &); wait"
```
Expected: one tick reports `mode=normal`, the other reports `mode=skipped, reason=lock` (or logs a lock conflict).

If the lock is not held strictly enough (both ticks succeed), check the coordination skill version and `claim()` behavior.

- [ ] **Step 10.9: Update Atlas roadmap**

Modify `docs/roadmap/atlas.md`. Add a new milestone entry near the bottom (above "Descoped Items"):

```markdown
### M15: Notion State Poller + /task add ✅ SHIPPED 2026-05-02

**Closed bidirectional-sync gap.** Notion stays the editing surface; agentsHQ catches up automatically via 5-min poller. Plus one Telegram verb for fast capture.

- `orchestrator/notion_state_poller.py`: 5-min heartbeat tick, queries Notion for rows changed in last 6min, diffs against `data/notion_state_cache.json`, appends to `docs/audits/changelog.md`. 22 unit tests.
- `orchestrator/handlers_commands.py`: `handle_task_add()` for `/task add "<title>" [--owner] [--sprint] [--p0]`. Auto-assigns next T-YYxxxx, single-P0 invariant. 11 unit tests.
- Changelog format locked as public contract. Downstream consumers (3-day past-due digest, daily standup, Golden Gem nudge) deferred to future milestones.

**Spec:** `docs/superpowers/specs/2026-05-02-task-poller-and-add-design.md`
**Plan:** `docs/superpowers/plans/2026-05-02-task-poller-and-add.md`
**Branch:** `feature/task-poller` (merged)
```

Commit:
```bash
git add docs/roadmap/atlas.md
git commit -m "roadmap(atlas): M15 Notion state poller + /task add SHIPPED"
git push origin main
```

- [ ] **Step 10.10: Final 3-way verify**

Run:
```bash
echo "local"; git rev-parse HEAD
echo "github"; git ls-remote origin main | head -1
echo "vps"; ssh root@72.60.209.109 "cd /root/agentsHQ && git rev-parse HEAD"
```
Expected: all three same SHA.

---

## Self-review checklist

Before declaring done:

- [ ] All 22 poller tests + 11 /task add tests passing locally and inside the container
- [ ] `python -m py_compile orchestrator/notion_state_poller.py` clean
- [ ] `python -m py_compile orchestrator/handlers_commands.py` clean
- [ ] C1, C2, C3, C4 all verified against the live VPS
- [ ] No em-dashes in any new file (em-dash hook will block commit otherwise)
- [ ] No `--no-verify` used on any commit
- [ ] `docs/audits/changelog.md` exists, has at least one `system | backfill` line and at least one real event
- [ ] Atlas roadmap updated with M15 SHIPPED entry

---

## Out of scope (deferred per spec section 7)

- All `/task` verbs other than `add` (done, p0, sprint, block, archive, reopen, reassign).
- 3-day past-due Telegram digest (separate work; reads changelog).
- Daily standup / Golden Gem nudge / weekly recap generators.
- Notion webhook subscriber (paid-tier dependency).
- `--due` flag on `/task add`.
- Automated changelog rotation when file >5MB (manual when needed).

Each is a future task with an explicit revisit trigger in the spec.

---

## Cross-references

- **Spec:** `docs/superpowers/specs/2026-05-02-task-poller-and-add-design.md`
- **Notion Tasks DB:** `https://app.notion.com/p/249bcf1a302980739c26c61cad212477`
- **Existing wakes for reference:** `orchestrator/scheduler.py:540-571`
- **Notion helper:** `skills/notion_skill/notion_tool.py` (env var `NOTION_SECRET`)
- **Coordination skill:** `skills/coordination/__init__.py`
- **Prior audit spec/plan:** `docs/superpowers/specs/2026-05-01-notion-task-audit-design.md`, `docs/superpowers/plans/2026-05-01-notion-task-audit.md`
