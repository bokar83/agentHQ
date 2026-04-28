import os
import pytest
from unittest.mock import patch
from startup_check import assert_required_env_vars, REQUIRED_VARS


def _full_env():
    return {v: "test-value" for v in REQUIRED_VARS}


def test_all_vars_present_passes():
    with patch.dict(os.environ, _full_env(), clear=False):
        assert_required_env_vars()  # must not raise or exit


def test_missing_var_exits_1(monkeypatch):
    env = _full_env()
    env.pop(REQUIRED_VARS[0])
    monkeypatch.delenv(REQUIRED_VARS[0], raising=False)
    with patch.dict(os.environ, env, clear=False):
        with pytest.raises(SystemExit) as exc:
            assert_required_env_vars()
    assert exc.value.code == 1


def test_empty_string_var_exits_1(monkeypatch):
    env = _full_env()
    env[REQUIRED_VARS[0]] = ""
    with patch.dict(os.environ, env, clear=False):
        with pytest.raises(SystemExit) as exc:
            assert_required_env_vars()
    assert exc.value.code == 1
