"""Tests for scripts/check_rule_redundancy.py (Compass M2)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "check_rule_redundancy.py"


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
    (repo / "docs" / "memory").mkdir(parents=True)
    (repo / "scripts").mkdir(exist_ok=True)
    return repo


def _install_hook(repo: Path) -> Path:
    target = repo / "scripts" / "check_rule_redundancy.py"
    shutil.copy(HOOK, target)
    return target


def _run(repo: Path, *paths: Path, strict: bool = False) -> tuple[int, str]:
    hook = _install_hook(repo)
    rel_paths = [str(p.relative_to(repo)) for p in paths]
    env = {**os.environ}
    if strict:
        env["RULE_REDUNDANCY_STRICT"] = "1"
    proc = subprocess.run(
        [sys.executable, str(hook), *rel_paths],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return proc.returncode, proc.stdout + proc.stderr


def test_passes_on_clean_addition(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    sop = repo / "docs" / "AGENT_SOP.md"
    sop.write_text("# SOP\n\nOriginal sentence one.\n", encoding="utf-8")
    _git(repo, "add", str(sop))
    _git(repo, "commit", "-q", "-m", "init")
    sop.write_text(
        "# SOP\n\nOriginal sentence one.\n\nA brand new rule about coffee that nobody else has written about anywhere in this corpus today.\n",
        encoding="utf-8",
    )
    _git(repo, "add", str(sop))
    code, out = _run(repo, sop)
    assert code == 0, out
    assert "near-duplicate" not in out


def test_warns_on_duplicate_across_files(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    sop = repo / "docs" / "AGENT_SOP.md"
    mem = repo / "docs" / "memory" / "feedback_dup.md"
    sentence = (
        "Never use the word delete; archive to zzzArchive with a manifest entry "
        "documenting the original path and reason."
    )
    sop.write_text(f"---\nname: x\n---\n# SOP\n\n{sentence}\n", encoding="utf-8")
    mem.write_text(
        "---\nname: dup\ndescription: d\ntype: feedback\n---\nbody only\n",
        encoding="utf-8",
    )
    _git(repo, "add", str(sop), str(mem))
    _git(repo, "commit", "-q", "-m", "init")
    # Now stage a near-duplicate in mem.
    mem.write_text(
        "---\nname: dup\ndescription: d\ntype: feedback\n---\n"
        + f"body. {sentence}\n",
        encoding="utf-8",
    )
    _git(repo, "add", str(mem))
    code, out = _run(repo, mem)
    # Default mode is warn-only.
    assert code == 0, out
    assert "near-duplicate" in out
    assert "AGENT_SOP.md" in out


def test_strict_mode_fails(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    sop = repo / "docs" / "AGENT_SOP.md"
    mem = repo / "docs" / "memory" / "feedback_dup.md"
    sentence = (
        "The Boubacar memory rule about archive over delete must always include a manifest "
        "entry showing the original path."
    )
    sop.write_text(f"# SOP\n\n{sentence}\n", encoding="utf-8")
    mem.write_text(
        "---\nname: dup\ndescription: d\ntype: feedback\n---\nbody\n",
        encoding="utf-8",
    )
    _git(repo, "add", str(sop), str(mem))
    _git(repo, "commit", "-q", "-m", "init")
    mem.write_text(
        "---\nname: dup\ndescription: d\ntype: feedback\n---\n" + f"{sentence}\n",
        encoding="utf-8",
    )
    _git(repo, "add", str(mem))
    code, out = _run(repo, mem, strict=True)
    assert code == 1, out
    assert "near-duplicate" in out


def test_skips_short_lines(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    sop = repo / "docs" / "AGENT_SOP.md"
    mem = repo / "docs" / "memory" / "feedback_short.md"
    sop.write_text("# SOP\n\nShort.\n", encoding="utf-8")
    mem.write_text(
        "---\nname: x\ndescription: y\ntype: feedback\n---\nbody\n",
        encoding="utf-8",
    )
    _git(repo, "add", str(sop), str(mem))
    _git(repo, "commit", "-q", "-m", "init")
    mem.write_text(
        "---\nname: x\ndescription: y\ntype: feedback\n---\nbody\nShort.\n",
        encoding="utf-8",
    )
    _git(repo, "add", str(mem))
    code, out = _run(repo, mem)
    assert code == 0, out
    assert "near-duplicate" not in out


def test_skips_non_corpus_files(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    other = repo / "docs" / "some_random.md"
    other.write_text("Some content that nobody cares about for redundancy purposes.\n", encoding="utf-8")
    _git(repo, "add", str(other))
    _git(repo, "commit", "-q", "-m", "init")
    other.write_text(
        "Some content that nobody cares about for redundancy purposes. New very long line "
        "that would surely match itself but the file is not in the corpus so we skip.\n",
        encoding="utf-8",
    )
    _git(repo, "add", str(other))
    code, out = _run(repo, other)
    assert code == 0, out
    assert "near-duplicate" not in out
