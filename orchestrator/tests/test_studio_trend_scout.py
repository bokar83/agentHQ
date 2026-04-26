"""Unit tests for studio_trend_scout.py.

Mocks YouTube Data API + Notion + Telegram. No network calls.
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


@pytest.fixture(autouse=True)
def _env_setup(monkeypatch):
    monkeypatch.setenv("NOTION_STUDIO_PIPELINE_DB_ID", "test-db-id")
    monkeypatch.setenv("OWNER_TELEGRAM_CHAT_ID", "12345")


# ═════════════════════════════════════════════════════════════════════════════
# Seeds loading
# ═════════════════════════════════════════════════════════════════════════════

def test_load_seeds_falls_back_to_module_default():
    """When no file exists, returns the module-level _DEFAULT_SEEDS."""
    import studio_trend_scout as scout
    seeds = scout._load_seeds()
    assert "african-folktales" in seeds
    assert "ai-displacement" in seeds
    assert "first-gen-money" in seeds


def test_load_seeds_reads_env_override(tmp_path, monkeypatch):
    custom = tmp_path / "custom_seeds.json"
    custom.write_text(json.dumps({"test-niche": {"channel": "X", "youtube_seed_search_terms": []}}))
    monkeypatch.setenv("STUDIO_TREND_SEEDS_FILE", str(custom))
    import importlib
    import studio_trend_scout as scout
    importlib.reload(scout)
    seeds = scout._load_seeds()
    assert "test-niche" in seeds


# ═════════════════════════════════════════════════════════════════════════════
# YouTube API helpers (mocked)
# ═════════════════════════════════════════════════════════════════════════════

def test_yt_api_key_returns_none_when_missing(monkeypatch):
    import studio_trend_scout as scout
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert scout._yt_api_key() is None


def test_yt_api_key_prefers_youtube_over_google(monkeypatch):
    import studio_trend_scout as scout
    monkeypatch.setenv("YOUTUBE_API_KEY", "yt-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    assert scout._yt_api_key() == "yt-key"


def test_yt_api_key_falls_back_to_google_api_key(monkeypatch):
    import studio_trend_scout as scout
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    assert scout._yt_api_key() == "google-key"


def test_yt_search_returns_empty_without_api_key(monkeypatch):
    import studio_trend_scout as scout
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert scout._yt_search("anything") == []


# ═════════════════════════════════════════════════════════════════════════════
# scout_niche (mocked YouTube)
# ═════════════════════════════════════════════════════════════════════════════

def _yt_search_response(items):
    """Build a mocked httpx response object."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"items": items}
    return resp


def _video_search_item(vid, title, channel_title="Test Channel", published="2026-04-25T12:00:00Z"):
    return {
        "id": {"videoId": vid},
        "snippet": {
            "title": title,
            "channelTitle": channel_title,
            "publishedAt": published,
        },
    }


def _video_stats_item(vid, views=1000, duration="PT5M"):
    return {
        "id": vid,
        "statistics": {"viewCount": str(views)},
        "contentDetails": {"duration": duration},
    }


def test_scout_niche_returns_empty_without_api_key(monkeypatch):
    import studio_trend_scout as scout
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    config = {"channel": "Test", "youtube_seed_search_terms": ["test"]}
    candidates = scout.scout_niche("test-niche", config)
    assert candidates == []


def test_scout_niche_scores_by_view_velocity(monkeypatch):
    import studio_trend_scout as scout
    monkeypatch.setenv("YOUTUBE_API_KEY", "test-key")

    def fake_get(self, url, params=None, **kwargs):
        if "search" in url:
            return _yt_search_response([
                _video_search_item("vid1", "high velocity"),
                _video_search_item("vid2", "low velocity"),
            ])
        elif "videos" in url:
            return _yt_search_response([
                _video_stats_item("vid1", views=10000),
                _video_stats_item("vid2", views=100),
            ])
        return MagicMock(status_code=404)

    with patch("httpx.Client.get", fake_get):
        config = {"channel": "Test Channel", "youtube_seed_search_terms": ["x"]}
        candidates = scout.scout_niche("test-niche", config)

    assert len(candidates) == 2
    # vid1 should rank first (higher views, same time delta)
    assert candidates[0].source_url.endswith("vid1")
    assert candidates[0].views == 10000
    assert candidates[0].channel == "Test Channel"
    assert candidates[0].niche == "test-niche"


def test_scout_niche_dedupes_video_ids_across_search_terms(monkeypatch):
    """Same vid returned by multiple search terms should appear once."""
    import studio_trend_scout as scout
    monkeypatch.setenv("YOUTUBE_API_KEY", "test-key")

    def fake_get(self, url, params=None, **kwargs):
        if "search" in url:
            # Both terms return the same video
            return _yt_search_response([_video_search_item("dup-vid", "duplicate")])
        elif "videos" in url:
            return _yt_search_response([_video_stats_item("dup-vid", views=5000)])
        return MagicMock(status_code=404)

    with patch("httpx.Client.get", fake_get):
        config = {"channel": "Test", "youtube_seed_search_terms": ["term1", "term2"]}
        candidates = scout.scout_niche("test-niche", config)

    assert len(candidates) == 1


def test_scout_niche_respects_top_n_cap(monkeypatch):
    import studio_trend_scout as scout
    monkeypatch.setenv("YOUTUBE_API_KEY", "test-key")
    monkeypatch.setenv("STUDIO_TREND_SCOUT_TOP_N", "3")

    # Reload to pick up env-var override
    import importlib
    importlib.reload(scout)

    items = [_video_search_item(f"vid-{i}", f"t-{i}") for i in range(8)]
    stats = [_video_stats_item(f"vid-{i}", views=i * 1000) for i in range(8)]

    def fake_get(self, url, params=None, **kwargs):
        if "search" in url:
            return _yt_search_response(items)
        elif "videos" in url:
            return _yt_search_response(stats)
        return MagicMock(status_code=404)

    with patch("httpx.Client.get", fake_get):
        config = {"channel": "Test", "youtube_seed_search_terms": ["x"]}
        candidates = scout.scout_niche("test-niche", config)

    assert len(candidates) == 3


# ═════════════════════════════════════════════════════════════════════════════
# Idempotency: existing-source-URLs filter
# ═════════════════════════════════════════════════════════════════════════════

def test_existing_source_urls_returns_set():
    import studio_trend_scout as scout
    notion = MagicMock()
    notion.query_database.return_value = [
        {"properties": {"Source URL": {"url": "https://youtube.com/watch?v=a"}}},
        {"properties": {"Source URL": {"url": "https://youtube.com/watch?v=b"}}},
        {"properties": {"Source URL": {"url": None}}},
    ]
    out = scout._existing_source_urls_today(notion, "2026-04-25")
    assert "https://youtube.com/watch?v=a" in out
    assert "https://youtube.com/watch?v=b" in out
    assert len(out) == 2


def test_existing_source_urls_returns_empty_without_db_id(monkeypatch):
    """No env var = empty set. Implementation reads env lazily so no module reload needed."""
    import studio_trend_scout as scout
    monkeypatch.delenv("NOTION_STUDIO_PIPELINE_DB_ID", raising=False)
    monkeypatch.setattr(scout, "PIPELINE_DB_ID", "")
    notion = MagicMock()
    out = scout._existing_source_urls_today(notion, "2026-04-25")
    assert out == set()


# ═════════════════════════════════════════════════════════════════════════════
# Telegram brief format
# ═════════════════════════════════════════════════════════════════════════════

def test_format_brief_with_picks():
    import studio_trend_scout as scout
    cand = scout.TrendCandidate(
        niche="african-folktales",
        channel="Under the Baobab",
        source_url="https://youtube.com/watch?v=xyz",
        source_channel="Test Source",
        title="A test title",
        views=5000,
        published_at="2026-04-25T12:00:00Z",
        velocity_per_hour=200.0,
    )
    msg = scout._format_brief({"african-folktales": [cand], "ai-displacement": []}, "2026-04-25")
    assert "Studio Trend Scout 2026-04-25" in msg
    assert "Under the Baobab" not in msg  # channel is in candidate niche line, not header
    assert "(no candidates this run)" in msg  # ai-displacement is empty
    assert "Total: 1 candidates" in msg


def test_format_brief_no_picks_alerts_about_api_key():
    import studio_trend_scout as scout
    msg = scout._format_brief({"african-folktales": [], "ai-displacement": []}, "2026-04-25")
    assert "0 total candidates" in msg
    assert "YOUTUBE_API_KEY" in msg


# ═════════════════════════════════════════════════════════════════════════════
# studio_trend_scout_tick (end-to-end mocked)
# ═════════════════════════════════════════════════════════════════════════════

def test_tick_with_no_api_key_still_writes_zero_candidates_and_sends_brief(monkeypatch):
    """Without YOUTUBE_API_KEY, tick still runs cleanly: 0 candidates,
    brief sent with the zero-candidates warning.
    """
    import studio_trend_scout as scout
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    notion = MagicMock()
    notion.query_database.return_value = []  # no existing records

    mock_client_cls = MagicMock(return_value=notion)
    mock_notifier = MagicMock()

    with patch("skills.forge_cli.notion_client.NotionClient", mock_client_cls), \
         patch.dict("sys.modules", {"notifier": mock_notifier}):
        scout.studio_trend_scout_tick()

    # Notion not written to (no candidates)
    assert not notion.create_page.called
    # Telegram brief sent
    assert mock_notifier.send_message.called


def test_tick_writes_candidates_when_api_returns_results(monkeypatch):
    import studio_trend_scout as scout
    monkeypatch.setenv("YOUTUBE_API_KEY", "test-key")

    notion = MagicMock()
    notion.query_database.return_value = []
    notion.create_page.return_value = {"id": "new-page-id"}

    mock_client_cls = MagicMock(return_value=notion)
    mock_notifier = MagicMock()

    def fake_get(self, url, params=None, **kwargs):
        if "search" in url:
            return _yt_search_response([_video_search_item("v1", "t1")])
        elif "videos" in url:
            return _yt_search_response([_video_stats_item("v1", views=2000)])
        return MagicMock(status_code=404)

    with patch("skills.forge_cli.notion_client.NotionClient", mock_client_cls), \
         patch.dict("sys.modules", {"notifier": mock_notifier}), \
         patch("httpx.Client.get", fake_get):
        scout.studio_trend_scout_tick()

    # Notion writes happened (one per niche per candidate)
    assert notion.create_page.call_count >= 1
    assert mock_notifier.send_message.called


def test_tick_skips_dupes_against_existing_pipeline(monkeypatch):
    """Records already in the pipeline (same Source URL) should not be re-written."""
    import studio_trend_scout as scout
    monkeypatch.setenv("YOUTUBE_API_KEY", "test-key")

    notion = MagicMock()
    # Pretend the pipeline already has this Source URL
    notion.query_database.return_value = [
        {"properties": {"Source URL": {"url": "https://youtube.com/watch?v=v1"}}}
    ]
    notion.create_page.return_value = {"id": "new-page-id"}

    mock_client_cls = MagicMock(return_value=notion)
    mock_notifier = MagicMock()

    def fake_get(self, url, params=None, **kwargs):
        if "search" in url:
            return _yt_search_response([_video_search_item("v1", "t1")])
        elif "videos" in url:
            return _yt_search_response([_video_stats_item("v1", views=2000)])
        return MagicMock(status_code=404)

    with patch("skills.forge_cli.notion_client.NotionClient", mock_client_cls), \
         patch.dict("sys.modules", {"notifier": mock_notifier}), \
         patch("httpx.Client.get", fake_get):
        scout.studio_trend_scout_tick()

    # No writes (all dupes)
    assert not notion.create_page.called
