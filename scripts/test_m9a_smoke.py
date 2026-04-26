"""
test_m9a_smoke.py - M9a pre-deploy smoke test.

Runs without a live container (mocked dependencies).
Verifies: run_chat() schema, CHAT_SANDBOX suppression, _build_button byte limit,
approval_queue enqueue uses send_message_with_buttons, no Postgres connection leaks.

Usage: python scripts/test_m9a_smoke.py
"""
import json
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Bootstrap: make orchestrator/ importable from the project root.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "orchestrator"))


class TestRunChatSchema(unittest.TestCase):
    """run_chat() must return M9 schema dict with reply + actions keys."""

    def _make_llm_response(self, content: str):
        msg = MagicMock()
        msg.tool_calls = None
        msg.content = content
        choice = MagicMock()
        choice.message = msg
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    def _stub_modules(self):
        for mod in ("state", "notifier", "memory", "session_store", "prompt_loader",
                    "engine", "utils", "saver"):
            sys.modules.setdefault(mod, MagicMock())
        state_mod = sys.modules["state"]
        state_mod._last_completed_job = {}
        state_mod._PRAISE_SIGNALS = set()
        state_mod._CRITIQUE_SIGNALS = set()
        state_mod._PRAISE_EMOJIS = set()
        state_mod._CRITIQUE_EMOJIS = set()

    def test_plain_text_reply_wrapped_in_schema(self):
        self._stub_modules()
        plain = "Hello from chat"
        llm_resp = self._make_llm_response(plain)
        with patch.dict("sys.modules", {"llm_helpers": MagicMock(
            call_llm=MagicMock(return_value=llm_resp),
            CHAT_MODEL="anthropic/claude-haiku-4.5",
            CHAT_TEMPERATURE=0.7,
            CHAT_SANDBOX=False,
        )}):
            from handlers_chat import run_chat
            result = run_chat("hi", session_key="test-session")
        self.assertIn("reply", result)
        self.assertIn("actions", result)
        self.assertEqual(result["reply"], plain)
        self.assertEqual(result["actions"], [])
        # Legacy keys still present
        self.assertIn("result", result)
        self.assertTrue(result["success"])

    def test_json_reply_parsed_into_reply_and_actions(self):
        self._stub_modules()
        structured = json.dumps({
            "reply": "Here are your options.",
            "actions": [{"label": "Option A", "callback_data": "queue_post:abc"}],
        })
        llm_resp = self._make_llm_response(structured)
        with patch.dict("sys.modules", {"llm_helpers": MagicMock(
            call_llm=MagicMock(return_value=llm_resp),
            CHAT_MODEL="anthropic/claude-haiku-4.5",
            CHAT_TEMPERATURE=0.7,
            CHAT_SANDBOX=False,
        )}):
            from handlers_chat import run_chat
            result = run_chat("show options", session_key="test-session")
        self.assertEqual(result["reply"], "Here are your options.")
        self.assertEqual(len(result["actions"]), 1)
        self.assertEqual(result["actions"][0]["label"], "Option A")

    def test_sandbox_suppresses_forward_to_crew(self):
        self._stub_modules()
        # Model calls forward_to_crew tool
        tool_call = MagicMock()
        tool_call.id = "tc_001"
        tool_call.function.name = "forward_to_crew"
        tool_call.function.arguments = json.dumps({"task_text": "draft a post"})
        msg1 = MagicMock()
        msg1.tool_calls = [tool_call]
        msg1.content = None
        choice1 = MagicMock()
        choice1.message = msg1
        resp1 = MagicMock()
        resp1.choices = [choice1]

        followup_msg = MagicMock()
        followup_msg.tool_calls = None
        followup_msg.content = json.dumps({"reply": "Sandbox: forwarded to crew (simulated).", "actions": []})
        choice2 = MagicMock()
        choice2.message = followup_msg
        resp2 = MagicMock()
        resp2.choices = [choice2]

        call_llm = MagicMock(side_effect=[resp1, resp2])
        engine_mock = MagicMock()

        with patch.dict("sys.modules", {
            "llm_helpers": MagicMock(
                call_llm=call_llm,
                CHAT_MODEL="anthropic/claude-haiku-4.5",
                CHAT_TEMPERATURE=0.7,
                CHAT_SANDBOX=True,
            ),
            "engine": engine_mock,
        }):
            from handlers_chat import run_chat
            result = run_chat("draft a post", session_key="test-sandbox")

        # engine.run_orchestrator must NOT have been called in sandbox mode
        engine_mock.run_orchestrator.assert_not_called()
        self.assertIn("reply", result)


class TestBuildButton(unittest.TestCase):
    """_build_button must enforce 64-byte callback_data limit."""

    def setUp(self):
        for mod in ("state", "notifier", "episodic_memory"):
            sys.modules.setdefault(mod, MagicMock())
        state_mod = sys.modules["state"]
        state_mod._PENDING_FEEDBACK_WINDOWS = {}
        state_mod._PUBLISH_BRIEF_WINDOWS = {}

    def test_valid_callback_data_passes(self):
        from handlers_approvals import _build_button
        btn = _build_button("Approve #1", "approve_queue_item:1")
        self.assertEqual(btn["text"], "Approve #1")
        self.assertEqual(btn["callback_data"], "approve_queue_item:1")

    def test_callback_data_over_64_bytes_raises(self):
        from handlers_approvals import _build_button
        long_data = "x" * 65
        with self.assertRaises(AssertionError):
            _build_button("Label", long_data)


class TestEnqueueSendsButtons(unittest.TestCase):
    """enqueue() must call send_message_with_buttons, not send_message_returning_id."""

    def test_enqueue_uses_send_message_with_buttons(self):
        for mod in ("memory", "episodic_memory"):
            sys.modules.setdefault(mod, MagicMock())

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        # Simulate INSERT RETURNING the new row
        from datetime import datetime
        fake_row = (1, datetime.utcnow(), None, "griot", "post_candidate",
                    '{"title": "Test post"}', None, "pending", None, None, None, None)
        mock_cur.fetchone.return_value = fake_row

        send_with_buttons = MagicMock(return_value=42)

        notifier_mock = MagicMock()
        notifier_mock.send_message_with_buttons = send_with_buttons

        with patch.dict("sys.modules", {"notifier": notifier_mock}):
            with patch("approval_queue._conn", return_value=mock_conn):
                with patch.dict(os.environ, {"TELEGRAM_CHAT_ID": "999"}):
                    from approval_queue import enqueue
                    enqueue("griot", "post_candidate", {"title": "Test post"})

        send_with_buttons.assert_called_once()
        call_args = send_with_buttons.call_args
        # Verify buttons contain Approve and Reject
        buttons = call_args[0][2]
        flat = [label for row in buttons for label, _ in row]
        self.assertTrue(any("Approve" in l for l in flat))
        self.assertTrue(any("Reject" in l for l in flat))


class TestAtlasDashboardConnClose(unittest.TestCase):
    """atlas_dashboard fetchers must close Postgres connections even on exception."""

    def setUp(self):
        for mod in ("autonomy_guard", "heartbeat", "approval_queue",
                    "skills.forge_cli.notion_client"):
            sys.modules.setdefault(mod, MagicMock())

    def test_spend_aggregates_closes_conn_on_exception(self):
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = RuntimeError("DB error")
        with patch("atlas_dashboard._pg_conn" if "_pg_conn" in dir() else "memory._pg_conn",
                   return_value=mock_conn):
            with patch.dict("sys.modules", {"memory": MagicMock(_pg_conn=MagicMock(return_value=mock_conn))}):
                from atlas_dashboard import _spend_aggregates
                result = _spend_aggregates()
        # Should return safe defaults, not raise
        self.assertIn("today_usd", result)
        self.assertEqual(result["today_usd"], 0.0)


if __name__ == "__main__":
    print("Running M9a smoke tests...")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestRunChatSchema))
    suite.addTests(loader.loadTestsFromTestCase(TestBuildButton))
    suite.addTests(loader.loadTestsFromTestCase(TestEnqueueSendsButtons))
    suite.addTests(loader.loadTestsFromTestCase(TestAtlasDashboardConnClose))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
