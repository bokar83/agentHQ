"""Tests for scripts/check_memory_frontmatter.py (Compass M2)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "check_memory_frontmatter.py"


def _run(memory_file: Path) -> tuple[int, str]:
    """Invoke the hook with one path argument; return (exit_code, combined_output)."""
    proc = subprocess.run(
        [sys.executable, str(HOOK), str(memory_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout + proc.stderr


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_passes_on_valid_memory_file(tmp_path: Path) -> None:
    valid = REPO_ROOT / "docs" / "memory" / "feedback_general.md"
    code, out = _run(valid)
    assert code == 0, out


def test_fails_on_missing_frontmatter(tmp_path: Path, monkeypatch) -> None:
    # File must live under docs/memory/ to be checked, so use a temp file inside the repo.
    target = REPO_ROOT / "docs" / "memory" / "_pytest_tmp_no_frontmatter.md"
    _write(target, "no frontmatter here\n")
    try:
        code, out = _run(target)
        assert code == 1
        assert "missing opening '---'" in out
    finally:
        target.unlink(missing_ok=True)


def test_fails_on_missing_type_field(tmp_path: Path) -> None:
    target = REPO_ROOT / "docs" / "memory" / "_pytest_tmp_missing_type.md"
    _write(target, "---\nname: x\ndescription: y\n---\nbody\n")
    try:
        code, out = _run(target)
        assert code == 1
        assert "missing or empty 'type:'" in out
    finally:
        target.unlink(missing_ok=True)


def test_fails_on_invalid_type_value(tmp_path: Path) -> None:
    target = REPO_ROOT / "docs" / "memory" / "_pytest_tmp_bad_type.md"
    _write(
        target,
        "---\nname: x\ndescription: y\ntype: nonsense\n---\nbody\n",
    )
    try:
        code, out = _run(target)
        assert code == 1
        assert "is not one of" in out
    finally:
        target.unlink(missing_ok=True)


def test_skips_memory_index_file(tmp_path: Path) -> None:
    # MEMORY.md has no frontmatter and must NOT be flagged.
    code, out = _run(REPO_ROOT / "docs" / "memory" / "MEMORY.md")
    assert code == 0, out


def test_skips_files_outside_docs_memory(tmp_path: Path) -> None:
    # Ordinary docs/ files (e.g. AGENT_SOP.md) must not be flagged.
    code, out = _run(REPO_ROOT / "docs" / "AGENT_SOP.md")
    assert code == 0, out


def test_passes_when_path_does_not_exist(tmp_path: Path) -> None:
    code, _ = _run(tmp_path / "nonexistent.md")
    assert code == 0
