import os
import logging
import httpx
from datetime import date

logger = logging.getLogger(__name__)

NOTION_VERSION = "2022-06-28"

def get_notion_headers():
    token = os.environ.get("NOTION_SECRET")
    if not token:
        raise ValueError("NOTION_SECRET not found in environment.")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

def search_databases(query=""):
    """Search for Notion databases."""
    headers = get_notion_headers()
    payload = {"filter": {"value": "database", "property": "object"}}
    if query:
        payload["query"] = query
    
    r = httpx.post("https://api.notion.com/v1/search", headers=headers, json=payload, timeout=10)
    r.raise_for_status()
    return r.json().get("results", [])

def create_page(database_id, title, content=""):
    """Create a new page in a Notion database."""
    headers = get_notion_headers()
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "title": {"title": [{"text": {"content": title}}]}
        }
    }
    if content:
        payload["children"] = [
            {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": content}}]}}
        ]
    
    r = httpx.post("https://api.notion.com/v1/pages", headers=headers, json=payload, timeout=10)
    r.raise_for_status()
    return r.json().get("url")

def append_block(block_id, content):
    """Append a paragraph block to a Notion page or block."""
    headers = get_notion_headers()
    payload = {
        "children": [
            {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": content}}]}}
        ]
    }
    
    r = httpx.patch(f"https://api.notion.com/v1/blocks/{block_id}/children", headers=headers, json=payload, timeout=10)
    r.raise_for_status()
    return r.status_code == 200


def create_database(parent_page_id: str, title: str) -> dict:
    """Create a new Notion database under the given parent page."""
    headers = get_notion_headers()
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": {
            "Name": {"title": {}},
            "Content": {"rich_text": {}},
            "Source": {
                "select": {
                    "options": [
                        {"name": "Telegram", "color": "blue"},
                        {"name": "Manual", "color": "gray"},
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "New", "color": "green"},
                        {"name": "Reviewed", "color": "yellow"},
                        {"name": "Archived", "color": "gray"},
                    ]
                }
            },
            "Category": {
                "select": {
                    "options": [
                        {"name": "Tool", "color": "purple"},
                        {"name": "Agent", "color": "blue"},
                        {"name": "Feature", "color": "orange"},
                        {"name": "Business", "color": "red"},
                        {"name": "Personal", "color": "pink"},
                    ]
                }
            },
            "Created": {"date": {}},
        },
    }
    r = httpx.post("https://api.notion.com/v1/databases", headers=headers, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


def query_database(database_id: str, filter_body: dict = None, sorts: list = None) -> list:
    """Query records from a Notion database. Returns list of page objects."""
    headers = get_notion_headers()
    payload = {}
    if filter_body:
        payload["filter"] = filter_body
    if sorts:
        payload["sorts"] = sorts
    r = httpx.post(
        f"https://api.notion.com/v1/databases/{database_id}/query",
        headers=headers,
        json=payload,
        timeout=10,
    )
    r.raise_for_status()
    return r.json().get("results", [])


def create_idea_page(
    database_id: str,
    title: str,
    content: str,
    category: str = "Feature",
    impact: str = "",
    effort: str = "",
) -> str:
    """Create a new idea page in the Ideas database. Returns the Notion URL."""
    headers = get_notion_headers()
    properties = {
        "Name": {"title": [{"text": {"content": title}}]},
        "Content": {"rich_text": [{"text": {"content": content[:2000]}}]},
        "Source": {"select": {"name": "Telegram"}},
        "Status": {"select": {"name": "New"}},
        "Category": {"select": {"name": category}},
        "Created": {"date": {"start": date.today().isoformat()}},
    }
    if impact in ("High", "Medium", "Low"):
        properties["Impact"] = {"select": {"name": impact}}
    if effort in ("High", "Medium", "Low"):
        properties["Effort"] = {"select": {"name": effort}}
    payload = {"parent": {"database_id": database_id}, "properties": properties}
    r = httpx.post("https://api.notion.com/v1/pages", headers=headers, json=payload, timeout=10)
    r.raise_for_status()
    return r.json().get("url", "")
