"""
One-time build script for The Forge 2.0 Notion page.
Run: python -m skills.forge_cli.page_builder

This script:
1. Clears the page content
2. Applies premium cover and icon
3. Builds the KPI Bar, sections, and placeholder callouts
4. Adds Playbook and Archives toggle sections
"""
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from skills.notion_stylist.notion_stylist import NotionStylist, COVER_IMAGES
from skills.forge_cli.notion_client import NotionClient
from skills.forge_cli import config

FORGE_PAGE_ID = config.FORGE_PAGE_ID or "249bcf1a3029807f86e8fb97e2671154"


def build_forge_page():
    stylist = NotionStylist()
    client = NotionClient(secret=config.NOTION_SECRET)

    print("[1/8] Applying premium cover and icon...")
    stylist.set_premium_style(
        FORGE_PAGE_ID,
        cover_url=COVER_IMAGES["dark_network"],
        icon_emoji="\U0001f525",
    )
    # Rename page
    client.update_page(FORGE_PAGE_ID, {
        "title": {"title": [{"text": {"content": "The Forge 2.0 -- Execution OS"}}]},
    })

    print("[2/8] Clearing existing page content...")
    stylist.clear_page_content(FORGE_PAGE_ID)
    time.sleep(1)

    print("[3/8] Building hero callout...")
    stylist.add_callout(
        FORGE_PAGE_ID,
        "The Forge 2.0 -- Your execution OS.\nAgent-populated. Human-read. Revenue-focused.",
        emoji="\U0001f525",
        color="cyan",
    )
    stylist.add_divider(FORGE_PAGE_ID)

    print("[4/8] Building KPI Bar...")
    kpi_col_1 = [
        _make_callout("**$0**\nPipeline $", "\U0001f4b0", "blue_background"),
        _make_callout("**$0**\nRevenue MTD", "\U0001f4b5", "blue_background"),
    ]
    kpi_col_2 = [
        _make_callout("**0**\nPosts This Month", "\U0001f4dd", "blue_background"),
        _make_callout("**0**\nTasks Done This Week", "\u2705", "blue_background"),
    ]
    stylist.create_column_layout(FORGE_PAGE_ID, [kpi_col_1, kpi_col_2], ratios=[0.5, 0.5])
    stylist.add_divider(FORGE_PAGE_ID)

    print("[5/8] Building This Week section...")
    stylist.add_heading(FORGE_PAGE_ID, "\U0001f3af This Week", level=2)
    stylist.add_divider(FORGE_PAGE_ID)
    stylist.add_callout(
        FORGE_PAGE_ID,
        "Add a linked view of Tasks database here (Status=Active, Due=This Week).\nUse `forge task add` to create tasks.",
        emoji="\U0001f4cb",
        color="slate",
    )

    print("[6/8] Building Growth Engine section...")
    stylist.add_heading(FORGE_PAGE_ID, "\U0001f4b0 Growth Engine", level=2)
    stylist.add_divider(FORGE_PAGE_ID)
    stylist.add_callout(
        FORGE_PAGE_ID,
        "Add linked views here:\n1. Consulting Pipeline (Board view, grouped by Status)\n2. Revenue Log (Table view, sorted by Date desc)\nUse `forge pipeline add` and `forge revenue` to populate.",
        emoji="\U0001f4c8",
        color="slate",
    )

    print("[7/8] Building Content section...")
    stylist.add_heading(FORGE_PAGE_ID, "\U0001f4dd Content", level=2)
    stylist.add_divider(FORGE_PAGE_ID)
    stylist.add_callout(
        FORGE_PAGE_ID,
        "Add linked views of Content Board here:\n1. Ideas (Gallery, Status=Idea)\n2. Drafts (Table, Status=Draft)\n3. Queue (Table, Status=Queued, sorted by Scheduled Date)\nUse `forge content idea` to brainstorm.",
        emoji="\u270d\ufe0f",
        color="slate",
    )

    print("[8/8] Building Playbook and Archives...")
    playbook_children = [
        _make_bookmark("Frameworks & Thinking Tools", "https://www.notion.so/272bcf1a302980948c96cb77e79efa48"),
        _make_bookmark("Playbooks, Workshops, & Tools", "https://www.notion.so/272bcf1a30298002a68bce3c38a6e97a"),
        _make_bookmark("Catalyst10K Roadmap", "https://www.notion.so/2b0bcf1a30298072ab20d4912032148a"),
    ]
    stylist.add_toggle(FORGE_PAGE_ID, "\U0001f4da Playbook", playbook_children)

    archive_children = [
        _make_bookmark("Agent Activity Log", "https://www.notion.so/339bcf1a3029818c8f27fb4203b23603"),
        _make_bookmark("Catalyst Engines", "https://www.notion.so/285bcf1a302980ff8a30e3eed798e972"),
        _make_bookmark("Products & Landing Pages", "https://www.notion.so/249bcf1a30298063b7d1f20c4f4d30c5"),
    ]
    stylist.add_toggle(FORGE_PAGE_ID, "\U0001f5c4\ufe0f Archives", archive_children)

    print("\nThe Forge 2.0 built successfully!")
    print(f"View: https://www.notion.so/{FORGE_PAGE_ID.replace('-', '')}")
    print("\nNext steps:")
    print("1. Replace placeholder callouts with linked database views (Notion UI)")
    print("2. Create Content Board database (run create_content_db.py)")
    print("3. Record KPI block IDs in .env (FORGE_KPI_BLOCK_IDS)")
    print("4. Run `forge kpi refresh` to populate KPI numbers")


def _make_callout(text: str, emoji: str, color: str) -> dict:
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
            "icon": {"type": "emoji", "emoji": emoji},
            "color": color,
        },
    }


def _make_bookmark(title: str, url: str) -> dict:
    return {
        "object": "block",
        "type": "bookmark",
        "bookmark": {"url": url, "caption": [{"type": "text", "text": {"content": title}}]},
    }


if __name__ == "__main__":
    build_forge_page()
