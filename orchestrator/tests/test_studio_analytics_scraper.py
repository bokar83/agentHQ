"""Regression tests for studio_analytics_scraper.py YouTube view parsing.

Locks the 2026-05-15 fix for the locale + originalViewCount bug:

- VPS curl on YouTube watch pages returned Indonesian-locale view text
  ("14 tontonan" instead of "14 views"), and the parser only matched the
  English regex on `originalViewCount`. For low-view videos
  YouTube serves `originalViewCount: "0"` regardless of locale, so even
  the English path silently wrote 0 to Notion.

Concrete failures captured 2026-05-14:
  AIC 5_W94dhnJDU -- real 14 views, Notion stored 0
  UTB 5W0A3jf8Gcs -- real 57 views, Notion stored 0
  AIC gkLqInBX9QU -- real 24 views, Notion stored 24 (parsed by accident)

Tests:
  1. Indonesian-locale low-view video parses correct integer
  2. English-locale low-view video parses correct integer
  3. originalViewCount = 0 does NOT win over simpleText
  4. Comma thousand separator works (1,234)
  5. Dot thousand separator works (1.234 European style)
  6. Spanish "vistas" parses
  7. French "vues" parses
  8. Empty / no-match returns None
  9. _parse_leading_int handles edge cases
 10. Full _scrape_views with mocked httpx forces en-US Accept-Language
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)

from studio_analytics_scraper import (  # noqa: E402
    _parse_leading_int,
    _parse_youtube_views,
    _scrape_views,
    _HTTP_HEADERS,
)


# ---- Fixtures: realistic snippets captured from production VPS curls ----

YT_INDONESIAN_LOW_VIEW = (
    '{"videoViewCountRenderer":{"viewCount":{"simpleText":"14 tontonan"},'
    '"shortViewCount":{"simpleText":"14 tontonan"}}},'
    '"originalViewCount":"0"'
)

YT_ENGLISH_LOW_VIEW = (
    '{"videoViewCountRenderer":{"viewCount":{"simpleText":"57 views"},'
    '"shortViewCount":{"simpleText":"57 views"}}},'
    '"originalViewCount":"0"'
)

YT_HIGH_VIEW_WITH_COMMA = (
    '{"videoViewCountRenderer":{"viewCount":{"simpleText":"1,234 views"},'
    '"shortViewCount":{"simpleText":"1.2K views"}}},'
    '"originalViewCount":"1234"'
)

YT_SPANISH = (
    '{"videoViewCountRenderer":{"viewCount":{"simpleText":"42 vistas"}}}'
)

YT_FRENCH = (
    '{"videoViewCountRenderer":{"viewCount":{"simpleText":"99 vues"}}}'
)

YT_EUROPEAN_DOT_SEPARATOR = (
    '{"videoViewCountRenderer":{"viewCount":{"simpleText":"1.234 visualizaciones"}}}'
)


# ---- _parse_leading_int unit tests ----

class TestParseLeadingInt:
    def test_simple_integer(self):
        assert _parse_leading_int("14") == 14

    def test_with_trailing_word(self):
        assert _parse_leading_int("14 views") == 14

    def test_indonesian(self):
        assert _parse_leading_int("14 tontonan") == 14

    def test_comma_separator(self):
        assert _parse_leading_int("1,234 views") == 1234

    def test_european_dot_separator(self):
        # German / Spanish thousands use "1.234"
        assert _parse_leading_int("1.234 vistas") == 1234

    def test_space_separator(self):
        # French uses non-breaking space; ASCII space here for portability
        assert _parse_leading_int("1 234 vues") == 1234

    def test_empty_string(self):
        assert _parse_leading_int("") is None

    def test_no_digits(self):
        assert _parse_leading_int("views") is None

    def test_leading_whitespace(self):
        assert _parse_leading_int("   42 views") == 42


# ---- _parse_youtube_views integration tests ----

class TestParseYoutubeViews:
    def test_indonesian_low_view_does_not_return_zero(self):
        """The exact bug from 2026-05-14: 14 tontonan + originalViewCount:0
        must return 14, not 0."""
        result = _parse_youtube_views(YT_INDONESIAN_LOW_VIEW)
        assert result == 14

    def test_english_low_view(self):
        assert _parse_youtube_views(YT_ENGLISH_LOW_VIEW) == 57

    def test_high_view_with_comma(self):
        assert _parse_youtube_views(YT_HIGH_VIEW_WITH_COMMA) == 1234

    def test_spanish(self):
        assert _parse_youtube_views(YT_SPANISH) == 42

    def test_french(self):
        assert _parse_youtube_views(YT_FRENCH) == 99

    def test_european_dot_separator(self):
        assert _parse_youtube_views(YT_EUROPEAN_DOT_SEPARATOR) == 1234

    def test_no_match_returns_none(self):
        assert _parse_youtube_views("<html>nothing</html>") is None

    def test_only_originalviewcount_zero_returns_none(self):
        """If the only signal is originalViewCount:0, return None
        instead of the misleading 0."""
        html = '"originalViewCount":"0"'
        assert _parse_youtube_views(html) is None

    def test_originalviewcount_nonzero_used_as_fallback(self):
        """If simpleText is missing but originalViewCount > 0, use it."""
        html = '"originalViewCount":"5000"'
        assert _parse_youtube_views(html) == 5000


# ---- _scrape_views: verify Accept-Language header is sent ----

class TestScrapeViewsHeaders:
    def test_youtube_request_sends_en_us_accept_language(self):
        """Belt-and-suspenders: even with the locale-tolerant parser,
        we force en-US to get the simpler English text path."""
        mock_response = MagicMock()
        mock_response.text = YT_ENGLISH_LOW_VIEW
        mock_response.raise_for_status = MagicMock()

        with patch("studio_analytics_scraper.httpx.get", return_value=mock_response) as mock_get:
            result = _scrape_views("https://www.youtube.com/watch?v=abc", "youtube")

        assert result == 57
        # Verify the Accept-Language header went out
        call_kwargs = mock_get.call_args.kwargs
        assert "headers" in call_kwargs
        assert call_kwargs["headers"]["Accept-Language"].startswith("en-US")

    def test_x_platform_short_circuits(self):
        # No HTTP call for X (handled separately)
        with patch("studio_analytics_scraper.httpx.get") as mock_get:
            assert _scrape_views("https://x.com/foo", "x") is None
            mock_get.assert_not_called()

    def test_indonesian_payload_via_scrape_views(self):
        """End-to-end: even if YT ignores Accept-Language and serves
        Indonesian, we still parse correctly."""
        mock_response = MagicMock()
        mock_response.text = YT_INDONESIAN_LOW_VIEW
        mock_response.raise_for_status = MagicMock()

        with patch("studio_analytics_scraper.httpx.get", return_value=mock_response):
            result = _scrape_views("https://www.youtube.com/watch?v=5_W94dhnJDU", "youtube")

        assert result == 14, "Indonesian-locale low-view bug regression"


def test_http_headers_module_constant_present():
    """Sanity: the headers constant is exported and contains the expected fields."""
    assert "Accept-Language" in _HTTP_HEADERS
    assert "User-Agent" in _HTTP_HEADERS
