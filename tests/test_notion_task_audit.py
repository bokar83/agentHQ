"""Tests for scripts/notion_task_audit.py."""
import subprocess
import sys
import shutil
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "notion_task_audit.py"


@pytest.fixture
def tmp_path():
    base = REPO_ROOT / "pytest_tmp_work"
    base.mkdir(exist_ok=True)
    path = base / f"tmp_{uuid.uuid4().hex}"
    path.mkdir()
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


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


def test_main_dry_run_walk_only(tmp_path, monkeypatch, capsys):
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import notion_task_audit  # noqa: E402
    (tmp_path / "docs/roadmap").mkdir(parents=True)
    (tmp_path / "docs/roadmap/atlas.md").write_text("# atlas")
    monkeypatch.setattr(notion_task_audit, "REPO_ROOT", tmp_path)
    rc = notion_task_audit.main(["--dry-run", "--stages=walk"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "1 feeder" in captured.out or "atlas.md" in captured.out
