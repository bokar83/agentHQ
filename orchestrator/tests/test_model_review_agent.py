"""Tests for model_review_agent.py."""
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

ORCH_DIR = Path(__file__).resolve().parents[1]
if str(ORCH_DIR) not in sys.path:
    sys.path.insert(0, str(ORCH_DIR))

import model_review_agent as mra


def test_rubric_loaded_from_file_not_hardcoded(tmp_path):
    """Rubric text must come from RUBRIC_PATH at runtime, not be embedded in code."""
    sentinel = "SENTINEL_RUBRIC_TEXT_12345"
    fake_rubric = tmp_path / "rubric.md"
    fake_rubric.write_text(sentinel, encoding="utf-8")

    with patch.object(mra, "RUBRIC_PATH", fake_rubric):
        with patch("model_review_agent._generate_draft", return_value="draft"):
            with patch("model_review_agent._score_draft", return_value={
                "hook_strength": 2, "voice_fidelity": 2, "diagnosis_clarity": 2,
                "ai_slop_absence": 2, "cta_sharpness": 2, "total": 10,
            }):
                with patch("model_review_agent._fetch_seed_posts", return_value=mra._default_seeds()):
                    with patch("model_review_agent._write_report", return_value=tmp_path / "report.md") as mock_write:
                        with patch("model_review_agent._send_telegram_summary"):
                            with patch("os.environ.get", side_effect=lambda k, d=None: "fake-key" if k == "OPENROUTER_API_KEY" else d):
                                # Run only Sunday gate test -- patch weekday
                                import datetime
                                with patch("model_review_agent.datetime") as mock_dt:
                                    fake_now = MagicMock()
                                    fake_now.weekday.return_value = 6  # Sunday
                                    fake_now.strftime.return_value = "2026-04-27"
                                    mock_dt.now.return_value = fake_now
                                    mra.model_review_tick()

    # Verify _write_report was called (meaning rubric was loaded and run proceeded)
    mock_write.assert_called_once()


def test_scoring_prompt_quotes_rubric_verbatim():
    """The score_draft call must pass rubric text into the prompt, not a summary."""
    captured_prompt = {}

    def fake_completion(model, messages, **kwargs):
        # Capture the user message content
        captured_prompt["content"] = messages[-1]["content"]
        resp = MagicMock()
        resp.choices[0].message.content = json.dumps({
            "hook_strength": 3, "voice_fidelity": 3, "diagnosis_clarity": 3,
            "ai_slop_absence": 3, "cta_sharpness": 3,
        })
        return resp

    rubric = "UNIQUE_RUBRIC_MARKER_XYZ: score each criterion 1-3"
    with patch("model_review_agent.completion", side_effect=fake_completion):
        result = mra._score_draft("some post text", rubric)

    assert "UNIQUE_RUBRIC_MARKER_XYZ" in captured_prompt.get("content", ""), \
        "Rubric text must appear verbatim in the scoring prompt"
    assert result["total"] == 15


def test_threshold_triggers_recommendation():
    """When challenger beats incumbent by >= 3 pts total, recommendation is set."""
    n_seeds = 3
    incumbent_total = 27  # 9 per post
    challenger_total = 30  # 10 per post, delta=3 -- exactly at threshold

    results = [
        {"model": mra.INCUMBENT_MODEL, "scores": [{"total": 9}] * n_seeds, "total": incumbent_total},
        {"model": "anthropic/claude-sonnet-4.6", "scores": [{"total": 10}] * n_seeds, "total": challenger_total},
    ]

    with patch("model_review_agent._emit_routing_proposal") as mock_emit:
        with patch("model_review_agent._write_report", return_value=Path("/tmp/r.md")):
            with patch("model_review_agent._send_telegram_summary"):
                with patch("model_review_agent._fetch_seed_posts", return_value=mra._default_seeds()):
                    with patch("model_review_agent._generate_draft", return_value="draft"):
                        with patch("model_review_agent._score_draft") as mock_score:
                            # Arrange scores so incumbent=9, challenger=10 per seed
                            call_count = [0]
                            def score_side_effect(draft, rubric):
                                call_count[0] += 1
                                # challenger calls come after incumbent calls
                                total = 9 if call_count[0] <= n_seeds else 10
                                return {"hook_strength": 2, "voice_fidelity": 2,
                                        "diagnosis_clarity": 2, "ai_slop_absence": 2,
                                        "cta_sharpness": 1 if total == 9 else 2, "total": total}
                            mock_score.side_effect = score_side_effect

                            with patch("os.environ.get", side_effect=lambda k, d=None: "key" if k == "OPENROUTER_API_KEY" else d):
                                import datetime
                                with patch("model_review_agent.RUBRIC_PATH") as mock_path:
                                    mock_path.exists.return_value = True
                                    mock_path.read_text.return_value = "rubric content"
                                    with patch("model_review_agent.datetime") as mock_dt:
                                        fake_now = MagicMock()
                                        fake_now.weekday.return_value = 6
                                        fake_now.strftime.return_value = "2026-04-27"
                                        mock_dt.now.return_value = fake_now
                                        mra.model_review_tick()

    mock_emit.assert_called_once()
    call_kwargs = mock_emit.call_args
    assert call_kwargs[0][1] == mra.INCUMBENT_MODEL  # incumbent arg


def test_no_routing_change_made_automatically():
    """model_review_agent must NOT import agents or autonomy_guard (structural guard)."""
    import importlib
    import sys

    # Reload the module fresh
    if "model_review_agent" in sys.modules:
        del sys.modules["model_review_agent"]

    import model_review_agent as fresh_mra

    module_source = Path(fresh_mra.__file__).read_text(encoding="utf-8")

    # Only actual import lines (not docstring mentions) must be checked.
    import_lines = [
        line.strip() for line in module_source.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    forbidden_modules = {"agents", "autonomy_guard"}
    for line in import_lines:
        parts = line.split()
        # "import agents" or "from agents import ..."
        imported = parts[1].split(".")[0] if len(parts) >= 2 else ""
        assert imported not in forbidden_modules, \
            f"model_review_agent must not import routing config: found '{line}'"


def test_below_threshold_no_proposal_emitted():
    """When gap < 3 pts, no approval_queue proposal is emitted."""
    with patch("model_review_agent._emit_routing_proposal") as mock_emit:
        with patch("model_review_agent._write_report", return_value=Path("/tmp/r.md")):
            with patch("model_review_agent._send_telegram_summary"):
                with patch("model_review_agent._fetch_seed_posts", return_value=mra._default_seeds()):
                    with patch("model_review_agent._generate_draft", return_value="draft"):
                        with patch("model_review_agent._score_draft", return_value={
                            "hook_strength": 2, "voice_fidelity": 2, "diagnosis_clarity": 2,
                            "ai_slop_absence": 2, "cta_sharpness": 2, "total": 10,
                        }):
                            with patch("os.environ.get", side_effect=lambda k, d=None: "key" if k == "OPENROUTER_API_KEY" else d):
                                with patch("model_review_agent.RUBRIC_PATH") as mock_path:
                                    mock_path.exists.return_value = True
                                    mock_path.read_text.return_value = "rubric"
                                    with patch("model_review_agent.datetime") as mock_dt:
                                        fake_now = MagicMock()
                                        fake_now.weekday.return_value = 6
                                        fake_now.strftime.return_value = "2026-04-27"
                                        mock_dt.now.return_value = fake_now
                                        mra.model_review_tick()

    mock_emit.assert_not_called()


def test_sunday_gate_skips_non_sunday():
    """model_review_tick must be a no-op on any day except Sunday."""
    with patch("model_review_agent._generate_draft") as mock_gen:
        with patch("model_review_agent.datetime") as mock_dt:
            fake_now = MagicMock()
            fake_now.weekday.return_value = 0  # Monday
            fake_now.strftime.return_value = "2026-04-28"
            mock_dt.now.return_value = fake_now
            mra.model_review_tick()

    mock_gen.assert_not_called()
