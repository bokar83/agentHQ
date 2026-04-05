from unittest.mock import MagicMock
from skills.forge_cli.kpi import KPIRefresher


def _make_page(props):
    return {"properties": props}


def test_pipeline_total():
    mock_client = MagicMock()
    mock_client.query_database.return_value = [
        _make_page({"Deal Value": {"number": 5000}, "Status": {"select": {"name": "Discovery"}}}),
        _make_page({"Deal Value": {"number": 3000}, "Status": {"select": {"name": "Proposal"}}}),
        _make_page({"Deal Value": {"number": 2000}, "Status": {"select": {"name": "Closed Lost"}}}),
    ]
    kpi = KPIRefresher(client=mock_client)
    total = kpi.compute_pipeline_total()
    assert total == 10000  # All 3 pages returned by mock; Closed Lost filtering happens at Notion API level


def test_revenue_mtd():
    mock_client = MagicMock()
    mock_client.query_database.return_value = [
        _make_page({"Amount": {"number": 2500}}),
        _make_page({"Amount": {"number": 1500}}),
    ]
    kpi = KPIRefresher(client=mock_client)
    total = kpi.compute_revenue_mtd()
    assert total == 4000


def test_format_kpi_text():
    kpi = KPIRefresher(client=MagicMock())
    text = kpi.format_kpi("Pipeline $", 8000)
    assert "$8,000" in text
    assert "Pipeline $" in text
