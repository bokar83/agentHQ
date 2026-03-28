# Handoff: Etsy Template #5 — All-in-One Budget Dashboard
**Status:** Design spec complete. Implementation plan NOT written. Build NOT executed.
**Next action:** Write the plan, then execute the build via the sheet-mint skill.
**Owner:** Boubacar (bokar83@gmail.com)
**Date created:** 2026-03-27

---

## WHAT YOU ARE BUILDING

A premium Google Sheets digital product to sell on Etsy for $16–$22. It is an **All-in-One Budget + Debt + Savings Dashboard** — 6 financial tools in one workbook, built via the GWS CLI from within Claude Code. The finished product is a Google Sheets link that gets delivered to Etsy buyers after purchase.

---

## WHAT HAS ALREADY BEEN DONE

1. ✅ Template selected from Etsy research list (#5 of 25)
2. ✅ Design decisions locked in:
   - Color theme: **Navy Slate** (`#2C3E6B` navy + green/amber/red accents)
   - Dashboard: **Card-based, YTD full-year view** (all 12 months at a glance, no month selector)
   - Debt method: **Both Snowball + Avalanche** with a toggle dropdown — user chooses
   - Budget structure: **Approach 1** — single BUDGET LOG transaction input tab → 12 hidden monthly summary tabs → YTD dashboard. 8 visible tabs total.
3. ✅ User preference: **Follow recommendations, only ask for input on truly huge directional decisions. Build for the market (what buyers expect) with improvements where they add value.**
4. ✅ Full design spec written and saved:
   - `D:\Ai_Sandbox\agentsHQ\docs\superpowers\specs\2026-03-25-etsy-template-5-allinone-budget-design.md`
5. ✅ Product directory created: `D:\Ai_Sandbox\agentsHQ\zzzArchive\testingSandbox\allinone-budget-dashboard\`
6. ❌ Implementation plan NOT yet written
7. ❌ BUILD_PROMPT.md NOT yet written
8. ❌ GWS CLI build NOT yet executed

---

## WHAT YOU NEED TO DO (IN ORDER)

### STEP 1 — Read the full design spec
Read this file completely before doing anything else:
```
D:\Ai_Sandbox\agentsHQ\docs\superpowers\specs\2026-03-25-etsy-template-5-allinone-budget-design.md
```
It contains every tab, every column, every formula, every color value, every chart spec, and all sample data. It is complete and approved. Do not redesign anything — just build it.

### STEP 2 — Read the sheet-mint skill
Read this file to understand the GWS CLI build system and exact command syntax:
```
D:\Ai_Sandbox\agentsHQ\skills\CatalystWorksSkills\sheet-mint\SKILL.md
```
Pay attention to Phase 3 (Execute the Build). It shows the exact `gws` CLI command patterns.

### STEP 3 — Write BUILD_PROMPT.md
Save to: `D:\Ai_Sandbox\agentsHQ\zzzArchive\testingSandbox\allinone-budget-dashboard\BUILD_PROMPT.md`

This is the comprehensive GWS build prompt following the sheet-mint format. It must include:
- Tab structure table (all 21 sheets with sheetIds)
- Color palette with RGB float values for the API
- Every column on every tab with exact formulas
- Sample data rows (42 rows pre-loaded in BUDGET LOG + sample data in other tabs)
- Chart spec for NET WORTH line chart
- All conditional formatting rules
- All data validation dropdowns
- Frozen rows/columns per tab
- Build order

### STEP 4 — Execute the build (Phase 3 of sheet-mint skill)

Follow these steps exactly in order:

**4a. Create spreadsheet with all 21 sheets:**
```bash
gws sheets spreadsheets create --params '{
  "properties": {"title": "All-in-One Financial Dashboard — 2026"},
  "sheets": [
    {"properties": {"sheetId": 0, "title": "START HERE", "index": 0}},
    {"properties": {"sheetId": 1, "title": "HEALTH SCORE", "index": 1}},
    {"properties": {"sheetId": 2, "title": "BUDGET LOG", "index": 2}},
    {"properties": {"sheetId": 3, "title": "DEBT PAYOFF", "index": 3}},
    {"properties": {"sheetId": 4, "title": "SAVINGS GOALS", "index": 4}},
    {"properties": {"sheetId": 5, "title": "SINKING FUNDS", "index": 5}},
    {"properties": {"sheetId": 6, "title": "NET WORTH", "index": 6}},
    {"properties": {"sheetId": 7, "title": "CASH ENVELOPES", "index": 7}},
    {"properties": {"sheetId": 8,  "title": "JAN", "index": 8,  "hidden": true}},
    {"properties": {"sheetId": 9,  "title": "FEB", "index": 9,  "hidden": true}},
    {"properties": {"sheetId": 10, "title": "MAR", "index": 10, "hidden": true}},
    {"properties": {"sheetId": 11, "title": "APR", "index": 11, "hidden": true}},
    {"properties": {"sheetId": 12, "title": "MAY", "index": 12, "hidden": true}},
    {"properties": {"sheetId": 13, "title": "JUN", "index": 13, "hidden": true}},
    {"properties": {"sheetId": 14, "title": "JUL", "index": 14, "hidden": true}},
    {"properties": {"sheetId": 15, "title": "AUG", "index": 15, "hidden": true}},
    {"properties": {"sheetId": 16, "title": "SEP", "index": 16, "hidden": true}},
    {"properties": {"sheetId": 17, "title": "OCT", "index": 17, "hidden": true}},
    {"properties": {"sheetId": 18, "title": "NOV", "index": 18, "hidden": true}},
    {"properties": {"sheetId": 19, "title": "DEC", "index": 19, "hidden": true}},
    {"properties": {"sheetId": 20, "title": "LOOKUP", "index": 20, "hidden": true}}
  ]
}'
```
Capture `spreadsheetId` from the response. Save it to:
`D:\Ai_Sandbox\agentsHQ\zzzArchive\testingSandbox\allinone-budget-dashboard\SPREADSHEET_ID.txt`

**4b. Build tab by tab in this order:**
1. LOOKUP (reference data — categories, dropdowns)
2. START HERE (welcome/onboarding)
3. BUDGET LOG (headers + input panel + sample data 42 rows)
4. JAN–DEC hidden tabs (SUMPRODUCT formulas pulling from BUDGET LOG)
5. HEALTH SCORE (formulas pulling from JAN–DEC tabs)
6. DEBT PAYOFF (debt table + what-if simulator + sample 3 debts)
7. SAVINGS GOALS (8 goal rows + sample 3 goals)
8. SINKING FUNDS (12 fund rows + sample 5 funds)
9. NET WORTH (asset/liability grid + sample 12-month data)
10. CASH ENVELOPES (10 envelopes + sample 5 envelopes)

**4c. Apply formatting — one batchUpdate per tab:**
- Navy header rows: bg `{red:0.173,green:0.243,blue:0.420}`, white text, 14pt bold
- Card background rows: bg `{red:0.933,green:0.945,blue:0.973}`
- Input cells: bg `{red:1.0,green:0.976,blue:0.769}` (yellow)
- Body text: 10pt, `{red:0.173,green:0.243,blue:0.314}`
- Progress bar columns: Courier New font for alignment

**4d. Add data validation:**
- BUDGET LOG C7:C200 — category dropdown from `'LOOKUP'!A2:A21`, strict
- BUDGET LOG D7:D200 — `["Income","Expense"]` strict
- DEBT PAYOFF B2 — `["Snowball","Avalanche"]` strict

**4e. Add conditional formatting:**
- HEALTH SCORE score cell: ≥80 green, 60–79 amber, <60 red
- SAVINGS GOALS col E: ≥100% green bg, ≥50% amber bg, <50% red bg
- SINKING FUNDS col F: same rules
- CASH ENVELOPES col D: <0 full row red bg; col E ≥100% red cell; col E ≥90% amber cell
- NET WORTH row 28 (MoM change): >0 green bg, <0 red bg
- DEBT PAYOFF col I (total interest): color scale green→red

**4f. Add NET WORTH line chart:**
- Type: LINE chart (use AREA style for fill under line)
- Data: Row 27 cols B–M (net worth values), Row 5 cols B–M (month headers)
- Series color: `#2C3E6B`
- Position: anchored at A31, 600×300px
- Title: "Net Worth — 2026"

**4g. Freeze rows:**
- All tabs: freeze row 1 (banner)
- BUDGET LOG: freeze rows 1–6
- All tabs with data tables: freeze the header row
- NET WORTH: freeze col A + row 5

**4h. Set column widths (pixels):**
- Name/label columns: 180
- Currency columns: 120
- Date columns: 110
- Progress bar columns: 140
- Status columns: 160
- NET WORTH month columns (B–M): 80 each

### STEP 5 — Quality check before declaring done
Run through this checklist:
- [ ] All 8 visible tabs present, 12 hidden + LOOKUP hidden
- [ ] BUDGET LOG sample data (42 rows) visible and formatted
- [ ] JAN/FEB/MAR hidden tabs showing correct SUMPRODUCT totals
- [ ] HEALTH SCORE shows an overall score (not blank/error)
- [ ] DEBT PAYOFF strategy toggle changes payoff order correctly
- [ ] SAVINGS GOALS progress bars render with █ characters
- [ ] SINKING FUNDS monthly contribution calculator working
- [ ] NET WORTH chart renders with data (not blank)
- [ ] CASH ENVELOPES shows correct remaining amounts
- [ ] No `#REF!`, `#NAME?`, or `#ERROR!` cells visible
- [ ] Dropdowns work in BUDGET LOG col C and D
- [ ] Conditional formatting triggering (March dining out should be amber/red)

### STEP 6 — Output result
```
✅ BUILD COMPLETE

Product: All-in-One Financial Dashboard — 2026
Spreadsheet ID: [ID]
Google Sheets link: https://docs.google.com/spreadsheets/d/[ID]/edit

To make it a sellable template:
1. Open the link above
2. File → Share → "Anyone with the link" → Viewer
3. Make a copy, then share the COPY link as the product
```

---

## KEY DESIGN DECISIONS (DO NOT CHANGE THESE)

| Decision | Value | Reason |
|----------|-------|--------|
| Color theme | Navy Slate — #2C3E6B primary | Broadest demographic appeal |
| Dashboard view | Full YTD (all 12 months) | User prefers year-at-a-glance over month selector |
| Debt method | Both snowball + avalanche with B2 toggle | User wants buyer to choose |
| Budget architecture | Single BUDGET LOG → 12 hidden summaries → dashboard | Approach 1, cleanest UX |
| Visible tab count | 8 tabs | Premium but not overwhelming |
| Progress bars | REPT("█",...) & REPT("░",...) | Native Sheets, no images needed |
| Input cells | Yellow background #FFF9C4 | Makes it obvious where to type |
| Sample data | 42 rows pre-loaded (Jan–Mar 2026) | Sheet works out of box on first open |
| Price point | $16–22 on Etsy | Research-backed sweet spot |

---

## CRITICAL FORMULAS REFERENCE

**BUDGET LOG col F (Month name):**
`=IF(A7="","",TEXT(A7,"MMM"))`

**BUDGET LOG col G (Month number):**
`=IF(A7="","",MONTH(A7))`

**Monthly summary tabs (example for JAN, month# = 1):**
- Income: `=SUMPRODUCT(('BUDGET LOG'!G$7:G$200=1)*('BUDGET LOG'!D$7:D$200="Income")*('BUDGET LOG'!E$7:E$200))`
- Expenses: `=SUMPRODUCT(('BUDGET LOG'!G$7:G$200=1)*('BUDGET LOG'!D$7:D$200="Expense")*('BUDGET LOG'!E$7:E$200))`
- Change month# 1→2 for FEB, 1→3 for MAR, etc.

**HEALTH SCORE — YTD income:**
`=SUM(JAN!B2,FEB!B2,MAR!B2,APR!B2,MAY!B2,JUN!B2,JUL!B2,AUG!B2,SEP!B2,OCT!B2,NOV!B2,DEC!B2)`

**HEALTH SCORE — YTD expenses:**
`=SUM(JAN!B3,FEB!B3,MAR!B3,APR!B3,MAY!B3,JUN!B3,JUL!B3,AUG!B3,SEP!B3,OCT!B3,NOV!B3,DEC!B3)`

**Budget Health Score (0–100):**
`=IF(ratio<=0.85,100,IF(ratio<=0.95,85,IF(ratio<=1.0,70,IF(ratio<=1.10,45,10))))`
where ratio = YTD expenses / YTD income

**DEBT PAYOFF col E (Payoff Order):**
`=IF(B7="","",IF($B$2="Snowball",RANK(B7,B$7:B$16,1),RANK(C7,C$7:C$16,0)))`

**DEBT PAYOFF col G (Months to Payoff):**
`=IF(B7="","",IFERROR(NPER(C7/12,-F7,B7),0))`

**SAVINGS GOALS col F (Monthly needed):**
`=IF(OR(B5="",D5=""),"",IFERROR((B5-C5)/MAX(1,DATEDIF(TODAY(),D5,"M")),0))`

**Progress bar (10-block):**
`=IF(B5="","",REPT("█",MIN(10,ROUND(E5*10,0)))&REPT("░",MAX(0,10-MIN(10,ROUND(E5*10,0)))))`

---

## COLOR PALETTE (API-ready RGB floats)

| Name | Hex | Red | Green | Blue |
|------|-----|-----|-------|------|
| Navy primary | #2C3E6B | 0.173 | 0.243 | 0.420 |
| Success green | #27AE60 | 0.153 | 0.682 | 0.376 |
| Warning amber | #E67E22 | 0.902 | 0.494 | 0.133 |
| Danger red | #E74C3C | 0.906 | 0.298 | 0.235 |
| Light bg | #F7F8FA | 0.969 | 0.973 | 0.980 |
| Card bg | #EEF1F8 | 0.933 | 0.945 | 0.973 |
| Input yellow | #FFF9C4 | 1.000 | 0.976 | 0.769 |
| Light green bg | #D5F5E3 | 0.835 | 0.961 | 0.890 |
| Light amber bg | #FAD7A0 | 0.980 | 0.843 | 0.627 |
| Light red bg | #FADBD8 | 0.980 | 0.859 | 0.847 |

---

## SAMPLE DATA REFERENCE

### BUDGET LOG (42 rows, pre-load these)

**January 2026 (15 rows):**
2026-01-01 | Paycheck | Salary | Income | 3500
2026-01-03 | Rent | Housing | Expense | 1200
2026-01-05 | Groceries - Walmart | Groceries | Expense | 187.43
2026-01-08 | Electric Bill | Utilities | Expense | 94.20
2026-01-10 | Netflix | Subscriptions | Expense | 15.99
2026-01-10 | Spotify | Subscriptions | Expense | 10.99
2026-01-12 | Gas - Shell | Transportation | Expense | 52.30
2026-01-15 | Paycheck | Salary | Income | 3500
2026-01-18 | Dinner out - Olive Garden | Dining Out | Expense | 67.45
2026-01-20 | Groceries - Kroger | Groceries | Expense | 143.22
2026-01-22 | Internet Bill | Utilities | Expense | 59.99
2026-01-25 | Amazon purchase | Shopping | Expense | 34.99
2026-01-26 | Coffee shop | Dining Out | Expense | 23.40
2026-01-28 | Car Insurance | Auto | Expense | 120.00
2026-01-30 | Gym membership | Health & Fitness | Expense | 35.00

**February 2026 (14 rows):**
2026-02-01 | Paycheck | Salary | Income | 3500
2026-02-03 | Rent | Housing | Expense | 1200
2026-02-06 | Groceries - Walmart | Groceries | Expense | 204.17
2026-02-08 | Electric Bill | Utilities | Expense | 87.50
2026-02-10 | Netflix | Subscriptions | Expense | 15.99
2026-02-10 | Spotify | Subscriptions | Expense | 10.99
2026-02-14 | Valentine's Dinner | Dining Out | Expense | 112.80
2026-02-15 | Paycheck | Salary | Income | 3500
2026-02-17 | Gas - Shell | Transportation | Expense | 48.60
2026-02-20 | Groceries - Target | Groceries | Expense | 167.34
2026-02-22 | Internet Bill | Utilities | Expense | 59.99
2026-02-24 | New shoes | Clothing | Expense | 79.99
2026-02-26 | Coffee shop | Dining Out | Expense | 31.20
2026-02-28 | Gym membership | Health & Fitness | Expense | 35.00

**March 2026 (13 rows — Dining Out over budget, triggers amber/red):**
2026-03-01 | Paycheck | Salary | Income | 3500
2026-03-03 | Rent | Housing | Expense | 1200
2026-03-05 | Groceries - Walmart | Groceries | Expense | 221.88
2026-03-07 | Electric Bill | Utilities | Expense | 101.40
2026-03-10 | Netflix | Subscriptions | Expense | 15.99
2026-03-10 | Spotify | Subscriptions | Expense | 10.99
2026-03-12 | Gas - Shell | Transportation | Expense | 61.40
2026-03-15 | Paycheck | Salary | Income | 3500
2026-03-16 | Birthday dinner - group | Dining Out | Expense | 89.50
2026-03-19 | Lunch - work meeting | Dining Out | Expense | 43.20
2026-03-22 | Groceries - Kroger | Groceries | Expense | 188.65
2026-03-25 | Coffee + snacks | Dining Out | Expense | 28.75
2026-03-28 | Internet Bill | Utilities | Expense | 59.99

### DEBT PAYOFF (3 debts pre-loaded in rows 7–9)
| Name | Balance | Rate | Min Payment |
|------|---------|------|-------------|
| Credit Card - Chase | 4200 | 0.22 | 105 |
| Car Loan | 8500 | 0.065 | 245 |
| Student Loan | 18000 | 0.045 | 195 |
Strategy default: "Snowball" | Extra payment: $0

### SAVINGS GOALS (3 goals pre-loaded in rows 5–7)
| Goal | Target | Current | Target Date |
|------|--------|---------|-------------|
| Emergency Fund | 10000 | 3400 | 2026-12-31 |
| Vacation Fund | 3500 | 1200 | 2026-07-01 |
| Down Payment | 25000 | 8750 | 2028-01-01 |

### SINKING FUNDS (5 funds pre-loaded in rows 5–9)
| Fund | Target | Current | Target Date |
|------|--------|---------|-------------|
| Car Insurance (Semi-Annual) | 720 | 360 | 2026-07-01 |
| Christmas Gifts | 1200 | 300 | 2026-12-01 |
| Home Repairs | 2000 | 650 | 2026-12-31 |
| Medical Deductible | 1500 | 500 | 2026-12-31 |
| Gifts & Birthdays | 600 | 150 | 2026-12-31 |

### NET WORTH (12 months of upward trend)
Row 5 headers: Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec

Assets (sample values — trending up):
- Checking Account: 4200 | 4100 | 4500 | 4300 | 4600 | 4800 | 5000 | 4900 | 5200 | 5400 | 5600 | 5800
- Savings Account: 3400 | 3600 | 3850 | 4100 | 4350 | 4600 | 4850 | 5100 | 5350 | 5600 | 5850 | 6100
- Investment/Brokerage: 12000 | 12400 | 11800 | 12600 | 13000 | 13400 | 13800 | 14200 | 14600 | 15000 | 15400 | 15800
- Retirement 401k: 18500 | 19000 | 18200 | 19500 | 20000 | 20500 | 21000 | 21500 | 22000 | 22500 | 23000 | 23500
- Vehicle Value: 12000 | 11800 | 11600 | 11400 | 11200 | 11000 | 10800 | 10600 | 10400 | 10200 | 10000 | 9800
- Other Assets (rows 8–11): 0 for all months

Liabilities (sample values — trending down):
- Credit Card Balances: 4200 | 4100 | 3950 | 3800 | 3650 | 3500 | 3350 | 3200 | 3050 | 2900 | 2750 | 2600
- Car Loan: 8500 | 8300 | 8100 | 7900 | 7700 | 7500 | 7300 | 7100 | 6900 | 6700 | 6500 | 6300
- Student Loan: 18000 | 17850 | 17700 | 17550 | 17400 | 17250 | 17100 | 16950 | 16800 | 16650 | 16500 | 16350
- Other liabilities: 0 for all months

Net Worth Jan = (4200+3400+12000+18500+12000) - (4200+8500+18000) = 50100 - 30700 = **$19,400**
Net Worth Dec = (5800+6100+15800+23500+9800) - (2600+6300+16350) = 61000 - 25250 = **$35,750**

### CASH ENVELOPES (5 envelopes pre-loaded in rows 5–9)
| Envelope | Budget | Spent |
|----------|--------|-------|
| Groceries | 500 | 324.65 |
| Dining Out | 200 | 190.85 |
| Entertainment | 150 | 47.00 |
| Gas / Transportation | 180 | 92.30 |
| Personal Care | 100 | 38.50 |

---

## LOOKUP TAB DATA (write to LOOKUP!A:C)

**Column A — Categories (A1 header: "CATEGORY", A2:A21 values):**
Housing, Utilities, Groceries, Dining Out, Transportation, Auto, Health & Fitness, Subscriptions, Shopping, Entertainment, Personal Care, Clothing, Education, Gifts & Donations, Travel, Insurance, Savings Transfer, Investments, Other Expense, Salary

**Column B — Budget Bucket (B1 header: "BUCKET", B2:B21):**
Needs, Needs, Needs, Wants, Needs, Needs, Wants, Wants, Wants, Wants, Wants, Wants, Wants, Wants, Wants, Needs, Savings, Savings, Needs, Income

**Column C — Type mapping (C1: "DEFAULT TYPE", C2:C21):**
Expense (×18), Expense, Income (for Salary row)

---

## ETSY LISTING (ready to use)

**Title:** `Budget Spreadsheet Google Sheets | All-in-One Budget Planner Debt Tracker Savings Dashboard Net Worth Template 2026`

**Price:** $17 (hits the $17 psychological sweet spot — research shows $11, $17, $29, $37 outperform round numbers on Etsy)

**13 Tags:** budget spreadsheet, google sheets budget, debt payoff tracker, savings goal tracker, net worth tracker, sinking funds spreadsheet, cash envelope system, budget planner 2026, debt snowball spreadsheet, financial dashboard, budget template google sheets, personal finance spreadsheet, all in one budget planner

---

## LESSONS LEARNED IN THIS SESSION

1. **Navy Slate is the right default** for financial templates targeting couples/families — avoids the pink/feminine bias of pastel themes and the niche narrowing of dark mode
2. **YTD dashboard > month selector** for buyers — they want to see the full picture on first open, not hunt for a selector
3. **Both debt methods, not one** — Snowball vs Avalanche is a personal finance religion debate; give buyers the toggle and let them choose. Increases perceived value.
4. **Approach 1 (hidden monthly tabs)** is the cleanest architecture — 8 visible tabs feels premium, the 12 hidden summary tabs do the work invisibly
5. **User preference: move fast, don't ask** — Boubacar trusts the build direction. Only surface blockers that would change the fundamental product.
6. **Sheet-mint skill is the right tool** — it has the exact GWS CLI command patterns. Always read `SKILL.md` before building.
7. **Build order matters** — write LOOKUP first, then data tabs, then dashboard tabs (so cross-sheet references resolve correctly)
8. **Progress bars with REPT** — `REPT("█",n)&REPT("░",10-n)` is the native Sheets progress bar. Use Courier New font on that column for alignment.
9. **Yellow input cells** (#FFF9C4) are essential UX — they make it immediately obvious where buyers should type without reading instructions

---

## FILE LOCATIONS SUMMARY

| File | Path |
|------|------|
| Design spec (READ FIRST) | `D:\Ai_Sandbox\agentsHQ\docs\superpowers\specs\2026-03-25-etsy-template-5-allinone-budget-design.md` |
| Sheet-mint skill | `D:\Ai_Sandbox\agentsHQ\skills\CatalystWorksSkills\sheet-mint\SKILL.md` |
| Product directory | `D:\Ai_Sandbox\agentsHQ\zzzArchive\testingSandbox\allinone-budget-dashboard\` |
| BUILD_PROMPT.md (create here) | `D:\Ai_Sandbox\agentsHQ\zzzArchive\testingSandbox\allinone-budget-dashboard\BUILD_PROMPT.md` |
| Spreadsheet ID (save here) | `D:\Ai_Sandbox\agentsHQ\zzzArchive\testingSandbox\allinone-budget-dashboard\SPREADSHEET_ID.txt` |
| This handoff doc | `D:\Ai_Sandbox\agentsHQ\docs\handoff\2026-03-27-etsy-template-5-handoff.md` |

---

## HOW TO START THE NEW CHAT

Upload this file and say:
> "Continue building Etsy Template #5 — the All-in-One Budget Dashboard. Read the handoff doc and execute to completion."

Claude should then:
1. Read the design spec
2. Read the sheet-mint skill
3. Write BUILD_PROMPT.md
4. Execute Phase 3 of the sheet-mint skill (build via GWS CLI)
5. Output the Google Sheets link

No brainstorming needed. No design decisions needed. Just build it.
