#!/usr/bin/env python3
"""
One-time bootstrap: create the agentsHQ Ideas Notion database and seed it.

Usage (run locally or on VPS):
    NOTION_SECRET=<token> NOTION_PARENT_PAGE_ID=<page_id> python scripts/bootstrap_ideas_db.py

The script will:
1. Create the "agentsHQ Ideas" database under the given parent page.
2. Seed it with the first known idea (Practice Runner).
3. Print the new DB ID — copy it to .env as IDEAS_DB_ID.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from skills.notion_skill.notion_tool import create_database, create_idea_page

PARENT_PAGE_ID = os.environ.get("NOTION_PARENT_PAGE_ID", "")
if not PARENT_PAGE_ID:
    print("ERROR: Set NOTION_PARENT_PAGE_ID env var to the Notion page where the DB should live.")
    print("  Find it: open a Notion page, copy the last 32 chars of the URL (no dashes).")
    sys.exit(1)

print("Creating agentsHQ Ideas database in Notion...")
result = create_database(PARENT_PAGE_ID, "agentsHQ Ideas")
db_id = result["id"]
db_url = result.get("url", "")
print(f"Database created!")
print(f"  ID:  {db_id}")
print(f"  URL: {db_url}")
print()
print("Seeding first idea: Practice Runner...")

seed_ideas = [
    {
        "title": "Practice Runner — AI Roleplay Feedback Tool",
        "content": (
            "An app or tool where Boubacar can record himself or have a conversation with an AI "
            "to practice different scenarios: running a session with a client, speaking a language, "
            "doing interviews, sales calls, presentations. After the practice session, the AI gives "
            "detailed feedback on performance and what to improve. "
            "Preferred modality: video (primary), voice, or chat. "
            "Potential positioning: personal coach for high-stakes conversations. "
            "Side project — not a client deliverable."
        ),
        "category": "Tool",
    },
]

for idea in seed_ideas:
    url = create_idea_page(db_id, idea["title"], idea["content"], idea["category"])
    print(f"  Seeded: '{idea['title']}' — {url}")

print()
print("=" * 60)
print("NEXT STEP: Add this to your .env and docker-compose.yml:")
print(f"  IDEAS_DB_ID={db_id}")
print("=" * 60)
