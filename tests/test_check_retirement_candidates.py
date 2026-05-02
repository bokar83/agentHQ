"""Tests for scripts/check_retirement_candidates.py (Compass M2)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "check_retirement_candidates.py"


def _git(repo: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=env,
    )


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@t.t")
    _git(repo, "config", "user.name", "t")
    (repo / "docs" / "memory").mkdir(parents=True)
    (repo / "scripts").mkdir(exist_ok=True)
    return repo


def _install_hook(repo: Path) -> Path:
    target = repo / "scripts" / "check_retirement_candidates.py"
    shutil.copy(HOOK, target)
    return target


def _commit_at(repo: Path, path: Path, ts: int, message: str) -> None:
    """Commit a file with a fixed committer/author date (Unix timestamp)."""
    _git(repo, "add", str(path))
    env = {
        **os.environ,
        "GIT_AUTHOR_DATE": f"{ts} +0000",
        "GIT_COMMITTER_DATE": f"{ts} +0000",
    }
    _git(repo, "commit", "-q", "-m", message, env=env)


def _run(repo: Path, *cli_args: str) -> tuple[int, str]:
    hook = _install_hook(repo)
    proc = subprocess.run(
        [sys.executable, str(hook), *cli_args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout + proc.stderr


def test_no_candidates_when_recent(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    sop = repo / "docs" / "AGENT_SOP.md"
    sop.write_text("# SOP\nbody\n", encoding="utf-8")
    # Commit "now": GIT_AUTHOR_DATE omitted, so it's the current time.
    _git(repo, "add", str(sop))
    _git(repo, "commit", "-q", "-m", "init")
    code, out = _run(repo, "--days", "90")
    assert code == 0, out
    assert "No retirement candidates" in out


def test_lists_old_files(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    sop = repo / "docs" / "AGENT_SOP.md"
    mem = repo / "docs" / "memory" / "feedback_old.md"
    sop.write_text("# SOP\nbody\n", encoding="utf-8")
    mem.write_text(
        "---\nname: old\ndescription: d\ntype: feedback\n---\nbody\n",
        encoding="utf-8",
    )
    # Commit both ~120 days ago.
    import time
    old_ts = int(time.time()) - 120 * 86400
    _commit_at(repo, sop, old_ts, "old sop")
    _commit_at(repo, mem, old_ts, "old mem")
    code, out = _run(repo, "--days", "90")
    assert code == 0
    assert "AGENT_SOP.md" in out
    assert "feedback_old.md" in out


def test_threshold_filtering(tmp_path: Path) -> None:
    """A 60-day-old file appears at --days 30 but not at --days 90."""
    repo = _make_repo(tmp_path)
    mem = repo / "docs" / "memory" / "feedback_mid.md"
    mem.write_text(
        "---\nname: mid\ndescription: d\ntype: feedback\n---\nbody\n",
        encoding="utf-8",
    )
    import time
    mid_ts = int(time.time()) - 60 * 86400
    _commit_at(repo, mem, mid_ts, "mid commit")

    code_30, out_30 = _run(repo, "--days", "30")
    assert "feedback_mid.md" in out_30, out_30

    code_90, out_90 = _run(repo, "--days", "90")
    assert "feedback_mid.md" not in out_90, out_90


def test_skips_zzz_archive(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    archived = repo / "zzzArchive" / "AGENTS.md"
    archived.parent.mkdir(parents=True)
    archived.write_text("# old\nbody\n", encoding="utf-8")
    import time
    old_ts = int(time.time()) - 200 * 86400
    _commit_at(repo, archived, old_ts, "archive")
    code, out = _run(repo, "--days", "90")
    assert code == 0, out
    assert "zzzArchive" not in out


def test_plain_format(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    sop = repo / "docs" / "AGENT_SOP.md"
    sop.write_text("# SOP\nbody\n", encoding="utf-8")
    import time
    old_ts = int(time.time()) - 120 * 86400
    _commit_at(repo, sop, old_ts, "old")
    code, out = _run(repo, "--days", "90", "--format", "plain")
    assert code == 0
    assert "AGENT_SOP.md" in out
    # Markdown table marker should not appear in plain mode.
    assert "| --- |" not in out
