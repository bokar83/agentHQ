# The Forge 2.0 -- Execution OS Design Spec

**Date:** 2026-04-05
**Author:** Claude Opus 4.6 + Boubacar Barry
**Status:** Approved
**Hub Page ID:** 249bcf1a3029807f86e8fb97e2671154

---

## 1. Problem Statement

The Forge 1.0 was built 8 months ago as a digital product factory with 18 databases across 4 overlapping command centers. None have been used since November 2025. Root causes:

1. Every database required manual entry. Boubacar builds; he doesn't do data entry.
2. No uncomfortable metrics. Empty dashboards feel bad, so they get ignored.
3. Four "command centers" with no single entry point. No habit formed.
4. The agentsHQ system (VPS, CLI, CrewAI) does the real work but doesn't write to Notion.

## 2. Design Principles

1. **Agent-populated, human-read.** agentsHQ on the VPS writes data. Boubacar opens Notion to see state. One manual-entry database (Revenue Log) because logging revenue should feel like a win.
2. **CLI-first wiring.** A unified `forge` CLI handles all Notion writes. No MCP servers, no middleware.
3. **Google Drive for files, Notion for state.** Deliverables go to Drive in structured folders. Notion tracks what happened, who did it, what's next.
4. **10-second rule.** Every interaction must complete in under 10 seconds. If it takes longer, the design is wrong.
5. **No empty containers.** Every section either auto-populates from agent activity or contains reference content already written. Nothing requires manual maintenance.

## 3. Architecture

### 3.1 Page Structure

```
The Forge 2.0 -- Execution OS
|
+-- [KPI BAR] 4 metrics in a 2x2 column layout
|   Pipeline $  |  Revenue MTD
|   Posts Month  |  Tasks Done Week
|
+-- [THIS WEEK]
|   Linked view: Tasks (Status=Active, Due=This Week)
|   Max 7 items. No backlog on landing page.
|
+-- [GROWTH ENGINE]
|   Linked view: Consulting Pipeline (Status != Closed Lost)
|   Linked view: Revenue Log (This Month)
|
+-- [CONTENT]
|   Linked view: Ideas (Status=Idea, last 5)
|   Linked view: Drafts (Status=Draft)
|   Linked view: Queue (Status=Queued, sorted by Scheduled Date, next 5)
|
+-- [PLAYBOOK]
|   Link: Frameworks & Thinking Tools (page 272bcf1a)
|   Link: Playbooks, Workshops, & Tools (page 272bcf1a30298002)
|   Link: Catalyst10K Roadmap (database 2b0bcf1a)
|
+-- [ARCHIVES] (collapsed toggle)
|   Link: Agent Activity Log
|   Link: Catalyst Engines
|   Link: Products & Landing Pages
|   Link: The Forge 1.0 (archived original)
```

### 3.2 KPI Bar Implementation

Four Notion callout blocks arranged in a 2-column layout (`width_ratio: [0.5, 0.5]`), two rows. Each callout contains a single metric number (emoji + bold number + label). Updated by `forge kpi refresh` which queries each source database, computes the metric, and patches the callout block's rich_text via the Notion API. This approach is chosen over formula/rollup properties because it works across multiple databases without requiring relations.

| Metric | Source | Calculation |
|---|---|---|
| Pipeline $ | Consulting Pipeline DB | Sum of Deal Value where Status != Closed Lost |
| Revenue MTD | Revenue Log DB | Sum of Amount where Date >= first of month |
| Posts This Month | Content Board DB | Count where Posted Date >= first of month |
| Tasks Done | Tasks DB | Count where Status=Done and Completed Date >= Monday |

### 3.3 Visual Design System (UI/UX Pro Max Reviewed)

Design intelligence sourced from UI/UX Pro Max (Executive Dashboard style, Consulting Firm color palette, Dark Mode OLED aesthetic). Adapted to Notion's constrained block canvas.

**Cover Image:**
Dark abstract/network aesthetic, 1500px+ wide, landscape, centered composition.
- Primary: `https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1500&q=80` (dark globe/network)
- Alt 1: `https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=1500&q=80` (dark abstract geometry)
- Alt 2: `https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=1500&q=80` (dark forge/anvil aesthetic)

**Icon:** Custom uploaded icon (Catalyst Works logo or forge/anvil SVG), NOT an emoji. Emojis look unprofessional on a premium dashboard.

**Color System (Notion API Mappings):**

Sourced from boubacarbarry.com (#070A13 base, #0EA5E9 cyan, #F59E0B gold) and catalystworks.consulting (#071A2E navy, #00B7C2 cyan, #FF7A00 orange). The Forge uses the darker Catalyst Works palette. Notion's block colors are the closest available matches.

| Brand Color | Source Hex | Notion API Value | Usage |
|---|---|---|---|
| Cyan (Primary) | #00B7C2 | `blue_background` | KPI callouts, hero section, primary emphasis |
| Orange (CTA/Action) | #FF7A00 | `orange_background` | Active items, alerts, pipeline highlights, CTAs |
| Navy (Authority) | #071A2E | `default` | Body content (Notion dark mode renders this naturally) |
| Slate (Secondary) | #1E222A | `gray_background` | Archives, secondary info, muted content |
| Teal (Success) | #2dd4bf | `green_background` | Success states, completed items, positive KPIs |
| Alert | #EF4444 | `red_background` | Blocked tasks, overdue items (use sparingly) |

Note: Notion's dark mode uses #191919 as base background, which is close to our Carbon (#1E222A). The `default` color (no background) renders best in dark mode. Use colored backgrounds only for emphasis, not as default. This keeps the dark aesthetic clean.

**Layout Rules:**
- All column layouts use explicit `width_ratio` values. Never more than 3 columns per `column_list`.
- KPI Bar: 2 rows of 2 columns each, `width_ratio: [0.5, 0.5]`
- Navigation grids: max 3 columns, `width_ratio: [0.33, 0.34, 0.33]`

**Section Pattern (consistent across all 5 sections):**
```
## [Emoji] Section Name
---
[linked database view or content]
```
No callout wrapping on section headers. Clean, not cluttered.

**Database View Types:**

| Database | View Type | Rationale |
|---|---|---|
| Tasks (This Week) | Table, filtered by Active + Due This Week | Scannable: Priority, Status, Due Date at a glance |
| Consulting Pipeline | Board (kanban by Status) | Visual pipeline flow: Discovery -> Proposal -> Negotiation -> Won |
| Revenue Log | Table, sorted by Date desc | Latest revenue first, celebration view |
| Content Ideas | Gallery | Visual cards with title + platform tags |
| Content Queue | Table, sorted by Scheduled Date asc | Chronological, next-to-post first |

**Empty State Design:**
If a section has no data, show a single callout with `gray_background`:
"No [items] yet. Use `forge [command]` to add one."
Never show blank space or "under construction" placeholders.

**Notion Aesthetic Tips (sourced from Thomas Frank + UI/UX Pro Max):**

1. **Callout styling:** Use `default` background on callouts (renders as subtle grey outline in dark mode) instead of solid colored backgrounds. Reserve colored backgrounds for KPI emphasis only.
2. **Toggle menus:** Nest the Archives and Playbook links inside toggle blocks to reduce dashboard clutter. Toggle stays collapsed by default.
3. **Cover images:** 1600x900px (16:9), under 5MB. Use Unsplash CDN links with `?w=1600&q=80`.
4. **Native Notion icons:** Use Notion's built-in icon set (not random emojis) with consistent color. For the page icon, upload a custom SVG/PNG (Catalyst Works mark).
5. **Board view covers:** For Content Board gallery view, set Card Preview to "Page Cover" so content cards show visual thumbnails.
6. **Colored board columns:** Enable Color Columns on Pipeline board view so Discovery/Proposal/Negotiation/Won columns have distinct colors.
7. **Property hiding:** Use "Hide when empty" for optional properties, "Always hide" for internal/automation properties (Agent, Drive Link).
8. **Inline monospace:** Use backtick code styling for CLI command hints in empty states (e.g., `forge pipeline add`).
9. **Page font:** Set to Default (sans-serif) for clean dashboard feel. Not Serif, not Mono.
10. **Full width:** Enable full page width for the dashboard. More breathing room for database views.

**Anti-Patterns (Must Avoid):**
- No random emojis as structural icons (use Notion's native icon set with consistent color)
- No inline databases on landing page (use linked views from source pages)
- No deep nesting (max 1 level of sub-pages from landing)
- No decorative empty blocks or excessive dividers
- No more than 3 columns in any layout
- No solid colored backgrounds on body content (dark mode looks best with `default` or subtle outlines)
- No sidebar-dependent layouts (breaks on mobile -- Notion stacks columns vertically)

## 4. Database Schemas

### 4.1 Tasks (MERGED from Tasks & Sprints + Execution)

Merge the two existing task databases into one. Database ID: use existing Tasks & Sprints (249bcf1a302980739c26c61cad212477). Migrate Execution records into it.

| Property | Type | Values/Notes |
|---|---|---|
| Task | title | What needs to happen |
| Priority | select | P1, P2, P3 |
| Status | select | To Do, Active, Done, Blocked |
| Due Date | date | When it's due |
| Completed Date | date | When it was finished |
| Owner | select | Boubacar, Agent, Social Crew, Hunter |
| Area | select | Build, Growth, Content, Ops |
| Sprint | select | Week identifier (e.g., W15-2026) |
| Notes | rich_text | Context, blockers, links |
| Is Open | formula | Status != "Done" |

### 4.2 Consulting Pipeline

Keep existing database (249bcf1a302980f58d84cbbf4fa4dbdb). Clear "XYZ Inc." placeholder. Schema:

| Property | Type | Values/Notes |
|---|---|---|
| Lead/Company | title | Company or person name |
| Contact Name | rich_text | Decision maker |
| Email | email | Contact email |
| Source | select | Hunter Agent, LinkedIn, Referral, Inbound |
| Status | select | Discovery, Proposal, Negotiation, Closed Won, Closed Lost |
| Deal Value | number | Dollar amount (currency format) |
| Next Action | rich_text | What's the next step |
| Next Action Date | date | When to follow up |
| Notes | rich_text | Context |
| Created | created_time | Auto |

### 4.3 Revenue Log

Keep existing database (24abcf1a3029801f8231d694427dca35). Clean up duplicate relation. Schema:

| Property | Type | Values/Notes |
|---|---|---|
| Description | title | What was sold |
| Amount | number | Dollar amount (currency format) |
| Date | date | When payment received |
| Source | select | Consulting, Digital Product, Workshop, Other |
| Buyer | rich_text | Who paid |
| Notes | rich_text | Context |
| Month | formula | formatDate(Date, "YYYY-MM") |

### 4.4 Content Board (NEW)

Create new database on The Forge 2.0 page.

| Property | Type | Values/Notes |
|---|---|---|
| Title | title | Post headline or working title |
| Status | select | Idea, Draft, Ready, Queued, Posted |
| Platform | multi_select | LinkedIn, X, YouTube |
| Type | select | Post, Article, Thread, Video, Carousel |
| Content | rich_text | The actual post text |
| Drive Link | url | Link to Google Drive file for long-form/assets |
| Scheduled Date | date | When automation should post it |
| Posted Date | date | When it actually went live |
| Agent | select | Boubacar, Social Crew, leGriot |
| Topic | multi_select | AI, Leadership, Systems, TOC, Catalyst Works, Personal |

**Automation contract:** Status=Queued AND Scheduled Date <= today -> post it. After posting: flip Status to Posted, fill Posted Date.

**Dashboard views:**
- Landing page: Ideas (last 5), Drafts, Queue (next 5 by Scheduled Date)
- Sub-page "Content Calendar": Full board/calendar view for planning sessions

### 4.5 Catalyst Engines (KEEP AS-IS)

Database ID: linked from Catalyst10K. 13 records. Do not modify schema. Linked from Archives section.

### 4.6 Catalyst10K Roadmap (KEEP AS-IS)

Database ID: 2b0bcf1a. 10 records. Do not modify. Linked from Playbook section.

### 4.7 Agent Activity Log (KEEP)

Database ID: 339bcf1a3029818c8f27fb4203b23603. Schema stays. Every agent action writes here via `forge log`. Linked from Archives section, not on main dashboard.

### 4.8 Knowledge Base (KEEP)

Database ID: 339bcf1a302981919f81fec7a0bb875d. Empty now, populates as agent memory architecture ships. Linked from Archives.

## 5. The Forge CLI

Unified Python CLI replacing NotionCLI, NotionStylist, and notion_tool. Lives at `skills/forge_cli/forge.py`.

### 5.1 Commands

```bash
# Logging agent actions
forge log "Built homepage for client X" --agent Designer --status Success

# Task management
forge task add "Wire Hunter to Pipeline" --priority P1 --due 2026-04-12 --area Growth
forge task done <page_id>

# Pipeline management
forge pipeline add "Acme Corp" --contact "John Smith" --email "john@acme.com" \
  --value 5000 --status Discovery --source "Hunter Agent"

# Revenue logging
forge revenue 2500 --source Consulting --buyer "Acme Corp" --description "AI Diagnostic"

# Content management
forge content idea "Why AI adoption stalls at leadership" --platform LinkedIn --topic AI,Leadership
forge content draft <page_id> --content "Post text here..." --drive-link "https://drive.google.com/..."
forge content queue <page_id> --scheduled 2026-04-10
forge content posted <page_id>

# KPI refresh (updates the callout blocks on the landing page)
forge kpi refresh

# System status
forge status
```

### 5.2 Implementation Notes

- Uses `httpx` for Notion API calls (consistent with existing code)
- Reads `NOTION_SECRET` and database IDs from `.env`
- New env vars needed:
  - `FORGE_PAGE_ID` -- The Forge 2.0 landing page ID
  - `FORGE_TASKS_DB` -- Tasks database ID
  - `FORGE_PIPELINE_DB` -- Consulting Pipeline database ID
  - `FORGE_REVENUE_DB` -- Revenue Log database ID
  - `FORGE_CONTENT_DB` -- Content Board database ID
  - `FORGE_KPI_BLOCK_IDS` -- Comma-separated block IDs for the 4 KPI callouts
- Rate limiting: 3 req/sec max, exponential backoff on 429
- All commands return the Notion page URL on success

### 5.3 CrewAI Integration

Every crew's final task step calls `forge log` to record output. Specific crews also write to relevant databases:

| Crew | Forge Command | Database |
|---|---|---|
| All crews | `forge log` | Agent Activity Log |
| hunter_crew | `forge pipeline add` | Consulting Pipeline |
| social_crew | `forge content draft` | Content Board |
| All crews | saver.py `save_to_drive()` | Google Drive |

## 6. Google Drive Structure

### 6.1 Folder Hierarchy

```
agentsHQ Outputs/ (ID: 1LWRslgiBwvLEbdh8Th9bKgVsHwFBFd1s)
|-- deliverables/
|   |-- research/          # Research reports
|   |-- consulting/        # Proposals, briefs, diagnostics
|   |-- websites/          # Website builds, HTML exports
|   |-- social/
|   |   |-- linkedin/      # LinkedIn posts and articles
|   |   |-- x/             # X posts and threads
|   |   |-- youtube/        # Video scripts, thumbnails
|   |-- code/              # Scripts, tools, automations
|-- leads/                 # Hunter agent lead lists
|-- sessions/              # Session logs, handoffs
```

### 6.2 Saver.py Updates

Update `save_to_drive()` to accept `task_type` and route to the correct sub-folder. Create sub-folders on first use if they don't exist.

Mapping:
- research_report -> deliverables/research/
- consulting_deliverable -> deliverables/consulting/
- website_build -> deliverables/websites/
- social_content -> deliverables/social/ (further routed by platform)
- code_task -> deliverables/code/
- hunter_task -> leads/
- default -> deliverables/

## 7. NotionStylist Fixes

### 7.1 Column Width Fix

Add `width_ratio` to every column block. Current code creates columns without width specification, causing Notion to render zero-width columns.

```python
# Before (broken)
{"type": "column", "column": {"children": [...]}}

# After (fixed)
{"type": "column", "column": {"children": [...]}, "width_ratio": 0.5}
```

### 7.2 Row Chunking

`create_navigation_grid()` must chunk items into rows of max 3 columns. Each row is a separate `column_list` block.

### 7.3 Brand Color Map

```python
BRAND_COLORS = {
    "teal": "green_background",
    "orange": "orange_background",
    "slate": "gray_background",
    "dark": "default",
}
```

### 7.4 Cover Images

Use stable Unsplash CDN direct links (not source.unsplash.com redirects):
- `https://images.unsplash.com/photo-XXXXX?w=1500&q=80`
- Minimum 1500px wide, landscape orientation

### 7.5 Clear and Rebuild

Add `clear_page_content(page_id)` method that deletes all child blocks before rebuilding. Prevents duplicate content on re-runs.

### 7.6 Crew Registry Fix

Router.py line 64: change `"crew": "notion_overhaul_crew"` to `"crew": "notion_overhaul"` to match CREW_REGISTRY key.

## 8. Migration Plan

### 8.1 Archive The Forge 1.0

1. Duplicate The Forge page via Notion API
2. Rename duplicate to "The Forge (Archive -- v1.0)"
3. Move to a collapsed section or separate area

### 8.2 Build The Forge 2.0

1. Clear the original Forge page content (keep the page ID alive)
2. Rename to "The Forge 2.0 -- Execution OS"
3. Apply premium cover and icon
4. Build KPI Bar (4 callout blocks in 2x2 column layout)
5. Build each section with linked database views
6. Create Content Board database
7. Merge Execution records into Tasks & Sprints
8. Clear placeholder data from Consulting Pipeline
9. Clean up Revenue Log (remove duplicate relation)

### 8.3 Wire the VPS

1. Build `forge` CLI tool
2. Add new env vars to `.env` and VPS Docker config
3. Update `saver.py` with folder routing
4. Update crew final-step tasks to call `forge log`
5. Update hunter_crew to call `forge pipeline add`
6. Update social_crew to call `forge content draft`

### 8.4 Create Google Drive Folders

1. Create sub-folder structure under existing outputs folder
2. Update `GOOGLE_DRIVE_FOLDER_ID` references or add folder ID mappings

## 9. Social Media Posting: Blotato Integration

### 9.1 Why Blotato

LinkedIn's API requires manual approval (adversarial process, weeks of waiting, frequent rejections). Blotato ($29/mo Starter plan) already has approved OAuth credentials with LinkedIn, X, and YouTube. It provides a REST API at `https://backend.blotato.com/v2/posts` that accepts a simple POST with text content and publishes directly. No OAuth dance on our end.

### 9.2 Setup (One-Time)

1. Sign up for Blotato Starter ($29/mo) at blotato.com
2. Connect LinkedIn and X accounts in Blotato dashboard (GUI, one-time)
3. Copy API key from Settings -> API Access
4. Add to `.env`: `BLOTATO_API_KEY` and `BLOTATO_ACCOUNT_IDS` (JSON mapping of platform -> accountId)

### 9.3 Posting Flow

```
Content Board (Notion)          Forge CLI               Blotato API
Status=Queued              ->   forge content publish   ->   POST /v2/posts
Scheduled Date <= today         reads content from DB        publishes to platform
                           <-   updates Status=Posted   <-   returns success
                                fills Posted Date
```

### 9.4 API Call (Python)

```python
import requests

response = requests.post(
    "https://backend.blotato.com/v2/posts",
    headers={
        "blotato-api-key": BLOTATO_API_KEY,
        "Content-Type": "application/json"
    },
    json={
        "accountId": ACCOUNT_IDS["linkedin"],
        "content": {"text": post_content},
        "target": {"targetType": "publish"}
    }
)
```

### 9.5 n8n Fallback

Blotato has an official n8n community node (`@blotato/n8n-nodes-blotato`). If direct API calling from the forge CLI proves unreliable, wire through n8n as a fallback. But direct Python calls are preferred (CLI-first principle).

### 9.6 Content Board Schema Impact

No schema changes needed. The Content Board schema already has Platform (multi_select) and Scheduled Date (date) which are the two fields Blotato needs. The `accountId` mapping lives in `.env` configuration, not in the database.

## 10. Future Extensions (Not Built Now)

- **Blotato auto-posting (Phase 2, target: April 2026):** Wire `forge content publish` to Blotato API. Schema is ready. Do not let this drift past April.
- **Engagement tracking:** Pull likes/comments/views back into Content Board via Blotato or platform APIs
- **Charts:** Add trend charts to KPI Bar when 3+ months of Revenue data exists
- **Agent Memory:** Populate Knowledge Base as shared memory architecture ships. DB stays in Archives with no dashboard visibility until then.
- **Webhooks:** Notion webhooks (API 2025-09-03) for real-time sync
- **YouTube automation:** Blotato supports YouTube; wire when video content pipeline is ready

## 10. Success Criteria

1. Boubacar opens Notion and sees 4 current KPI numbers without clicking anything
2. Every agent crew run produces a visible entry in Notion
3. Every deliverable lands in the correct Google Drive folder
4. Content ideas can be captured in under 5 seconds via `forge content idea`
5. The landing page loads clean with no empty sections or stale data
6. Zero manual data entry required except Revenue Log (intentional)
