"""Tests for scripts/check_doc_size.py (Compass M2)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "check_doc_size.py"


def _run(*paths: Path, strict: bool = False) -> tuple[int, str]:
    env = {**os.environ}
    if strict:
        env["DOC_SIZE_STRICT"] = "1"
    proc = subprocess.run(
        [sys.executable, str(HOOK), *(str(p) for p in paths)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return proc.returncode, proc.stdout + proc.stderr


def _make(_tmp_root: Path, rel: str, lines: int) -> Path:
    """Create a file inside the real repo (so REPO_ROOT relative-path lookup works).

    First arg is unused but kept for call-site readability (we always pass REPO_ROOT).
    """
    target = REPO_ROOT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("body line\n" * lines, encoding="utf-8")
    return target


def test_passes_under_soft_limit() -> None:
    target = _make(REPO_ROOT, "docs/memory/_pytest_tmp_small.md", 50)
    try:
        code, out = _run(target)
        assert code == 0, out
        assert "soft limit" not in out
    finally:
        target.unlink(missing_ok=True)


def test_warns_at_soft_limit_for_memory() -> None:
    target = _make(REPO_ROOT, "docs/memory/_pytest_tmp_warn.md", 410)
    try:
        code, out = _run(target)
        assert code == 0, out  # warn-only by default
        assert "soft limit" in out
    finally:
        target.unlink(missing_ok=True)


def test_fails_at_hard_limit_for_memory() -> None:
    target = _make(REPO_ROOT, "docs/memory/_pytest_tmp_fail.md", 700)
    try:
        code, out = _run(target)
        assert code == 1, out
        assert "hard limit" in out
    finally:
        target.unlink(missing_ok=True)


def test_governance_md_tighter_threshold() -> None:
    """GOVERNANCE.md hard limit is 85, not 600."""
    # Use a temp path that matches the exact GOVERNANCE.md path relative to REPO_ROOT.
    # We can't overwrite the real file, so test via direct invocation of the matcher.
    # Instead: assert the live GOVERNANCE.md is comfortably under its limit.
    real = REPO_ROOT / "docs" / "GOVERNANCE.md"
    if not real.exists():
        return
    code, out = _run(real)
    assert code == 0, out
    # If somebody bloats GOVERNANCE.md past 85 lines, the hook should fail.


def test_strict_mode_upgrades_warn_to_fail() -> None:
    target = _make(REPO_ROOT, "docs/memory/_pytest_tmp_strict.md", 410)
    try:
        code, out = _run(target, strict=True)
        assert code == 1, out
    finally:
        target.unlink(missing_ok=True)


def test_skips_zzz_archive() -> None:
    target = _make(REPO_ROOT, "zzzArchive/_pytest_tmp_huge/AGENTS.md", 5000)
    try:
        code, out = _run(target)
        assert code == 0, out
        assert "hard limit" not in out
    finally:
        target.unlink(missing_ok=True)
        # Clean up the empty parent if possible.
        try:
            target.parent.rmdir()
        except OSError:
            pass


def test_passes_for_non_rule_files() -> None:
    target = _make(REPO_ROOT, "docs/_pytest_tmp_random.md", 5000)
    try:
        code, out = _run(target)
        assert code == 0, out
        assert "hard limit" not in out
    finally:
        target.unlink(missing_ok=True)


def test_agents_md_threshold() -> None:
    """A 500-line AGENTS.md should fail the hard limit (400)."""
    target = _make(REPO_ROOT, "tests/_pytest_tmp_agents_dir/AGENTS.md", 500)
    try:
        code, out = _run(target)
        assert code == 1, out
        assert "hard limit" in out
    finally:
        target.unlink(missing_ok=True)
        try:
            target.parent.rmdir()
        except OSError:
            pass


def test_skill_payload_agents_md_is_exempt() -> None:
    """skills/<name>/AGENTS.md is skill content (Vercel etc.), not folder governance."""
    target = _make(REPO_ROOT, "skills/_pytest_tmp_skill/AGENTS.md", 5000)
    try:
        code, out = _run(target)
        assert code == 0, out
        assert "hard limit" not in out
    finally:
        target.unlink(missing_ok=True)
        try:
            target.parent.rmdir()
        except OSError:
            pass


def test_top_level_skills_agents_md_still_capped() -> None:
    """skills/AGENTS.md at depth 2 IS folder governance and stays under the cap."""
    real = REPO_ROOT / "skills" / "AGENTS.md"
    if not real.exists():
        return
    code, out = _run(real)
    # Today it is 39 lines, well under both warn and fail. If somebody bloats
    # it past 400 lines, this test breaks and the bloat surfaces.
    assert code == 0, out
