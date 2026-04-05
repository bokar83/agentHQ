# The Forge 2.0 -- Project Decision Summary & Build Plan

**Date:** 2026-04-05
**Owner:** Boubacar Barry (Catalyst Works Consulting)
**System:** agentsHQ (personal multi-agent system)
**Status:** Design approved, ready for implementation

---

## What This Document Is

This is a complete decision record for "The Forge 2.0" -- a rebuild of Boubacar's Notion workspace into a unified execution dashboard that is automatically populated by his agent system (agentsHQ) running on a VPS. Use this document to understand what was decided, why, and what needs to be built. It is designed to be consumed by any LLM assisting Boubacar on this project.

---

## Context: What Exists Today

### agentsHQ (The Execution Engine)
- A multi-agent system built with CrewAI, running on a VPS at 72.60.209.109
- Orchestrator routes tasks to specialized crews (research, social, website, consulting, hunter/prospecting, code, etc.)
- Agents are triggered via Telegram bot (@agentsHQ4Bou_bot) or CLI
- All code lives at `D:\Ai_Sandbox\agentsHQ` (local) and is deployed to VPS via Docker
- GitHub repo: `bokar83/agentHQ`

### The Forge 1.0 (The Problem)
- A Notion workspace built 8 months ago with 18 databases across 4 overlapping "command centers"
- **Not used since November 2025.** Every database required manual entry. Boubacar builds; he doesn't do data entry.
- Over-architected for a pre-revenue consulting practice (full e-commerce data model with Products, Packages, Variants, Licenses, Changelogs, etc.)
- 7 of 18 databases were empty shells with placeholder data

### The agentsHQ Notion Hub (Also Broken)
- A separate Notion page (ID: 327bcf1a302980b79b1ed77f94c9c61c) meant to be the agent operations dashboard
- Attempted visual overhaul failed: columns rendered at zero width (text displayed vertically), covers didn't apply, colors didn't work
- Root cause: NotionStylist tool didn't set `width_ratio` on column blocks, crew registry key mismatch prevented the crew from even running

---

## What Was Decided

### Core Principle
**Agent-populated, human-read.** Boubacar never manually enters data into Notion. agentsHQ on the VPS writes it. Boubacar opens Notion to see the state of his world. The only manual-entry database is Revenue Log, because logging revenue should feel like a celebration.

### Architecture Decision: One Page, Five Sections

Merge The Forge and the agentsHQ Hub into a single page called **"The Forge 2.0 -- Execution OS"**. The original Forge is archived as "The Forge (Archive -- v1.0)".

```
The Forge 2.0 -- Execution OS
|
+-- [KPI BAR] 4 metrics: Pipeline $ | Revenue MTD | Posts This Month | Tasks Done This Week
|
+-- [THIS WEEK] -- Tasks due in the next 7 days only. No backlog.
|
+-- [GROWTH ENGINE] -- Consulting Pipeline + Revenue Log
|
+-- [CONTENT] -- Ideas, Drafts, Queue (next 5 scheduled)
|
+-- [PLAYBOOK] -- Links to Frameworks, Playbooks, Catalyst10K Roadmap
|
+-- [ARCHIVES] -- Collapsed toggle with Agent Activity Log, Catalyst Engines, Products
```

### Database Decisions (18 -> 8)

**KEEP (8 databases):**
1. **Tasks** -- Merged from "Tasks & Sprints" (21 records) + "Execution" (7 records) into one database
2. **Consulting Pipeline** -- Lead/deal tracking. Populated by Hunter agent.
3. **Revenue Log** -- Revenue tracking. Only manual-entry DB. Has goal formulas.
4. **Content Board** -- NEW. Social media content lifecycle: Idea -> Draft -> Ready -> Queued -> Posted
5. **Catalyst Engines** -- 13 revenue stream entries. Read-only reference.
6. **Catalyst10K Roadmap** -- 10 strategic milestone entries. Read-only reference.
7. **Agent Activity Log** -- Every agent action writes here. Observability layer.
8. **Knowledge Base** -- Empty now. Populates when agent memory architecture ships.

**KILLED (10 databases):**
Packages & Versions, Variants & Licenses, Assets & Media, Changelogs & Release Notes, FAQs & Docs, Customers & Testimonials, Channels & Listings, Execution Tracker (agentsHQ duplicate), Products (archived, not killed -- accessible from Archives)

### Content Board Schema (Social Media)

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

**Automation contract:** Status=Queued AND Scheduled Date <= today -> post via Blotato -> flip Status to Posted, fill Posted Date.

### Social Media Posting: Blotato ($29/mo)

**Why Blotato, not direct API:**
- LinkedIn API requires manual approval (adversarial process, weeks of waiting, frequent rejections). Blotato already has approved OAuth credentials.
- Supports LinkedIn, X, YouTube (all platforms Boubacar needs)
- REST API at `https://backend.blotato.com/v2/posts` -- simple POST call from Python
- Official n8n community node as fallback
- $29/mo Starter plan includes unlimited text posts and API access

**How it wires in:**
1. Forge CLI reads Content Board entries where Status=Queued and Scheduled Date <= today
2. For each entry, calls Blotato API with post content and target platform accountId
3. On success, updates Notion entry: Status=Posted, Posted Date=now
4. Account IDs stored in `.env` as `BLOTATO_ACCOUNT_IDS` (JSON map of platform -> accountId)

### File Storage: Google Drive (Not Notion, Not Google Sheets)

**Existing:** Flat folder at Drive ID `1LWRslgiBwvLEbdh8Th9bKgVsHwFBFd1s` with 18 markdown files dumped unsorted.

**New structure:**
```
agentsHQ Outputs/
|-- deliverables/
|   |-- research/          # Research reports
|   |-- consulting/        # Proposals, briefs, diagnostics
|   |-- websites/          # Website builds, HTML exports
|   |-- social/
|   |   |-- linkedin/      # LinkedIn posts and articles
|   |   |-- x/             # X posts and threads
|   |   |-- youtube/       # Video scripts, thumbnails
|   |-- code/              # Scripts, tools, automations
|-- leads/                 # Hunter agent lead lists
|-- sessions/              # Session logs, handoffs
```

The existing `saver.py` already has Google Drive integration via OAuth. It gets updated to route files by `task_type` into the correct sub-folder.

### CLI-First Wiring: The Forge CLI

A unified Python CLI tool replacing three existing tools (NotionCLI, NotionStylist, notion_tool):

```bash
forge log "Built homepage" --agent Designer --status Success     # Agent Activity Log
forge task add "Wire Hunter" --priority P1 --due 2026-04-12      # Tasks DB
forge pipeline add "Acme Corp" --value 5000 --status Discovery   # Consulting Pipeline
forge revenue 2500 --source Consulting --buyer "Acme Corp"       # Revenue Log
forge content idea "AI adoption stalls at leadership" --platform LinkedIn  # Content Board
forge content queue <page_id> --scheduled 2026-04-10             # Set scheduled date
forge content publish                                            # Post all due content via Blotato
forge kpi refresh                                                # Update KPI Bar callout numbers
```

Every crew's final step calls `forge log`. Hunter crew calls `forge pipeline add`. Social crew calls `forge content draft`.

### NotionStylist Bug Fixes

| Bug | Fix |
|---|---|
| Zero-width columns (vertical text) | Add `width_ratio` float (0-1) to every column block |
| Too many columns per row | Chunk items into max 3 columns per column_list |
| Brand colors not applying | Map: teal -> green_background, orange -> orange_background, slate -> gray_background |
| Cover images failing | Use stable Unsplash CDN links (images.unsplash.com/photo-XXX), not redirect URLs |
| Duplicate content on re-runs | Add clear_page_content() to wipe blocks before rebuilding |
| Crew never runs | Router.py says "notion_overhaul_crew" but CREW_REGISTRY key is "notion_overhaul" -- one-line fix |

### KPI Bar (Dashboard Metrics)

Four callout blocks in a 2x2 column layout at the top of the landing page. Updated by `forge kpi refresh` which queries each database and patches the callout text.

| Metric | Source | Drives This Behavior |
|---|---|---|
| Pipeline $ | Consulting Pipeline, sum of Deal Value (open deals) | Prospecting activity |
| Revenue MTD | Revenue Log, sum this month | Closing activity |
| Posts This Month | Content Board, count where Posted Date = this month | Visibility activity |
| Tasks Done | Tasks, count where Status=Done this week | Execution velocity |

---

## What Is NOT Being Built (Phase 2+)

- **Blotato auto-posting (Phase 2, target: April 2026):** `forge content publish` wired to Blotato API. Schema is ready. Do not let this drift past April.
- Engagement tracking (likes/comments/views pulled back into Content Board)
- Trend charts (add when 3+ months of Revenue data exists)
- Agent shared memory system (Knowledge Base DB stays in Archives with zero dashboard visibility until memory architecture ships)
- Notion webhooks for real-time sync

## Review Notes (Cross-LLM Feedback)

**From Claude Chat (2026-04-05):**
1. Step 1 (NotionStylist fixes) is load-bearing. Verify column layouts on a scratch page BEFORE touching the real Forge page build.
2. Content Board has two data entry paths: manual via `forge content idea` CLI (Boubacar) and automated via social_crew (agents). This is intentional. CLI keeps it frictionless (5 seconds), distinct from opening Notion GUI.
3. Blotato auto-posting must not drift past April 2026. Phase 2 has a deadline now.
4. Knowledge Base DB moved fully to Archives. No dashboard visibility until memory architecture ships.

---

## Implementation Sequence

1. **Fix NotionStylist** -- Column width_ratio, row chunking, brand color map, cover images, clear-and-rebuild, crew registry key fix
2. **Build Forge CLI** -- Unified CLI at `skills/forge_cli/forge.py` with all commands above
3. **Create Google Drive folder structure** -- Sub-folders under existing outputs folder
4. **Update saver.py** -- Route files by task_type to correct Drive sub-folder
5. **Archive Forge 1.0** -- Duplicate page, rename to archive
6. **Build Forge 2.0 page** -- KPI Bar, This Week, Growth Engine, Content, Playbook, Archives sections
7. **Create Content Board database** -- New database with schema above
8. **Merge task databases** -- Move Execution records into Tasks & Sprints
9. **Wire crews to Forge CLI** -- Update crew final-step tasks to call forge commands
10. **Visual verification** -- Open in browser, confirm layout, test data flow

---

## Key Technical Details for Any LLM Picking This Up

- **Notion Page ID (The Forge):** 249bcf1a3029807f86e8fb97e2671154
- **Notion API Version:** 2022-06-28
- **Notion Secret env var:** NOTION_SECRET
- **VPS:** 72.60.209.109, Docker-based, Ubuntu
- **Google Drive folder ID:** 1LWRslgiBwvLEbdh8Th9bKgVsHwFBFd1s
- **Google OAuth creds:** /app/secrets/gws-oauth-credentials.json (on VPS)
- **n8n instance:** https://n8n.srv1040886.hstgr.cloud
- **Blotato API:** https://backend.blotato.com/v2/posts (auth via blotato-api-key header)
- **GitHub repo:** bokar83/agentHQ
- **Local project path:** D:\Ai_Sandbox\agentsHQ
- **Full design spec:** docs/superpowers/specs/2026-04-05-forge-2-design.md

---

## Rules for Any LLM Working on This

1. Never create files on the C: drive. All work goes in D:\Ai_Sandbox\agentsHQ or D:\Ai_Sandbox\
2. Never touch n8n Docker or VPS infrastructure directly (no docker stop, no SQLite edits). Use n8n UI or REST API only.
3. CLI-first. No MCP servers for this build.
4. Skills go in agentsHQ/skills/ first, then copy to ~/.claude/skills/
5. No em dashes in any output. Rewrite the sentence instead.
6. Use subagent-driven execution for implementation.
7. The user's name is Boubacar Barry (NOT Diallo). Address him as Boubacar.
8. Catalyst Works is a pre-revenue solo AI strategy consulting practice. The buyer is SMB owner-operators (50-500 employees), NOT enterprise CIOs.
9. agentsHQ is an internal tool. Never reference it as a product or something deployed for clients.
