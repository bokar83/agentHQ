"""Tests for newsletter anchor selection in studio_trend_scout."""
from __future__ import annotations

import os
import sys
from datetime import date
from unittest.mock import MagicMock, patch

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)


def _make_pick(
    title: str,
    fit_score: int,
    velocity_per_hour: float,
    url: str,
    notion_page_id: str = "",
):
    from studio_trend_scout import TrendCandidate

    return TrendCandidate(
        niche="catalyst",
        channel="Catalyst Works",
        source_url=url,
        source_channel="Example Source",
        title=title,
        views=0,
        published_at="2026-05-04T06:00:00+00:00",
        velocity_per_hour=velocity_per_hour,
        fit_score=fit_score,
        medium="Newsletter",
        first_line="opening line",
        unique_add="unique angle",
        destination="Content Board",
        snippet="snippet",
        notion_page_id=notion_page_id,
    )


def test_anchor_reuses_existing_newsletter_page_for_sunday_reply():
    from studio_trend_scout import _select_and_tag_anchor

    notion = MagicMock()
    notion.query_database.return_value = [
        {
            "id": "existing-anchor-page",
            "properties": {
                "Anchor Date": {"date": {"start": "2026-05-04"}},
                "Type": {"select": {"name": "Newsletter"}},
            },
        }
    ]

    with patch("studio_trend_scout.get_reply_for_week", return_value="Clients want X."), \
         patch("studio_trend_scout._send_anchor_alert") as mock_alert:
        page_id = _select_and_tag_anchor(notion, [_make_pick("Top pick", 5, 80.0, "https://a.com")], date(2026, 5, 4))

    assert page_id == "existing-anchor-page"
    notion.create_page.assert_not_called()
    notion.update_page.assert_not_called()
    mock_alert.assert_not_called()


def test_anchor_creates_synthetic_newsletter_page_for_sunday_reply_when_missing():
    from studio_trend_scout import _select_and_tag_anchor

    notion = MagicMock()
    notion.query_database.return_value = []
    notion.create_page.return_value = {"id": "synthetic-page-id"}

    with patch("studio_trend_scout.get_reply_for_week", return_value="Clients keep asking about margin visibility."), \
         patch("studio_trend_scout._send_anchor_alert") as mock_alert:
        page_id = _select_and_tag_anchor(notion, [_make_pick("Top pick", 5, 80.0, "https://a.com")], date(2026, 5, 4))

    assert page_id == "synthetic-page-id"
    notion.update_page.assert_not_called()
    notion.create_page.assert_called_once()
    props = notion.create_page.call_args.kwargs["properties"]
    assert props["Type"]["select"]["name"] == "Newsletter"
    assert props["Status"]["select"]["name"] == "Ready"
    assert props["Anchor Date"]["date"]["start"] == "2026-05-04"
    assert "Clients keep asking about margin visibility." in props["Title"]["title"][0]["text"]["content"]
    mock_alert.assert_not_called()


def test_anchor_uses_highest_ranked_untyped_scout_pick():
    from studio_trend_scout import _select_and_tag_anchor

    notion = MagicMock()
    notion.query_database.return_value = []
    notion.get_page.side_effect = [
        {"id": "typed-page", "properties": {"Type": {"select": {"name": "LinkedIn Post"}}}},
        {"id": "winner-page", "properties": {"Type": {"select": None}}},
    ]

    picks = [
        _make_pick("Lower fit", 3, 200.0, "https://lower.com", notion_page_id="lower-page"),
        _make_pick("Typed top fit", 5, 400.0, "https://typed.com", notion_page_id="typed-page"),
        _make_pick("Winner", 5, 250.0, "https://winner.com", notion_page_id="winner-page"),
    ]

    with patch("studio_trend_scout.get_reply_for_week", return_value=None), \
         patch("studio_trend_scout._send_anchor_alert") as mock_alert:
        page_id = _select_and_tag_anchor(notion, picks, date(2026, 5, 4))

    assert page_id == "winner-page"
    notion.update_page.assert_called_once()
    assert notion.update_page.call_args.args[0] == "winner-page"
    props = notion.update_page.call_args.kwargs["properties"]
    assert props["Type"]["select"]["name"] == "Newsletter"
    assert props["Anchor Date"]["date"]["start"] == "2026-05-04"
    mock_alert.assert_not_called()


def test_anchor_alerts_when_all_top_picks_already_typed():
    from studio_trend_scout import _select_and_tag_anchor

    notion = MagicMock()
    notion.query_database.return_value = []
    notion.get_page.side_effect = [
        {"id": "page-1", "properties": {"Type": {"select": {"name": "LinkedIn Post"}}}},
        {"id": "page-2", "properties": {"Type": {"select": {"name": "X Post"}}}},
    ]

    picks = [
        _make_pick("Top pick", 5, 400.0, "https://typed-a.com", notion_page_id="page-1"),
        _make_pick("Second pick", 4, 300.0, "https://typed-b.com", notion_page_id="page-2"),
    ]

    with patch("studio_trend_scout.get_reply_for_week", return_value=None), \
         patch("studio_trend_scout._send_anchor_alert") as mock_alert:
        page_id = _select_and_tag_anchor(notion, picks, date(2026, 5, 4))

    assert page_id is None
    notion.update_page.assert_not_called()
    notion.create_page.assert_not_called()
    mock_alert.assert_called_once()
    assert "all top picks already typed; tag manually" in mock_alert.call_args.args[0]
