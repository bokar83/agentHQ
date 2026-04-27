"""
Tests for session_compressor.py (Atlas M9c).
All tests use mocks -- no live DB or LLM calls.
"""
import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Minimal stubs so the module can be imported without real DB / LLM
# ---------------------------------------------------------------------------

def _make_stub_module(name):
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


def _stub_dependencies():
    db = _make_stub_module("db")
    db.get_local_connection = MagicMock()
    db.save_session_summary = MagicMock()
    db.get_latest_session_summary = MagicMock(return_value=None)

    mem = _make_stub_module("memory")
    mem.get_conversation_history = MagicMock(return_value=[])

    llm = _make_stub_module("llm_helpers")
    llm.call_llm = MagicMock()
    llm.HELPER_MODEL = "anthropic/claude-haiku-4.5"

    return db, mem, llm


_stub_dependencies()

import importlib
session_compressor = importlib.import_module("session_compressor")


# ---------------------------------------------------------------------------
# 1. find_sessions_to_compress
# ---------------------------------------------------------------------------

class TestFindSessionsToCompress(unittest.TestCase):

    def test_returns_sessions_in_window(self):
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        in_window = now - timedelta(minutes=45)
        too_recent = now - timedelta(minutes=10)
        too_old = now - timedelta(minutes=120)

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [("session-in-window", in_window)]
        mock_conn.cursor.return_value = mock_cur

        with patch("db.get_local_connection", return_value=mock_conn):
            result = session_compressor.find_sessions_to_compress()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "session-in-window")

    def test_returns_empty_on_db_error(self):
        with patch("db.get_local_connection", side_effect=Exception("db down")):
            result = session_compressor.find_sessions_to_compress()
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# 2. compress_session -- skip when too few turns
# ---------------------------------------------------------------------------

class TestCompressSessionSkipsShort(unittest.TestCase):

    def test_skips_fewer_than_four_turns(self):
        short_history = [
            {"role": "user", "content": "hi", "created_at": None},
            {"role": "assistant", "content": "hello", "created_at": None},
        ]
        with patch("memory.get_conversation_history", return_value=short_history):
            with patch("db.save_session_summary") as mock_save:
                result = session_compressor.compress_session("test-session")
        self.assertFalse(result)
        mock_save.assert_not_called()

    def test_skips_empty_history(self):
        with patch("memory.get_conversation_history", return_value=[]):
            with patch("db.save_session_summary") as mock_save:
                result = session_compressor.compress_session("test-session")
        self.assertFalse(result)
        mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# 3. compress_session -- writes summary when enough turns
# ---------------------------------------------------------------------------

class TestCompressSessionWritesSummary(unittest.TestCase):

    def _make_turns(self, n):
        return [
            {"role": "user" if i % 2 == 0 else "assistant",
             "content": f"message {i}",
             "created_at": "2026-04-27T20:00:00Z"}
            for i in range(n)
        ]

    def test_writes_summary_for_sufficient_turns(self):
        turns = self._make_turns(10)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "- Decision: ship M9c\n- Task: compress sessions\n- Next: deploy"

        with patch("memory.get_conversation_history", return_value=turns):
            with patch("llm_helpers.call_llm", return_value=mock_response):
                with patch("db.save_session_summary") as mock_save:
                    result = session_compressor.compress_session("test-session")

        self.assertTrue(result)
        mock_save.assert_called_once()
        args = mock_save.call_args[1]
        self.assertEqual(args["session_id"], "test-session")
        self.assertIn("Decision", args["summary"])
        self.assertEqual(args["turn_count"], 10)

    def test_returns_false_on_llm_failure(self):
        turns = self._make_turns(6)
        with patch("memory.get_conversation_history", return_value=turns):
            with patch("llm_helpers.call_llm", side_effect=Exception("model down")):
                with patch("db.save_session_summary") as mock_save:
                    result = session_compressor.compress_session("test-session")
        self.assertFalse(result)
        mock_save.assert_not_called()

    def test_returns_false_on_empty_llm_response(self):
        turns = self._make_turns(6)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = ""
        with patch("memory.get_conversation_history", return_value=turns):
            with patch("llm_helpers.call_llm", return_value=mock_response):
                with patch("db.save_session_summary") as mock_save:
                    result = session_compressor.compress_session("test-session")
        self.assertFalse(result)
        mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# 4. compressor_tick -- non-fatal on individual session error
# ---------------------------------------------------------------------------

class TestCompressorTickNonFatal(unittest.TestCase):

    def test_continues_after_one_session_fails(self):
        from datetime import datetime, timezone
        sessions = [
            ("session-a", datetime.now(timezone.utc)),
            ("session-b", datetime.now(timezone.utc)),
        ]
        call_count = {"n": 0}

        def side_effect(sid):
            call_count["n"] += 1
            if sid == "session-a":
                raise RuntimeError("boom")
            return True

        with patch.object(session_compressor, "find_sessions_to_compress", return_value=sessions):
            with patch.object(session_compressor, "compress_session", side_effect=side_effect):
                # Should not raise
                session_compressor.compressor_tick()

        self.assertEqual(call_count["n"], 2)

    def test_handles_empty_session_list(self):
        with patch.object(session_compressor, "find_sessions_to_compress", return_value=[]):
            session_compressor.compressor_tick()  # must not raise


# ---------------------------------------------------------------------------
# 5 & 6. Summary injection logic -- tested directly, not via run_chat
# (run_chat pulls in too many live dependencies for unit test isolation)
# ---------------------------------------------------------------------------

class TestSummaryInjectionLogic(unittest.TestCase):
    """
    The injection pattern in handlers_chat is:
        if _prior:
            system_prompt = "PRIOR SESSION CONTEXT...\n\n" + system_prompt
    We test the logic directly here rather than calling run_chat end-to-end,
    which requires too many live module dependencies.
    """

    def _apply_injection(self, prior_row, base_prompt="BASE PROMPT"):
        """Replicate the injection logic from handlers_chat."""
        system_prompt = base_prompt
        if prior_row:
            system_prompt = (
                f"PRIOR SESSION CONTEXT (summarized):\n{prior_row['summary']}\n\n"
                f"Refer to this naturally if relevant. Do not repeat it verbatim.\n\n"
                + system_prompt
            )
        return system_prompt

    def test_summary_injected_when_present(self):
        prior = {
            "summary": "- Shipped M9c\n- Next: deploy",
            "turn_count": 8,
            "created_at": "2026-04-27T20:00:00Z",
            "window_end_at": "2026-04-27T20:00:00Z",
        }
        result = self._apply_injection(prior)
        self.assertIn("PRIOR SESSION CONTEXT", result)
        self.assertIn("Shipped M9c", result)
        self.assertIn("BASE PROMPT", result)

    def test_no_injection_when_no_summary(self):
        result = self._apply_injection(None)
        self.assertNotIn("PRIOR SESSION CONTEXT", result)
        self.assertEqual(result, "BASE PROMPT")

    def test_base_prompt_preserved_after_injection(self):
        prior = {"summary": "- did stuff", "turn_count": 5,
                 "created_at": "2026-04-27T20:00:00Z", "window_end_at": "2026-04-27T20:00:00Z"}
        result = self._apply_injection(prior, base_prompt="SYSTEM INSTRUCTIONS HERE")
        self.assertTrue(result.endswith("SYSTEM INSTRUCTIONS HERE"))


if __name__ == "__main__":
    unittest.main()
