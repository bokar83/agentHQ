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
  prompt generation, and GWS CLI execution — end to end, no separate steps needed.
---

# Sheet Mint — Spreadsheet-to-Product Builder

You are building a **sellable Google Sheets digital product** end to end. The output is a
fully functional, visually polished spreadsheet that lands directly in the user's Google Drive
and is ready to share as a template for sale.

This skill has three phases. Complete all three without stopping unless you genuinely need
user input.

---

## Phase 1 — Research & Design (2–5 minutes)

Gather everything you need before writing a single formula. The more you know upfront, the
better the product.

### What to extract from the conversation

Look at what the user has already provided:
- **Reference image** — note the layout, tab count, color scheme, chart types, key features
- **Product type** — budget tracker, planner, business dashboard, habit tracker, etc.
- **Differentiator** — what makes this one original vs. the reference (color palette swap,
  extra tab, different niche/audience)

### What to decide (you decide, don't ask unless truly blocked)

| Decision | Guidance |
|---|---|
| Product name | Memorable, sellable. "Smart 50/30/20 Budget Planner", "Freelancer Income Tracker" |
| Color palette | Pick 4–5 hex codes that feel cohesive. Avoid copying reference exactly. |
| Tab count | 4–7 tabs. Dashboard + data log + 2–3 specialty tabs + hidden ref tab |
| Differentiating feature | One thing the reference doesn't have (e.g., Annual Overview, Debt Snowball, Savings Goals, Year-at-a-Glance) |
| Target buyer | Helps shape category names and sample data |

### Announce your design choices

Before proceeding to Phase 2, briefly tell the user:
- Product name and one-line description
- Color palette (show hex codes)
- Tab list
- The one differentiating feature
- Estimated Etsy price point ($10–$20)

Ask: "Happy with this direction, or want to adjust anything?" Wait for a green light or
specific changes, then proceed.

---

## Phase 2 — Generate the Build Prompt

Read the full prompt generator guide:
**`references/prompt-generator.md`**

Using that guide as your framework, write a comprehensive `BUILD_PROMPT.md` that Claude Code
can execute without any follow-up questions. Save it to:

```
D:\Ai_Sandbox\agentsHQ\zzzArchive\testingSandbox\[product-slug]\BUILD_PROMPT.md
```

Where `[product-slug]` is a short kebab-case folder name (e.g., `smart-budget-planner`,
`freelancer-income-tracker`).

The BUILD_PROMPT.md must include:
- Tab structure table with sheetId numbers
- Color palette table with hex + RGB float values
- Every column on every tab (header, type, formula or dropdown options)
- Exact formula logic (write actual formulas, not descriptions)
- 25–40 rows of realistic sample data across 2–3 months or periods
- Chart specs (type, data source ranges, colors, position, size)
- Conditional formatting rules
- Data validation dropdowns
- Frozen rows/columns per tab
- Build order (reference tab first, then data tabs, then dashboard)
- Final requirements checklist

Tell the user: "Build prompt saved to `[path]`. Starting build now."

---

## Phase 3 — Execute the Build via GWS CLI

Now actually build the spreadsheet. Work through it methodically in this order:

### Step 1 — Create the spreadsheet with all sheets

```bash
gws sheets spreadsheets create --params '{
  "properties": {"title": "[Product Name]"},
  "sheets": [
    {"properties": {"sheetId": 0, "title": "Dashboard", "index": 0}},
    {"properties": {"sheetId": 1, "title": "Transactions", "index": 1}},
    ...
    {"properties": {"sheetId": 6, "title": "_Ref", "index": 6,
      "hidden": true}}
  ]
}'
```

Capture the `spreadsheetId` from the response — you need it for every subsequent call.

### Step 2 — Populate reference/lookup tab first

Write all dropdown source data to the hidden `_Ref` tab using the values API:

```bash
gws sheets spreadsheets values update \
  --spreadsheet-id [ID] \
  --range "'_Ref'!A1:A13" \
  --params '{"values": [["MONTHS"],["January"],...],"valueInputOption":"USER_ENTERED"}'
```

### Step 3 — Write data and formulas to each tab

Use `valueInputOption: USER_ENTERED` so formulas are parsed. Write tab by tab:
1. Setup tab (income inputs, ratio controls)
2. Transactions tab (headers + all sample data rows)
3. Other data tabs (Debt Tracker, Savings Goals, etc.)
4. Dashboard tab (headers, KPI formulas, QUERY formulas) — last, so cross-references resolve

For large value writes, batch into logical sections (headers, sample data rows, formula rows)
to stay within API limits.

### Step 4 — Apply all formatting via batchUpdate

Group all formatting into ONE batchUpdate call per tab to minimize API calls. Include:
- `repeatCell` for header rows (background color, text color, bold, font size)
- `repeatCell` for body rows (number formats, alternating colors)
- `mergeCells` for title banners and section headers
- `updateDimensionProperties` for column widths and row heights
- `updateSheetProperties` for tab colors
- `updateFrozenProperties` for frozen rows/columns

Color conversion: hex `#264653` → `{red: 0.149, green: 0.275, blue: 0.325}`

### Step 5 — Add data validation (dropdowns)

One batchUpdate with all `setDataValidation` requests:

```json
{
  "setDataValidation": {
    "range": {"sheetId": 1, "startRowIndex": 1, "endRowIndex": 1000,
               "startColumnIndex": 2, "endColumnIndex": 3},
    "rule": {
      "condition": {"type": "ONE_OF_RANGE",
                    "values": [{"userEnteredValue": "='_Ref'!M1:M2"}]},
      "strict": true, "showCustomUi": true
    }
  }
}
```

### Step 6 — Add conditional formatting

One batchUpdate with all `addConditionalFormatRule` requests. Apply in priority order
(most specific rules first, catch-all rules last).

### Step 7 — Add charts

One chart per `addChart` request. For each chart, specify:
- `spec.basicChart` or `spec.pieChart`
- Source ranges as `GridRange` objects (sheetId + row/col indices, zero-indexed, end-exclusive)
- `position.overlayPosition` with `anchorCell`, `offsetXPixels`, `offsetYPixels`, `widthPixels`, `heightPixels`

### Step 8 — Output the result

After all calls succeed, output:

```
✅ BUILD COMPLETE

Product: [Name]
Spreadsheet ID: [ID]
Google Sheets link: https://docs.google.com/spreadsheets/d/[ID]/edit
Files saved to: D:\Ai_Sandbox\agentsHQ\zzzArchive\testingSandbox\[slug]\

To make it a sellable template:
1. Open the link above
2. File → Share → "Anyone with the link" → Viewer
3. File → Share → Publish to web (for Etsy delivery)
4. OR: Make a copy, then share the copy link as your product
```

---

## Error Handling

- **403 API not enabled**: Run `gcloud services enable sheets.googleapis.com` then retry
- **400 invalid range**: Check that sheet names with spaces are wrapped in single quotes in A1 notation: `'My Sheet'!A1:B10`
- **400 batchUpdate**: Log the failing request index, fix that single request, retry only the failed batch
- **Formula errors in output**: Verify `valueInputOption` is `USER_ENTERED` not `RAW`
- **Chart data mismatch**: Remember all ranges are zero-indexed and end-exclusive in the Sheets API

---

## Quality Bar

The finished spreadsheet should meet this bar before you declare it done:

- [ ] Dashboard updates when you change the month selector in Setup
- [ ] All charts render with data (not blank)
- [ ] Dropdowns work on Transactions tab
- [ ] Sample data populates all charts and conditional formatting rules
- [ ] No `#REF!`, `#NAME?`, or `#ERROR!` cells visible
- [ ] Tab colors set, frozen rows in place
- [ ] Shareable link output to user
