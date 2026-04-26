"""Unit tests for blotato_publisher.py.

Mocks httpx.Client so no real HTTP calls fire. Covers: success path, failure
status, timeout, malformed response, missing API key, missing platform,
unsupported platform, normalize Notion-side platform name.
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
# Init
# ═════════════════════════════════════════════════════════════════════════════

def test_init_requires_api_key(monkeypatch):
    monkeypatch.delenv("BLOTATO_API_KEY", raising=False)
    from blotato_publisher import BlotatoPublisher
    with pytest.raises(ValueError, match="BLOTATO_API_KEY"):
        BlotatoPublisher()


def test_init_uses_explicit_api_key():
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="explicit-key")
    assert pub.api_key == "explicit-key"


def test_init_reads_env_api_key(monkeypatch):
    monkeypatch.setenv("BLOTATO_API_KEY", "env-key")
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher()
    assert pub.api_key == "env-key"


# ═════════════════════════════════════════════════════════════════════════════
# publish() input validation
# ═════════════════════════════════════════════════════════════════════════════

def test_publish_empty_text_raises():
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    with pytest.raises(ValueError, match="text"):
        pub.publish(text="", account_id="123", platform="linkedin")


def test_publish_missing_account_id_raises():
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    with pytest.raises(ValueError, match="account_id"):
        pub.publish(text="hi", account_id="", platform="linkedin")


def test_publish_unsupported_platform_raises():
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    with pytest.raises(ValueError, match="unsupported platform"):
        pub.publish(text="hi", account_id="123", platform="myspace")


def test_publish_normalizes_notion_platform_name():
    """Notion uses 'X', Blotato uses 'twitter'. Publisher normalizes."""
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    fake_client = MagicMock()
    fake_client.post.return_value = _http_response(200, {"postSubmissionId": "sub-1"})
    pub._client = fake_client
    sub_id = pub.publish(text="hi", account_id="17065", platform="X")
    assert sub_id == "sub-1"
    # Verify the body sent to Blotato uses 'twitter', not 'X'.
    posted = fake_client.post.call_args
    body = posted.kwargs["json"]
    assert body["post"]["content"]["platform"] == "twitter"
    assert body["post"]["target"]["targetType"] == "twitter"


def test_publish_normalizes_linkedin_personal():
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    fake_client = MagicMock()
    fake_client.post.return_value = _http_response(200, {"postSubmissionId": "sub-2"})
    pub._client = fake_client
    sub_id = pub.publish(text="hi", account_id="19365", platform="LinkedIn")
    assert sub_id == "sub-2"
    body = fake_client.post.call_args.kwargs["json"]
    assert body["post"]["target"]["targetType"] == "linkedin"
    # Personal LinkedIn omits pageId.
    assert "pageId" not in body["post"]["target"]


def test_publish_includes_page_id_for_company_page():
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    fake_client = MagicMock()
    fake_client.post.return_value = _http_response(200, {"postSubmissionId": "sub-3"})
    pub._client = fake_client
    pub.publish(
        text="hi", account_id="19365", platform="LinkedIn",
        page_id="company-999",
    )
    body = fake_client.post.call_args.kwargs["json"]
    assert body["post"]["target"]["pageId"] == "company-999"


def test_publish_scheduled_time_is_root_level_not_inside_post():
    """CRITICAL: scheduledTime must be sibling of post, not inside it.
    Misnesting causes silent immediate publish per Blotato docs.
    """
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    fake_client = MagicMock()
    fake_client.post.return_value = _http_response(200, {"postSubmissionId": "sub-4"})
    pub._client = fake_client
    pub.publish(
        text="hi", account_id="123", platform="twitter",
        scheduled_time_iso="2026-05-01T10:00:00Z",
    )
    body = fake_client.post.call_args.kwargs["json"]
    assert body["scheduledTime"] == "2026-05-01T10:00:00Z"
    assert "scheduledTime" not in body["post"], "scheduledTime must NOT be nested inside post"


# ═════════════════════════════════════════════════════════════════════════════
# publish() error handling
# ═════════════════════════════════════════════════════════════════════════════

def test_publish_http_500_raises_runtimeerror():
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    fake_client = MagicMock()
    fake_client.post.return_value = _http_response(500, text="internal error")
    pub._client = fake_client
    with pytest.raises(RuntimeError, match="500"):
        pub.publish(text="hi", account_id="123", platform="twitter")


def test_publish_http_422_quota_raises_runtimeerror():
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    fake_client = MagicMock()
    fake_client.post.return_value = _http_response(422, text="quota exceeded")
    pub._client = fake_client
    with pytest.raises(RuntimeError, match="422"):
        pub.publish(text="hi", account_id="123", platform="twitter")


def test_publish_no_post_submission_id_raises():
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    fake_client = MagicMock()
    fake_client.post.return_value = _http_response(200, {"some_other_field": "value"})
    pub._client = fake_client
    with pytest.raises(RuntimeError, match="postSubmissionId"):
        pub.publish(text="hi", account_id="123", platform="twitter")


# ═════════════════════════════════════════════════════════════════════════════
# poll_until_terminal()
# ═════════════════════════════════════════════════════════════════════════════

def test_poll_returns_published_immediately():
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    fake_client = MagicMock()
    fake_client.get.return_value = _http_response(200, {
        "postSubmissionId": "sub-1",
        "status": "published",
        "publicUrl": "https://twitter.com/x/status/123",
    })
    pub._client = fake_client
    result = pub.poll_until_terminal("sub-1", timeout_sec=5, interval_sec=1)
    assert result.ok
    assert result.status == "published"
    assert result.public_url == "https://twitter.com/x/status/123"
    assert result.error_message is None


def test_poll_returns_failed_with_error_message():
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    fake_client = MagicMock()
    fake_client.get.return_value = _http_response(200, {
        "postSubmissionId": "sub-1",
        "status": "failed",
        "errorMessage": "X API rate limited",
    })
    pub._client = fake_client
    result = pub.poll_until_terminal("sub-1", timeout_sec=5, interval_sec=1)
    assert not result.ok
    assert result.status == "failed"
    assert "X API rate limited" in result.error_message


def test_poll_transient_error_then_published():
    """Network blip on first poll, success on second."""
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    fake_client = MagicMock()
    fake_client.get.side_effect = [
        _http_response(500, text="transient"),
        _http_response(200, {"status": "published", "publicUrl": "https://ok"}),
    ]
    pub._client = fake_client
    with patch("blotato_publisher.time.sleep"):
        result = pub.poll_until_terminal("sub-1", timeout_sec=10, interval_sec=1)
    assert result.ok
    assert result.public_url == "https://ok"


def test_poll_timeout_returns_timeout_status():
    """All polls return in-progress; final result is timeout."""
    import time
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    fake_client = MagicMock()
    fake_client.get.return_value = _http_response(200, {"status": "in-progress"})
    pub._client = fake_client
    # Patch time.time to advance fast: 1st call returns t0, then t0+999 (past deadline).
    real_time = time.time
    t0 = real_time()
    times = iter([t0, t0 + 0.1, t0 + 999, t0 + 999])
    with patch("blotato_publisher.time.time", side_effect=lambda: next(times, t0 + 999)):
        with patch("blotato_publisher.time.sleep"):
            result = pub.poll_until_terminal("sub-1", timeout_sec=5, interval_sec=1)
    assert result.status == "timeout"
    assert result.public_url is None


def test_poll_handles_nested_status_field():
    """Some Blotato responses nest status under 'post'. Accept both shapes."""
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    fake_client = MagicMock()
    fake_client.get.return_value = _http_response(200, {
        "post": {"status": "published", "publicUrl": "https://nested"}
    })
    pub._client = fake_client
    result = pub.poll_until_terminal("sub-1", timeout_sec=5, interval_sec=1)
    assert result.ok
    assert result.public_url == "https://nested"


# ═════════════════════════════════════════════════════════════════════════════
# get_status()
# ═════════════════════════════════════════════════════════════════════════════

def test_get_status_empty_id_raises():
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    with pytest.raises(ValueError, match="post_submission_id"):
        pub.get_status("")


def test_get_status_returns_parsed_json():
    from blotato_publisher import BlotatoPublisher
    pub = BlotatoPublisher(api_key="k")
    fake_client = MagicMock()
    fake_client.get.return_value = _http_response(200, {"status": "in-progress"})
    pub._client = fake_client
    data = pub.get_status("sub-1")
    assert data["status"] == "in-progress"
