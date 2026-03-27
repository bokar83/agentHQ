---
name: sheet-mint
description: >
  Use this skill when the user wants to build a sellable Google Sheets template or dashboard
  as a digital product — budget trackers, planners, business dashboards, habit trackers,
  wedding planners, or any spreadsheet meant for sale on Etsy, Gumroad, or similar platforms.
  TRIGGER on phrases like: "build a spreadsheet", "create a template to sell", "make a budget
  tracker", "I want to sell a Google Sheet", "build me a dashboard", "create a planner",
  "make a tracker", "sheet-mint", or whenever a reference image of a spreadsheet is provided
  alongside intent to build or sell it. This skill covers the FULL workflow: research,
  prompt generation, GWS CLI execution, and Etsy listing copy — end to end, no separate steps needed.
---

# Sheet Mint — Spreadsheet-to-Product Builder

You are building a **sellable Google Sheets digital product** end to end. The output is a
fully functional, visually polished spreadsheet that lands directly in the user's Google Drive
and is ready to share as a template for sale.

This skill has four phases. Complete all four without stopping unless you genuinely need
user input. **The finished product must look premium — not like a school project.**

---

## THE DESIGN STANDARD (Read This First, Every Time)

Before touching a single formula, internalize this: **the #1 reason spreadsheet templates
fail to sell is poor visual design, not missing functionality.** A spreadsheet with 80%
of the features but 100% of the visual polish will outsell a feature-complete but ugly one
every time.

The target is a product that a buyer looks at and immediately thinks: *"This looks worth $15."*

### Locked Design Rules

These rules apply to EVERY build. They are not suggestions.

#### Rule 1 — Color System
Every build uses exactly ONE of these two color systems. Choose based on the target buyer:

**Dark Premium (modern, tech-savvy buyers — budget trackers, business dashboards):**
```
Base (dashboard bg):     #0A0F1E   {red:0.039, green:0.059, blue:0.118}
Section bg (cards):      #141B2D   {red:0.078, green:0.106, blue:0.176}
Alt rows:                #1C2540   {red:0.110, green:0.145, blue:0.251}
Primary accent (vivid):  #00E676   {red:0.000, green:0.902, blue:0.463}  ← Needs
Secondary accent:        #FF4D8D   {red:1.000, green:0.302, blue:0.553}  ← Wants
Tertiary accent:         #00B0FF   {red:0.000, green:0.690, blue:1.000}  ← Savings/Debt
Text primary:            #F0F4FF   {red:0.941, green:0.957, blue:1.000}
Text muted:              #8892B0   {red:0.533, green:0.573, blue:0.690}
Border/divider:          #2A3555   {red:0.165, green:0.208, blue:0.333}
```

**Light Elegant (lifestyle buyers — wedding planners, habit trackers, personal finance):**
```
Base (dashboard bg):     #FAFAFA   {red:0.980, green:0.980, blue:0.980}
Section bg (cards):      #FFFFFF   {red:1.000, green:1.000, blue:1.000}
Alt rows:                #F5F7F2   {red:0.961, green:0.969, blue:0.949}
Primary accent:          #6B9E78   {red:0.420, green:0.620, blue:0.471}  ← sage green
Secondary accent:        #C97B6A   {red:0.788, green:0.482, blue:0.416}  ← terracotta
Tertiary accent:         #8FA8D8   {red:0.561, green:0.659, blue:0.847}  ← dusty blue
Text primary:            #1A1F2E   {red:0.102, green:0.122, blue:0.180}
Text muted:              #6B7280   {red:0.420, green:0.447, blue:0.502}
Border/divider:          #E2E8E0   {red:0.886, green:0.910, blue:0.878}
```

You may adjust the accent hues to match a reference image, but **never use navy as a base
on a dark theme** (reads soft/dull) and **never use generic green/teal combos without
one warm accent to break the monotony.**

#### Rule 2 — Typography Hierarchy (mandatory font sizes)
```
Dashboard title banner:   22pt, bold, accent color
Section header:           11pt, bold, ALL CAPS, muted text on section-bg
KPI value (the big number): 24pt, bold, primary accent color
KPI label (above value):   8pt, regular, muted text
KPI sublabel (below value): 8pt, italic, muted text
Table header row:          10pt, bold, header-bg background
Body / data rows:          10pt, regular
Chart title:               11pt, bold (set in chart spec)
```

**If any KPI value is smaller than 20pt, the product looks amateur. Non-negotiable.**

#### Rule 3 — Row Heights (mandatory)
```
Title banner row:          54px
Subtitle row:              28px
Spacer rows:               10px  ← use these between EVERY section
KPI label row:             22px
KPI value row:             46px
KPI sublabel row:          20px
Section header row:        32px
Table header row:          32px
Data rows:                 26px
```

#### Rule 4 — Card Structure for KPI Blocks
Never place a KPI value directly adjacent to a table or another section. Each KPI card must be:
- A block of 3 rows: label row / value row / sublabel row
- Wrapped in its own background color (section bg)
- Separated from adjacent cards by a narrow spacer column (12px wide)
- Left and right gutters: column A = 14px, last used column + 1 = 14px

**The card border technique:** Apply a thick top border (2px, accent color) to the label row
to visually frame each card. This is what makes a spreadsheet look like a designed dashboard.

#### Rule 5 — Progress Bars (use on every percentage/goal metric)
For any cell showing "X of budget used" or "progress toward goal," always add a progress bar
row directly below it using this formula:
```
=IFERROR(
  REPT("█", MIN(ROUND((actual/budget)*20), 20)) &
  REPT("░", MAX(20 - ROUND((actual/budget)*20), 0)),
  "░░░░░░░░░░░░░░░░░░░░"
)
```
- Font: Courier New or any monospace font, 8pt
- Color: Accent color when under budget, red when over budget (conditional formatting)
- Row height: 18px

This single element is the most visible difference between amateur and premium templates.

#### Rule 6 — Section Dividers
Between every logical section on the dashboard, insert:
- 1 spacer row (10px height, base background color)
- A section header row (merged across the full width, ALL CAPS, 11pt bold)

#### Rule 7 — Chart Standards
- **Minimum size:** 420px wide × 260px tall — smaller charts look cheap
- **Background color must match the dashboard background** — never leave the default white chart background on a dark dashboard
- **Always use the design system accent colors** for series (not Google's default blue/red)
- **Donut charts** (pieHole: 0.5) are more modern than pie charts — prefer them
- **Position charts to fill space** — don't leave large empty areas on the dashboard
- For dark themes: set chart backgroundColor, titleTextStyle color, legendTextStyle color,
  and axis textStyle color all to match the design palette

#### Rule 8 — Column Width Discipline
- Gutter columns (A and last): 14px
- Label columns: 120–160px
- Number/amount columns: 110–130px
- Category/status columns: 100–140px
- Notes/description columns: 180–240px
- Narrow spacer columns between card groups: 12px

---

## Phase 1 — Research & Design (2–5 minutes)

### Step 1A — Extract from reference images (if provided)

If the user provides reference images, extract ALL of the following before deciding anything:

| What to extract | Why it matters |
| --- | --- |
| **Color system** | Dark vs. light; exact accent hues | Sets the entire palette |
| **Layout grid** | How many KPI cards across? 3 or 4? | Drives column structure |
| **Card borders** | Thick top border? Full box? Shadow illusion? | Most visible design element |
| **Chart types and placement** | Donut? Bar? Where on the page? | Drives chart spec |
| **Typography scale** | How large are the KPI numbers relative to labels? | Sets font sizes |
| **Progress indicators** | Bars, gauges, percentage rings? | Add REPT bars for these |
| **Tab count and names** | What specialty tabs exist beyond the dashboard? | Drives tab structure |
| **Section arrangement** | What order? KPIs → Charts → Tables? | Drives row layout |

### Step 1B — Make your design decisions

| Decision | Guidance |
| --- | --- |
| Dark or Light theme | Dark = modern/tech; Light = lifestyle/elegant. Match the reference if given. |
| Color system | Use the locked palettes above. Only adjust accent hues to match reference. |
| Product name | Memorable and sellable. E.g., "Smart 50/30/20 Budget Planner" |
| Tab count | 4–7 tabs: Dashboard + data log + 2–3 specialty tabs + hidden _Ref |
| Differentiating feature | One thing better than the reference (annual overview, debt payoff, etc.) |
| Target price | $12–$20 on Etsy |

### Step 1C — Announce choices before Phase 2

Tell the user:
- Product name + one-liner
- Theme: Dark or Light, with primary accent color
- Tab list
- The one differentiating feature

**Auto-proceed rule:** If product type, niche, and a reference image exist → skip confirmation
and announce choices inline as you start Phase 2.

---

## Phase 2 — Generate the Build Prompt

Read the full reference:
**`references/prompt-generator.md`**

Write a comprehensive `BUILD_PROMPT.md` and save it to:
```
D:\Ai_Sandbox\agentsHQ\zzzArchive\testingSandbox\[product-slug]\BUILD_PROMPT.md
```

The BUILD_PROMPT.md **must include the Design System section** (see prompt-generator.md).
Without explicit pixel dimensions, font sizes, border specs, and card structure, the build
will produce a functional but visually amateur result.

Tell the user: "Build prompt saved. Starting build now."

---

## Phase 3 — Execute the Build via GWS CLI

### Technical Reference
The correct syntax for GWS CLI:
- `--params` = URL/query parameters (spreadsheetId, valueInputOption)
- `--json` = request body (data, requests)
- Write complex JSON to temp files at `C:\tmp\` (bash path: `/c/tmp/`) and pass with `$(cat /c/tmp/file.json)`
- Use `gws sheets spreadsheets values batchUpdate` for writing cell data
- Use `gws sheets spreadsheets batchUpdate` for formatting, validation, charts

### Build Order (never deviate)

1. **Create spreadsheet** with all sheets named and sheetIds assigned
2. **Populate _Ref tab** — all dropdown source data first
3. **Write data tabs** — headers, sample data, formulas (bottom-up: data tabs before dashboard)
4. **Write dashboard** — KPI formulas, QUERY formulas, layout text
5. **Apply ALL formatting** in one batchUpdate — merges, backgrounds, fonts, column widths, row heights, tab colors, frozen rows
6. **Apply data validation** (dropdowns)
7. **Apply conditional formatting** (including progress bar color rules)
8. **Add charts** — sized and positioned per spec, with matching background colors

### Design Implementation Checklist

For each batchUpdate formatting call, verify these are included:

**Dashboard:**
- [ ] Title banner: merged full-width, 54px tall, base bg, accent text, 22pt bold
- [ ] Spacer row after title: 10px, base bg
- [ ] KPI cards: 3-row structure (label/value/sublabel), 22/46/20px heights
- [ ] Thick top border on KPI label rows (accent color, 2px)
- [ ] Card spacer columns: 12px between each KPI card
- [ ] Left/right gutter columns: 14px
- [ ] Section headers: merged, ALL CAPS, 11pt bold, section-bg
- [ ] Spacer rows between every section: 10px
- [ ] Progress bar rows: 18px, Courier New font, 8pt

**Charts:**
- [ ] backgroundColor set to base bg color (not white)
- [ ] titleTextStyle foregroundColor set to accent or text-primary
- [ ] At least 420px wide, 260px tall
- [ ] Series colors match the design system palette

**All tabs:**
- [ ] Header row: 32px, header-bg, accent text, 10pt bold, frozen
- [ ] Data rows: 26px
- [ ] Tab colors match the design system

### Step 8 — Output the result

```
✅ BUILD COMPLETE

Product: [Name]
Spreadsheet ID: [ID]
Link: https://docs.google.com/spreadsheets/d/[ID]/edit

To make it a sellable template:
1. Open the link above
2. File → Share → "Anyone with the link" → Viewer
3. Copy that link — it's your product delivery URL
```

---

## Phase 4 — Listing & Mockup (Optional but recommended)

### 4a — Mockup image
Tell the user to screenshot the Dashboard tab, then use Gemini or photop.com:

**Gemini prompt:**
```
Take this spreadsheet screenshot and place it on a realistic MacBook Pro or iPad Pro
mockup. Clean background, slight drop shadow, professional studio lighting. No text overlays.
Make it look like a premium Etsy digital product listing image.
```

### 4b — Etsy listing copy

**Title (max 140 chars):**
```
[Product Name] | Google Sheets Budget Template | Instant Download | Excel Compatible
```

**Description:**
```
Stop guessing where your money goes. The [Product Name] gives you a complete, beautiful
picture of your finances in one Google Sheets template.

✅ WHAT YOU GET:
[One line per tab describing what it does]

✅ KEY FEATURES:
• [Feature 1]
• [Feature 2]
• [Feature 3]
• Works on Google Sheets (free) and Microsoft Excel
• Instant download — no waiting, no shipping
• Lifetime access — yours forever

HOW IT WORKS:
1. Purchase → instant download link delivered
2. Click the link → copy goes straight to your Google Drive
3. Open Setup tab → enter your income and you're ready to go

PERFECT FOR:
[1-2 sentences describing the target buyer]

Questions? Message me — I respond within 24 hours.
```

**Tags:** Generate 13 tags mixing product terms, buyer intent, and format terms.

### 4c — Template delivery
1. File → Share → "Anyone with the link" → Viewer
2. Copy the link
3. In Etsy listing → Digital Downloads → upload a PDF with the link + instructions

---

## Error Handling

- **403 API not enabled:** `gcloud services enable sheets.googleapis.com` then retry
- **400 invalid range:** Sheet names with spaces need quotes: `'My Sheet'!A1:B10`
- **Chart background not applying:** Set backgroundColor as a top-level chart spec property
- **Formula not parsing:** Verify `valueInputOption` is `USER_ENTERED` not `RAW`
- **Bash JSON escaping issues:** Write JSON to `C:\tmp\file.json` using Write tool, then `$(cat /c/tmp/file.json)`

---

## Quality Bar — Visual AND Functional

Do not declare the build complete until all of these pass:

### Functional
- [ ] Dashboard updates when month selector changes
- [ ] All charts render with data (not blank)
- [ ] Dropdowns work on all data tabs
- [ ] No `#REF!`, `#NAME?`, or `#ERROR!` cells visible
- [ ] Cross-sheet formulas wrapped in IFERROR

### Visual (equally mandatory)
- [ ] KPI values are at least 20pt — if not, fix before declaring done
- [ ] Each KPI card has a visible thick top border in accent color
- [ ] Progress bars present for every percentage/goal metric
- [ ] Charts have matching background color — no white boxes on dark theme
- [ ] Spacer rows between every section (at least 10px)
- [ ] No cells where content runs edge-to-edge without padding
- [ ] Left and right gutter columns exist on the dashboard
- [ ] Section headers are visually distinct from data rows
- [ ] Tab colors are set and match the design system
- [ ] The dashboard looks like a designed product, not a formatted spreadsheet
