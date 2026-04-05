from datetime import datetime, date, timedelta
from typing import List, Optional
from skills.forge_cli.notion_client import NotionClient
from skills.forge_cli import config


class ForgeDB:
    """Database-specific write operations for The Forge 2.0."""

    def __init__(self, client: Optional[NotionClient] = None):
        self.client = client or NotionClient(secret=config.NOTION_SECRET)

    def log_action(self, action: str, agent: str = "System", status: str = "Success", transcript: str = "") -> dict:
        props = {
            "Action": {"title": [{"text": {"content": action}}]},
            "Agent": {"select": {"name": agent}},
            "Status": {"select": {"name": status}},
        }
        if transcript:
            props["Transcript"] = {"rich_text": [{"text": {"content": transcript[:2000]}}]}
        return self.client.create_page(database_id=config.ACTIVITY_LOG_DB, properties=props)

    # Priority map: CLI uses P1/P2/P3, Tasks DB uses High/Medium/Low
    PRIORITY_MAP = {"P1": "High", "P2": "Medium", "P3": "Low", "High": "High", "Medium": "Medium", "Low": "Low"}

    def add_task(self, task: str, priority: str = "P2", due: str = "", owner: str = "Boubacar") -> dict:
        resolved_priority = self.PRIORITY_MAP.get(priority, priority)
        props = {
            "Task": {"title": [{"text": {"content": task}}]},
            "Priority": {"select": {"name": resolved_priority}},
            "Status": {"select": {"name": "Not Started"}},
            "Owner": {"multi_select": [{"name": owner}]},
        }
        if due:
            props["Due Date"] = {"date": {"start": due}}
        return self.client.create_page(database_id=config.TASKS_DB, properties=props)

    def mark_task_done(self, page_id: str) -> dict:
        return self.client.update_page(page_id, properties={
            "Status": {"select": {"name": "Done"}},
        })

    def add_pipeline_lead(self, company: str, contact: str = "", email: str = "", value: int = 0, status: str = "New", source: str = "LinkedIn", next_action: str = "", notes: str = "") -> dict:
        props = {
            "Lead/Company": {"title": [{"text": {"content": company}}]},
            "Status": {"select": {"name": status}},
            "Source": {"select": {"name": source}},
        }
        if contact:
            props["Contact Name"] = {"rich_text": [{"text": {"content": contact}}]}
        if email:
            props["Email"] = {"email": email}
        if value:
            props["Deal Value"] = {"number": value}
        if next_action:
            props["Next Action"] = {"rich_text": [{"text": {"content": next_action}}]}
        if notes:
            props["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
        return self.client.create_page(database_id=config.PIPELINE_DB, properties=props)

    def log_revenue(self, amount: float, source: str = "Consulting", buyer: str = "", description: str = "", notes: str = "") -> dict:
        props = {
            "Offer": {"title": [{"text": {"content": description or f"Revenue - {source}"}}]},
            "Amount": {"number": amount},
            "Date": {"date": {"start": date.today().isoformat()}},
            "Source": {"select": {"name": source}},
        }
        if buyer:
            props["Buyer"] = {"rich_text": [{"text": {"content": buyer}}]}
        if notes:
            props["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
        return self.client.create_page(database_id=config.REVENUE_DB, properties=props)

    def add_content_idea(self, title: str, platforms: List[str] = None, topics: List[str] = None, content_type: str = "Post", content: str = "", agent: str = "Boubacar") -> dict:
        props = {
            "Title": {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": "Idea"}},
            "Type": {"select": {"name": content_type}},
            "Agent": {"select": {"name": agent}},
        }
        if platforms:
            props["Platform"] = {"multi_select": [{"name": p} for p in platforms]}
        if topics:
            props["Topic"] = {"multi_select": [{"name": t} for t in topics]}
        if content:
            props["Content"] = {"rich_text": [{"text": {"content": content[:2000]}}]}
        return self.client.create_page(database_id=config.CONTENT_DB, properties=props)

    def update_content_status(self, page_id: str, status: str, scheduled_date: str = "", posted_date: str = "", drive_link: str = "") -> dict:
        props = {"Status": {"select": {"name": status}}}
        if scheduled_date:
            props["Scheduled Date"] = {"date": {"start": scheduled_date}}
        if posted_date:
            props["Posted Date"] = {"date": {"start": posted_date}}
        if drive_link:
            props["Drive Link"] = {"url": drive_link}
        return self.client.update_page(page_id, properties=props)

    # ---- P0 / Streak / Week methods ----

    def get_p0_for_date(self, date_str: str) -> Optional[dict]:
        """Return the P0=True task for a given date, or None."""
        pages = self.client.query_database(
            config.TASKS_DB,
            filter_obj={
                "and": [
                    {"property": "P0", "checkbox": {"equals": True}},
                    {"property": "Due Date", "date": {"equals": date_str}},
                ]
            },
        )
        return pages[0] if pages else None

    def create_p0(self, task_name: str, date_str: str, phase: int = 0) -> dict:
        """Create a P0 task for the given date."""
        props = {
            "Task": {"title": [{"text": {"content": task_name}}]},
            "P0": {"checkbox": True},
            "Status": {"select": {"name": "Not Started"}},
            "Category": {"select": {"name": "Revenue"}},
            "Day Type": {"select": {"name": "A-Day"}},
            "Phase": {"number": phase},
            "Due Date": {"date": {"start": date_str}},
        }
        return self.client.create_page(database_id=config.TASKS_DB, properties=props)

    def uncheck_p0(self, page_id: str) -> dict:
        """Set P0=False on a task."""
        return self.client.update_page(page_id, properties={"P0": {"checkbox": False}})

    def set_streak_anchor(self, page_id: str, value: bool = True) -> dict:
        """Set Streak Anchor checkbox on a task."""
        return self.client.update_page(page_id, properties={"Streak Anchor": {"checkbox": value}})

    def get_todays_tasks(self) -> list:
        """Return all tasks for today."""
        today = date.today().isoformat()
        return self.client.query_database(
            config.TASKS_DB,
            filter_obj={"property": "Due Date", "date": {"equals": today}},
        )

    def get_week_tasks(self) -> list:
        """Return all tasks for current Mon-Sun week."""
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return self.client.query_database(
            config.TASKS_DB,
            filter_obj={
                "and": [
                    {"property": "Due Date", "date": {"on_or_after": monday.isoformat()}},
                    {"property": "Due Date", "date": {"on_or_before": sunday.isoformat()}},
                ]
            },
            sorts=[{"property": "Due Date", "direction": "ascending"}],
        )

    def calculate_streak(self) -> tuple:
        """
        Calculate current streak from P0 records.
        Returns (streak_count, list_of_qualifying_page_ids).
        Counts consecutive days going back from yesterday where P0=Done.
        Today counts only if Status=Done.
        """
        pages = self.client.query_database(
            config.TASKS_DB,
            filter_obj={"property": "P0", "checkbox": {"equals": True}},
            sorts=[{"property": "Due Date", "direction": "descending"}],
        )
        if not pages:
            return 0, []

        # Build a dict of date -> (status, page_id)
        by_date = {}
        for p in pages:
            due = (p["properties"].get("Due Date", {}).get("date") or {}).get("start")
            status = (p["properties"].get("Status", {}).get("select") or {}).get("name", "")
            if due:
                by_date[due] = (status, p["id"])

        today = date.today()
        streak = 0
        qualifying = []

        # Check today first (only counts if Done)
        today_str = today.isoformat()
        if today_str in by_date and by_date[today_str][0] == "Done":
            streak += 1
            qualifying.append(by_date[today_str][1])
            start_check = today - timedelta(days=1)
        else:
            start_check = today - timedelta(days=1)

        # Walk backward from yesterday
        check_date = start_check
        while True:
            check_str = check_date.isoformat()
            if check_str not in by_date:
                break
            status, pid = by_date[check_str]
            if status != "Done":
                break
            streak += 1
            qualifying.append(pid)
            check_date -= timedelta(days=1)

        return streak, qualifying
