import os
import argparse
import httpx
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

# Load environment variables from the project's .env file
load_dotenv()

NOTION_SECRET = os.getenv("NOTION_SECRET")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID") # Defaults to Agent Activity Log
NOTION_VERSION = "2022-06-28"

class NotionCLI:
    def __init__(self, secret: Optional[str] = None):
        self.secret = secret or NOTION_SECRET
        if not self.secret:
            raise ValueError("NOTION_SECRET not found in .env or provided.")
        self.headers = {
            "Authorization": f"Bearer {self.secret}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"https://api.notion.com/v1/{endpoint}"
        with httpx.Client() as client:
            response = client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()

    def log_action(self, action: str, status: str = "Success", agent: str = "Code", transcript: str = "", artifacts: str = ""):
        """Create a new entry in the Agent Activity Log database."""
        if not NOTION_DATABASE_ID:
            print("Error: NOTION_DATABASE_ID not configured in .env")
            return

        payload = {
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": {
                "Action": {"title": [{"text": {"content": action}}]},
                "Status": {"select": {"name": status}},
                "Agent": {"select": {"name": agent}},
                "Transcript": {"rich_text": [{"text": {"content": transcript}}]},
                "Link": {"url": artifacts if artifacts.startswith("http") else None}
            }
        }
        return self._post("pages", payload)

    def search(self, query: str):
        """Search Notion for pages or databases."""
        payload = {"query": query}
        return self._post("search", payload)

def main():
    parser = argparse.ArgumentParser(description="agentsHQ Notion CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Command: log-action
    log_parser = subparsers.add_parser("log-action", help="Log an agent action")
    log_parser.add_argument("title", help="Title of the action")
    log_parser.add_argument("--status", default="Success", choices=["Success", "In Progress", "Failed", "Pending Review"], help="Status of the action")
    log_parser.add_argument("--agent", default="Code", help="Name of the agent")
    log_parser.add_argument("--transcript", default="", help="Detailed transcript or summary")
    log_parser.add_argument("--artifacts", default="", help="URL or path to artifacts")

    # Command: search
    search_parser = subparsers.add_parser("search", help="Search Notion")
    search_parser.add_argument("query", help="Search query")

    args = parser.parse_args()
    cli = NotionCLI()

    if args.command == "log-action":
        result = cli.log_action(args.title, args.status, args.agent, args.transcript, args.artifacts)
        if result:
            print(f"Action logged successfully: {result.get('url')}")
    elif args.command == "search":
        result = cli.search(args.query)
        for item in result.get("results", []):
            title_objs = item.get("properties", {}).get("title", {}).get("title", []) or item.get("title", [])
            title = title_objs[0].get("plain_text", "Untitled") if title_objs else "Untitled"
            print(f"[{item['object'].upper()}] {title} ({item['id']})")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
