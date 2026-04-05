from datetime import datetime, date
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
