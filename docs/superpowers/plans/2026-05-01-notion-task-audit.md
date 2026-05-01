# Notion Task Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `scripts/notion_task_audit.py` that walks 176 markdown files, extracts atomic tasks via Claude Haiku, classifies each (Live / Shipped / Archived / Golden Gem / Needs review), and upserts the Live + Shipped + Gems to the Notion Tasks DB with one P0 row at the top. Output also includes three audit markdown files.

**Architecture:** Single-file Python script, ~300 lines. Reuses existing `skills/notion_skill/notion_tool.py` helpers. Calls OpenRouter for Haiku LLM extraction + classification. Idempotent (safe to re-run via `--mode=sweep`). Read-only on feeders, write-only on Notion + audit files.

**Tech Stack:** Python 3.11, `httpx` (already in deps), `pytest`, `python-frontmatter` (likely already installed; falls back to manual parse if not), Notion API v2022-06-28, OpenRouter for `anthropic/claude-haiku-4-5`.

**Spec:** `docs/superpowers/specs/2026-05-01-notion-task-audit-design.md`

---

## File Structure

| File | Responsibility | Status |
|------|----------------|--------|
| `scripts/notion_task_audit.py` | The harvester: CLI, walk, extract, classify, dedupe, upsert | Create |
| `tests/test_notion_task_audit.py` | Unit tests for pure functions (parsing, classification rules, dedupe, P0 selection) | Create |
| `scripts/notion_task_audit/__init__.py` | NOT created. Single-file script keeps decomposition flat. | n/a |
| `docs/audits/2026-05-01-archived.md` | Output: archived items | Created at runtime |
| `docs/audits/2026-05-01-needs-review.md` | Output: ambiguous items | Created at runtime |
| `docs/audits/2026-05-01-summary.md` | Output: counts + P0 + Gems | Created at runtime |
| `docs/audits/2026-05-01-p0-decision.md` | Output: only if user overrides P0 | Created on demand |

**Decomposition rationale:** the harvester has six logical phases (walk, extract, classify, dedupe, upsert, write-files). Each phase is a pure function (or near-pure) so each gets its own pytest unit test. The CLI glue is the only impure section. Single file because (a) the script is run, not imported, and (b) splitting into 6 modules creates an installable Python package that nothing imports.

---

## Required reads before coding

- `docs/superpowers/specs/2026-05-01-notion-task-audit-design.md` (the full spec)
- `skills/notion_skill/notion_tool.py` (existing Notion helpers, env var is `NOTION_SECRET`)
- `orchestrator/tools.py:1526-1601` (existing `NotionQueryTasksTool`, sample task-row parser)
- `scripts/bootstrap_ideas_db.py` (existing pattern for one-shot Notion population scripts)

---

## Pre-flight: Environment + save point

### Task 0: Confirm environment

**Files:**
- Read: `d:/Ai_Sandbox/agentsHQ/.env`

- [ ] **Step 0.1: Confirm required env vars exist**

Run: `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('NOTION_SECRET ok' if os.environ.get('NOTION_SECRET') else 'MISSING'); print('OPENROUTER_API_KEY ok' if os.environ.get('OPENROUTER_API_KEY') else 'MISSING'); print('NOTION_TASK_DB_ID', os.environ.get('NOTION_TASK_DB_ID', '249bcf1a302980739c26c61cad212477'))"`

Expected: all three print "ok" or a value, none print "MISSING".

If `NOTION_SECRET` is missing, stop and ask Boubacar. If `OPENROUTER_API_KEY` is missing, stop and ask. If only `NOTION_TASK_DB_ID` is missing, that's fine because the hardcoded fallback `249bcf1a302980739c26c61cad212477` is correct.

- [ ] **Step 0.2: Create save-point tag**

Run:
```bash
git tag savepoint-pre-task-audit-2026-05-01
git push origin savepoint-pre-task-audit-2026-05-01
```

Expected: tag created, pushed to origin.

- [ ] **Step 0.3: Create `docs/audits/` directory**

Run: `mkdir -p docs/audits/`

Expected: directory exists.

---

## Task 1: Skeleton CLI + dry-run flag

**Files:**
- Create: `scripts/notion_task_audit.py`
- Create: `tests/test_notion_task_audit.py`

### Task 1: CLI skeleton

- [ ] **Step 1.1: Write the failing test**

Add to `tests/test_notion_task_audit.py`:
```python
"""Tests for scripts/notion_task_audit.py."""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "notion_task_audit.py"


def test_script_help_runs():
    """Script must run with --help and exit 0."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, result.stderr
    assert "--dry-run" in result.stdout
    assert "--stages" in result.stdout
    assert "--mode" in result.stdout
```

- [ ] **Step 1.2: Run test to verify it fails**

Run: `pytest tests/test_notion_task_audit.py::test_script_help_runs -v`
Expected: FAIL with "No such file or directory" or similar.

- [ ] **Step 1.3: Write the script skeleton**

Create `scripts/notion_task_audit.py`:
```python
"""Notion Task Audit harvester.

Walks markdown feeders, extracts atomic tasks, classifies each, upserts to Notion.

Usage:
    python scripts/notion_task_audit.py --dry-run
    python scripts/notion_task_audit.py
    python scripts/notion_task_audit.py --mode=sweep --window=14d

See docs/superpowers/specs/2026-05-01-notion-task-audit-design.md for the design.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_NOTION_TASK_DB_ID = "249bcf1a302980739c26c61cad212477"
DEFAULT_LLM_MODEL = "anthropic/claude-haiku-4-5"
HARD_LLM_CALL_CAP = 200
HARD_LIVE_ROW_CAP = 200


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Notion Task Audit harvester")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write to Notion or audit files; print what would happen.",
    )
    parser.add_argument(
        "--stages",
        default="all",
        help="Comma-separated stages to run: walk,extract,classify,dedupe,upsert,write. Default: all.",
    )
    parser.add_argument(
        "--mode",
        choices=["full", "sweep"],
        default="full",
        help="full = full archaeology pass. sweep = bi-monthly maintenance over a recent window.",
    )
    parser.add_argument(
        "--window",
        default="14d",
        help="For --mode=sweep, only include feeders modified within this window. Default 14d.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(f"notion_task_audit: mode={args.mode} stages={args.stages} dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 1.4: Run test to verify it passes**

Run: `pytest tests/test_notion_task_audit.py::test_script_help_runs -v`
Expected: PASS.

- [ ] **Step 1.5: Commit**

```bash
git add scripts/notion_task_audit.py tests/test_notion_task_audit.py
git commit -m "feat(audit): notion task audit harvester skeleton"
```

---

## Task 2: Schema migration helper (add Source + Completion Criteria fields)

**Files:**
- Modify: `scripts/notion_task_audit.py`
- Modify: `tests/test_notion_task_audit.py`

### Task 2: Schema migration

- [ ] **Step 2.1: Write the failing test**

Append to `tests/test_notion_task_audit.py`:
```python
from unittest.mock import patch, MagicMock


def test_ensure_schema_adds_missing_fields(monkeypatch):
    """ensure_schema must PATCH the database with the two new fields if missing."""
    monkeypatch.setenv("NOTION_SECRET", "fake-token")

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    fake_existing = {
        "properties": {
            "Task": {"type": "title"},
            "Status": {"type": "select"},
        }
    }

    captured = {}

    def fake_get(url, headers, timeout):
        m = MagicMock()
        m.status_code = 200
        m.json.return_value = fake_existing
        m.raise_for_status = lambda: None
        return m

    def fake_patch(url, headers, json, timeout):
        captured["url"] = url
        captured["json"] = json
        m = MagicMock()
        m.status_code = 200
        m.raise_for_status = lambda: None
        return m

    with patch("notion_task_audit.httpx.get", side_effect=fake_get), \
         patch("notion_task_audit.httpx.patch", side_effect=fake_patch):
        notion_task_audit.ensure_schema("dbid")

    assert "Source" in captured["json"]["properties"]
    assert "Completion Criteria" in captured["json"]["properties"]
    assert captured["json"]["properties"]["Source"] == {"rich_text": {}}
    assert captured["json"]["properties"]["Completion Criteria"] == {"rich_text": {}}


def test_ensure_schema_skips_when_present(monkeypatch):
    """When both fields already exist, ensure_schema must NOT PATCH."""
    monkeypatch.setenv("NOTION_SECRET", "fake-token")

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    fake_existing = {
        "properties": {
            "Task": {"type": "title"},
            "Source": {"type": "rich_text"},
            "Completion Criteria": {"type": "rich_text"},
        }
    }
    patched_called = {"yes": False}

    def fake_get(url, headers, timeout):
        m = MagicMock()
        m.json.return_value = fake_existing
        m.raise_for_status = lambda: None
        return m

    def fake_patch(*a, **kw):
        patched_called["yes"] = True
        m = MagicMock()
        m.raise_for_status = lambda: None
        return m

    with patch("notion_task_audit.httpx.get", side_effect=fake_get), \
         patch("notion_task_audit.httpx.patch", side_effect=fake_patch):
        notion_task_audit.ensure_schema("dbid")

    assert patched_called["yes"] is False
```

- [ ] **Step 2.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: both `test_ensure_schema_*` fail with `AttributeError: module 'notion_task_audit' has no attribute 'ensure_schema'`.

- [ ] **Step 2.3: Add `ensure_schema` to the script**

Add to `scripts/notion_task_audit.py` (after the constants block):
```python
import httpx
import os

NOTION_VERSION = "2022-06-28"


def _notion_headers() -> dict:
    token = os.environ.get("NOTION_SECRET")
    if not token:
        raise RuntimeError("NOTION_SECRET not in environment.")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def ensure_schema(database_id: str) -> dict:
    """Add Source + Completion Criteria fields to the Tasks DB if missing.

    Idempotent: if both already exist, returns without writing.
    Returns the final list of property names.
    """
    headers = _notion_headers()
    r = httpx.get(
        f"https://api.notion.com/v1/databases/{database_id}",
        headers=headers,
        timeout=15,
    )
    r.raise_for_status()
    existing = r.json()
    props = existing.get("properties", {})

    needed = {}
    if "Source" not in props:
        needed["Source"] = {"rich_text": {}}
    if "Completion Criteria" not in props:
        needed["Completion Criteria"] = {"rich_text": {}}

    if not needed:
        return {"unchanged": True, "properties": list(props.keys())}

    patch_body = {"properties": needed}
    r = httpx.patch(
        f"https://api.notion.com/v1/databases/{database_id}",
        headers=headers,
        json=patch_body,
        timeout=15,
    )
    r.raise_for_status()
    return {"unchanged": False, "added": list(needed.keys())}
```

- [ ] **Step 2.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: all 3 tests PASS.

- [ ] **Step 2.5: Commit**

```bash
git add scripts/notion_task_audit.py tests/test_notion_task_audit.py
git commit -m "feat(audit): ensure_schema adds Source + Completion Criteria fields"
```

---

## Task 3: Walk feeders (Stage 1 part A)

**Files:**
- Modify: `scripts/notion_task_audit.py`
- Modify: `tests/test_notion_task_audit.py`

### Task 3: Source file walker

- [ ] **Step 3.1: Write the failing test**

Append to `tests/test_notion_task_audit.py`:
```python
def test_walk_feeders_returns_expected_files(tmp_path, monkeypatch):
    """walk_feeders must return all .md files from the feeder directories."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    # Build a fake repo
    (tmp_path / "docs/roadmap").mkdir(parents=True)
    (tmp_path / "docs/roadmap/atlas.md").write_text("# atlas")
    (tmp_path / "docs/roadmap/harvest.md").write_text("# harvest")
    (tmp_path / "docs/superpowers/plans").mkdir(parents=True)
    (tmp_path / "docs/superpowers/plans/2026-04-25-plan.md").write_text("# plan")
    (tmp_path / "docs/superpowers/specs").mkdir(parents=True)
    (tmp_path / "docs/superpowers/specs/2026-04-25-spec.md").write_text("# spec")
    (tmp_path / "docs/handoff").mkdir(parents=True)
    (tmp_path / "docs/handoff/2026-04-25-handoff.md").write_text("# handoff")
    # Should NOT be picked up
    (tmp_path / "docs/handoff/session-handoff.md").write_text("legacy")
    (tmp_path / "docs/some-other-dir").mkdir()
    (tmp_path / "docs/some-other-dir/x.md").write_text("# x")

    files = notion_task_audit.walk_feeders(tmp_path)
    paths = sorted(str(f.relative_to(tmp_path)).replace("\\", "/") for f in files)

    assert "docs/roadmap/atlas.md" in paths
    assert "docs/roadmap/harvest.md" in paths
    assert "docs/superpowers/plans/2026-04-25-plan.md" in paths
    assert "docs/superpowers/specs/2026-04-25-spec.md" in paths
    assert "docs/handoff/2026-04-25-handoff.md" in paths
    # session-handoff.md IS included (legacy is part of corpus)
    assert "docs/handoff/session-handoff.md" in paths
    # Out-of-scope dirs not included
    assert "docs/some-other-dir/x.md" not in paths


def test_walk_feeders_sweep_window(tmp_path, monkeypatch):
    """In sweep mode, only files modified within window are returned."""
    import time
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    (tmp_path / "docs/roadmap").mkdir(parents=True)
    fresh = tmp_path / "docs/roadmap/fresh.md"
    fresh.write_text("# fresh")
    stale = tmp_path / "docs/roadmap/stale.md"
    stale.write_text("# stale")
    # Make stale appear 30 days old
    stale_ts = time.time() - 30 * 86400
    os_utime = __import__("os").utime
    os_utime(stale, (stale_ts, stale_ts))

    files_full = notion_task_audit.walk_feeders(tmp_path, mode="full")
    files_sweep = notion_task_audit.walk_feeders(tmp_path, mode="sweep", window_days=14)

    full_names = {f.name for f in files_full}
    sweep_names = {f.name for f in files_sweep}
    assert {"fresh.md", "stale.md"} <= full_names
    assert "fresh.md" in sweep_names
    assert "stale.md" not in sweep_names
```

- [ ] **Step 3.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: 2 new tests FAIL with `AttributeError: ... walk_feeders`.

- [ ] **Step 3.3: Add `walk_feeders`**

Add to `scripts/notion_task_audit.py`:
```python
import time as _time

FEEDER_GLOBS = (
    "docs/roadmap/*.md",
    "docs/superpowers/plans/*.md",
    "docs/superpowers/specs/*.md",
    "docs/handoff/*.md",
)


def walk_feeders(repo_root: Path, mode: str = "full", window_days: int = 14) -> list[Path]:
    """Return list of feeder markdown files.

    mode='full': all files matching FEEDER_GLOBS.
    mode='sweep': only files modified within window_days.
    """
    out: list[Path] = []
    cutoff = _time.time() - (window_days * 86400) if mode == "sweep" else None
    for pattern in FEEDER_GLOBS:
        for path in sorted((repo_root).glob(pattern)):
            if cutoff is not None:
                if path.stat().st_mtime < cutoff:
                    continue
            out.append(path)
    return out
```

- [ ] **Step 3.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: all PASS.

- [ ] **Step 3.5: Commit**

```bash
git add scripts/notion_task_audit.py tests/test_notion_task_audit.py
git commit -m "feat(audit): walk_feeders enumerates source markdown files"
```

---

## Task 4: Section extraction (Stage 1 part B)

**Files:**
- Modify: `scripts/notion_task_audit.py`
- Modify: `tests/test_notion_task_audit.py`

### Task 4: Extract milestone-or-block units from each file

- [ ] **Step 4.1: Write the failing test**

Append:
```python
def test_extract_units_finds_roadmap_milestones(tmp_path):
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    sample = tmp_path / "harvest.md"
    sample.write_text(
        """# Harvest

### R1: First Signal Works contract

**Status:** In progress.

**Actions:**
- Follow up on inbox replies
- Close at $500 setup.

### R2: SaaS Audit offer ✅ SHIPPED 2026-04-29

What it is: a one-page PDF.
""",
        encoding="utf-8",
    )

    units = notion_task_audit.extract_units(sample)
    titles = [u["title"] for u in units]
    assert "R1: First Signal Works contract" in titles
    assert "R2: SaaS Audit offer ✅ SHIPPED 2026-04-29" in titles

    r2 = next(u for u in units if u["title"].startswith("R2"))
    assert r2["status_marker"] in {"SHIPPED", "shipped"}
    assert "PDF" in r2["body"]
    assert r2["source_path"].endswith("harvest.md")


def test_extract_units_handoff_next_section(tmp_path):
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    sample = tmp_path / "2026-05-01-handoff.md"
    sample.write_text(
        """# Handoff

Some prose.

## Next

- Finish hook page for Rod
- Push to Vercel
""",
        encoding="utf-8",
    )

    units = notion_task_audit.extract_units(sample)
    next_unit = [u for u in units if u["title"].lower() == "next"]
    assert len(next_unit) == 1
    assert "hook page" in next_unit[0]["body"].lower()
```

- [ ] **Step 4.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: 2 FAIL with `AttributeError: extract_units`.

- [ ] **Step 4.3: Add `extract_units`**

Add to `scripts/notion_task_audit.py`:
```python
import re

_HEADER_RE = re.compile(r"^(#{2,4})\s+(.+?)\s*$")
_SHIPPED_RE = re.compile(r"\b(SHIPPED|DONE|shipped|✅)\b")
_INPROGRESS_RE = re.compile(r"\b(IN PROGRESS|QUEUED|NOT STARTED|IN FLIGHT|🟡|⏳)\b", re.IGNORECASE)


def extract_units(path: Path) -> list[dict]:
    """Split a markdown file into milestone-or-block units.

    A unit is a heading (## / ### / ####) plus the body text up to the next
    same-or-higher-level heading. Each unit gets a 'status_marker' if a
    recognized marker appears in the heading or first 30 lines of body.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    units: list[dict] = []
    current: dict | None = None

    for idx, line in enumerate(lines):
        m = _HEADER_RE.match(line)
        if m:
            if current is not None:
                units.append(current)
            current = {
                "title": m.group(2).strip(),
                "level": len(m.group(1)),
                "body": "",
                "line_no": idx + 1,
                "status_marker": "",
                "source_path": str(path),
            }
            continue
        if current is not None:
            current["body"] += line + "\n"

    if current is not None:
        units.append(current)

    # Tag each unit with a status marker
    for u in units:
        head = u["title"]
        body_head = u["body"][:2000]
        if _SHIPPED_RE.search(head) or _SHIPPED_RE.search(body_head):
            u["status_marker"] = "SHIPPED"
        elif _INPROGRESS_RE.search(head) or _INPROGRESS_RE.search(body_head):
            u["status_marker"] = "IN_PROGRESS"

    return units
```

- [ ] **Step 4.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: all PASS.

- [ ] **Step 4.5: Commit**

```bash
git add scripts/notion_task_audit.py tests/test_notion_task_audit.py
git commit -m "feat(audit): extract_units splits feeders into milestone blocks"
```

---

## Task 5: LLM extraction of atomic tasks (Stage 2)

**Files:**
- Modify: `scripts/notion_task_audit.py`
- Modify: `tests/test_notion_task_audit.py`

### Task 5: Atomic task extraction via Haiku

- [ ] **Step 5.1: Write the failing test**

Append:
```python
def test_extract_tasks_from_unit_calls_llm(monkeypatch):
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")

    unit = {
        "title": "M3: Reconciliation Polling",
        "level": 3,
        "body": "Twice daily, query LinkedIn for posts.",
        "line_no": 100,
        "status_marker": "IN_PROGRESS",
        "source_path": "docs/roadmap/atlas.md",
    }

    fake_response = {
        "choices": [
            {
                "message": {
                    "content": (
                        '[{"title":"Add LinkedIn polling cron",'
                        '"completion_criteria":"Cron fires every 12h and writes one row per matched post.",'
                        '"estimated_hours":2,"source_section":"M3: Reconciliation Polling"}]'
                    )
                }
            }
        ]
    }

    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["json"] = json
        m = MagicMock()
        m.json.return_value = fake_response
        m.raise_for_status = lambda: None
        m.status_code = 200
        return m

    with patch("notion_task_audit.httpx.post", side_effect=fake_post):
        tasks = notion_task_audit.extract_tasks_from_unit(unit)

    assert len(tasks) == 1
    assert tasks[0]["title"] == "Add LinkedIn polling cron"
    assert tasks[0]["estimated_hours"] == 2
    assert tasks[0]["source_path"].endswith("atlas.md")
    assert "M3" in tasks[0]["source_section"]
    assert "openrouter.ai" in captured["url"]


def test_extract_tasks_from_unit_handles_empty_response(monkeypatch):
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")
    unit = {
        "title": "Status Snapshot",
        "level": 2,
        "body": "Just a status block.",
        "line_no": 30,
        "status_marker": "",
        "source_path": "docs/roadmap/atlas.md",
    }
    fake_response = {"choices": [{"message": {"content": "[]"}}]}

    def fake_post(url, headers, json, timeout):
        m = MagicMock()
        m.json.return_value = fake_response
        m.raise_for_status = lambda: None
        return m

    with patch("notion_task_audit.httpx.post", side_effect=fake_post):
        tasks = notion_task_audit.extract_tasks_from_unit(unit)

    assert tasks == []
```

- [ ] **Step 5.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: 2 FAIL with `AttributeError: extract_tasks_from_unit`.

- [ ] **Step 5.3: Add `extract_tasks_from_unit`**

Add to `scripts/notion_task_audit.py`:
```python
import json as _json

EXTRACT_PROMPT = """\
Given this milestone or block from a markdown doc, extract atomic tasks.

A task is action-verb-led work bite of <= 8 hours, OR <= 10% of the parent
milestone's expected duration, whichever is smaller. Anything bigger gets
split.

Return a JSON ARRAY (no prose) of objects with these keys:
- title: action verb first, no fluff (e.g. "Add LinkedIn polling cron")
- completion_criteria: one sentence, verifiable. It must be obvious whether
  the task is done by comparing output with the criterion.
- estimated_hours: number (1, 2, 4, 8 max)
- source_section: the heading where this came from

Special rules:
- If the milestone is already shipped (you'll see SHIPPED, ✅, DONE markers),
  return one task per shipped sub-deliverable, with completion_criteria
  starting "Already shipped: ".
- If the block has no actionable work (just a status snapshot, table of
  contents, etc.), return [].
- If the block describes a future milestone with a trigger date in the future,
  return tasks but mark estimated_hours conservatively.

UNIT TITLE: {title}
STATUS MARKER: {status_marker}
SOURCE: {source_path}

BODY:
{body}

Return only the JSON array. No prose.
"""


def extract_tasks_from_unit(unit: dict, model: str = DEFAULT_LLM_MODEL) -> list[dict]:
    """Call OpenRouter Haiku to extract atomic tasks from a unit. Returns list."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not in environment.")

    body_truncated = unit["body"][:6000]
    prompt = EXTRACT_PROMPT.format(
        title=unit["title"],
        status_marker=unit.get("status_marker", ""),
        source_path=unit["source_path"],
        body=body_truncated,
    )

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    r = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"].strip()

    # Tolerate code-fence wrapping
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:].lstrip()
        # Remove trailing fence
        content = content.rsplit("```", 1)[0].strip() if "```" in content else content

    try:
        raw = _json.loads(content) if content else []
    except _json.JSONDecodeError:
        return []

    if not isinstance(raw, list):
        return []

    tasks: list[dict] = []
    for entry in raw:
        if not isinstance(entry, dict) or not entry.get("title"):
            continue
        tasks.append({
            "title": entry["title"].strip(),
            "completion_criteria": entry.get("completion_criteria", "").strip(),
            "estimated_hours": entry.get("estimated_hours", 0),
            "source_section": entry.get("source_section", unit["title"]),
            "source_path": unit["source_path"],
            "source_status_marker": unit.get("status_marker", ""),
        })
    return tasks
```

- [ ] **Step 5.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: all PASS.

- [ ] **Step 5.5: Commit**

```bash
git add scripts/notion_task_audit.py tests/test_notion_task_audit.py
git commit -m "feat(audit): extract_tasks_from_unit calls OpenRouter Haiku"
```

---

## Task 6: Classification (Stage 3)

**Files:**
- Modify: `scripts/notion_task_audit.py`
- Modify: `tests/test_notion_task_audit.py`

### Task 6: Disposition rules

- [ ] **Step 6.1: Write the failing tests**

Append:
```python
def test_classify_shipped_marker():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    task = {
        "title": "Implemented foo",
        "completion_criteria": "Already shipped: foo deployed.",
        "estimated_hours": 2,
        "source_section": "M2",
        "source_path": "docs/roadmap/atlas.md",
        "source_status_marker": "SHIPPED",
    }
    d = notion_task_audit.classify_task(task, file_mtime_days_ago=5)
    assert d["disposition"] == "Shipped"


def test_classify_inprogress_marker():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    task = {
        "title": "Add polling cron",
        "completion_criteria": "Cron fires every 12h.",
        "estimated_hours": 2,
        "source_section": "M3",
        "source_path": "docs/roadmap/atlas.md",
        "source_status_marker": "IN_PROGRESS",
    }
    d = notion_task_audit.classify_task(task, file_mtime_days_ago=5)
    assert d["disposition"] == "Live"


def test_classify_archived_when_old_no_status():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    task = {
        "title": "Old plan idea",
        "completion_criteria": "",
        "estimated_hours": 4,
        "source_section": "Section",
        "source_path": "docs/superpowers/plans/2026-03-30-old.md",
        "source_status_marker": "",
    }
    d = notion_task_audit.classify_task(task, file_mtime_days_ago=70)
    assert d["disposition"] == "Archived"


def test_classify_needs_review_when_ambiguous():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    task = {
        "title": "Maybe do thing",
        "completion_criteria": "",
        "estimated_hours": 0,
        "source_section": "Misc",
        "source_path": "docs/superpowers/plans/2026-04-20-vague.md",
        "source_status_marker": "",
    }
    d = notion_task_audit.classify_task(task, file_mtime_days_ago=15)
    assert d["disposition"] in {"Live", "NeedsReview"}
```

- [ ] **Step 6.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: 4 FAIL.

- [ ] **Step 6.3: Add `classify_task`**

Add to `scripts/notion_task_audit.py`:
```python
def classify_task(task: dict, file_mtime_days_ago: int) -> dict:
    """Apply Section 5.1 classification rules. Returns task with 'disposition' set.

    Disposition is one of: Shipped, Live, Archived, GoldenGem, NeedsReview.
    GoldenGem is only set later by gem_check_task() (second LLM pass).
    """
    marker = (task.get("source_status_marker") or "").upper()
    crit = (task.get("completion_criteria") or "").lower()

    if marker == "SHIPPED" or "already shipped" in crit:
        return {**task, "disposition": "Shipped"}

    if marker == "IN_PROGRESS":
        return {**task, "disposition": "Live"}

    # No status marker: check age
    if file_mtime_days_ago >= 60:
        return {**task, "disposition": "Archived"}

    # Recent file, no status marker, no completion criterion: review
    if not task.get("completion_criteria") and task.get("estimated_hours", 0) == 0:
        return {**task, "disposition": "NeedsReview"}

    return {**task, "disposition": "Live"}
```

- [ ] **Step 6.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: all PASS.

- [ ] **Step 6.5: Commit**

```bash
git add scripts/notion_task_audit.py tests/test_notion_task_audit.py
git commit -m "feat(audit): classify_task applies disposition rules"
```

---

## Task 7: Golden Gem second-pass classifier

**Files:**
- Modify: `scripts/notion_task_audit.py`
- Modify: `tests/test_notion_task_audit.py`

### Task 7: Gem check via second LLM pass

- [ ] **Step 7.1: Write the failing test**

Append:
```python
def test_gem_check_returns_gem(monkeypatch):
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")
    task = {
        "title": "Multi-channel publisher",
        "completion_criteria": "Publishes to YouTube + LinkedIn from one queue.",
        "estimated_hours": 8,
        "source_section": "Phase 4",
        "source_path": "docs/superpowers/plans/2026-03-30-publisher.md",
        "source_status_marker": "",
        "disposition": "Live",
    }
    fake = {
        "choices": [
            {"message": {"content": '{"verdict":"gem","reason":"Better than current single-platform"}'}}
        ]
    }

    def fake_post(url, headers, json, timeout):
        m = MagicMock()
        m.json.return_value = fake
        m.raise_for_status = lambda: None
        return m

    with patch("notion_task_audit.httpx.post", side_effect=fake_post):
        out = notion_task_audit.gem_check_task(task)

    assert out["disposition"] == "GoldenGem"
    assert "Better than" in out["gem_reason"]


def test_gem_check_returns_archive(monkeypatch):
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")
    task = {
        "title": "Old defunct idea",
        "completion_criteria": "",
        "estimated_hours": 2,
        "source_section": "n/a",
        "source_path": "docs/superpowers/plans/2026-03-30-old.md",
        "source_status_marker": "",
        "disposition": "Live",
    }
    fake = {
        "choices": [
            {"message": {"content": '{"verdict":"archive","reason":"Superseded by current"}'}}
        ]
    }

    def fake_post(url, headers, json, timeout):
        m = MagicMock()
        m.json.return_value = fake
        m.raise_for_status = lambda: None
        return m

    with patch("notion_task_audit.httpx.post", side_effect=fake_post):
        out = notion_task_audit.gem_check_task(task)

    assert out["disposition"] == "Archived"
    assert "Superseded" in out["gem_reason"]
```

- [ ] **Step 7.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: 2 FAIL.

- [ ] **Step 7.3: Add `gem_check_task`**

Add to `scripts/notion_task_audit.py`:
```python
GEM_PROMPT = """\
Given this task and source context, decide:
- Is this idea still sound, or stale/superseded?
- If sound, is there any chance it is *better than or complementary to*
  current active work?

Return ONLY one JSON object (no prose) with two keys:
- verdict: one of "live" | "gem" | "archive"
  - "live"   : sound, fits in active work as-is
  - "gem"    : sound AND possibly better than current approach (worth a fresh look)
  - "archive": stale, superseded, or no longer relevant
- reason: one sentence (max 25 words) explaining the verdict.

TASK TITLE: {title}
COMPLETION CRITERION: {completion_criteria}
SOURCE: {source_path}
SOURCE SECTION: {source_section}
SOURCE STATUS: {source_status_marker}
"""


def gem_check_task(task: dict, model: str = DEFAULT_LLM_MODEL) -> dict:
    """Run second LLM pass to flag Golden Gems vs archive vs keep-as-Live."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not in environment.")

    prompt = GEM_PROMPT.format(
        title=task["title"],
        completion_criteria=task.get("completion_criteria", ""),
        source_path=task["source_path"],
        source_section=task.get("source_section", ""),
        source_status_marker=task.get("source_status_marker", ""),
    )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    r = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:].lstrip()
        if "```" in content:
            content = content.rsplit("```", 1)[0].strip()
    try:
        obj = _json.loads(content) if content else {}
    except _json.JSONDecodeError:
        obj = {}

    verdict = obj.get("verdict", "live").lower()
    reason = obj.get("reason", "")

    if verdict == "gem":
        return {**task, "disposition": "GoldenGem", "gem_reason": reason}
    if verdict == "archive":
        return {**task, "disposition": "Archived", "gem_reason": reason}
    return {**task, "disposition": "Live", "gem_reason": reason}
```

- [ ] **Step 7.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: all PASS.

- [ ] **Step 7.5: Commit**

```bash
git add scripts/notion_task_audit.py tests/test_notion_task_audit.py
git commit -m "feat(audit): gem_check_task second-pass classifier"
```

---

## Task 8: Dedupe (Stage 4)

**Files:**
- Modify: `scripts/notion_task_audit.py`
- Modify: `tests/test_notion_task_audit.py`

### Task 8: Title-normalized dedupe

- [ ] **Step 8.1: Write the failing test**

Append:
```python
def test_dedupe_collapses_same_title_keeps_newest():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    older = {
        "title": "Build hook page for Rod",
        "completion_criteria": "Hook live.",
        "source_path": "docs/superpowers/plans/2026-04-25-old.md",
        "source_mtime": 1000,
        "disposition": "Live",
    }
    newer = {
        "title": "Build hook page for Rod!",  # same after normalize
        "completion_criteria": "Hook live on Vercel.",
        "source_path": "docs/handoff/2026-05-01-handoff.md",
        "source_mtime": 2000,
        "disposition": "Live",
    }
    third = {
        "title": "Different task",
        "completion_criteria": "n/a",
        "source_path": "docs/roadmap/atlas.md",
        "source_mtime": 1500,
        "disposition": "Live",
    }
    out = notion_task_audit.dedupe([older, newer, third])

    assert len(out) == 2
    rod = next(t for t in out if t["title"].startswith("Build hook"))
    # Kept the newer one's text (latest source mtime wins)
    assert "Vercel" in rod["completion_criteria"]
    # Source aggregates both paths
    assert "2026-04-25-old.md" in rod["source_path"]
    assert "2026-05-01-handoff.md" in rod["source_path"]


def test_normalize_title_strips_dates_punct():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    n = notion_task_audit._normalize_title
    assert n("Ship Rod hook (2026-05-01)") == n("ship rod hook!")
    assert n("M3: foo") == n("M3 foo")
```

- [ ] **Step 8.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: 2 FAIL.

- [ ] **Step 8.3: Add `dedupe` and `_normalize_title`**

Add to `scripts/notion_task_audit.py`:
```python
_DATE_RE = re.compile(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b")
_PUNCT_RE = re.compile(r"[^\w\s]")


def _normalize_title(title: str) -> str:
    s = _DATE_RE.sub("", title or "")
    s = _PUNCT_RE.sub(" ", s)
    s = " ".join(s.lower().split())
    return s


def dedupe(tasks: list[dict]) -> list[dict]:
    """Group tasks by normalized title. Keep the newest by source_mtime.

    The kept entry's source_path is updated to a semicolon-joined string
    of every original source_path that mapped to the same normalized title.
    """
    groups: dict[str, list[dict]] = {}
    for t in tasks:
        key = _normalize_title(t.get("title", ""))
        groups.setdefault(key, []).append(t)

    out: list[dict] = []
    for _, members in groups.items():
        members_sorted = sorted(
            members,
            key=lambda m: m.get("source_mtime", 0),
            reverse=True,
        )
        winner = dict(members_sorted[0])
        all_paths = []
        for m in members_sorted:
            p = m.get("source_path", "")
            if p and p not in all_paths:
                all_paths.append(p)
        winner["source_path"] = "; ".join(all_paths)
        out.append(winner)
    return out
```

- [ ] **Step 8.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: all PASS.

- [ ] **Step 8.5: Commit**

```bash
git add scripts/notion_task_audit.py tests/test_notion_task_audit.py
git commit -m "feat(audit): dedupe groups by normalized title, keeps newest"
```

---

## Task 9: P0 dictator selection

**Files:**
- Modify: `scripts/notion_task_audit.py`
- Modify: `tests/test_notion_task_audit.py`

### Task 9: P0 selection rule

- [ ] **Step 9.1: Write the failing tests**

Append:
```python
def test_pick_p0_revenue_due_within_7d():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    from datetime import date, timedelta
    today = date(2026, 5, 1)

    live = [
        {"title": "A revenue task soon",
         "category": "Revenue",
         "due_date": (today + timedelta(days=3)).isoformat(),
         "priority": "Medium",
         "source_path": "docs/roadmap/harvest.md",
         "disposition": "Live"},
        {"title": "A revenue task farther",
         "category": "Revenue",
         "due_date": (today + timedelta(days=20)).isoformat(),
         "priority": "High",
         "source_path": "docs/roadmap/harvest.md",
         "disposition": "Live"},
        {"title": "A high build task",
         "category": "Build",
         "due_date": (today + timedelta(days=1)).isoformat(),
         "priority": "High",
         "source_path": "docs/roadmap/atlas.md",
         "disposition": "Live"},
    ]
    p0 = notion_task_audit.pick_p0(live, today=today)
    assert p0["title"] == "A revenue task soon"


def test_pick_p0_falls_through_to_high_priority_when_no_revenue():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    from datetime import date, timedelta
    today = date(2026, 5, 1)

    live = [
        {"title": "Build task soon",
         "category": "Build",
         "due_date": (today + timedelta(days=2)).isoformat(),
         "priority": "High",
         "source_path": "docs/roadmap/atlas.md",
         "disposition": "Live"},
        {"title": "Health task low",
         "category": "Health",
         "due_date": (today + timedelta(days=1)).isoformat(),
         "priority": "Low",
         "source_path": "docs/roadmap/atlas.md",
         "disposition": "Live"},
    ]
    p0 = notion_task_audit.pick_p0(live, today=today)
    assert p0["title"] == "Build task soon"


def test_pick_p0_returns_none_when_empty():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    from datetime import date
    assert notion_task_audit.pick_p0([], today=date(2026, 5, 1)) is None
```

- [ ] **Step 9.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: 3 FAIL.

- [ ] **Step 9.3: Add `pick_p0`**

Add to `scripts/notion_task_audit.py`:
```python
from datetime import date, timedelta

_ROADMAP_PRIORITY = {"harvest.md": 0, "atlas.md": 1, "studio.md": 2, "echo.md": 3}


def _due_within(task: dict, today: date, days: int) -> bool:
    raw = task.get("due_date")
    if not raw:
        return False
    try:
        d = date.fromisoformat(raw)
    except ValueError:
        return False
    return today <= d <= today + timedelta(days=days)


def _roadmap_rank(task: dict) -> int:
    src = task.get("source_path", "")
    for name, rank in _ROADMAP_PRIORITY.items():
        if name in src:
            return rank
    return 99


def pick_p0(live_tasks: list[dict], today: date | None = None) -> dict | None:
    """Pick exactly one P0 from Live tasks. See spec section 5.2 for rule."""
    today = today or date.today()
    if not live_tasks:
        return None

    only_live = [t for t in live_tasks if t.get("disposition") == "Live"]
    if not only_live:
        return None

    # Rule 1: Revenue + due within 7d, soonest first
    rule1 = [t for t in only_live if t.get("category") == "Revenue" and _due_within(t, today, 7)]
    if rule1:
        return min(rule1, key=lambda t: t.get("due_date", "9999-99-99"))

    # Rule 2: source roadmap rank, then highest revenue impact
    rule2 = sorted(only_live, key=lambda t: (_roadmap_rank(t), t.get("due_date", "9999-99-99")))
    # Only apply rule 2 if any task is in a roadmap source (rank < 99)
    if rule2 and _roadmap_rank(rule2[0]) < 99:
        return rule2[0]

    # Rule 3: soonest-due High priority
    rule3 = [t for t in only_live if t.get("priority") == "High"]
    if rule3:
        return min(rule3, key=lambda t: t.get("due_date", "9999-99-99"))

    # Rule 4: anything with NN2: Revenue Movement, soonest due
    rule4 = [t for t in only_live if "NN2" in (t.get("non_negotiables") or "")]
    if rule4:
        return min(rule4, key=lambda t: t.get("due_date", "9999-99-99"))

    # Fallback: first live task by due date
    return min(only_live, key=lambda t: t.get("due_date", "9999-99-99"))
```

- [ ] **Step 9.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: all PASS.

- [ ] **Step 9.5: Commit**

```bash
git add scripts/notion_task_audit.py tests/test_notion_task_audit.py
git commit -m "feat(audit): pick_p0 implements 4-rule priority dictator"
```

---

## Task 10: Notion upsert (Stage 5 part A)

**Files:**
- Modify: `scripts/notion_task_audit.py`
- Modify: `tests/test_notion_task_audit.py`

### Task 10: Idempotent upsert by title

- [ ] **Step 10.1: Write the failing test**

Append:
```python
def test_upsert_creates_new_when_not_exists(monkeypatch):
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    monkeypatch.setenv("NOTION_SECRET", "fake")

    task = {
        "title": "New task",
        "completion_criteria": "It works.",
        "source_path": "docs/roadmap/atlas.md",
        "disposition": "Live",
        "category": "Build",
        "priority": "High",
        "is_p0": False,
    }
    posts = []

    def fake_post(url, headers, json, timeout):
        posts.append((url, json))
        m = MagicMock()
        m.json.return_value = {"id": "new-page-id", "results": []}
        m.raise_for_status = lambda: None
        return m

    with patch("notion_task_audit.httpx.post", side_effect=fake_post):
        action = notion_task_audit.upsert_task("dbid", task)

    assert action == "created"
    # First post = query, second = create
    assert any("/query" in url for url, _ in posts)
    assert any("/pages" in url and "/query" not in url for url, _ in posts)


def test_upsert_skips_when_exists_and_done(monkeypatch):
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    monkeypatch.setenv("NOTION_SECRET", "fake")

    task = {
        "title": "Done task",
        "completion_criteria": "n/a",
        "source_path": "docs/roadmap/atlas.md",
        "disposition": "Shipped",
        "is_p0": False,
    }

    existing = {
        "results": [
            {
                "id": "existing-id",
                "properties": {
                    "Status": {"select": {"name": "Done"}},
                    "Task": {"title": [{"plain_text": "Done task"}]},
                },
            }
        ]
    }

    def fake_post(url, headers, json, timeout):
        m = MagicMock()
        m.json.return_value = existing if "/query" in url else {}
        m.raise_for_status = lambda: None
        return m

    patches_called = {"yes": False}

    def fake_patch(*a, **kw):
        patches_called["yes"] = True
        m = MagicMock()
        m.raise_for_status = lambda: None
        return m

    with patch("notion_task_audit.httpx.post", side_effect=fake_post), \
         patch("notion_task_audit.httpx.patch", side_effect=fake_patch):
        action = notion_task_audit.upsert_task("dbid", task)

    assert action == "skipped"
    assert patches_called["yes"] is False
```

- [ ] **Step 10.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: 2 FAIL.

- [ ] **Step 10.3: Add `upsert_task` and helpers**

Add to `scripts/notion_task_audit.py`:
```python
DISPOSITION_TO_STATUS = {
    "Live": "Not Started",
    "Shipped": "Done",
    "GoldenGem": "Not Started",
}


def _build_notion_props(task: dict) -> dict:
    """Build a Notion properties payload for create or update."""
    props: dict = {}
    title = task["title"]
    notes = task.get("notes", "")
    if task.get("disposition") == "GoldenGem":
        gem_reason = task.get("gem_reason", "")
        notes = f"🔍 GOLDEN GEM: {gem_reason} {notes}".strip()

    props["Task"] = {"title": [{"text": {"content": title}}]}
    status = DISPOSITION_TO_STATUS.get(task.get("disposition", "Live"), "Not Started")
    props["Status"] = {"select": {"name": status}}

    if task.get("category"):
        props["Category"] = {"select": {"name": task["category"]}}
    if task.get("priority"):
        props["Priority"] = {"select": {"name": task["priority"]}}
    if task.get("source_path"):
        props["Source"] = {"rich_text": [{"text": {"content": task["source_path"][:1900]}}]}
    if task.get("completion_criteria"):
        props["Completion Criteria"] = {
            "rich_text": [{"text": {"content": task["completion_criteria"][:1900]}}]
        }
    if notes:
        props["Notes"] = {"rich_text": [{"text": {"content": notes[:1900]}}]}
    if task.get("disposition") == "Shipped":
        outcome = f"shipped {task.get('shipped_date', '2026-05-01')}"
        props["Outcome"] = {"rich_text": [{"text": {"content": outcome}}]}
    if task.get("is_p0"):
        props["P0"] = {"checkbox": True}
    # Owner default
    props["Owner"] = {"multi_select": [{"name": "Boubacar"}]}
    return props


def _query_existing(database_id: str, title: str) -> dict | None:
    """Find a row by exact title match. Returns the page object or None."""
    headers = _notion_headers()
    payload = {
        "filter": {
            "property": "Task",
            "title": {"equals": title},
        },
        "page_size": 5,
    }
    r = httpx.post(
        f"https://api.notion.com/v1/databases/{database_id}/query",
        headers=headers,
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0] if results else None


def upsert_task(database_id: str, task: dict) -> str:
    """Create or update a Notion page for this task.

    Returns one of: 'created', 'updated', 'skipped'.
    Skipped when the existing row is already Done and our task is Shipped or
    not-an-update.
    """
    existing = _query_existing(database_id, task["title"])
    headers = _notion_headers()
    props = _build_notion_props(task)

    if existing is None:
        payload = {"parent": {"database_id": database_id}, "properties": props}
        r = httpx.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=payload,
            timeout=30,
        )
        r.raise_for_status()
        return "created"

    # Existing row: skip if Status==Done already
    existing_status = ""
    sel = existing.get("properties", {}).get("Status", {}).get("select")
    if sel:
        existing_status = sel.get("name", "")
    if existing_status == "Done":
        return "skipped"

    # Update Source + Completion Criteria + Notes only; do NOT stomp Status
    update_props = {
        k: v for k, v in props.items()
        if k in {"Source", "Completion Criteria", "Notes", "P0"}
    }
    page_id = existing["id"]
    r = httpx.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=headers,
        json={"properties": update_props},
        timeout=30,
    )
    r.raise_for_status()
    return "updated"
```

- [ ] **Step 10.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: all PASS.

- [ ] **Step 10.5: Commit**

```bash
git add scripts/notion_task_audit.py tests/test_notion_task_audit.py
git commit -m "feat(audit): upsert_task with idempotent title-match logic"
```

---

## Task 11: Audit file writers (Stage 5 part B)

**Files:**
- Modify: `scripts/notion_task_audit.py`
- Modify: `tests/test_notion_task_audit.py`

### Task 11: Three audit markdown writers

- [ ] **Step 11.1: Write the failing tests**

Append:
```python
def test_write_archived_md(tmp_path):
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    archived = [
        {
            "title": "Old idea",
            "source_path": "docs/superpowers/plans/2026-03-30-old.md",
            "completion_criteria": "n/a",
            "gem_reason": "Superseded.",
        }
    ]
    out = tmp_path / "2026-05-01-archived.md"
    notion_task_audit.write_archived_md(out, archived, run_date="2026-05-01")
    text = out.read_text(encoding="utf-8")
    assert "Old idea" in text
    assert "2026-03-30-old.md" in text
    assert "Superseded" in text


def test_write_summary_md(tmp_path):
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    summary = {
        "live": 30,
        "shipped": 40,
        "gems": 5,
        "archived": 70,
        "needs_review": 10,
        "p0": {"title": "Convert Rod (followup window)", "source_path": "docs/roadmap/harvest.md"},
        "gems_list": [
            {"title": "Multi-channel publisher", "source_path": "docs/superpowers/plans/2026-03-30-publisher.md", "gem_reason": "Better than current"}
        ],
    }
    out = tmp_path / "2026-05-01-summary.md"
    notion_task_audit.write_summary_md(out, summary, run_date="2026-05-01")
    text = out.read_text(encoding="utf-8")
    assert "Live: 30" in text
    assert "Shipped: 40" in text
    assert "Convert Rod" in text
    assert "Multi-channel publisher" in text


def test_write_needs_review_md(tmp_path):
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    items = [
        {"title": "Maybe", "source_path": "docs/superpowers/plans/2026-04-20-vague.md", "completion_criteria": ""}
    ]
    out = tmp_path / "2026-05-01-needs-review.md"
    notion_task_audit.write_needs_review_md(out, items, run_date="2026-05-01")
    text = out.read_text(encoding="utf-8")
    assert "Maybe" in text
    assert "2026-04-20-vague.md" in text
```

- [ ] **Step 11.2: Run tests to verify they fail**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: 3 FAIL.

- [ ] **Step 11.3: Add the three writer functions**

Add to `scripts/notion_task_audit.py`:
```python
def write_archived_md(path: Path, archived: list[dict], run_date: str) -> None:
    lines = [
        f"# Archived items, audit {run_date}",
        "",
        "| Title | Source | Why archived |",
        "| --- | --- | --- |",
    ]
    for t in archived:
        title = t.get("title", "").replace("|", "\\|")
        src = t.get("source_path", "").replace("|", "\\|")
        why = (t.get("gem_reason") or "Old, no status, untouched > 60 days").replace("|", "\\|")
        lines.append(f"| {title} | {src} | {why} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_needs_review_md(path: Path, items: list[dict], run_date: str) -> None:
    lines = [
        f"# Needs review, audit {run_date}",
        "",
        "Items the classifier could not place confidently. Decide row by row.",
        "",
        "| Title | Source | Completion criterion (if any) |",
        "| --- | --- | --- |",
    ]
    for t in items:
        title = t.get("title", "").replace("|", "\\|")
        src = t.get("source_path", "").replace("|", "\\|")
        crit = (t.get("completion_criteria") or "").replace("|", "\\|")
        lines.append(f"| {title} | {src} | {crit} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary_md(path: Path, summary: dict, run_date: str) -> None:
    p0 = summary.get("p0") or {}
    lines = [
        f"# Audit summary, {run_date}",
        "",
        "## Counts",
        "",
        f"- Live: {summary.get('live', 0)}",
        f"- Shipped: {summary.get('shipped', 0)}",
        f"- Golden Gems: {summary.get('gems', 0)}",
        f"- Archived: {summary.get('archived', 0)}",
        f"- Needs review: {summary.get('needs_review', 0)}",
        "",
        "## P0 (the dictator at the top of the board)",
        "",
        f"**{p0.get('title', '(none)')}** ",
        f"Source: {p0.get('source_path', '')}",
        "",
        "## Golden Gems",
        "",
    ]
    for g in summary.get("gems_list", []):
        lines.append(f"- **{g.get('title', '')}** ({g.get('source_path', '')}): {g.get('gem_reason', '')}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
```

- [ ] **Step 11.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: all PASS.

- [ ] **Step 11.5: Commit**

```bash
git add scripts/notion_task_audit.py tests/test_notion_task_audit.py
git commit -m "feat(audit): three audit markdown writers"
```

---

## Task 12: Wire `main()` end-to-end + dry-run + cost cap

**Files:**
- Modify: `scripts/notion_task_audit.py`
- Modify: `tests/test_notion_task_audit.py`

### Task 12: Glue everything together

- [ ] **Step 12.1: Write the failing test**

Append:
```python
def test_main_dry_run_walk_only(tmp_path, monkeypatch, capsys):
    """`main` with --dry-run --stages=walk must print file count and not call LLM or Notion."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402

    # Build a fake repo
    (tmp_path / "docs/roadmap").mkdir(parents=True)
    (tmp_path / "docs/roadmap/atlas.md").write_text("# atlas")
    monkeypatch.setattr(notion_task_audit, "REPO_ROOT", tmp_path)

    rc = notion_task_audit.main(["--dry-run", "--stages=walk"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "atlas.md" in captured.out or "1 feeder" in captured.out
```

- [ ] **Step 12.2: Run test to verify it fails**

Run: `pytest tests/test_notion_task_audit.py::test_main_dry_run_walk_only -v`
Expected: FAIL.

- [ ] **Step 12.3: Wire `main()`**

Replace the existing `main()` in `scripts/notion_task_audit.py`:
```python
def _stages_from_arg(arg: str) -> set[str]:
    if arg == "all":
        return {"walk", "extract", "classify", "dedupe", "upsert", "write"}
    return {s.strip() for s in arg.split(",") if s.strip()}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    stages = _stages_from_arg(args.stages)
    repo = REPO_ROOT
    db_id = os.environ.get("NOTION_TASK_DB_ID", DEFAULT_NOTION_TASK_DB_ID)
    audits_dir = repo / "docs" / "audits"
    audits_dir.mkdir(parents=True, exist_ok=True)
    run_date = "2026-05-01"

    print(f"notion_task_audit: mode={args.mode} stages={sorted(stages)} dry_run={args.dry_run}")

    # WALK
    files = walk_feeders(
        repo,
        mode=args.mode,
        window_days=int(args.window.rstrip("d")) if args.window.endswith("d") else 14,
    )
    print(f"  walk: {len(files)} feeder files")
    if "extract" not in stages:
        return 0

    # EXTRACT
    units: list[dict] = []
    for f in files:
        units.extend(extract_units(f))
    print(f"  extract: {len(units)} units")

    if args.dry_run:
        # Cap LLM in dry-run to avoid burning budget
        units = units[:5]
        print(f"  dry-run: capped to {len(units)} units")

    tasks: list[dict] = []
    llm_calls = 0
    for u in units:
        if llm_calls >= HARD_LLM_CALL_CAP:
            print(f"  [STOP] LLM call cap {HARD_LLM_CALL_CAP} reached.")
            break
        try:
            extracted = extract_tasks_from_unit(u)
            llm_calls += 1
        except Exception as e:
            print(f"  extract error on {u['source_path']}: {e}")
            continue
        # Attach mtime
        try:
            mtime = (repo / u["source_path"]).stat().st_mtime if isinstance(u["source_path"], str) else 0
        except Exception:
            mtime = 0
        for t in extracted:
            t["source_mtime"] = mtime
            tasks.append(t)
    print(f"  tasks extracted: {len(tasks)} (llm calls: {llm_calls})")

    if "classify" not in stages:
        return 0

    # CLASSIFY
    classified: list[dict] = []
    today_ts = _time.time()
    for t in tasks:
        try:
            mtime_days = int((today_ts - t.get("source_mtime", today_ts)) / 86400)
        except Exception:
            mtime_days = 0
        ct = classify_task(t, file_mtime_days_ago=mtime_days)
        classified.append(ct)

    # Gem check on Live + old (> 21d)
    gem_candidates = [t for t in classified if t["disposition"] == "Live" and (today_ts - t.get("source_mtime", today_ts)) > 21 * 86400]
    final: list[dict] = []
    for t in classified:
        if t in gem_candidates and llm_calls < HARD_LLM_CALL_CAP:
            try:
                t = gem_check_task(t)
                llm_calls += 1
            except Exception as e:
                print(f"  gem error on {t['title']}: {e}")
        final.append(t)
    print(f"  classified: live={sum(1 for t in final if t['disposition']=='Live')} "
          f"shipped={sum(1 for t in final if t['disposition']=='Shipped')} "
          f"gems={sum(1 for t in final if t['disposition']=='GoldenGem')} "
          f"archived={sum(1 for t in final if t['disposition']=='Archived')} "
          f"needs_review={sum(1 for t in final if t['disposition']=='NeedsReview')}")

    if "dedupe" not in stages:
        return 0

    # DEDUPE
    deduped = dedupe(final)
    print(f"  deduped: {len(deduped)}")

    # Hard cap on Live
    live_only = [t for t in deduped if t["disposition"] == "Live"]
    if len(live_only) > HARD_LIVE_ROW_CAP:
        print(f"  [STOP] live row count {len(live_only)} > cap {HARD_LIVE_ROW_CAP}. Re-scope per spec.")
        return 2

    # P0
    today = date.today()
    p0 = pick_p0(live_only, today=today)
    if p0 is not None:
        for t in deduped:
            if t["title"] == p0["title"] and t["source_path"] == p0["source_path"]:
                t["is_p0"] = True

    if "upsert" not in stages:
        if args.dry_run:
            print(f"  [DRY] would upsert {len([t for t in deduped if t['disposition'] in {'Live','Shipped','GoldenGem'}])} tasks")
            print(f"  [DRY] P0 candidate: {p0['title'] if p0 else '(none)'}")
            return 0
        return 0

    # UPSERT
    if not args.dry_run:
        ensure_schema(db_id)
        actions = {"created": 0, "updated": 0, "skipped": 0}
        for t in deduped:
            if t["disposition"] not in {"Live", "Shipped", "GoldenGem"}:
                continue
            try:
                a = upsert_task(db_id, t)
                actions[a] = actions.get(a, 0) + 1
            except Exception as e:
                print(f"  upsert error on {t['title']}: {e}")
        print(f"  upsert: {actions}")
    else:
        print(f"  [DRY] would call upsert for {sum(1 for t in deduped if t['disposition'] in {'Live','Shipped','GoldenGem'})} tasks")
        print(f"  [DRY] P0 candidate: {p0['title'] if p0 else '(none)'}")

    if "write" not in stages:
        return 0

    # WRITE FILES
    archived = [t for t in deduped if t["disposition"] == "Archived"]
    needs = [t for t in deduped if t["disposition"] == "NeedsReview"]
    gems = [t for t in deduped if t["disposition"] == "GoldenGem"]
    summary = {
        "live": sum(1 for t in deduped if t["disposition"] == "Live"),
        "shipped": sum(1 for t in deduped if t["disposition"] == "Shipped"),
        "gems": len(gems),
        "archived": len(archived),
        "needs_review": len(needs),
        "p0": p0,
        "gems_list": gems,
    }
    if not args.dry_run:
        write_archived_md(audits_dir / f"{run_date}-archived.md", archived, run_date)
        write_needs_review_md(audits_dir / f"{run_date}-needs-review.md", needs, run_date)
        write_summary_md(audits_dir / f"{run_date}-summary.md", summary, run_date)
        print(f"  wrote 3 audit files in {audits_dir}")
    else:
        print(f"  [DRY] would write 3 audit files in {audits_dir}")
        print(f"  [DRY] summary: {summary['live']} live / {summary['shipped']} shipped / "
              f"{summary['gems']} gems / {summary['archived']} archived / {summary['needs_review']} review")

    return 0
```

- [ ] **Step 12.4: Run tests to verify they pass**

Run: `pytest tests/test_notion_task_audit.py -v`
Expected: all PASS.

- [ ] **Step 12.5: Commit**

```bash
git add scripts/notion_task_audit.py tests/test_notion_task_audit.py
git commit -m "feat(audit): wire main() end-to-end with stage gates and caps"
```

---

## Task 13: Schema migration (live, run once)

**Files:** none

### Task 13: Apply schema to Notion Tasks DB

- [ ] **Step 13.1: Run schema migration**

Run:
```bash
python -c "
from dotenv import load_dotenv
load_dotenv()
import sys
sys.path.insert(0, 'scripts')
import notion_task_audit
print(notion_task_audit.ensure_schema('249bcf1a302980739c26c61cad212477'))
"
```

Expected: prints either `{'unchanged': True, 'properties': [...]}` or `{'unchanged': False, 'added': ['Source', 'Completion Criteria']}`.

- [ ] **Step 13.2: Verify in Notion UI**

Open https://app.notion.com/p/249bcf1a302980739c26c61cad212477. Check that the `Source` and `Completion Criteria` properties exist.

If they don't exist, the migration silently failed. Re-run with explicit error printing.

---

## Task 14: Stage 1+2 dry-run + eyeball

**Files:** none (verification only)

### Task 14: Walk + extract dry-run

- [ ] **Step 14.1: Run dry-run for walk + extract**

Run:
```bash
python scripts/notion_task_audit.py --dry-run --stages=walk,extract
```

Expected output: `walk: ~175 feeder files`, `extract: ~500-800 units`, `tasks extracted: ~5-15` (capped to 5 units in dry-run).

- [ ] **Step 14.2: Eyeball extracted milestones**

Read the "tasks extracted" list. Verify:
- At least one task originates from `docs/roadmap/atlas.md`
- At least one from `docs/roadmap/harvest.md`
- Each task has a non-empty title and completion_criteria

If any roadmap is missing from the source paths, the walk regex needs tuning. Stop and fix `extract_units` regex before continuing.

---

## Task 15: Stage 3 dry-run + eyeball

- [ ] **Step 15.1: Run dry-run with classify**

Run:
```bash
python scripts/notion_task_audit.py --dry-run --stages=walk,extract,classify
```

Expected: prints classified counts.

- [ ] **Step 15.2: Spot-check 5 classifications**

For 5 randomly sampled tasks from the output, verify:
- A task tagged `SHIPPED` in roadmap correctly classifies as Shipped (e.g., M1, M2, M7a, M7b)
- A task in `harvest.md` R1a-v3 (in flight) correctly classifies as Live
- A task from a >60d-old plan with no status correctly classifies as Archived

If any spot-check fails, fix `classify_task` and re-run.

---

## Task 16: Full dry-run + eyeball P0

- [ ] **Step 16.1: Run full dry-run**

Run:
```bash
python scripts/notion_task_audit.py --dry-run
```

Expected: prints summary including `[DRY] P0 candidate: <title>`.

- [ ] **Step 16.2: Eyeball P0 choice**

Verify the P0 candidate is the single most important revenue or autonomy task today. If not, stop and either:
- Adjust the `pick_p0` rule, OR
- Note the override; the user will manually flip P0 after live run, then we log to `2026-05-01-p0-decision.md`.

---

## Task 17: LIVE RUN

- [ ] **Step 17.1: Remove the dry-run cap and run for real**

Run:
```bash
python scripts/notion_task_audit.py
```

Expected: prints summary, writes 3 audit files, upserts to Notion. Live row count must be < 200 (or script halts with code 2).

- [ ] **Step 17.2: Manual filter update in Notion UI**

Open https://app.notion.com/p/249bcf1a302980739c26c61cad212477. Open `Active Tasks` view. Add filter:
- Property: `Notes`
- Condition: `does not start with`
- Value: `🔍`

Save view.

- [ ] **Step 17.3: Commit audit files**

```bash
git add docs/audits/
git commit -m "audit(2026-05-01): full archaeology pass output"
```

---

## Task 18: Verification of success criteria

- [ ] **Step 18.1: Verify C1 (P0 dictator)**

Open `Active Tasks` view in Notion. Confirm:
- Exactly ONE row has `P0 = true` (sort by P0 descending to see).
- The P0 row reads as the single most important revenue or autonomy task right now.

If wrong, ask user to name correct P0. Edit row in Notion. Write reason to `docs/audits/2026-05-01-p0-decision.md`. Commit.

- [ ] **Step 18.2: Verify C2 (Source field populated)**

Run via `query_database` filter:
```bash
python -c "
from dotenv import load_dotenv
load_dotenv()
import sys, json
sys.path.insert(0, 'skills')
from notion_skill.notion_tool import query_database
rows = query_database(
  '249bcf1a302980739c26c61cad212477',
  filter_body={'and': [
    {'property': 'Status', 'select': {'does_not_equal': 'Done'}},
    {'property': 'Source', 'rich_text': {'is_empty': True}},
  ]}
)
print(f'rows missing Source: {len(rows)}')
for r in rows[:5]:
    title = r['properties'].get('Task', {}).get('title', [])
    name = title[0]['plain_text'] if title else '?'
    print(f'  - {name}')
"
```

Expected: `rows missing Source: 0`. Any non-zero count = bug. The legacy 25 rows from 2026-04-05 will likely show up here. They go through `2026-05-01-needs-review.md`.

- [ ] **Step 18.3: Verify C3 (audit files exist + readable)**

Run:
```bash
ls docs/audits/
cat docs/audits/2026-05-01-summary.md | head -30
wc -l docs/audits/*.md
```

Expected: 3 files (summary, archived, needs-review), summary readable in <5 min, each entry has title + source + 1-line rationale.

- [ ] **Step 18.4: Final commit + push**

```bash
git add docs/audits/
git commit -m "audit(2026-05-01): verification + p0 decision log" --allow-empty
git push origin main
```

---

## Self-review checklist

Before declaring done:

- [ ] All 12 unit-test tasks passing
- [ ] Schema migration applied to live Notion DB (Task 13)
- [ ] Three dry-runs eyeballed (Tasks 14, 15, 16)
- [ ] Live run completed without halt (Task 17)
- [ ] Manual filter update applied in Notion UI (Task 17.2)
- [ ] C1, C2, C3 all verified (Task 18)
- [ ] All audit markdown files committed
- [ ] No em-dashes in any new file (em-dash hook will block commit if violated)
- [ ] No bare `print` statements that leak secrets (the `_notion_headers` token is never printed)

---

## Out of scope (explicitly NOT in this plan, per spec section 12)

- No bidirectional sync (Notion to roadmap docs)
- No automatic roadmap edits
- No CrewAI integration
- No scheduled cron or heartbeat
- No new Notion saved views (only filter on existing `Active Tasks` view)
- No `AGENT_SOP.md` edit (forward-going contract deferred)
- No `Disposition` field (Karpathy: dropped)
- No task predecessor/successor relations

---

## Cross-references

- **Spec:** `docs/superpowers/specs/2026-05-01-notion-task-audit-design.md`
- **Notion Tasks DB:** https://app.notion.com/p/249bcf1a302980739c26c61cad212477
- **Existing helpers reused:** `skills/notion_skill/notion_tool.py` (env var `NOTION_SECRET`)
- **Sample task-row parser:** `orchestrator/tools.py:1529-1601` (`NotionQueryTasksTool`)
- **Bootstrap precedent:** `scripts/bootstrap_ideas_db.py`
- **Save-point tag:** `savepoint-pre-task-audit-2026-05-01`
