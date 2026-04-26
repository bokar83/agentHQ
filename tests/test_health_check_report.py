"""
Tests for the weekly health check email formatter and delivery webhook.
Written BEFORE implementation — all tests must fail first.

Tests cover:
  notifier._format_health_check_html()  — HTML formatter
  notifier.send_health_check_report()   — full send function
  orchestrator POST /internal/health-report — webhook endpoint
"""
import os
import pytest
from unittest.mock import patch, MagicMock

# Set required env vars before importing modules
os.environ.setdefault("ORCHESTRATOR_TELEGRAM_BOT_TOKEN", "123:test")
os.environ.setdefault("TELEGRAM_CHAT_ID", "7792432594")
os.environ.setdefault("HEALTH_REPORT_TOKEN", "test-internal-token-abc123")

import sys
sys.path.insert(0, "orchestrator")


# ══════════════════════════════════════════════════════════════
# HTML FORMATTER TESTS
# ══════════════════════════════════════════════════════════════

class TestFormatHealthCheckHtml:

    def setup_method(self):
        from notifier import _format_health_check_html
        self._format = _format_health_check_html

    def test_returns_valid_html_string(self):
        html = self._format("GREEN", "# Report\n## Status: GREEN\nAll good.", "2026-04-07")
        assert isinstance(html, str)
        assert html.strip().startswith("<!DOCTYPE html")
        assert "</html>" in html

    def test_green_status_renders_green_badge(self):
        html = self._format("GREEN", "# Report\n## Status: GREEN\nAll good.", "2026-04-07")
        # Green status should use the brand green colour token
        assert "#16A34A" in html

    def test_yellow_status_renders_amber_badge(self):
        html = self._format("YELLOW", "# Report\n## Status: YELLOW\n- Some issue found.", "2026-04-07")
        assert "#D97706" in html

    def test_red_status_renders_red_badge(self):
        html = self._format("RED", "# Report\n## Status: RED\n- Broken routing.", "2026-04-07")
        assert "#DC2626" in html

    def test_report_date_appears_in_output(self):
        html = self._format("GREEN", "# Report", "2026-04-07")
        assert "2026-04-07" in html or "April 07, 2026" in html or "7 Apr 2026" in html

    def test_catalyst_works_branding_present(self):
        html = self._format("GREEN", "# Report", "2026-04-07")
        assert "Catalyst Works" in html

    def test_report_body_text_is_embedded(self):
        report = "# agentsHQ Weekly Health Check\n## Status: GREEN\nNo issues found."
        html = self._format("GREEN", report, "2026-04-07")
        assert "No issues found" in html

    def test_html_escapes_special_characters_in_report(self):
        # Report text with HTML special chars should not break the email
        report = "Issue in file <orchestrator.py> — check line 42 & fix it"
        html = self._format("GREEN", report, "2026-04-07")
        # Should be escaped — raw < should not appear in unescaped form in body
        assert "<orchestrator.py>" not in html or "&lt;orchestrator.py&gt;" in html

    def test_uses_brand_accent_colour(self):
        # Primary brand blue must appear (header, links, borders)
        html = self._format("GREEN", "# Report", "2026-04-07")
        assert "#2563EB" in html

    def test_plain_text_fallback_excluded(self):
        # The formatter only returns HTML — the send_email wrapper adds plain text
        html = self._format("GREEN", "# Report", "2026-04-07")
        assert html.startswith("<!DOCTYPE") or html.startswith("<html")


# ══════════════════════════════════════════════════════════════
# SEND FUNCTION TESTS
# ══════════════════════════════════════════════════════════════

class TestSendHealthCheckReport:

    def test_calls_send_email_with_html_true(self):
        from notifier import send_health_check_report
        with patch("notifier.send_email") as mock_send:
            mock_send.return_value = True
            send_health_check_report("GREEN", "# Report\nAll good.", "2026-04-07")
            mock_send.assert_called_once()
            _, kwargs = mock_send.call_args[0], mock_send.call_args[1]
            # html=True must be passed
            assert mock_send.call_args[1].get("html") is True or \
                   (len(mock_send.call_args[0]) >= 4 and mock_send.call_args[0][3] is True)

    def test_subject_contains_status_and_date(self):
        from notifier import send_health_check_report
        with patch("notifier.send_email") as mock_send:
            mock_send.return_value = True
            send_health_check_report("YELLOW", "# Report\nSome issues.", "2026-04-07")
            subject = mock_send.call_args[0][0]
            assert "YELLOW" in subject
            assert "2026" in subject or "Apr" in subject

    def test_sends_to_all_three_addresses(self):
        from notifier import send_health_check_report
        with patch("notifier.send_email") as mock_send:
            mock_send.return_value = True
            send_health_check_report("GREEN", "# Report", "2026-04-07")
            to_addresses = mock_send.call_args[1].get("to_addresses") or \
                           (mock_send.call_args[0][2] if len(mock_send.call_args[0]) > 2 else None)
            assert to_addresses is not None
            assert "bokar83@gmail.com" in to_addresses
            assert "boubacarbusiness@gmail.com" in to_addresses
            assert "catalystworks.ai@gmail.com" in to_addresses

    def test_returns_true_on_success(self):
        from notifier import send_health_check_report
        with patch("notifier.send_email", return_value=True):
            result = send_health_check_report("GREEN", "# Report", "2026-04-07")
            assert result is True

    def test_returns_false_when_send_email_fails(self):
        from notifier import send_health_check_report
        with patch("notifier.send_email", return_value=False):
            result = send_health_check_report("GREEN", "# Report", "2026-04-07")
            assert result is False


# ══════════════════════════════════════════════════════════════
# WEBHOOK ENDPOINT TESTS
# ══════════════════════════════════════════════════════════════

class TestHealthReportWebhook:

    def setup_method(self):
        from fastapi.testclient import TestClient
        # Must patch send_health_check_report before importing the app
        # so the endpoint doesn't try to actually send email
        self.send_patch = patch("notifier.send_health_check_report", return_value=True)
        self.send_patch.start()
        import importlib
        import app
        importlib.reload(app)
        self.client = TestClient(app.app)

    def teardown_method(self):
        self.send_patch.stop()

    def test_rejects_missing_token(self):
        response = self.client.post("/internal/health-report", json={
            "status": "GREEN",
            "report": "# Report\nAll good.",
            "date": "2026-04-07"
        })
        assert response.status_code == 401

    def test_rejects_wrong_token(self):
        response = self.client.post("/internal/health-report",
            headers={"X-Internal-Token": "wrong-token"},
            json={"status": "GREEN", "report": "# Report", "date": "2026-04-07"}
        )
        assert response.status_code == 401

    def test_accepts_correct_token_and_returns_ok(self):
        response = self.client.post("/internal/health-report",
            headers={"X-Internal-Token": "test-internal-token-abc123"},
            json={"status": "GREEN", "report": "# Report\nAll good.", "date": "2026-04-07"}
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_rejects_missing_status_field(self):
        response = self.client.post("/internal/health-report",
            headers={"X-Internal-Token": "test-internal-token-abc123"},
            json={"report": "# Report", "date": "2026-04-07"}
        )
        assert response.status_code == 422

    def test_rejects_missing_report_field(self):
        response = self.client.post("/internal/health-report",
            headers={"X-Internal-Token": "test-internal-token-abc123"},
            json={"status": "GREEN", "date": "2026-04-07"}
        )
        assert response.status_code == 422

    def test_valid_status_values_accepted(self):
        for status in ["GREEN", "YELLOW", "RED"]:
            response = self.client.post("/internal/health-report",
                headers={"X-Internal-Token": "test-internal-token-abc123"},
                json={"status": status, "report": "# Report", "date": "2026-04-07"}
            )
            assert response.status_code == 200, f"Status {status} was rejected"

    def test_response_includes_email_delivery_result(self):
        response = self.client.post("/internal/health-report",
            headers={"X-Internal-Token": "test-internal-token-abc123"},
            json={"status": "GREEN", "report": "# Report\nAll good.", "date": "2026-04-07"}
        )
        body = response.json()
        assert "email_sent" in body
