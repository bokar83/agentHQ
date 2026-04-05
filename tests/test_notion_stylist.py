import json
import pytest
from unittest.mock import patch, MagicMock
from skills.notion_stylist.notion_stylist import NotionStylist


@pytest.fixture
def stylist():
    return NotionStylist(secret="test-secret")  # pragma: allowlist secret


def test_navigation_grid_creates_columns_without_width_ratio(stylist):
    """Columns should not include width_ratio (Notion API does not support it on create)."""
    items = [
        {"title": "Sprint Board", "emoji": "\U0001f3af"},
        {"title": "Growth Engine", "emoji": "\U0001f4b0"},
    ]
    with patch.object(stylist, '_patch', return_value={"results": []}) as mock_patch:
        stylist.create_navigation_grid("fake-page-id", items)
        payload = mock_patch.call_args[0][1]
        columns = payload["children"][0]["column_list"]["children"]
        assert len(columns) == 2
        for col in columns:
            assert "width_ratio" not in col, "width_ratio should not be in create payload"


def test_navigation_grid_chunks_into_rows(stylist):
    """More than 3 items should produce multiple column_list blocks."""
    items = [
        {"title": f"Item {i}", "emoji": "\U0001f4cc"} for i in range(5)
    ]
    with patch.object(stylist, '_patch', return_value={"results": []}) as mock_patch:
        stylist.create_navigation_grid("fake-page-id", items)
        payload = mock_patch.call_args[0][1]
        column_lists = [c for c in payload["children"] if c["type"] == "column_list"]
        assert len(column_lists) == 2, f"Expected 2 rows, got {len(column_lists)}"
        assert len(column_lists[0]["column_list"]["children"]) == 3
        assert len(column_lists[1]["column_list"]["children"]) == 2


def test_brand_color_map(stylist):
    """Brand color names should map to Notion API color values."""
    from skills.notion_stylist.notion_stylist import BRAND_COLORS
    assert BRAND_COLORS["cyan"] == "blue_background"
    assert BRAND_COLORS["orange"] == "orange_background"
    assert BRAND_COLORS["slate"] == "gray_background"
    assert BRAND_COLORS["teal"] == "green_background"
    assert BRAND_COLORS["dark"] == "default"


def test_clear_page_content(stylist):
    """clear_page_content should delete all child blocks."""
    mock_blocks = {
        "results": [
            {"id": "block-1", "has_children": False},
            {"id": "block-2", "has_children": False},
        ],
        "has_more": False,
    }
    with patch("httpx.Client") as MockClient:
        client = MockClient.return_value.__enter__.return_value
        client.get.return_value = MagicMock(status_code=200, json=lambda: mock_blocks)
        client.delete.return_value = MagicMock(status_code=200)
        stylist.clear_page_content("fake-page-id")
        assert client.delete.call_count == 2


def test_compute_ratios_sum_to_one():
    """Ratios should always sum to 1.0."""
    for n in range(1, 6):
        ratios = NotionStylist._compute_ratios(n)
        assert len(ratios) == n
        assert abs(sum(ratios) - 1.0) < 0.01, f"n={n}: ratios sum to {sum(ratios)}"
