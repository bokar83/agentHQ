import os
import sys

# Hand-rolled dotenv loader for maximum robustness
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
    if not notion_secret:
        print("Error: NOTION_SECRET / NOTION_API_KEY / NOTION_TOKEN not found in env.")
        sys.exit(1)
        
    notion = NotionClient(secret=notion_secret)
    db_id = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
    print(f"Querying Notion Content Board (DB: {db_id}) for 'Posted' items...")
    
    # Let's filter by Status = Posted
    filter_obj = {
        "property": "Status",
        "select": {
            "equals": "Posted"
        }
    }
    
    posts = notion.query_database(db_id, filter_obj=filter_obj)
    print(f"Found {len(posts)} posted items.")
    
    for i, p in enumerate(posts[:10]):
        props = p.get("properties", {})
        
        # Extract title
        title_prop = props.get("Title", {}).get("title", [])
        title = title_prop[0].get("plain_text", "") if title_prop else "Untitled"
        
        # Extract submission ID
        sub_id_prop = props.get("Submission ID", {}).get("rich_text", [])
        sub_id = "".join(t.get("plain_text", "") for t in sub_id_prop) if sub_id_prop else ""
        
        # Extract platforms
        platforms_prop = props.get("Platform", {}).get("multi_select", [])
        platforms = [x.get("name") for x in platforms_prop] if platforms_prop else []
        
        # Extract posted URL
        li_url = props.get("LinkedIn Posted URL", {}).get("url")
        x_url = props.get("X Posted URL", {}).get("url")
        
        print(f"\n{i+1}. Title: {title}")
        print(f"   Platforms: {platforms}")
        print(f"   Submission ID: {sub_id}")
        if li_url: print(f"   LinkedIn URL: {li_url}")
        if x_url: print(f"   X URL: {x_url}")
        
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
