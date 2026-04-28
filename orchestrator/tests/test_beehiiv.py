"""Unit tests for beehiiv.py.

Mocks httpx.post so no real HTTP calls fire. Covers:
- Successful draft creation returns URL
- Missing env vars skips gracefully (returns None, no HTTP call)
- API error returns None (non-fatal)
- Non-JSON response returns None (non-fatal)
- Subtitle included in payload when provided
- Post ID returned as fallback when URL field absent
"""
from __future__ import annotations

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)


def _http_response(status_code: int, json_body=None, text: str = ""):
    resp = MagicMock()
    resp.status_code = status_code
    if json_body is not None:
        resp.json.return_value = json_body
        resp.text = json.dumps(json_body)
    else:
        resp.text = text
        resp.json.side_effect = ValueError("not json")
    return resp


# ═════════════════════════════════════════════════════════════════════════════
# Missing env vars
# ═════════════════════════════════════════════════════════════════════════════

def test_missing_api_key_returns_none(monkeypatch):
    """No BEEHIIV_API_KEY: skip gracefully, no HTTP call."""
    monkeypatch.delenv("BEEHIIV_API_KEY", raising=False)
    monkeypatch.setenv("BEEHIIV_PUBLICATION_ID", "pub-123")
    from beehiiv import create_draft
    with patch("httpx.post") as mock_post:
        result = create_draft(title="Test", content="<p>hi</p>")
    assert result is None
    mock_post.assert_not_called()


def test_missing_publication_id_returns_none(monkeypatch):
    """No BEEHIIV_PUBLICATION_ID: skip gracefully, no HTTP call."""
    monkeypatch.setenv("BEEHIIV_API_KEY", "key-abc")
    monkeypatch.delenv("BEEHIIV_PUBLICATION_ID", raising=False)
    from beehiiv import create_draft
    with patch("httpx.post") as mock_post:
        result = create_draft(title="Test", content="<p>hi</p>")
    assert result is None
    mock_post.assert_not_called()


def test_both_env_vars_missing_returns_none(monkeypatch):
    """Neither env var set: skip gracefully."""
    monkeypatch.delenv("BEEHIIV_API_KEY", raising=False)
    monkeypatch.delenv("BEEHIIV_PUBLICATION_ID", raising=False)
    from beehiiv import create_draft
    with patch("httpx.post") as mock_post:
        result = create_draft(title="Test", content="<p>hi</p>")
    assert result is None
    mock_post.assert_not_called()


# ═════════════════════════════════════════════════════════════════════════════
# Successful draft creation
# ═════════════════════════════════════════════════════════════════════════════

def test_successful_draft_returns_url(monkeypatch):
    """200 response with data.url: return the URL."""
    monkeypatch.setenv("BEEHIIV_API_KEY", "key-abc")
    monkeypatch.setenv("BEEHIIV_PUBLICATION_ID", "pub-123")
    from beehiiv import create_draft
    fake_resp = _http_response(201, {
        "data": {
            "id": "post-999",
            "url": "https://www.beehiiv.com/p/my-newsletter-draft",
        }
    })
    with patch("httpx.post", return_value=fake_resp) as mock_post:
        result = create_draft(title="My Subject", content="<p>body</p>")
    assert result == "https://www.beehiiv.com/p/my-newsletter-draft"
    mock_post.assert_called_once()


def test_successful_draft_returns_id_when_url_absent(monkeypatch):
    """200 response with data.id but no url: fall back to post ID."""
    monkeypatch.setenv("BEEHIIV_API_KEY", "key-abc")
    monkeypatch.setenv("BEEHIIV_PUBLICATION_ID", "pub-123")
    from beehiiv import create_draft
    fake_resp = _http_response(200, {
        "data": {
            "id": "post-777",
        }
    })
    with patch("httpx.post", return_value=fake_resp):
        result = create_draft(title="Subject", content="<p>content</p>")
    assert result == "post-777"


def test_successful_draft_payload_shape(monkeypatch):
    """Verify the POST payload matches the beehiiv API contract."""
    monkeypatch.setenv("BEEHIIV_API_KEY", "key-abc")
    monkeypatch.setenv("BEEHIIV_PUBLICATION_ID", "pub-123")
    from beehiiv import create_draft
    fake_resp = _http_response(201, {"data": {"id": "post-1", "url": "https://beehiiv.com/p/x"}})
    with patch("httpx.post", return_value=fake_resp) as mock_post:
        create_draft(title="Hello World", content="<p>newsletter</p>", subtitle="Preview text")
    call_kwargs = mock_post.call_args.kwargs
    payload = call_kwargs["json"]
    assert payload["status"] == "draft"
    assert payload["title"] == "Hello World"
    assert payload["subtitle"] == "Preview text"
    assert payload["content"]["free"]["web"]["type"] == "html"
    assert payload["content"]["free"]["web"]["value"] == "<p>newsletter</p>"


def test_subtitle_omitted_when_not_provided(monkeypatch):
    """subtitle key must not appear in payload when subtitle=None."""
    monkeypatch.setenv("BEEHIIV_API_KEY", "key-abc")
    monkeypatch.setenv("BEEHIIV_PUBLICATION_ID", "pub-123")
    from beehiiv import create_draft
    fake_resp = _http_response(200, {"data": {"id": "post-2", "url": "https://beehiiv.com/p/y"}})
    with patch("httpx.post", return_value=fake_resp) as mock_post:
        create_draft(title="No Subtitle", content="<p>body</p>")
    payload = mock_post.call_args.kwargs["json"]
    assert "subtitle" not in payload


def test_auth_header_uses_bearer_token(monkeypatch):
    """Authorization header must be 'Bearer <key>'."""
    monkeypatch.setenv("BEEHIIV_API_KEY", "my-secret-key")
    monkeypatch.setenv("BEEHIIV_PUBLICATION_ID", "pub-456")
    from beehiiv import create_draft
    fake_resp = _http_response(201, {"data": {"id": "post-3", "url": "https://beehiiv.com/p/z"}})
    with patch("httpx.post", return_value=fake_resp) as mock_post:
        create_draft(title="Auth test", content="<p>x</p>")
    headers = mock_post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer my-secret-key"


# ═════════════════════════════════════════════════════════════════════════════
# API error handling (non-fatal)
# ═════════════════════════════════════════════════════════════════════════════

def test_api_400_returns_none(monkeypatch):
    """HTTP 4xx: non-fatal, returns None."""
    monkeypatch.setenv("BEEHIIV_API_KEY", "key-abc")
    monkeypatch.setenv("BEEHIIV_PUBLICATION_ID", "pub-123")
    from beehiiv import create_draft
    fake_resp = _http_response(400, text="bad request")
    with patch("httpx.post", return_value=fake_resp):
        result = create_draft(title="Test", content="<p>x</p>")
    assert result is None


def test_api_500_returns_none(monkeypatch):
    """HTTP 5xx: non-fatal, returns None."""
    monkeypatch.setenv("BEEHIIV_API_KEY", "key-abc")
    monkeypatch.setenv("BEEHIIV_PUBLICATION_ID", "pub-123")
    from beehiiv import create_draft
    fake_resp = _http_response(500, text="internal server error")
    with patch("httpx.post", return_value=fake_resp):
        result = create_draft(title="Test", content="<p>x</p>")
    assert result is None


def test_network_error_returns_none(monkeypatch):
    """Network exception: non-fatal, returns None."""
    monkeypatch.setenv("BEEHIIV_API_KEY", "key-abc")
    monkeypatch.setenv("BEEHIIV_PUBLICATION_ID", "pub-123")
    from beehiiv import create_draft
    with patch("httpx.post", side_effect=Exception("connection refused")):
        result = create_draft(title="Test", content="<p>x</p>")
    assert result is None


def test_non_json_response_returns_none(monkeypatch):
    """Non-JSON 200 body: non-fatal, returns None."""
    monkeypatch.setenv("BEEHIIV_API_KEY", "key-abc")
    monkeypatch.setenv("BEEHIIV_PUBLICATION_ID", "pub-123")
    from beehiiv import create_draft
    fake_resp = _http_response(200, text="not json at all")
    with patch("httpx.post", return_value=fake_resp):
        result = create_draft(title="Test", content="<p>x</p>")
    assert result is None


def test_missing_id_and_url_in_response_returns_none(monkeypatch):
    """200 but no id or url fields: non-fatal, returns None."""
    monkeypatch.setenv("BEEHIIV_API_KEY", "key-abc")
    monkeypatch.setenv("BEEHIIV_PUBLICATION_ID", "pub-123")
    from beehiiv import create_draft
    fake_resp = _http_response(200, {"data": {"status": "draft"}})
    with patch("httpx.post", return_value=fake_resp):
        result = create_draft(title="Test", content="<p>x</p>")
    assert result is None
