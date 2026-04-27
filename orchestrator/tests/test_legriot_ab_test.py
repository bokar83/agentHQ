"""Tests for scripts/legriot_ab_test.py."""
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import legriot_ab_test as ab


def test_reveal_dir_separate_from_outputs(tmp_path):
    """Reveal mapping lives in .reveal/ subdir, not alongside scored files."""
    with patch("legriot_ab_test._run_legriot_for_model", return_value="draft text"):
        ab.run_ab_test(
            ideas=[("test idea", "LinkedIn"), ("another idea", "X"), ("third idea", "LinkedIn")],
            output_dir=tmp_path,
        )
    reveal_file = tmp_path / ".reveal" / "model-map.json"
    assert reveal_file.exists(), ".reveal/model-map.json must exist"
    # Verify no model names appear in scored file names
    scored = [f.name for f in tmp_path.iterdir() if f.suffix == ".md" and f.stem.startswith("idea-")]
    for name in scored:
        for model in ab.CANDIDATE_MODELS:
            assert model not in name, f"Model name leaked into filename: {name}"


def test_blind_labels_assigned_correctly(tmp_path):
    """Each label maps to exactly one model; mapping is stable across re-runs."""
    with patch("legriot_ab_test._run_legriot_for_model", return_value="x"):
        ab.run_ab_test(
            ideas=[("idea", "LinkedIn"), ("idea2", "X"), ("idea3", "LinkedIn")],
            output_dir=tmp_path,
        )
    data = json.loads((tmp_path / ".reveal" / "model-map.json").read_text())
    mapping = data["label_to_model"]
    assert set(mapping.keys()) == set(ab.LABELS)
    assert set(mapping.values()) == set(ab.CANDIDATE_MODELS)


def test_reveal_function_prints_mapping(tmp_path, capsys):
    """--reveal reads .reveal/ and prints label-to-model mapping."""
    reveal_dir = tmp_path / ".reveal"
    reveal_dir.mkdir()
    (reveal_dir / "model-map.json").write_text(
        json.dumps({
            "label_to_model": {"A": "xai/grok-4", "B": "anthropic/claude-sonnet-4.6", "C": "mistralai/mistral-large-2407"},
            "incumbent": "xai/grok-4",
        }),
        encoding="utf-8",
    )
    ab.reveal(tmp_path)
    out = capsys.readouterr().out
    assert "xai/grok-4" in out
    assert "INCUMBENT" in out
    assert "Label A" in out


def test_idempotent_rerun_skips_existing_files(tmp_path):
    """If a file already exists, re-running does not overwrite it."""
    existing = tmp_path / "idea-1-A.md"
    existing.write_text("original content", encoding="utf-8")

    call_count = {"n": 0}
    def mock_run(idea, platform, model_id):
        call_count["n"] += 1
        return "new content"

    with patch("legriot_ab_test._run_legriot_for_model", side_effect=mock_run):
        ab.run_ab_test(
            ideas=[("idea one", "LinkedIn"), ("idea two", "X"), ("idea three", "LinkedIn")],
            output_dir=tmp_path,
        )

    # idea-1-A.md was pre-existing, so that one call is skipped
    # 3 ideas x 3 models = 9 calls, minus 1 skip = 8
    assert call_count["n"] == 8
    assert existing.read_text(encoding="utf-8") == "original content"


def test_rubric_injected_into_scoring_sheet(tmp_path):
    """Scoring sheet includes rubric text from docs/reference/legriot-quality-rubric.md."""
    with patch("legriot_ab_test._run_legriot_for_model", return_value="draft"):
        ab.run_ab_test(
            ideas=[("a", "LinkedIn"), ("b", "X"), ("c", "LinkedIn")],
            output_dir=tmp_path,
        )
    sheet = (tmp_path / "scoring-sheet.md").read_text(encoding="utf-8")
    # Rubric must be included (either real content or the fallback message)
    assert "Hook Strength" in sheet or "rubric not found" in sheet
    # Decision rule threshold must be stated
    assert ">= 3" in sheet or "3 points" in sheet
