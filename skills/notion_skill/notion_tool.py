import os
import json
import logging
import httpx

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
