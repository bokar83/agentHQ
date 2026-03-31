"""
test_council.py — Sankofa Council end-to-end test
===================================================
Uses the retention/turnover consulting scenario from the virtual council
test session. Run this BEFORE wiring council into crews.py.

Run from d:/Ai_Sandbox/agentsHQ/:
  python -m pytest tests/test_council.py -v -s

Requires OPENROUTER_API_KEY set in environment.
This test makes REAL API calls and costs ~$1-3.
"""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'orchestrator'))

import pytest

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")


@pytest.mark.skipif(not OPENROUTER_API_KEY, reason="OPENROUTER_API_KEY not set")
def test_council_full_run():
    """Full end-to-end: 5 voices + peer review + chairman synthesis."""
    from council import SankofaCouncil, should_invoke_council, CouncilTier

    # Verify gate logic
    assert should_invoke_council("consulting_deliverable") == CouncilTier.FULL
    assert should_invoke_council("social_content") == CouncilTier.NONE
    assert should_invoke_council("website_build", {"high_stakes": True}) == CouncilTier.FULL

    council = SankofaCouncil()

    result = council.run(
        query=(
            "A 45-person professional services firm (engineering consultancy) "
            "has been losing mid-level talent for 18 months. They've raised salaries twice. "
            "Turnover continues. The CEO believes the problem is compensation. "
            "Diagnose the actual constraint and recommend an intervention."
        ),
        context="Apply Theory of Constraints diagnostic thinking.",
        task_type="consulting_deliverable",
    )

    # Structure checks
    assert "chairman_synthesis" in result
    assert "convergence_note" in result
    assert "member_responses" in result
    assert len(result["member_responses"]) == 5
    assert "peer_reviews" in result
    assert len(result["peer_reviews"]) == 5
    assert "convergence_score" in result
    assert 0.0 <= result["convergence_score"] <= 1.0
    assert result["rounds"] >= 1
    assert result["rounds"] <= 3
    assert "log_file_path" in result
    assert "html_file_path" in result

    # Content checks
    assert len(result["chairman_synthesis"]) > 100, "Chairman synthesis too short"
    assert len(result["convergence_note"]) > 20, "Convergence note too short"

    # Log file was written
    assert os.path.exists(result["log_file_path"]), "JSON log not found on disk"
    with open(result["log_file_path"], encoding="utf-8") as f:
        log = json.load(f)
    assert log["task_type"] == "consulting_deliverable"

    # HTML file was written
    assert os.path.exists(result["html_file_path"]), "HTML report not found on disk"
    html_content = open(result["html_file_path"], encoding="utf-8").read()
    assert "Sankofa Council" in html_content
    assert "Chairman" in html_content

    # Print summary for visual inspection
    print("\n" + "="*60)
    print("SANKOFA COUNCIL — END-TO-END TEST RESULT")
    print("="*60)
    print(f"Rounds to converge: {result['rounds']}")
    print(f"Convergence score:  {result['convergence_score']:.2f}")
    print(f"Converged:          {result['converged']}")
    print(f"\nModels used:")
    for voice, model in result["models_used"].items():
        print(f"  {voice:<20} -> {model}")
    print(f"\n--- CHAIRMAN SYNTHESIS ---")
    print(result["chairman_synthesis"])
    print(f"\n--- CONVERGENCE NOTE ---")
    print(result["convergence_note"])
    print(f"\n--- NEXT STEP ---")
    print(result.get("next_step", ""))
    print(f"\n--- OPEN QUESTION ---")
    print(result.get("open_question", ""))
    print("="*60)
