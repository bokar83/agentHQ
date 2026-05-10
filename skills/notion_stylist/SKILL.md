---
name: notion-stylist
description: Applies premium Catalyst Works visual styling to Notion pages and databases. Triggers on "notion stylist", "style this notion page", "notion branding", "format notion", "notion design".
---

# Notion Stylist Skill — agentsHQ Premium Branding

**Description:** Provides agents with the ability to apply high-end visual styling to Notion pages and databases. This includes setting branded covers, high-resolution icons, and creating complex multi-column layouts using the Catalyst Works color palette.

## Functions

- `set_page_style(page_id, cover_url, icon_emoji_or_url)`: Applies a premium cover and icon to a page.
- `create_hero_section(page_id, title, subtitle)`: Adds a high-impact callout block at the top of a page.
- `create_quick_grid(page_id, links)`: Generates a 2 or 3-column layout for dashboard navigation.
- `apply_brand_color(block_id, color_name)`: Updates a block's color to the Catalyst Works palette (Teal, Orange, Slate).

## Design Rules (Catalyst Works Protocol)
- **Primary Accent**: Teal (`#2dd4bf`) — Use for "Success" and "Knowledge" indicators.
- **Secondary Accent**: Orange (`#f97316`) — Use for "Active Task" and "Execution" indicators.
- **Background**: Strict Dark Mode compatibility. Use "Default" background (transparent on dark mode) for callouts.
- **Typography**: Logic-first. Outcome-first headings.

## Integration
This skill wraps the `notion-mcp-server` and provides a CLI for the orchestrator's agents to call during a `notion_overhaul` task.
