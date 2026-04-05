from datetime import date, timedelta
from typing import Optional
from skills.forge_cli.notion_client import NotionClient
from skills.forge_cli import config


class KPIRefresher:
    """Compute KPI metrics from Notion databases and update callout blocks."""

    def __init__(self, client: Optional[NotionClient] = None):
        self.client = client or NotionClient(secret=config.NOTION_SECRET)

    def compute_pipeline_total(self) -> float:
        pages = self.client.query_database(
            config.PIPELINE_DB,
            filter_obj={
                "property": "Status",
                "select": {"does_not_equal": "Lost"},
            },
        )
        total = 0
        for p in pages:
            val = p.get("properties", {}).get("Deal Value", {}).get("number")
            if val:
                total += val
        return total

    def compute_revenue_mtd(self) -> float:
        first_of_month = date.today().replace(day=1).isoformat()
        pages = self.client.query_database(
            config.REVENUE_DB,
            filter_obj={
                "property": "Date",
                "date": {"on_or_after": first_of_month},
            },
        )
        total = 0
        for p in pages:
            val = p.get("properties", {}).get("Amount", {}).get("number")
            if val:
                total += val
        return total

    def compute_posts_this_month(self) -> int:
        first_of_month = date.today().replace(day=1).isoformat()
        pages = self.client.query_database(
            config.CONTENT_DB,
            filter_obj={
                "property": "Posted Date",
                "date": {"on_or_after": first_of_month},
            },
        )
        return len(pages)

    def compute_tasks_done_this_week(self) -> int:
        pages = self.client.query_database(
            config.TASKS_DB,
            filter_obj={
                "property": "Status",
                "select": {"equals": "Done"},
            },
        )
        return len(pages)

    @staticmethod
    def format_kpi(label: str, value, prefix: str = "$") -> str:
        if isinstance(value, (int, float)) and prefix == "$":
            formatted = f"${value:,.0f}"
        elif isinstance(value, (int, float)):
            formatted = f"{value:,}"
        else:
            formatted = str(value)
        return f"**{formatted}**\n{label}"

    def refresh_all(self):
        """Compute all KPIs and update the callout blocks on the landing page."""
        metrics = [
            ("Pipeline $", self.compute_pipeline_total(), "$", "\U0001f4b0"),
            ("Revenue MTD", self.compute_revenue_mtd(), "$", "\U0001f4b5"),
            ("Posts This Month", self.compute_posts_this_month(), "", "\U0001f4dd"),
            ("Tasks Done This Week", self.compute_tasks_done_this_week(), "", "\u2705"),
        ]
        block_ids = config.KPI_BLOCK_IDS
        results = []
        for i, (label, value, prefix, emoji) in enumerate(metrics):
            text = self.format_kpi(label, value, prefix)
            if i < len(block_ids) and block_ids[i]:
                self.client.update_block(block_ids[i], {
                    "callout": {
                        "rich_text": [{"type": "text", "text": {"content": text}}],
                        "icon": {"type": "emoji", "emoji": emoji},
                    }
                })
                results.append(f"{label}: {value}")
        return results
