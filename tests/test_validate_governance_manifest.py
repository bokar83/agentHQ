"""Tests for scripts/validate_governance_manifest.py (Compass M4)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "validate_governance_manifest.py"


def _run_against_repo(repo: Path) -> tuple[int, str]:
    """Run the script with REPO_ROOT pointing at `repo`."""
    scripts = repo / "scripts"
    scripts.mkdir(exist_ok=True)
    hook_copy = scripts / "validate_governance_manifest.py"
    shutil.copy(HOOK, hook_copy)
    proc = subprocess.run(
        [sys.executable, str(hook_copy)],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout + proc.stderr


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "docs").mkdir()
    (repo / "scripts").mkdir()
    return repo


def _write_min_governance(repo: Path, rows: int = 2) -> None:
    rows_md = "\n".join(f"| Rule {i} | Source {i} | Hook {i} | Cadence {i} |" for i in range(rows))
    body = (
        "# agentsHQ Governance\n\n"
        "Some prelude.\n\n"
        "## Routing table\n\n"
        "| Rule type | Source of truth | Enforcement | Review cadence |\n"
        "|---|---|---|---|\n"
        f"{rows_md}\n\n"
        "## Conflict resolution\n\n"
        "1. user wins.\n"
    )
    (repo / "docs" / "GOVERNANCE.md").write_text(body, encoding="utf-8")


def _write_min_manifest(repo: Path, rule_count: int = 2, hook_paths: list[str] | None = None) -> None:
    hook_paths = hook_paths or []
    manifest = {
        "version": "1.0.0",
        "rule_types": [
            {
                "name": f"rule_{i}",
                "source_of_truth": "docs/GOVERNANCE.md",
                "enforcement": ["manual"],
            }
            for i in range(rule_count)
        ],
        "conflict_resolution": [{"precedence": 1, "rule": "user"}],
        "retirement_protocol": {"principle": "x"},
        "enforcement_hooks": {
            "pre_commit": [
                {"id": f"h{i}", "script": p, "scope": "x", "mode": "hard-fail"}
                for i, p in enumerate(hook_paths)
            ]
        },
    }
    (repo / "docs" / "governance.manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


def test_passes_on_synced_state(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    _write_min_governance(repo, rows=2)
    _write_min_manifest(repo, rule_count=2)
    code, out = _run_against_repo(repo)
    assert code == 0, out
    assert "OK" in out


def test_fails_on_row_count_mismatch(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    _write_min_governance(repo, rows=3)
    _write_min_manifest(repo, rule_count=2)
    code, out = _run_against_repo(repo)
    assert code == 1, out
    assert "routing-table drift" in out


def test_fails_on_missing_hook_script(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    _write_min_governance(repo, rows=1)
    _write_min_manifest(
        repo, rule_count=1, hook_paths=["scripts/does_not_exist.py"]
    )
    code, out = _run_against_repo(repo)
    assert code == 1, out
    assert "missing script" in out


def test_fails_on_missing_required_keys(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    _write_min_governance(repo, rows=1)
    bad = {
        "version": "1.0.0",
        "rule_types": [{"name": "x"}],  # missing source_of_truth + enforcement
        "conflict_resolution": [],
        "retirement_protocol": {},
        "enforcement_hooks": {"pre_commit": []},
    }
    (repo / "docs" / "governance.manifest.json").write_text(
        json.dumps(bad), encoding="utf-8"
    )
    code, out = _run_against_repo(repo)
    assert code == 1, out
    assert "missing key" in out


def test_fails_on_invalid_json(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    _write_min_governance(repo, rows=1)
    (repo / "docs" / "governance.manifest.json").write_text("{ not json", encoding="utf-8")
    code, out = _run_against_repo(repo)
    assert code == 1, out
    assert "not valid JSON" in out


def test_fails_when_files_missing(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    code, out = _run_against_repo(repo)
    assert code == 1, out


def test_real_repo_manifest_validates() -> None:
    """The real shipped manifest must validate against the real GOVERNANCE.md."""
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
