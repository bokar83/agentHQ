"""Tests for Signal Works pipeline modules."""
import pytest
from unittest.mock import patch, MagicMock


def test_upsert_signal_works_lead_insert_path():
    """upsert_signal_works_lead INSERT path tags source='signal_works'."""
    from orchestrator.db import upsert_signal_works_lead
    lead = {
        "name": "Valley Dental",
        "email": "owner@valleydental.com",
        "phone": "801-555-1234",
        "website_url": "https://valleydental.com",
        "review_count": 47,
        "google_maps_url": "https://maps.google.com/?cid=12345",
        "niche": "pediatric dentist",
        "city": "Salt Lake City",
        "ai_score": 12,
    }
    with patch("orchestrator.db.get_crm_connection") as mock_conn:
        mock_cursor = MagicMock()
        # fetchone() returns None -> no existing row -> INSERT path
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__ = lambda s: mock_conn.return_value
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.return_value.cursor.return_value.__enter__ = lambda s: mock_cursor
        mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)
        upsert_signal_works_lead(lead)
        assert mock_cursor.execute.called
        # The INSERT statement is the last execute call; verify it targets 'leads'
        # and embeds the source literal 'signal_works' in the params tuple.
        insert_call = mock_cursor.execute.call_args_list[-1]
        sql, params = insert_call[0][0], insert_call[0][1]
        assert "leads" in sql.lower()
        assert "signal_works" in params


def test_scraper_returns_valid_lead_shape():
    """scrape_google_maps_leads returns list of dicts with required fields."""
    from signal_works.lead_scraper import scrape_google_maps_leads
    from unittest.mock import patch
    with patch("signal_works.lead_scraper._fetch_maps_results") as mock_fetch:
        mock_fetch.return_value = [
            {
                "name": "Test Dental",
                "phone": "801-555-0001",
                "website": "https://testdental.com",
                "rating": 4.5,
                "review_count": 62,
                "maps_url": "https://maps.google.com/?cid=99",
            }
        ]
        results = scrape_google_maps_leads("pediatric dentist", "Salt Lake City", min_reviews=20, max_reviews=100)
        assert len(results) >= 1
        r = results[0]
        assert "name" in r
        assert "review_count" in r
        assert r["review_count"] >= 20
        assert "niche" in r
        assert "city" in r


def test_ai_scorer_returns_score_dict():
    """score_business returns dict with score 0-100 and breakdown."""
    from signal_works.ai_scorer import score_business
    from unittest.mock import patch
    with patch("signal_works.ai_scorer._query_chatgpt") as mock_gpt, \
         patch("signal_works.ai_scorer._query_perplexity") as mock_perp, \
         patch("signal_works.ai_scorer._check_robots_txt") as mock_robots, \
         patch("signal_works.ai_scorer._check_serp_presence") as mock_serp:
        mock_gpt.return_value = False
        mock_perp.return_value = True
        mock_robots.return_value = True
        mock_serp.return_value = False
        result = score_business("Valley Dental", "Salt Lake City", "pediatric dentist", "https://valleydental.com")
        assert "score" in result
        assert 0 <= result["score"] <= 100
        assert "breakdown" in result
        assert result["breakdown"]["perplexity"] is True
        assert result["score"] == 50


def test_email_builder_fills_template():
    """build_email returns string with all placeholders replaced."""
    from signal_works.email_builder import build_email
    lead = {
        "name": "Valley Dental",
        "owner_name": "Dr. Smith",
        "email": "owner@valleydental.com",
        "niche": "pediatric dentist",
        "city": "Salt Lake City",
        "ai_score": 12,
        "ai_quick_wins": ["Fix robots.txt", "Claim Bing Places"],
        "demo_url": "https://demo-dental.vercel.app",
        "loom_url": "https://loom.com/share/abc123",
    }
    result = build_email(lead)
    assert "Valley Dental" in result
    assert "12/100" in result
    assert "Fix robots.txt" in result
    assert "{" not in result
