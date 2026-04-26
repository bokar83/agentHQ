"""
Tests for select_llm() and _validate_role_capability_dict().

Unit tests only -- no live OpenRouter calls. select_by_capability() is
mocked to return a fixed model string so tests run without API keys.
"""
import pytest
from unittest.mock import patch

MOCK_MODEL = "anthropic/claude-haiku-4.5"


@pytest.fixture(autouse=True)
def mock_select_by_capability():
    with patch("agents.select_by_capability", return_value=MOCK_MODEL) as m:
        yield m


@pytest.fixture(autouse=True)
def mock_get_llm():
    with patch("agents.get_llm") as m:
        m.side_effect = lambda model_id, temp: type(
            "LLM", (), {"model": model_id, "temperature": temp}
        )()
        yield m


def _all_role_keys():
    from agents import ROLE_CAPABILITY
    return list(ROLE_CAPABILITY.keys())


@pytest.mark.parametrize("role,complexity", _all_role_keys())
def test_select_llm_all_keys_return_llm(role, complexity):
    from agents import select_llm
    result = select_llm(role, complexity)
    assert result is not None
    assert hasattr(result, "model")
    assert result.model


def test_select_llm_unknown_role_falls_back(mock_select_by_capability):
    from agents import select_llm
    result = select_llm("unknown_role", "moderate")
    assert result is not None
    mock_select_by_capability.assert_called_with(
        "instruction_following", "medium", temperature=pytest.approx(0.3, abs=0.01)
    )


def test_select_llm_explicit_temperature_overrides():
    from agents import select_llm
    result = select_llm("writer", "complex", temperature=0.99)
    assert result.temperature == pytest.approx(0.99, abs=0.001)


def test_select_llm_uses_role_temperature_default():
    from agents import select_llm, ROLE_TEMPERATURE
    expected_temp = ROLE_TEMPERATURE.get(("writer", "complex"), 0.3)
    result = select_llm("writer", "complex")
    assert result.temperature == pytest.approx(expected_temp, abs=0.001)


def test_validate_role_capability_raises_on_bad_tag():
    from agents import ROLE_CAPABILITY
    import agents as agents_mod
    bad_key = ("_test_role", "simple")
    ROLE_CAPABILITY[bad_key] = ("typo_capabilty", "low")
    try:
        with pytest.raises(ValueError, match="unknown capability tag"):
            agents_mod._validate_role_capability_dict()
    finally:
        del ROLE_CAPABILITY[bad_key]


def test_all_capability_tags_are_valid():
    from agents import ROLE_CAPABILITY, _VALID_CAPABILITIES
    for key, (cap, _tier) in ROLE_CAPABILITY.items():
        assert cap in _VALID_CAPABILITIES, (
            f"ROLE_CAPABILITY[{key!r}] uses unknown capability {cap!r}"
        )


def test_consultant_complex_ceiling_is_medium_high():
    from agents import ROLE_CAPABILITY
    cap, tier = ROLE_CAPABILITY[("consultant", "complex")]
    assert tier == "medium-high", (
        f"consultant/complex ceiling must be medium-high (Sonnet-class minimum "
        f"for client-facing work), got {tier!r}"
    )
