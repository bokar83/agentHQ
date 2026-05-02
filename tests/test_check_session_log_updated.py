"""Tests for scripts/check_session_log_updated.py (Compass M2).

These tests use a throwaway git repo so we exercise the staged-diff path the
hook actually relies on.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "check_session_log_updated.py"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@t.t")
    _git(repo, "config", "user.name", "t")
    (repo / "docs" / "roadmap").mkdir(parents=True)
    return repo


def _write_initial_roadmap(repo: Path, name: str = "atlas.md") -> Path:
    body = textwrap.dedent(
        """
        # Atlas

        ## Milestones

        ### M1: First milestone
        Initial body.

        ## Session Log

        ### 2026-04-01: Roadmap created
        First entry.
        """
    ).lstrip()
    p = repo / "docs" / "roadmap" / name
    p.write_text(body, encoding="utf-8")
    _git(repo, "add", str(p))
    _git(repo, "commit", "-q", "-m", "init roadmap")
    return p


def _stage(repo: Path, p: Path, body: str) -> None:
    p.write_text(body, encoding="utf-8")
    _git(repo, "add", str(p))


def _run(repo: Path, *paths: Path) -> tuple[int, str]:
    """Run the hook from inside `repo` so its REPO_ROOT detection sees the temp repo.

    The hook resolves REPO_ROOT relative to its own __file__, so we must copy
    the script into the temp repo's scripts/ folder for the test repo to be
    detected as the root.
    """
    scripts = repo / "scripts"
    scripts.mkdir(exist_ok=True)
    hook_copy = scripts / "check_session_log_updated.py"
    shutil.copy(HOOK, hook_copy)
    rel_paths = [str(p.relative_to(repo)) for p in paths]
    proc = subprocess.run(
        [sys.executable, str(hook_copy), *rel_paths],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout + proc.stderr


def test_passes_when_log_entry_added(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    p = _write_initial_roadmap(repo)
    body = textwrap.dedent(
        """
        # Atlas

        ## Milestones

        ### M1: First milestone
        Body now mentions a new fact.
        ### M2: Second milestone
        Body.

        ## Session Log

        ### 2026-04-01: Roadmap created
        First entry.

        ### 2026-05-02: M2 added
        Logged.
        """
    ).lstrip()
    _stage(repo, p, body)
    code, out = _run(repo, p)
    assert code == 0, out


def test_fails_when_no_dated_entry_added(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    p = _write_initial_roadmap(repo)
    body = textwrap.dedent(
        """
        # Atlas

        ## Milestones

        ### M1: First milestone
        Body changed but no log entry.
        ### M2: Snuck in
        Body.

        ## Session Log

        ### 2026-04-01: Roadmap created
        First entry.
        """
    ).lstrip()
    _stage(repo, p, body)
    code, out = _run(repo, p)
    assert code == 1
    assert "without a new dated Session Log entry" in out


def test_passes_when_only_trivial_lines_changed(tmp_path: Path) -> None:
    """A timestamp bump alone (no real edits) should not require a new log entry."""
    repo = _make_repo(tmp_path)
    p = _write_initial_roadmap(repo)
    # Add only a "Last updated:" line, which is in TRIVIAL_LINE_RE.
    body = textwrap.dedent(
        """
        # Atlas

        *Last updated: 2026-05-02*

        ## Milestones

        ### M1: First milestone
        Initial body.

        ## Session Log

        ### 2026-04-01: Roadmap created
        First entry.
        """
    ).lstrip()
    _stage(repo, p, body)
    code, out = _run(repo, p)
    assert code == 0, out


def test_skips_readme(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    readme = repo / "docs" / "roadmap" / "README.md"
    readme.write_text("# Registry\n", encoding="utf-8")
    _git(repo, "add", str(readme))
    _git(repo, "commit", "-q", "-m", "init readme")
    readme.write_text("# Registry\n\nAdded a line.\n", encoding="utf-8")
    _git(repo, "add", str(readme))
    code, out = _run(repo, readme)
    assert code == 0, out


def test_skips_subfolder_roadmaps(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    sub = repo / "docs" / "roadmap" / "atlas" / "m7a-decision-spike.md"
    sub.parent.mkdir(parents=True)
    sub.write_text("# m7a notes\n", encoding="utf-8")
    _git(repo, "add", str(sub))
    _git(repo, "commit", "-q", "-m", "init sub")
    sub.write_text("# m7a notes\n\nNew content.\n", encoding="utf-8")
    _git(repo, "add", str(sub))
    code, out = _run(repo, sub)
    assert code == 0, out


def test_env_bypass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _make_repo(tmp_path)
    p = _write_initial_roadmap(repo)
    body = "# Atlas\n\nNew body without log entry.\n"
    _stage(repo, p, body)
    monkeypatch.setenv("SKIP_SESSION_LOG", "1")
    # Re-run with env set; subprocess inherits env.
    scripts = repo / "scripts"
    scripts.mkdir(exist_ok=True)
    hook_copy = scripts / "check_session_log_updated.py"
    shutil.copy(HOOK, hook_copy)
    proc = subprocess.run(
        [sys.executable, str(hook_copy), str(p.relative_to(repo))],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env={**os.environ, "SKIP_SESSION_LOG": "1"},
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
