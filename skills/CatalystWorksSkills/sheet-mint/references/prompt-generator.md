# Spreadsheet Prompt Generator — Reference Guide

This guide defines the exact structure for writing a BUILD_PROMPT.md that Claude Code can
execute end-to-end using the GWS CLI to produce a fully functional, sellable Google Sheets
spreadsheet.

---

## How the Build System Works

Two main APIs:

1. **Values API** (`gws sheets spreadsheets values update`) — writes cell data including text,
   numbers, and formulas. Uses A1 notation with sheet names (e.g., `'My Sheet'!A1:C10`).
   Must set `valueInputOption: USER_ENTERED` for formulas to be parsed.

2. **Batch Update API** (`gws sheets spreadsheets batchUpdate`) — handles everything visual
   and structural: cell formatting, merges, charts, data validation dropdowns, conditional
   formatting, frozen rows/columns, column widths, adding/renaming/hiding sheets. Uses numeric
   `sheetId` (not sheet names) and zero-indexed, end-exclusive ranges.

**Build order:**
1. Create spreadsheet with all named sheets
2. Populate reference/lookup data (hidden helper tabs)
3. Write all cell data and formulas
4. Apply formatting (colors, fonts, number formats, column widths)
5. Add data validation (dropdowns)
6. Add conditional formatting
7. Add charts
8. Freeze rows/columns (cannot freeze across merged cells)

---

## What Can Be Customized

### Structure
- Number of tabs/sheets (including hidden helper sheets)
- Row and column counts per sheet
- Hidden vs visible sheets
- Sheet ordering

### Cell Content
- Static text, numbers
- Formulas: VLOOKUP, INDEX/MATCH, SUMIFS, COUNTIFS, IF/IFS, QUERY, ARRAYFORMULA, TEXT,
  SPARKLINE, REPT, IFERROR, EDATE, NPER, etc.
- Cross-sheet references
- Sample/seed data (25–40 rows across 2–3 months so charts aren't empty on first open)

### Formatting
- Background colors (hex → 0.0–1.0 floats: `#264653` → `{red:0.149, green:0.275, blue:0.325}`)
- Text colors, bold, italic, font size
- Number formats: `$#,##0.00`, `0%`, `0.0%`, date formats, custom patterns
- Cell alignment (LEFT, CENTER, RIGHT; TOP, MIDDLE, BOTTOM)
- Column widths in pixels
- Row heights
- Cell merges for title banners and section headers
- Alternating row colors
- Borders (thin/medium/thick)

### Data Validation
- Dropdown lists (ONE_OF_LIST or ONE_OF_RANGE sourced from hidden ref tab)
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
Types: Bar/Column, Line/Area, Pie/Donut (pieHole: 0.4–0.5), Scatter, Combo, Stepped Area.

Per chart, specify:
- Type and subtype (stacked, grouped, percent-stacked)
- Title, legend position
- Source data ranges (as GridRange: sheetId + zero-indexed row/col, end-exclusive)
- Colors per series
- Position: anchorCell + offsetXPixels + offsetYPixels + widthPixels + heightPixels

### In-Cell Visualizations
- SPARKLINE formulas (line, bar, column) with custom colors
- REPT-based progress bars

---

## What CANNOT Be Done via API

- Images/logos inserted into cells (use `=IMAGE(url)` formula instead)
- Custom fonts beyond Google Sheets defaults
- Pivot tables
- Slicers
- Apps Script / macros
- Pivot tables
- Cell comments/notes
- Filter views with saved configurations

---

## BUILD_PROMPT.md Required Sections

### 1. Overview (1 paragraph)
What the spreadsheet does, who it's for, what makes it sellable.

### 2. Tab Structure Table
| sheetId | Name | Visible | Purpose |

Assign explicit sheetId numbers (0, 1, 2, ...) — required for batchUpdate calls.

### 3. Color Palette Table
| Semantic Role | Hex Code | RGB Float (R, G, B) |

Define colors for: header bg, header text, each data category, positive/negative indicators,
alternating rows, borders.

### 4. Hidden Reference Tab (_Ref) — ALWAYS sheetId: last
List every dropdown source range:
- Column A: months list
- Column C: bucket categories
- Column E: category group 1
- Column G: category group 2
- etc.

Build this tab first — it's the source for all dropdowns.

### 5. Column Definitions (per tab)
| Col | Header | Width | Type | Formula / Options |

For formulas, write the actual formula. For dropdowns, list every option or source range.

### 6. Cross-Sheet Formula Logic
Be explicit: which cells reference which other sheets, what SUMIFS criteria are used,
what the "active month" selector cell address is.

### 7. Sample Data
Specify 25–40 rows covering 2–3 time periods. Include enough variety to:
- Populate every chart series
- Trigger every conditional formatting rule
- Exercise every dropdown option at least once

### 8. Charts (per chart)
- Type (pie/donut/bar/column/line)
- Data source (which tab, which row/col ranges)
- Colors per series (tie to palette)
- Position (anchor row, approximate pixel dimensions)
- Legend position

### 9. Conditional Formatting Rules
- Range it applies to
- Condition and threshold
- Visual result (bg color, text color)
- Priority relative to other rules on same range

### 10. Data Validation
- Cell range
- Type (ONE_OF_LIST, ONE_OF_RANGE, checkbox, NUMBER_BETWEEN)
- Source or values list
- Strict or warning

### 11. Frozen Rows/Columns (per tab)
Note: do not freeze across merged cells.

### 12. Final Requirements Checklist
- Formulas must be native Google Sheets (no Apps Script)
- All cross-sheet formulas wrapped in IFERROR
- Dashboard must be driven by a month/period selector cell
- Spreadsheet title
- Expected shareable link output

---

## Tips for High-Quality Prompts

1. **Write actual formulas** — don't say "calculate the total"; write
   `=SUMIFS('Log'!F:F,'Log'!D:D,"Needs",'Log'!G:G,Setup!C5,'Log'!H:H,Setup!C6)`

2. **Assign sheetIds upfront** — prevents confusion in batchUpdate calls

3. **Give exact hex codes** — Claude converts them to 0-1 floats automatically

4. **Build reference tab first** — dashboard formulas that reference it won't error

5. **Wrap all cross-sheet formulas in IFERROR** — prevents broken-looking cells on empty months

6. **Sample data must exercise all features** — empty charts kill the sellability of a product

7. **Name your input cells** — e.g., "Setup!C5 is the Active Month selector"

8. **Keep merged cells and frozen rows compatible** — merging across the freeze boundary breaks freezing

---

## Example BUILD_PROMPT.md Structure

```
Build a [TYPE] in Google Sheets. Sellable digital product. Every formula, chart, and
dropdown must be functional on first open.

## Overview
[1 paragraph]

## Tab Structure
| sheetId | Name | Visible | Purpose |

## Color Palette
| Role | Hex | RGB Float |

## Tab N (Hidden): _Ref
[Range assignments for all dropdown sources]

## Tab 0: Dashboard
### Layout
[Row-by-row description with exact formulas]

## Tab 1: [Data Tab]
### Headers
| Col | Header | Width | Type | Details |
### Sample Data
[Table of 25-40 rows]

## Charts
1. [Type] — [what it shows]
   - Data: sheetId X, rows Y-Z, cols A-B
   - Colors: [series mapping]
   - Position: anchor row N, 400×260px

## Conditional Formatting
1. [Range]: [condition] → [color]

## Data Validation
1. [Range]: dropdown from _Ref!A1:A12, strict

## Frozen Rows
- Dashboard: freeze rows 1-2
- Transactions: freeze row 1

## Requirements
- Output spreadsheet ID and shareable link when done
- Title: "[Product Name]"
```
