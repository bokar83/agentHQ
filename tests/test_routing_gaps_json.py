import subprocess, json, sys
from pathlib import Path

REPO = str(Path(__file__).parent.parent)

def test_json_flag_outputs_valid_json():
    """--json must output parseable JSON to stdout."""
    result = subprocess.run(
        [sys.executable, "scripts/check_routing_gaps.py", "--json"],
        capture_output=True, text=True, cwd=REPO
    )
    data = json.loads(result.stdout)
    assert "skills_with_fixtures" in data
    assert "total_skills" in data
    assert "coverage_pct" in data
    assert isinstance(data["skills_with_fixtures"], int)
    assert isinstance(data["total_skills"], int)
    assert isinstance(data["coverage_pct"], float)

def test_json_flag_no_human_text_in_stdout():
    """--json stdout must be pure JSON, no human-readable text mixed in."""
    result = subprocess.run(
        [sys.executable, "scripts/check_routing_gaps.py", "--json"],
        capture_output=True, text=True, cwd=REPO
    )
    # Will raise ValueError/JSONDecodeError if stdout has mixed text
    json.loads(result.stdout)

def test_json_exit_code_zero():
    """--json always exits 0 (coverage data, not pass/fail)."""
    result = subprocess.run(
        [sys.executable, "scripts/check_routing_gaps.py", "--json"],
        capture_output=True, text=True, cwd=REPO
    )
    assert result.returncode == 0
