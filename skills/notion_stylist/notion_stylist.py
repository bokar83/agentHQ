import os
import httpx
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

load_dotenv()

NOTION_SECRET = os.getenv("NOTION_SECRET")
NOTION_VERSION = "2022-06-28"

BRAND_COLORS = {
    "cyan": "blue_background",
    "orange": "orange_background",
    "teal": "green_background",
    "slate": "gray_background",
    "dark": "default",
    "alert": "red_background",
}

COVER_IMAGES = {
    "dark_network": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1600&q=80",
    "dark_geometry": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=1600&q=80",
    "dark_forge": "https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=1600&q=80",
}


class NotionStylist:
    def __init__(self, secret: Optional[str] = None):
        self.secret = secret or NOTION_SECRET
        if not self.secret:
            raise ValueError("NOTION_SECRET not found in .env or provided.")
        self.headers = {
            "Authorization": f"Bearer {self.secret}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

    def _patch(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"https://api.notion.com/v1/{endpoint}"
        with httpx.Client(timeout=30) as client:
            response = client.patch(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"https://api.notion.com/v1/{endpoint}"
        with httpx.Client(timeout=30) as client:
            response = client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"https://api.notion.com/v1/{endpoint}"
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    def _delete(self, endpoint: str) -> None:
        url = f"https://api.notion.com/v1/{endpoint}"
        with httpx.Client(timeout=30) as client:
            response = client.delete(url, headers=self.headers)
            response.raise_for_status()

    def clear_page_content(self, page_id: str, preserve_databases: bool = True):
        """Delete all child blocks from a page. Preserves child databases by default."""
        cursor = None
        while True:
            params = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor
            result = self._get(f"blocks/{page_id}/children", params)
            for block in result.get("results", []):
                if preserve_databases and block.get("type") == "child_database":
                    continue
                self._delete(f"blocks/{block['id']}")
            if not result.get("has_more"):
                break
            cursor = result.get("next_cursor")

    def set_premium_style(self, page_id: str, cover_url: Optional[str] = None, icon_emoji: Optional[str] = None, icon_url: Optional[str] = None):
        """Apply cover and icon to a page or database."""
        payload = {}
        if cover_url:
            payload["cover"] = {"type": "external", "external": {"url": cover_url}}
        if icon_url:
            payload["icon"] = {"type": "external", "external": {"url": icon_url}}
        elif icon_emoji:
            payload["icon"] = {"type": "emoji", "emoji": icon_emoji}
        if not payload:
            return None
        try:
            return self._patch(f"pages/{page_id}", payload)
        except Exception as e:
            print(f"Page style failed ({e}), trying as database...")
            return self._patch(f"databases/{page_id}", payload)

    def add_callout(self, page_id: str, text: str, emoji: str = "🔥", color: str = "default"):
        """Add a callout block. Color accepts brand names or Notion API values."""
        resolved_color = BRAND_COLORS.get(color, color)
        payload = {
            "children": [
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [{"type": "text", "text": {"content": text}}],
                        "icon": {"type": "emoji", "emoji": emoji},
                        "color": resolved_color,
                    },
                }
            ]
        }
        return self._patch(f"blocks/{page_id}/children", payload)

    def add_heading(self, page_id: str, text: str, level: int = 2, color: str = "default"):
        """Add a heading block (level 1, 2, or 3)."""
        resolved_color = BRAND_COLORS.get(color, color)
        heading_type = f"heading_{level}"
        payload = {
            "children": [
                {
                    "object": "block",
                    "type": heading_type,
                    heading_type: {
                        "rich_text": [{"type": "text", "text": {"content": text}}],
                        "color": resolved_color,
                    },
                }
            ]
        }
        return self._patch(f"blocks/{page_id}/children", payload)

    def add_divider(self, page_id: str):
        """Add a divider block."""
        payload = {
            "children": [{"object": "block", "type": "divider", "divider": {}}]
        }
        return self._patch(f"blocks/{page_id}/children", payload)

    def add_toggle(self, page_id: str, text: str, children_blocks: Optional[List] = None):
        """Add a toggle heading block with optional children."""
        toggle = {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "is_toggleable": True,
            },
        }
        payload = {"children": [toggle]}
        result = self._patch(f"blocks/{page_id}/children", payload)
        if children_blocks and result.get("results"):
            toggle_id = result["results"][0]["id"]
            self._patch(f"blocks/{toggle_id}/children", {"children": children_blocks})
        return result

    def create_navigation_grid(self, page_id: str, items: List[Dict[str, str]], max_cols: int = 3):
        """Create a multi-column navigation grid, chunked into rows of max_cols."""
        all_blocks = []
        all_ratios = []
        for i in range(0, len(items), max_cols):
            chunk = items[i : i + max_cols]
            n = len(chunk)
            ratios = self._compute_ratios(n)
            columns = []
            for j, item in enumerate(chunk):
                rich_text_content = {"content": item["title"]}
                if "url" in item:
                    rich_text_content["link"] = {"url": item["url"]}
                columns.append(
                    {
                        "object": "block",
                        "type": "column",
                        "column": {
                            "children": [
                                {
                                    "object": "block",
                                    "type": "callout",
                                    "callout": {
                                        "rich_text": [
                                            {"type": "text", "text": rich_text_content}
                                        ],
                                        "icon": {
                                            "type": "emoji",
                                            "emoji": item.get("emoji", "📌"),
                                        },
                                        "color": BRAND_COLORS.get(
                                            item.get("color", "dark"),
                                            item.get("color", "default"),
                                        ),
                                    },
                                }
                            ]
                        },
                    }
                )
            all_blocks.append(
                {
                    "object": "block",
                    "type": "column_list",
                    "column_list": {"children": columns},
                }
            )
            all_ratios.append(ratios)
        payload = {"children": all_blocks}
        return self._patch(f"blocks/{page_id}/children", payload)

    def create_column_layout(self, page_id: str, columns_content: List[List[Dict]], **_kwargs):
        """Create a column layout. Notion auto-distributes equal widths."""
        columns = []
        for children in columns_content:
            columns.append(
                {
                    "object": "block",
                    "type": "column",
                    "column": {"children": children},
                }
            )
        payload = {
            "children": [
                {
                    "object": "block",
                    "type": "column_list",
                    "column_list": {"children": columns},
                }
            ]
        }
        return self._patch(f"blocks/{page_id}/children", payload)

    @staticmethod
    def _compute_ratios(n: int) -> List[float]:
        """Compute balanced width ratios for n columns that sum to 1.0."""
        if n <= 0:
            return []
        base = round(1.0 / n, 2)
        ratios = [base] * n
        remainder = round(1.0 - sum(ratios), 2)
        ratios[-1] = round(ratios[-1] + remainder, 2)
        return ratios


if __name__ == "__main__":
    import sys
    import json

    stylist = NotionStylist()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "set-style" and len(sys.argv) >= 3:
            page_id = sys.argv[2]
            cover = sys.argv[3] if len(sys.argv) > 3 else None
            icon = sys.argv[4] if len(sys.argv) > 4 else None
            print(json.dumps(stylist.set_premium_style(page_id, cover, icon)))
        elif cmd == "add-nav" and len(sys.argv) >= 3:
            page_id = sys.argv[2]
            items = json.loads(sys.argv[3])
            print(json.dumps(stylist.create_navigation_grid(page_id, items)))
        elif cmd == "clear" and len(sys.argv) >= 3:
            page_id = sys.argv[2]
            stylist.clear_page_content(page_id)
            print("Page cleared.")
