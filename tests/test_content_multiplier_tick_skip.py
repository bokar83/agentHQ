# tests/test_content_multiplier_tick_skip.py
"""multiplier_tick must skip records that raise ValueError in _source_from_page
and continue to the next viable record. Regression test for the 2026-05-12/13
"bad first record crashes every 5-min tick forever" bug.
"""
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "orchestrator"))
sys.path.insert(0, str(Path(__file__).parent.parent))


def _bad_page():
    return {"id": "bad-page-id", "properties": {}}


def _good_page():
    return {"id": "good-page-id", "properties": {}}


def _source_side_effect(page):
    if page["id"] == "bad-page-id":
        raise ValueError("Multiply record has no Source URL, URL, Link, or Draft: bad-page-id")
    return "https://example.com/good-source"


def test_multiplier_tick_skips_bad_record_and_uses_next(caplog):
    """Bad first record: skipped with warning. Good second record: picked and multiplied."""
    import content_multiplier_crew as cmc

    mock_notion = MagicMock()
    mock_notion.query_database.return_value = [_bad_page(), _good_page()]

    with (
        patch.object(cmc, "_notion_client", return_value=mock_notion),
        patch.object(cmc, "_content_db_id", return_value="db-id"),
        patch.object(cmc, "_source_from_page", side_effect=_source_side_effect) as mock_source,
        patch.object(cmc, "multiply_source") as mock_multiply,
        patch.object(cmc, "_remix_notes_from_page", return_value=None),
        caplog.at_level(logging.WARNING, logger="agentsHQ.content_multiplier_crew"),
    ):
        cmc.multiplier_tick()

    # multiply_source was called once, with the GOOD source
    assert mock_multiply.call_count == 1
    call_kwargs = mock_multiply.call_args.kwargs
    assert mock_multiply.call_args.args[0] == "https://example.com/good-source"
    assert call_kwargs["source_trend_notion_id"] == "good-page-id"

    # Notion update fired on good page only
    mock_notion.update_page.assert_called_once()
    assert mock_notion.update_page.call_args.args[0] == "good-page-id"

    # _source_from_page tried twice (once for each row)
    assert mock_source.call_count == 2

    # A warning was logged for the bad page
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("bad-page-id" in r.getMessage() for r in warnings), (
        f"Expected warning mentioning bad-page-id, got: {[r.getMessage() for r in warnings]}"
    )


def test_multiplier_tick_does_not_raise_when_all_records_bad(caplog):
    """All records bad: tick logs and returns cleanly. No exception bubbles."""
    import content_multiplier_crew as cmc

    mock_notion = MagicMock()
    mock_notion.query_database.return_value = [_bad_page(), _bad_page()]

    with (
        patch.object(cmc, "_notion_client", return_value=mock_notion),
        patch.object(cmc, "_content_db_id", return_value="db-id"),
        patch.object(cmc, "_source_from_page", side_effect=_source_side_effect),
        patch.object(cmc, "multiply_source") as mock_multiply,
        patch.object(cmc, "_remix_notes_from_page", return_value=None),
        caplog.at_level(logging.WARNING, logger="agentsHQ.content_multiplier_crew"),
    ):
        # MUST NOT raise
        cmc.multiplier_tick()

    # multiply_source never called
    mock_multiply.assert_not_called()
    # Notion update_page never called
    mock_notion.update_page.assert_not_called()

    # Warnings logged for both bad pages
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) >= 2


def test_multiplier_tick_happy_path_unchanged(caplog):
    """Good first record: behaves exactly as before. No skip, no warning."""
    import content_multiplier_crew as cmc

    mock_notion = MagicMock()
    mock_notion.query_database.return_value = [_good_page()]

    with (
        patch.object(cmc, "_notion_client", return_value=mock_notion),
        patch.object(cmc, "_content_db_id", return_value="db-id"),
        patch.object(cmc, "_source_from_page", side_effect=_source_side_effect),
        patch.object(cmc, "multiply_source") as mock_multiply,
        patch.object(cmc, "_remix_notes_from_page", return_value=None),
        caplog.at_level(logging.WARNING, logger="agentsHQ.content_multiplier_crew"),
    ):
        cmc.multiplier_tick()

    assert mock_multiply.call_count == 1
    assert mock_multiply.call_args.args[0] == "https://example.com/good-source"
    mock_notion.update_page.assert_called_once()

    # No skip warnings
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    skip_warnings = [r for r in warnings if "skipping page" in r.getMessage()]
    assert skip_warnings == []
