import json as _json
import os
import re
import httpx
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional

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

# ── Premium Layout Templates ───────────────────────────────────────────────────
# Each template defines:
#   cover: cover image key from COVER_IMAGES
#   icon: emoji for the page icon (unicode escapes avoid linter stripping)
#   description: human-readable summary
#   blocks: list of Notion block dicts appended after clearing the page

LAYOUT_TEMPLATES: Dict[str, Dict[str, Any]] = {

    "project_command_center": {
        "cover": "dark_geometry",
        "icon": "\U0001f680",
        "description": "3-column status board with quick links and a mission callout. Ideal for active projects.",
        "blocks": [
            {
                "object": "block", "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": "Mission: Deliver on time, on brief, on brand."}}],
                    "icon": {"type": "emoji", "emoji": "\U0001f3af"},
                    "color": "green_background",
                },
            },
            {"object": "block", "type": "divider", "divider": {}},
            {
                "object": "block", "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Status Board"}}],
                    "color": "default",
                },
            },
            {
                "object": "block", "type": "column_list",
                "column_list": {
                    "children": [
                        {
                            "object": "block", "type": "column",
                            "column": {"children": [
                                {
                                    "object": "block", "type": "callout",
                                    "callout": {
                                        "rich_text": [{"type": "text", "text": {"content": "In Progress\nList active tasks here."}}],
                                        "icon": {"type": "emoji", "emoji": "\u26a1"},
                                        "color": "orange_background",
                                    },
                                }
                            ]},
                        },
                        {
                            "object": "block", "type": "column",
                            "column": {"children": [
                                {
                                    "object": "block", "type": "callout",
                                    "callout": {
                                        "rich_text": [{"type": "text", "text": {"content": "Blocked\nItems needing decisions."}}],
                                        "icon": {"type": "emoji", "emoji": "\U0001f6a7"},
                                        "color": "red_background",
                                    },
                                }
                            ]},
                        },
                        {
                            "object": "block", "type": "column",
                            "column": {"children": [
                                {
                                    "object": "block", "type": "callout",
                                    "callout": {
                                        "rich_text": [{"type": "text", "text": {"content": "Done\nCompleted this sprint."}}],
                                        "icon": {"type": "emoji", "emoji": "\u2705"},
                                        "color": "green_background",
                                    },
                                }
                            ]},
                        },
                    ]
                },
            },
            {"object": "block", "type": "divider", "divider": {}},
            {
                "object": "block", "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Quick Links"}}],
                    "color": "default",
                },
            },
            {
                "object": "block", "type": "column_list",
                "column_list": {
                    "children": [
                        {
                            "object": "block", "type": "column",
                            "column": {"children": [
                                {
                                    "object": "block", "type": "callout",
                                    "callout": {
                                        "rich_text": [{"type": "text", "text": {"content": "Brief & Scope"}}],
                                        "icon": {"type": "emoji", "emoji": "\U0001f4cb"},
                                        "color": "blue_background",
                                    },
                                }
                            ]},
                        },
                        {
                            "object": "block", "type": "column",
                            "column": {"children": [
                                {
                                    "object": "block", "type": "callout",
                                    "callout": {
                                        "rich_text": [{"type": "text", "text": {"content": "Assets & Files"}}],
                                        "icon": {"type": "emoji", "emoji": "\U0001f4c1"},
                                        "color": "blue_background",
                                    },
                                }
                            ]},
                        },
                        {
                            "object": "block", "type": "column",
                            "column": {"children": [
                                {
                                    "object": "block", "type": "callout",
                                    "callout": {
                                        "rich_text": [{"type": "text", "text": {"content": "Meeting Notes"}}],
                                        "icon": {"type": "emoji", "emoji": "\U0001f5d2\ufe0f"},
                                        "color": "blue_background",
                                    },
                                }
                            ]},
                        },
                    ]
                },
            },
        ],
    },

    "client_portal": {
        "cover": "dark_network",
        "icon": "\U0001f91d",
        "description": "High-impact hero section with deliverables and feedback columns. Ideal for client-facing workspaces.",
        "blocks": [
            {
                "object": "block", "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": "Welcome. This is your dedicated workspace. Everything you need is here."}}],
                    "icon": {"type": "emoji", "emoji": "\U0001f31f"},
                    "color": "blue_background",
                },
            },
            {"object": "block", "type": "divider", "divider": {}},
            {
                "object": "block", "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Your Workspace"}}],
                    "color": "default",
                },
            },
            {
                "object": "block", "type": "column_list",
                "column_list": {
                    "children": [
                        {
                            "object": "block", "type": "column",
                            "column": {"children": [
                                {
                                    "object": "block", "type": "heading_3",
                                    "heading_3": {
                                        "rich_text": [{"type": "text", "text": {"content": "Deliverables"}}],
                                        "color": "green",
                                    },
                                },
                                {
                                    "object": "block", "type": "callout",
                                    "callout": {
                                        "rich_text": [{"type": "text", "text": {"content": "Phase 1: Discovery\nStatus: In Review"}}],
                                        "icon": {"type": "emoji", "emoji": "\U0001f4e6"},
                                        "color": "green_background",
                                    },
                                },
                                {
                                    "object": "block", "type": "callout",
                                    "callout": {
                                        "rich_text": [{"type": "text", "text": {"content": "Phase 2: Strategy\nStatus: Upcoming"}}],
                                        "icon": {"type": "emoji", "emoji": "\U0001f4e6"},
                                        "color": "gray_background",
                                    },
                                },
                            ]},
                        },
                        {
                            "object": "block", "type": "column",
                            "column": {"children": [
                                {
                                    "object": "block", "type": "heading_3",
                                    "heading_3": {
                                        "rich_text": [{"type": "text", "text": {"content": "Feedback & Approvals"}}],
                                        "color": "orange",
                                    },
                                },
                                {
                                    "object": "block", "type": "callout",
                                    "callout": {
                                        "rich_text": [{"type": "text", "text": {"content": "Leave comments below each deliverable or tag @Boubacar directly."}}],
                                        "icon": {"type": "emoji", "emoji": "\U0001f4ac"},
                                        "color": "orange_background",
                                    },
                                },
                            ]},
                        },
                    ]
                },
            },
            {"object": "block", "type": "divider", "divider": {}},
            {
                "object": "block", "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Key Dates"}}],
                    "color": "default",
                },
            },
            {
                "object": "block", "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": "Add project milestones and deadlines here."}}],
                    "icon": {"type": "emoji", "emoji": "\U0001f4c5"},
                    "color": "default",
                },
            },
        ],
    },

    "knowledge_hub": {
        "cover": "dark_forge",
        "icon": "\U0001f9e0",
        "description": "Toggle-based nested architecture for deep research and knowledge management.",
        "blocks": [
            {
                "object": "block", "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": "Knowledge compounds. Every insight captured here is a competitive advantage."}}],
                    "icon": {"type": "emoji", "emoji": "\U0001f4a1"},
                    "color": "blue_background",
                },
            },
            {"object": "block", "type": "divider", "divider": {}},
            {
                "object": "block", "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Research Library"}}],
                    "is_toggleable": True,
                    "color": "default",
                },
            },
            {
                "object": "block", "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Frameworks & Models"}}],
                    "is_toggleable": True,
                    "color": "default",
                },
            },
            {
                "object": "block", "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Source Material"}}],
                    "is_toggleable": True,
                    "color": "default",
                },
            },
            {
                "object": "block", "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Open Questions"}}],
                    "is_toggleable": True,
                    "color": "default",
                },
            },
            {"object": "block", "type": "divider", "divider": {}},
            {
                "object": "block", "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": "Archive\nMove completed research here to keep active sections lean."}}],
                    "icon": {"type": "emoji", "emoji": "\U0001f5c4\ufe0f"},
                    "color": "gray_background",
                },
            },
        ],
    },
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
        """Delete all child blocks from a page.

        Preserves child databases and child pages by default (preserve_databases=True).
        Child pages are ALWAYS preserved regardless of preserve_databases, because
        deleting a child_page block cascades to all its descendants silently in Notion.
        If a child_page is encountered it is logged as a warning and skipped.
        """
        cursor = None
        while True:
            params = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor
            result = self._get(f"blocks/{page_id}/children", params)
            for block in result.get("results", []):
                block_type = block.get("type")
                # Always preserve child pages — deleting cascades to all descendants
                if block_type == "child_page":
                    title = (block.get("child_page") or {}).get("title", block["id"])
                    print(f"[notion_stylist] WARNING: Skipping child_page '{title}' ({block['id']}) — cascade delete protection.")
                    continue
                if preserve_databases and block_type == "child_database":
                    continue
                self._delete(f"blocks/{block['id']}")
            if not result.get("has_more"):
                break
            cursor = result.get("next_cursor")

    def set_premium_style(self, page_id: str, cover_url: Optional[str] = None,
                          icon_emoji: Optional[str] = None, icon_url: Optional[str] = None):
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

    def add_callout(self, page_id: str, text: str, emoji: str = "\U0001f525", color: str = "default"):
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
            chunk = items[i: i + max_cols]
            n = len(chunk)
            ratios = self._compute_ratios(n)
            columns = []
            for item in chunk:
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
                                            "emoji": item.get("emoji", "\U0001f4cc"),
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

    # ── Template Application ──────────────────────────────────────────────────

    def apply_template(self, page_id: str, template_name: str,
                       preserve_databases: bool = True) -> Dict[str, Any]:
        """Clear page and apply a named LAYOUT_TEMPLATE.

        Returns dict with keys 'template', 'style_result', 'blocks_result'.
        """
        template = LAYOUT_TEMPLATES.get(template_name)
        if template is None:
            available = ", ".join(LAYOUT_TEMPLATES.keys())
            raise ValueError(f"Unknown template '{template_name}'. Available: {available}")

        self.clear_page_content(page_id, preserve_databases=preserve_databases)

        cover_url = COVER_IMAGES.get(template.get("cover", ""), None)
        icon_emoji = template.get("icon")
        style_result = self.set_premium_style(page_id, cover_url=cover_url, icon_emoji=icon_emoji)

        blocks = template.get("blocks", [])
        blocks_result = None
        if blocks:
            blocks_result = self._patch(f"blocks/{page_id}/children", {"children": blocks})

        return {"template": template_name, "style_result": style_result, "blocks_result": blocks_result}

    # ── Markdown-to-Block Conversion ─────────────────────────────────────────

    @staticmethod
    def markdown_to_blocks(md_text: str) -> List[Dict[str, Any]]:
        """Convert lightweight Markdown to a list of Notion block dicts (no API call).

        Supported syntax (max 2 nesting levels):
          # H1   ## H2   ### H3
          **bold** inline text
          - bullet list items
          > blockquote rendered as callout
          Blank lines and plain text become paragraphs.
        """
        blocks: List[Dict[str, Any]] = []

        def rich_text(raw: str) -> List[Dict[str, Any]]:
            parts = re.split(r"(\*\*[^*]+\*\*)", raw)
            segments = []
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    segments.append({
                        "type": "text",
                        "text": {"content": part[2:-2]},
                        "annotations": {"bold": True},
                    })
                elif part:
                    segments.append({"type": "text", "text": {"content": part}})
            return segments

        for line in md_text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("### "):
                blocks.append({
                    "object": "block", "type": "heading_3",
                    "heading_3": {"rich_text": rich_text(stripped[4:]), "color": "default"},
                })
            elif stripped.startswith("## "):
                blocks.append({
                    "object": "block", "type": "heading_2",
                    "heading_2": {"rich_text": rich_text(stripped[3:]), "color": "default"},
                })
            elif stripped.startswith("# "):
                blocks.append({
                    "object": "block", "type": "heading_1",
                    "heading_1": {"rich_text": rich_text(stripped[2:]), "color": "default"},
                })
            elif stripped.startswith("- "):
                blocks.append({
                    "object": "block", "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": rich_text(stripped[2:]), "color": "default"},
                })
            elif stripped.startswith("> "):
                blocks.append({
                    "object": "block", "type": "callout",
                    "callout": {
                        "rich_text": rich_text(stripped[2:]),
                        "icon": {"type": "emoji", "emoji": "\U0001f4a1"},
                        "color": "blue_background",
                    },
                })
            else:
                blocks.append({
                    "object": "block", "type": "paragraph",
                    "paragraph": {"rich_text": rich_text(stripped), "color": "default"},
                })

        return blocks

    def architect_page(self, page_id: str, md_text: str, set_style: bool = False,
                       cover_key: str = "dark_geometry",
                       icon_emoji: str = "\U0001f3d7\ufe0f") -> Dict[str, Any]:
        """Convert markdown to blocks and append them to a page.

        Args:
            page_id: Notion page ID.
            md_text: Markdown content to convert and append.
            set_style: If True, also apply cover and icon.
            cover_key: Key from COVER_IMAGES.
            icon_emoji: Page icon emoji.

        Returns:
            API response dict with added 'appended' count key.
        """
        blocks = self.markdown_to_blocks(md_text)
        if not blocks:
            return {"appended": 0}

        if set_style:
            cover_url = COVER_IMAGES.get(cover_key)
            self.set_premium_style(page_id, cover_url=cover_url, icon_emoji=icon_emoji)

        result = self._patch(f"blocks/{page_id}/children", {"children": blocks})
        result["appended"] = len(blocks)
        return result

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

    stylist = NotionStylist()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "set-style" and len(sys.argv) >= 3:
            page_id = sys.argv[2]
            cover = sys.argv[3] if len(sys.argv) > 3 else None
            icon = sys.argv[4] if len(sys.argv) > 4 else None
            print(_json.dumps(stylist.set_premium_style(page_id, cover, icon)))
        elif cmd == "add-nav" and len(sys.argv) >= 3:
            page_id = sys.argv[2]
            items = _json.loads(sys.argv[3])
            print(_json.dumps(stylist.create_navigation_grid(page_id, items)))
        elif cmd == "clear" and len(sys.argv) >= 3:
            page_id = sys.argv[2]
            stylist.clear_page_content(page_id)
            print("Page cleared.")
        elif cmd == "apply-template" and len(sys.argv) >= 4:
            page_id = sys.argv[2]
            template_name = sys.argv[3]
            result = stylist.apply_template(page_id, template_name)
            print(_json.dumps({"status": "ok", "template": result["template"]}))
        elif cmd == "architect" and len(sys.argv) >= 4:
            page_id = sys.argv[2]
            md_text = sys.argv[3]
            set_style = "--style" in sys.argv
            result = stylist.architect_page(page_id, md_text, set_style=set_style)
            print(_json.dumps({"status": "ok", "appended": result.get("appended", 0)}))
        elif cmd == "list-templates":
            for name, tpl in LAYOUT_TEMPLATES.items():
                print(f"{name}: {tpl.get('description', '')}")
