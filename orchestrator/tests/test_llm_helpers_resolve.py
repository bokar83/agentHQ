"""
Regression tests for llm_helpers._resolve_model and call_llm model selection.

Bug shipped pre-2026-04-30: chat traffic was hitting Haiku-4.5 even though
agent_config DB row said ATLAS_CHAT_MODEL = anthropic/claude-sonnet-4.6,
because run_atlas_chat passed model=ATLAS_CHAT_MODEL (a module-level constant
resolved at import time from an empty env var, so it fell back to the haiku
default). _resolve_model's `if model: return model` short-circuit then
bypassed the DB lookup entirely.

These tests pin the new contract:
  - Explicit string literal model arg: returned verbatim (deliberate pinning).
  - model=None + model_key=...: DB row wins, then env, then default.
  - The module-level constants must NEVER be passed implicitly by chat
    handlers; they pass model=None and let _resolve_model do the lookup.
"""
from __future__ import annotations

import importlib
import os
import sys
import unittest
from unittest.mock import patch


def _reload_llm_helpers():
    """Re-import llm_helpers so module-level env reads happen fresh."""
    if "llm_helpers" in sys.modules:
        del sys.modules["llm_helpers"]
    return importlib.import_module("llm_helpers")


class ResolveModelExplicitArg(unittest.TestCase):
    """An explicit model literal must always win. Studio trend scout, tools.py
    rely on this to pin specific models for cost-sensitive validator roles."""

    def test_explicit_literal_returned_as_is(self):
        llm_helpers = _reload_llm_helpers()
        result = llm_helpers._resolve_model("anthropic/claude-haiku-4.5")
        self.assertEqual(result, "anthropic/claude-haiku-4.5")

    def test_explicit_literal_wins_over_db(self):
        """Even if DB says sonnet, an explicit literal arg pins haiku."""
        llm_helpers = _reload_llm_helpers()
        with patch("agent_config.get_config", return_value="anthropic/claude-sonnet-4.6"):
            result = llm_helpers._resolve_model("anthropic/claude-haiku-4.5")
        self.assertEqual(result, "anthropic/claude-haiku-4.5")


class ResolveModelDBLookup(unittest.TestCase):
    """When model arg is None, DB lookup must run and DB value wins."""

    def test_none_arg_triggers_db_lookup_with_default_key(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CHAT_MODEL", None)
            llm_helpers = _reload_llm_helpers()
            with patch("agent_config.get_config", return_value="anthropic/claude-sonnet-4.6") as mock_get:
                result = llm_helpers._resolve_model(None)
                mock_get.assert_called_once()
                args, kwargs = mock_get.call_args
                self.assertEqual(args[0] if args else kwargs.get("key"), "CHAT_MODEL")
        self.assertEqual(result, "anthropic/claude-sonnet-4.6")

    def test_none_arg_with_atlas_key_looks_up_atlas_chat_model(self):
        """run_atlas_chat must be able to request the ATLAS_CHAT_MODEL DB row."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ATLAS_CHAT_MODEL", None)
            llm_helpers = _reload_llm_helpers()
            with patch("agent_config.get_config", return_value="anthropic/claude-sonnet-4.6") as mock_get:
                result = llm_helpers._resolve_model(None, key="ATLAS_CHAT_MODEL")
                mock_get.assert_called_once()
                args, kwargs = mock_get.call_args
                self.assertEqual(args[0] if args else kwargs.get("key"), "ATLAS_CHAT_MODEL")
        self.assertEqual(result, "anthropic/claude-sonnet-4.6")

    def test_db_returns_none_falls_back_to_env(self):
        """If DB has no row, env var is consulted next."""
        with patch.dict(os.environ, {"ATLAS_CHAT_MODEL": "anthropic/claude-opus-4-7"}, clear=False):
            llm_helpers = _reload_llm_helpers()
            with patch("agent_config.get_config", return_value=None):
                result = llm_helpers._resolve_model(None, key="ATLAS_CHAT_MODEL")
        self.assertEqual(result, "anthropic/claude-opus-4-7")

    def test_db_and_env_empty_returns_default(self):
        """All sources empty: hardcoded default is the floor."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CHAT_MODEL", None)
            os.environ.pop("ATLAS_CHAT_MODEL", None)
            llm_helpers = _reload_llm_helpers()
            with patch("agent_config.get_config", return_value=None):
                result = llm_helpers._resolve_model(None, key="ATLAS_CHAT_MODEL")
        self.assertTrue(result.startswith("anthropic/"))


class CallLLMRoutesViaModelKey(unittest.TestCase):
    """call_llm must accept a model_key= parameter and pass it to _resolve_model.
    This is the surface that chat handlers use to ask 'use whatever the DB says
    for ATLAS_CHAT_MODEL right now'."""

    def test_call_llm_accepts_model_key_param(self):
        llm_helpers = _reload_llm_helpers()
        # Construct a fake response to avoid hitting the network.
        fake_response = type("Resp", (), {
            "id": "test-gen-1",
            "choices": [type("C", (), {"finish_reason": "stop", "message": type("M", (), {"content": "x"})()})()],
        })
        with patch.object(llm_helpers, "get_openrouter_client") as mock_client, \
             patch("agent_config.get_config", return_value="anthropic/claude-sonnet-4.6") as mock_get:
            mock_client.return_value.chat.completions.create.return_value = fake_response
            llm_helpers.call_llm(
                messages=[{"role": "user", "content": "hi"}],
                model=None,
                model_key="ATLAS_CHAT_MODEL",
            )
            sent_kwargs = mock_client.return_value.chat.completions.create.call_args.kwargs
            self.assertEqual(sent_kwargs["model"], "anthropic/claude-sonnet-4.6")
            args, kwargs = mock_get.call_args
            self.assertEqual(args[0] if args else kwargs.get("key"), "ATLAS_CHAT_MODEL")


class DeprecatedConstantsLoudFail(unittest.TestCase):
    """Sankofa guardrail: any caller still passing the old import-time
    constants as model= must produce a loud RuntimeError, not silent haiku.
    Without this guardrail the same bug class returns under a new role name."""

    def test_deprecated_chat_model_constant_raises(self):
        llm_helpers = _reload_llm_helpers()
        with self.assertRaises(RuntimeError) as ctx:
            llm_helpers.call_llm(
                messages=[{"role": "user", "content": "hi"}],
                model=llm_helpers.CHAT_MODEL,
            )
        self.assertIn("deprecated", str(ctx.exception).lower())
        self.assertIn("model_key", str(ctx.exception))

    def test_deprecated_atlas_chat_model_constant_raises(self):
        llm_helpers = _reload_llm_helpers()
        with self.assertRaises(RuntimeError):
            llm_helpers.call_llm(
                messages=[{"role": "user", "content": "hi"}],
                model=llm_helpers.ATLAS_CHAT_MODEL,
            )

    def test_deprecated_helper_model_constant_raises(self):
        llm_helpers = _reload_llm_helpers()
        with self.assertRaises(RuntimeError):
            llm_helpers.call_llm(
                messages=[{"role": "user", "content": "hi"}],
                model=llm_helpers.HELPER_MODEL,
            )


class ResolvedModelAttachedToResponse(unittest.TestCase):
    """Sankofa guardrail: the resolved model must be readable from the response
    so the UI footer can show 'Atlas is using <model>'. Without this Boubacar
    cannot tell which model handled a turn."""

    def test_response_carries_resolved_model(self):
        llm_helpers = _reload_llm_helpers()

        class FakeResp:
            id = "test-gen-2"
            choices = [type("C", (), {
                "finish_reason": "stop",
                "message": type("M", (), {"content": "x"})(),
            })()]
        fake = FakeResp()

        with patch.object(llm_helpers, "get_openrouter_client") as mock_client, \
             patch("agent_config.get_config", return_value="anthropic/claude-sonnet-4.6"):
            mock_client.return_value.chat.completions.create.return_value = fake
            response = llm_helpers.call_llm(
                messages=[{"role": "user", "content": "hi"}],
                model=None,
                model_key="ATLAS_CHAT_MODEL",
            )
        self.assertEqual(getattr(response, "_resolved_model", None), "anthropic/claude-sonnet-4.6")


if __name__ == "__main__":
    unittest.main()
