"""
One-time script to create the Content Board database in Notion.
Run: python -m skills.forge_cli.create_content_db

Creates the database under The Forge 2.0 page with all properties defined in the spec.
Prints the database ID to add to .env as FORGE_CONTENT_DB.
"""
import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from skills.forge_cli import config

FORGE_PAGE_ID = config.FORGE_PAGE_ID or "249bcf1a3029807f86e8fb97e2671154"


def create_content_board():
    headers = {
        "Authorization": f"Bearer {config.NOTION_SECRET}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    payload = {
        "parent": {"type": "page_id", "page_id": FORGE_PAGE_ID},
        "icon": {"type": "emoji", "emoji": "\U0001f4dd"},
        "title": [{"type": "text", "text": {"content": "Content Board"}}],
        "properties": {
            "Title": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Idea", "color": "gray"},
                        {"name": "Draft", "color": "blue"},
                        {"name": "Ready", "color": "green"},
                        {"name": "Queued", "color": "orange"},
                        {"name": "Posted", "color": "purple"},
                    ]
                }
            },
            "Platform": {
                "multi_select": {
                    "options": [
                        {"name": "LinkedIn", "color": "blue"},
                        {"name": "X", "color": "gray"},
                        {"name": "YouTube", "color": "red"},
                    ]
                }
            },
            "Type": {
                "select": {
                    "options": [
                        {"name": "Post", "color": "default"},
                        {"name": "Article", "color": "blue"},
                        {"name": "Thread", "color": "green"},
                        {"name": "Video", "color": "red"},
                        {"name": "Carousel", "color": "orange"},
                    ]
                }
            },
            "Content": {"rich_text": {}},
            "Drive Link": {"url": {}},
            "Scheduled Date": {"date": {}},
            "Posted Date": {"date": {}},
            "Agent": {
                "select": {
                    "options": [
                        {"name": "Boubacar", "color": "blue"},
                        {"name": "Social Crew", "color": "green"},
                        {"name": "leGriot", "color": "orange"},
                    ]
                }
            },
            "Topic": {
                "multi_select": {
                    "options": [
                        {"name": "AI", "color": "blue"},
                        {"name": "Leadership", "color": "green"},
                        {"name": "Systems", "color": "orange"},
                        {"name": "TOC", "color": "purple"},
                        {"name": "Catalyst Works", "color": "red"},
                        {"name": "Personal", "color": "gray"},
                    ]
                }
            },
        },
    }
    response = httpx.post(
        "https://api.notion.com/v1/databases",
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    result = response.json()
    db_id = result["id"]
    print(f"Content Board created!")
    print(f"Database ID: {db_id}")
    print(f"Add to .env: FORGE_CONTENT_DB={db_id}")
    return db_id


if __name__ == "__main__":
    create_content_board()
