import os
import sys
import httpx

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

token = (os.environ.get("NOTION_API_KEY")
         or os.environ.get("NOTION_TOKEN")
         or os.environ.get("NOTION_SECRET"))
db_id = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")

if not token:
    print("Error: No Notion token found.")
    sys.exit(1)

url = f"https://api.notion.com/v1/databases/{db_id}"

headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Payload to add the 4 columns as numbers
payload = {
    "properties": {
        "Views": {
            "number": {
                "format": "number"
            }
        },
        "Likes": {
            "number": {
                "format": "number"
            }
        },
        "Comments": {
            "number": {
                "format": "number"
            }
        },
        "Reposts": {
            "number": {
                "format": "number"
            }
        }
    }
}

print(f"Sending PATCH request to {url}...")
try:
    with httpx.Client(timeout=30.0) as client:
        resp = client.patch(url, headers=headers, json=payload)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            print("Successfully added analytics columns to Notion Content Board database!")
        else:
            print(f"Failed to add columns: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
