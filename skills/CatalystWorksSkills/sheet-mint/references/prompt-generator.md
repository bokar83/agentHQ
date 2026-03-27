# Spreadsheet Prompt Generator — Reference Guide

This guide defines the exact structure for writing a BUILD_PROMPT.md that Claude Code can
execute end-to-end using the GWS CLI to produce a fully functional, **visually premium**,
sellable Google Sheets spreadsheet.

---

## How the Build System Works

Two main APIs:

1. **Values API** (`gws sheets spreadsheets values batchUpdate`) — writes cell data including
   text, numbers, and formulas. Uses A1 notation with sheet names (e.g., `'My Sheet'!A1:C10`).
   Must set `valueInputOption: USER_ENTERED` for formulas to be parsed.
   - `--params` = URL query params (spreadsheetId, valueInputOption)
   - `--json` = request body (data array)

2. **Batch Update API** (`gws sheets spreadsheets batchUpdate`) — handles everything visual
   and structural: cell formatting, merges, charts, data validation, conditional formatting,
   frozen rows/columns, column widths, adding/renaming/hiding sheets.
   - `--params` = URL query params (spreadsheetId)
   - `--json` = request body (requests array)

**For complex JSON, always write to `C:\tmp\file.json` (bash: `/c/tmp/file.json`) and pass
with `$(cat /c/tmp/file.json)` to avoid bash escaping failures.**

**Build order — never deviate:**

1. Create spreadsheet with all named sheets
2. Populate _Ref tab (dropdown sources first — other tabs reference it)
3. Write data tabs: headers, sample data rows, formulas
4. Write dashboard tab (last — so all cross-references resolve)
5. Apply ALL formatting in one batchUpdate per logical group
6. Apply data validation (dropdowns)
7. Apply conditional formatting
8. Add charts (sized and positioned per spec, background color matching dashboard)

---

## DESIGN SYSTEM — Required in Every BUILD_PROMPT

This section is **not optional**. Without it, the build produces a functional but visually
amateur result. The design system defines how the spreadsheet looks, feels, and sells.

### Choose One Theme

**Dark Premium** — use for: budget trackers, business dashboards, modern planners

```text
Base (dashboard bg):     #0A0F1E   {red:0.039, green:0.059, blue:0.118}
Section bg (cards):      #141B2D   {red:0.078, green:0.106, blue:0.176}
Alt rows:                #1C2540   {red:0.110, green:0.145, blue:0.251}
Accent 1 (primary):      #00E676   {red:0.000, green:0.902, blue:0.463}
Accent 2 (secondary):    #FF4D8D   {red:1.000, green:0.302, blue:0.553}
Accent 3 (tertiary):     #00B0FF   {red:0.000, green:0.690, blue:1.000}
Text primary:            #F0F4FF   {red:0.941, green:0.957, blue:1.000}
Text muted:              #8892B0   {red:0.533, green:0.573, blue:0.690}
Border/divider:          #2A3555   {red:0.165, green:0.208, blue:0.333}
```

**Light Elegant** — use for: wedding planners, habit trackers, lifestyle products

```text
Base (dashboard bg):     #FAFAFA   {red:0.980, green:0.980, blue:0.980}
Section bg (cards):      #FFFFFF   {red:1.000, green:1.000, blue:1.000}
Alt rows:                #F5F7F2   {red:0.961, green:0.969, blue:0.949}
Accent 1 (primary):      #6B9E78   {red:0.420, green:0.620, blue:0.471}
Accent 2 (secondary):    #C97B6A   {red:0.788, green:0.482, blue:0.416}
Accent 3 (tertiary):     #8FA8D8   {red:0.561, green:0.659, blue:0.847}
Text primary:            #1A1F2E   {red:0.102, green:0.122, blue:0.180}
Text muted:              #6B7280   {red:0.420, green:0.447, blue:0.502}
Border/divider:          #E2E8E0   {red:0.886, green:0.910, blue:0.878}
```

Accent hues may be adjusted to match a reference image. Never use navy as a dark base
(reads soft). Never use multiple competing vivid accents.

---

### Typography Hierarchy

These font sizes are locked. Smaller KPI values = amateur result.

| Element | Size | Style |
| --- | --- | --- |
| Dashboard title banner | 22pt | Bold, Accent 1 color |
| Section header | 11pt | Bold, ALL CAPS, Text muted |
| KPI value (the big number) | 24pt | Bold, Accent color for that category |
| KPI label (above value) | 8pt | Regular, Text muted |
| KPI sublabel (below value) | 8pt | Italic, Text muted |
| Table header row | 10pt | Bold, Text primary |
| Body / data rows | 10pt | Regular |

---

### Row Height Standards

| Row type | Height (px) |
| --- | --- |
| Title banner | 54 |
| Subtitle | 28 |
| Spacer (between sections) | 10 |
| KPI label row | 22 |
| KPI value row | 46 |
| KPI sublabel row | 20 |
| Section header | 32 |
| Table header | 32 |
| Data rows | 26 |
| Progress bar row | 18 |

**Spacer rows between every section are mandatory.** They are what makes a dashboard feel
breathable and designed rather than cramped.

---

### KPI Card Structure

Each KPI card on the dashboard is a 3-row block:

```text
Row N:   Label row     — 22px — "TOTAL INCOME" — 8pt, muted text, section-bg
Row N+1: Value row     — 46px — "$12,450"      — 24pt bold, accent color, section-bg
Row N+2: Sublabel row  — 20px — "This Month"   — 8pt italic, muted text, section-bg
```

**Card border:** Apply a thick top border (3px SOLID, Accent 1 color) to Row N.
This is the single most visible design element separating premium from amateur.

**Card spacing:** Separate adjacent cards with a narrow spacer column (12px wide).

**Gutter columns:** Column A and the last used column on the dashboard = 14px wide.
This creates padding and prevents content from running edge-to-edge.

Never place a KPI value directly adjacent to a table or another section without
a spacer row between them.

---

### Progress Bar Pattern

Use on every percentage, goal, or budget-vs-actual metric. Place in a row directly
below the KPI value:

```text
=IFERROR(
  REPT("█", MIN(ROUND((actual/budget)*20), 20)) &
  REPT("░", MAX(20 - ROUND((actual/budget)*20), 0)),
  "░░░░░░░░░░░░░░░░░░░░"
)
```

Formatting specs:

- Font: Courier New, 8pt (proportional fonts make the blocks uneven)
- Row height: 18px
- Color: Accent 1 when at/under budget, red `{red:1.0, green:0.231, blue:0.188}` when over

Apply conditional formatting to color this cell based on `actual/budget >= 1`.

This element is the most visible differentiator between amateur and premium templates.

---

### Chart Visual Standards

**Size minimums:** 420px wide × 260px tall. Smaller charts look cheap.

**Background:** Always set `backgroundColor` to match the dashboard base color.
A white chart box on a dark dashboard immediately signals "unfinished."

**Dark theme chart text:** Set `titleTextStyle`, `legendTextStyle`, and axis `textStyle`
foregroundColor to Text primary (`#F0F4FF`) so labels are visible on dark backgrounds.

**Colors:** Use design system accent colors for series. Never use Google's default blue/red.

**Chart type guidance:**

- Donut (`pieHole: 0.5`) over standard pie — looks more modern
- Column chart for month-over-month comparisons
- Line chart for trend/net profit over time
- Always include a chart title

**Positioning:** Charts should fill visual space. Aim for charts to occupy the middle
third of the dashboard height. Don't leave large empty areas.

---

### Section Divider Pattern

Between every logical section on the dashboard:

1. Spacer row: 10px height, base background color, no content
2. Section header row: merged full-width, ALL CAPS, 11pt bold, Text muted,
   slightly darker background (section-bg on dark / #F0F0EE on light)

---

### Column Width Standards

| Column type | Width (px) |
| --- | --- |
| Left/right gutter | 14 |
| Card spacer (between KPI groups) | 12 |
| Label / category | 120–160 |
| Amount / number | 110–130 |
| Status / type | 100–140 |
| Notes / description | 180–240 |
| Date | 100–110 |
| Auto-number (#) | 40–50 |

---

## What Can Be Done via API

### Structure

- Number of tabs/sheets (including hidden helper sheets)
- Row and column counts per sheet
- Hidden vs visible sheets
- Sheet ordering

### Cell Content

- Static text, numbers
- Formulas: VLOOKUP, INDEX/MATCH, SUMIFS, COUNTIFS, IF/IFS, QUERY, ARRAYFORMULA,
  TEXT, SPARKLINE, REPT, IFERROR, EDATE, NPER, etc.
- Cross-sheet references
- Sample/seed data (25–40 rows across 2–3 months)

### Formatting

- Background colors (hex → 0.0–1.0 floats)
- Text colors, bold, italic, font size, font family (Courier New for progress bars)
- Number formats: `$#,##0.00`, `0%`, `0.0%`, date formats, custom patterns
- Cell alignment (LEFT, CENTER, RIGHT; TOP, MIDDLE, BOTTOM)
- Column widths in pixels, row heights in pixels
- Cell merges for title banners and section headers
- Borders (style: SOLID, width: 1=thin, 2=medium, 3=thick; color as RGB)
- Alternating row colors

### Data Validation

- Dropdown lists (ONE_OF_RANGE sourced from hidden _Ref tab)
- Checkboxes
- Number ranges, date validation, text validation
- Strict mode (rejects invalid input) vs warning mode

### Conditional Formatting

- Value-based rules (NUMBER_LESS, NUMBER_GREATER, NUMBER_BETWEEN)
- Text-based rules (TEXT_CONTAINS, TEXT_EQ)
- Custom formula conditions
- Color scales (gradient)
- Priority order (lower index = higher priority)

### Charts

Types: Bar/Column, Line/Area, Pie/Donut (pieHole: 0.4–0.5), Scatter, Combo.

Per chart, specify:

- Type and subtype (stacked, grouped, percent-stacked)
- Title, legend position, backgroundColor
- titleTextStyle and legendTextStyle foregroundColor (critical for dark themes)
- Source data ranges (as GridRange: sheetId + zero-indexed row/col, end-exclusive)
- Colors per series
- Position: anchorCell + offsetXPixels + offsetYPixels + widthPixels + heightPixels

### In-Cell Visualizations

- SPARKLINE formulas (line, bar, column) with custom colors
- REPT-based progress bars (see Progress Bar Pattern above)

---

## What CANNOT Be Done via API

- Images/logos inserted into cells (use `=IMAGE(url)` formula instead)
- Custom fonts beyond Google Sheets defaults (Courier New and Arial are available)
- Pivot tables, slicers, Apps Script / macros
- Cell comments/notes
- Filter views with saved configurations

---

## BUILD_PROMPT.md Required Sections

### 1. Overview

What the spreadsheet does, who it's for, what makes it sellable, and the price point.

### 2. Theme Declaration

State clearly: **Dark Premium** or **Light Elegant**. List the 9 color roles with hex
and RGB float values. If adjusting accent hues, explain why.

### 3. Tab Structure Table

`| sheetId | Name | Visible | Purpose |`

Assign explicit sheetId numbers — required for batchUpdate calls.

### 4. Dashboard Layout (row-by-row) — most important section

Describe every row band with: row range + height, content, formulas, formatting,
and any borders. Be exhaustive. Example:

```text
Row 1 (54px): MERGED A1:L1 — "SMART BUDGET PLANNER" — base-bg, Accent 1 text, 22pt bold
Row 2 (10px): Spacer — base-bg
Row 3 (32px): Section header — MERGED A3:L3 — "BUDGET OVERVIEW" — section-bg, muted, 11pt ALL CAPS
Row 4 (10px): Spacer
Row 5-7: KPI Card 1 — B5:D7
  Row 5 (22px): "NEEDS (50%)" — 8pt muted — thick top border Accent 1, section-bg
  Row 6 (46px): =formula — 24pt bold, Accent 1 color, section-bg
  Row 7 (20px): "of $X budget" — 8pt italic muted, section-bg
Row 8 (18px): Progress bar — =REPT formula — Courier New 8pt
Row 9 (10px): Spacer
```

### 5. Color Palette Table

`| Role | Hex | RGB Float |` — all 9 roles plus any additional semantic colors.

### 6. Hidden Reference Tab (_Ref) — always last sheetId

Column assignments for all dropdown sources. Build this tab first.

### 7. Column Definitions (per data tab)

`| Col | Header | Width (px) | Type | Formula or Dropdown Options |`

Write the actual formula. List dropdown source range from _Ref.

### 8. Cross-Sheet Formula Logic

Which cells reference which sheets, what SUMIFS criteria are, what the selector cell is.

### 9. Sample Data

25–40 rows covering 2–3 time periods. Must populate every chart series, trigger every
conditional formatting rule, and exercise every dropdown option at least once.

### 10. Charts (per chart)

- Type, pieHole if donut
- Source: sheetId + row/col indices (zero-indexed, end-exclusive)
- backgroundColor, titleTextStyle foregroundColor, legendTextStyle foregroundColor
- Series colors from design palette
- Position: anchorCell, widthPixels, heightPixels (min 420×260)

### 11. Conditional Formatting Rules

Range, condition type and value, format result, priority index. Must include:

- Progress bar color rules (under/over budget)
- Status field colors (Paid/Overdue/Pending)
- Positive/negative net value colors

### 12. Data Validation

Cell range (sheetId + indices), type ONE_OF_RANGE with `"='_Ref'!$A$2:$A$13"` format,
strict: true.

### 13. Frozen Rows/Columns per tab

Do not freeze across merged cells.

### 14. Design Implementation Checklist

Before declaring BUILD_PROMPT complete, verify explicitly specified:

- [ ] KPI value font size is 24pt or larger
- [ ] Thick top border (3px SOLID, Accent 1) on every KPI card label row
- [ ] Progress bar row in Courier New for every budget/goal metric
- [ ] Spacer rows (10px) between every dashboard section
- [ ] Left/right gutter columns (14px) on dashboard
- [ ] Card spacer columns (12px) between KPI groups
- [ ] Chart backgroundColor set to base bg color
- [ ] Chart titleTextStyle and legendTextStyle foregroundColor set
- [ ] All charts at least 420×260px
- [ ] Section header rows merged and styled

### 15. Final Requirements Checklist

- [ ] All formulas native Google Sheets (no Apps Script)
- [ ] All cross-sheet formulas wrapped in IFERROR
- [ ] Dashboard driven by a single selector cell
- [ ] Spreadsheet title set
- [ ] Output spreadsheet ID and shareable link when done

---

## Tips for High-Quality Prompts

1. Write actual formulas — not descriptions of what a formula should do
2. Assign sheetIds upfront — prevents confusion in batchUpdate calls
3. Build _Ref first — other tabs reference it; building it last causes errors
4. Wrap all cross-sheet formulas in IFERROR
5. Sample data must cover all features — empty charts kill sellability
6. Name your input cells — e.g., "Dashboard!C4 is the Active Month selector"
7. Progress bars need Courier New font — proportional fonts make blocks uneven
8. Charts need backgroundColor set — always include it in chart spec
9. Dark theme charts need titleTextStyle/legendTextStyle foregroundColor set — otherwise labels invisible
10. Be explicit about border specs — include style, width (1/2/3), and color RGB in updateBorders
