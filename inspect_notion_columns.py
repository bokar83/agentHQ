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
    
    # Just fetch 1 page
    posts = notion.query_database(db_id, filter_obj=None)
    if posts:
        props = posts[0].get("properties", {})
        print("Columns in Notion Content Board:")
        for name, prop in sorted(props.items()):
            print(f" - {name}: {prop.get('type')}")
    else:
        print("No pages found in database.")
        
except Exception as e:
    print(f"Error: {e}")
