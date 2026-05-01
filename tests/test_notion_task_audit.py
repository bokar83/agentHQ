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
