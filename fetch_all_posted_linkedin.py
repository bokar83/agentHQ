import os
import sys

def load_env(path=".env"):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    val = val.strip().strip("'").strip('"')
                    os.environ[key.strip()] = val

load_env()
sys.path.append("orchestrator")

try:
    from skills.forge_cli.notion_client import NotionClient
    notion_secret = os.environ.get("NOTION_SECRET") or os.environ.get("NOTION_API_KEY") or os.environ.get("NOTION_TOKEN")
    notion = NotionClient(secret=notion_secret)
    db_id = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
    
    # Filter for Status = Posted and Platform contains LinkedIn
    filter_obj = {
        "and": [
            {
                "property": "Status",
                "select": {
                    "equals": "Posted"
                }
            },
            {
                "property": "Platform",
                "multi_select": {
                    "contains": "LinkedIn"
                }
            }
        ]
    }
    
    posts = notion.query_database(db_id, filter_obj=filter_obj)
    print(f"Found {len(posts)} posted LinkedIn items.")
    
    for i, p in enumerate(posts):
        props = p.get("properties", {})
        title_prop = props.get("Title", {}).get("title", [])
        title = title_prop[0].get("plain_text", "") if title_prop else "Untitled"
        li_url = props.get("LinkedIn Posted URL", {}).get("url")
        print(f"\n{i+1}. Title: {title}")
        print(f"   LinkedIn URL: {li_url}")
        
except Exception as e:
    print(f"Error: {e}")
