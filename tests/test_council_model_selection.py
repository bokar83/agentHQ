"""
test_council_model_selection.py
Tests for capability-based model selection.
Run from d:/Ai_Sandbox/agentsHQ/ with:
  python -m pytest tests/test_council_model_selection.py -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'orchestrator'))

# Mock env before importing
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")

from agents import select_by_capability, COUNCIL_MODEL_REGISTRY, COST_TIER_ORDER


def test_registry_has_required_keys():
    for model_id, meta in COUNCIL_MODEL_REGISTRY.items():
        assert "capabilities" in meta, f"{model_id} missing capabilities"
        assert "cost_tier" in meta, f"{model_id} missing cost_tier"
        assert "input_per_mtok" in meta, f"{model_id} missing input_per_mtok"


def test_select_deep_reasoning_returns_model():
    model_id = select_by_capability("deep_reasoning", max_cost_tier="high")
    assert model_id in COUNCIL_MODEL_REGISTRY


def test_select_fresh_perspective_returns_non_anthropic():
    model_id = select_by_capability("fresh_perspective", max_cost_tier="medium")
    assert not model_id.startswith("anthropic/"), \
        f"Expected non-Anthropic model for fresh_perspective, got {model_id}"


def test_select_cost_efficient_is_cheap():
    model_id = select_by_capability("cost_efficient", max_cost_tier="very_low")
    meta = COUNCIL_MODEL_REGISTRY[model_id]
    assert meta["input_per_mtok"] <= 1.00, \
        f"Expected cheap model, got {model_id} at ${meta['input_per_mtok']}/Mtok"


def test_select_returns_fallback_on_impossible_constraint():
    # "creative_divergence" with "very_low" cost might have no match — should fallback gracefully
    model_id = select_by_capability("creative_divergence", max_cost_tier="very_low")
    assert model_id in COUNCIL_MODEL_REGISTRY  # fallback must still be valid


def test_strip_style_markers_removes_bold():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'orchestrator'))
    from council import strip_style_markers
    result = strip_style_markers("**Important point** here")
    assert "**" not in result
    assert "Important point" in result


def test_strip_style_markers_removes_headers():
    from council import strip_style_markers
    result = strip_style_markers("## Section Title\nContent here")
    assert "##" not in result
    assert "Section Title" in result


def test_strip_style_markers_normalizes_em_dashes():
    from council import strip_style_markers
    result = strip_style_markers("This \u2014 that")
    assert "\u2014" not in result
    assert "-" in result
