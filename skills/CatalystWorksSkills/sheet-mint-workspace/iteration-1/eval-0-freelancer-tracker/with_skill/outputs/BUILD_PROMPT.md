# BUILD_PROMPT.md: Freelancer Finance Hub

Build a **Freelancer Finance Hub** in Google Sheets. This is a sellable digital product
targeting freelancers and independent contractors. Every formula, chart, and dropdown must
be fully functional on first open. No Apps Script. Price point: $15 on Etsy.

---

## Overview

The Freelancer Finance Hub is a professional income, expense, and invoice tracking system
for self-employed individuals. It includes a live Dashboard with KPI cards and charts, a
monthly Profit & Loss statement, an Invoice Log to track client billing and payment status,
a Transactions log for categorized income/expense entries, and a hidden reference tab for
dropdowns. The dark navy and gold color scheme makes it look premium and photogenic for
Etsy product listings. A differentiating feature is the **Year-at-a-Glance** tab that shows
a 12-month sparkline summary: not commonly seen in competing templates.

---

## Tab Structure

| sheetId | Name | Visible | Purpose |
|---|---|---|---|
| 0 | Dashboard | Yes | KPI cards, monthly summary, charts, month selector |
| 1 | Transactions | Yes | Income & expense log with categories and dates |
| 2 | Invoice Log | Yes | Client invoices with status, amounts, due dates |
| 3 | Monthly P&L | Yes | Auto-calculated profit & loss by month |
| 4 | Year Overview | Yes | 12-month sparkline summary (differentiating feature) |
| 5 | _Ref | No (hidden) | Dropdown source data for all validation |

---

## Color Palette

| Semantic Role | Hex Code | RGB Float (R, G, B) |
|---|---|---|
| Dark Navy (primary bg) | #0D1B2A | {red: 0.051, green: 0.106, blue: 0.165} |
| Mid Navy (section bg) | #1B2A3B | {red: 0.106, green: 0.165, blue: 0.231} |
| Gold (accent/header text) | #C9A84C | {red: 0.788, green: 0.659, blue: 0.298} |
| Light Gold (subtle accent) | #E8D5A3 | {red: 0.910, green: 0.835, blue: 0.639} |
| White (body text) | #FFFFFF | {red: 1.0, green: 1.0, blue: 1.0} |
| Income Green | #2ECC71 | {red: 0.180, green: 0.800, blue: 0.443} |
| Expense Red | #E74C3C | {red: 0.906, green: 0.298, blue: 0.235} |
| Paid Green (invoice) | #27AE60 | {red: 0.153, green: 0.682, blue: 0.376} |
| Overdue Red (invoice) | #C0392B | {red: 0.753, green: 0.224, blue: 0.169} |
| Pending Amber (invoice) | #F39C12 | {red: 0.953, green: 0.612, blue: 0.071} |
| Alt Row Navy | #162233 | {red: 0.086, green: 0.133, blue: 0.200} |
| Border Gold | #8B6914 | {red: 0.545, green: 0.412, blue: 0.078} |

---

## Tab 5 (Hidden): _Ref

Build this tab FIRST. All dropdowns source from here.

| Column | Range | Contents |
|---|---|---|
| A | A1:A13 | Months list: header "MONTHS" + Jan-Dec |
| C | C1:C3 | Transaction types: header "TYPE" + Income, Expense |
| E | E1:E11 | Income categories: header "INCOME_CAT" + Consulting, Design, Writing, Development, Photography, Coaching, Speaking, Retainer, Other Income |
| G | G1:G13 | Expense categories: header "EXPENSE_CAT" + Software, Hardware, Marketing, Office Supplies, Travel, Meals, Professional Fees, Insurance, Utilities, Education, Subscriptions, Other Expense |
| I | I1:I5 | Invoice status: header "STATUS" + Draft, Sent, Paid, Overdue, Cancelled |
| K | K1:K7 | Payment method: header "PAYMENT" + Bank Transfer, PayPal, Stripe, Wise, Cash, Check |

**Exact values to write:**

_Ref!A1:A13:
MONTHS, January, February, March, April, May, June, July, August, September, October, November, December

_Ref!C1:C3:
TYPE, Income, Expense

_Ref!E1:E11:
INCOME_CAT, Consulting, Design, Writing, Development, Photography, Coaching, Speaking, Retainer, Other Income

_Ref!G1:G13:
EXPENSE_CAT, Software, Hardware, Marketing, Office Supplies, Travel, Meals, Professional Fees, Insurance, Utilities, Education, Subscriptions, Other Expense

_Ref!I1:I5:
STATUS, Draft, Sent, Paid, Overdue, Cancelled

_Ref!K1:K7:
PAYMENT, Bank Transfer, PayPal, Stripe, Wise, Cash, Check

---

## Tab 0: Dashboard

### Layout Description

**Row 1:** Merged A1:L1: Title banner: "FREELANCER FINANCE HUB": Gold text on Dark Navy bg, bold, 20pt, centered

**Row 2:** Merged A2:L2: Subtitle: "Financial Dashboard": Light Gold text on Mid Navy, 11pt italic, centered

**Row 3:** Empty spacer row (height: 8px)

**Row 4:** Month selector label in B4: "Active Month:": Gold, bold, right-aligned
**Cell C4:** Month selector dropdown: value "March" (default). This is the master control cell. All dashboard formulas reference Dashboard!C4.
Column widths: A=20, B=130, C=140, D=20, E=130, F=140, G=20, H=130, I=140, J=20, K=130, L=140

**Row 5:** Spacer

**Rows 6-8:** KPI Cards: 4 cards across columns B-C, D-E, F-G, H-I

KPI Card 1: B6:C8: "TOTAL INCOME"
- B6: "TOTAL INCOME": Gold, bold, 9pt, Mid Navy bg
- B7: Formula: `=IFERROR(SUMIFS(Transactions!E:E,Transactions!C:C,"Income",Transactions!B:B,Dashboard!C4),"-")`
- B8: "This Month": Light Gold, 8pt

KPI Card 2: D6:E8: "TOTAL EXPENSES"
- D6: "TOTAL EXPENSES": Gold, bold, 9pt
- D7: Formula: `=IFERROR(SUMIFS(Transactions!E:E,Transactions!C:C,"Expense",Transactions!B:B,Dashboard!C4),"-")`
- D8: "This Month"

KPI Card 3: F6:G8: "NET PROFIT"
- F6: "NET PROFIT": Gold, bold, 9pt
- F7: Formula: `=IFERROR(B7-D7,"-")`
- F8: "This Month"

KPI Card 4: H6:I8: "OUTSTANDING INVOICES"
- H6: "OUTSTANDING INVOICES": Gold, bold, 9pt
- H7: Formula: `=IFERROR(SUMIFS('Invoice Log'!E:E,'Invoice Log'!G:G,"Sent")+SUMIFS('Invoice Log'!E:E,'Invoice Log'!G:G,"Overdue"),"-")`
- H8: "Unpaid Total"

**Rows 9 spacer**

**Rows 10-20:** Chart zone: left side (columns B:G) holds Income vs Expenses bar chart
**Rows 10-20:** Right side (columns H:L) holds Expense breakdown pie chart

**Rows 22-23:** Section header: "TOP INCOME CATEGORIES THIS MONTH": Gold, bold, Mid Navy bg

**Rows 24-28:** Top 3 income categories with SUMIFS formulas
- A24: Category label (from formula)
- B24: `=IFERROR(INDEX(Transactions!D:D,MATCH(LARGE(IF(Transactions!C:C="Income",IF(Transactions!B:B=Dashboard!C4,Transactions!E:E)),1),IF(Transactions!C:C="Income",IF(Transactions!B:B=Dashboard!C4,Transactions!E:E)),0)),"-")` (array formula)
- C24: Amount for top category

**Rows 30-31:** Section header: "RECENT INVOICES": Gold, bold

**Rows 32-36:** Last 5 invoices via QUERY:
- B32: `=IFERROR(QUERY('Invoice Log'!A:G,"SELECT A,B,C,E,G ORDER BY A DESC LIMIT 5 LABEL A 'Date', B 'Client', C 'Description', E 'Amount', G 'Status'",0),"No invoices yet")`

---

## Tab 1: Transactions

### Headers (Row 1): Dark Navy bg, Gold text, bold, frozen

| Col | Header | Width (px) | Type | Details |
|---|---|---|---|---|
| A | # | 45 | Auto | `=IF(B2="","",ROW()-1)` filled down |
| B | Month | 110 | Dropdown | Source: _Ref!A2:A13, strict |
| C | Type | 90 | Dropdown | Source: _Ref!C2:C3, strict |
| D | Category | 150 | Dropdown | Source: _Ref!E2:E11 (if Income) or _Ref!G2:G13 (if Expense): use single combined dropdown from _Ref!E2:G13 for simplicity |
| E | Amount | 110 | Currency | `$#,##0.00` format |
| F | Date | 100 | Date | `MM/DD/YYYY` format |
| G | Client / Vendor | 160 | Text | Free text |
| H | Notes | 200 | Text | Free text |
| I | Payment Method | 130 | Dropdown | Source: _Ref!K2:K7, strict |

Column A formula for rows 2-200: `=IF(B2="","",ROW()-1)`: auto-numbers rows

### Sample Data (35 rows: Jan, Feb, March)

| B (Month) | C (Type) | D (Category) | E (Amount) | F (Date) | G (Client/Vendor) | H (Notes) | I (Payment) |
|---|---|---|---|---|---|---|---|
| January | Income | Consulting | 3500.00 | 01/05/2026 | Acme Corp | Brand strategy | Bank Transfer |
| January | Income | Design | 1200.00 | 01/10/2026 | Startup XYZ | Logo package | PayPal |
| January | Income | Development | 2800.00 | 01/15/2026 | TechFlow | Dashboard build | Stripe |
| January | Expense | Software | 49.00 | 01/02/2026 | Adobe Inc | Creative Cloud | Stripe |
| January | Expense | Software | 29.00 | 01/02/2026 | Notion | Team plan | Stripe |
| January | Expense | Marketing | 150.00 | 01/08/2026 | Meta Ads | Social promotion | Stripe |
| January | Expense | Professional Fees | 200.00 | 01/20/2026 | Accountant | Monthly bookkeeping | Bank Transfer |
| January | Expense | Travel | 85.00 | 01/18/2026 | Uber | Client meetings | Cash |
| January | Expense | Meals | 62.00 | 01/22/2026 | Restaurant | Client lunch | Cash |
| January | Income | Retainer | 1500.00 | 01/28/2026 | GlobalBrand | Monthly retainer | Bank Transfer |
| February | Income | Consulting | 4200.00 | 02/03/2026 | Nexus Ltd | Strategy workshop | Bank Transfer |
| February | Income | Writing | 850.00 | 02/07/2026 | ContentHub | Blog series x5 | PayPal |
| February | Income | Design | 1600.00 | 02/12/2026 | Startup XYZ | Marketing collateral | PayPal |
| February | Income | Coaching | 900.00 | 02/19/2026 | IndieFounder | Business coaching | Stripe |
| February | Income | Retainer | 1500.00 | 02/28/2026 | GlobalBrand | Monthly retainer | Bank Transfer |
| February | Expense | Software | 49.00 | 02/02/2026 | Adobe Inc | Creative Cloud | Stripe |
| February | Expense | Software | 15.00 | 02/02/2026 | Grammarly | Annual plan / 12 | Stripe |
| February | Expense | Education | 299.00 | 02/10/2026 | Udemy | UX Design course | Stripe |
| February | Expense | Insurance | 120.00 | 02/15/2026 | Hiscox | Professional liability | Bank Transfer |
| February | Expense | Office Supplies | 45.00 | 02/20/2026 | Amazon | Desk supplies | Stripe |
| February | Expense | Meals | 38.00 | 02/25/2026 | Coffee shop | Work session | Cash |
| March | Income | Consulting | 5000.00 | 03/01/2026 | Enterprise Co | Q1 strategy | Bank Transfer |
| March | Income | Development | 3200.00 | 03/05/2026 | TechFlow | Feature build | Stripe |
| March | Income | Design | 950.00 | 03/10/2026 | LocalBiz | Website refresh | PayPal |
| March | Income | Photography | 600.00 | 03/14/2026 | EventCo | Product shoot | Cash |
| March | Income | Retainer | 1500.00 | 03/28/2026 | GlobalBrand | Monthly retainer | Bank Transfer |
| March | Income | Speaking | 1200.00 | 03/22/2026 | TechConf | Conference talk | Bank Transfer |
| March | Expense | Software | 49.00 | 03/02/2026 | Adobe Inc | Creative Cloud | Stripe |
| March | Expense | Marketing | 250.00 | 03/05/2026 | Google Ads | Search campaign | Stripe |
| March | Expense | Travel | 320.00 | 03/20/2026 | Delta Airlines | Client site visit | Stripe |
| March | Expense | Meals | 95.00 | 03/21/2026 | Restaurant | Client dinner | Cash |
| March | Expense | Professional Fees | 200.00 | 03/25/2026 | Accountant | Monthly bookkeeping | Bank Transfer |
| March | Expense | Hardware | 189.00 | 03/15/2026 | Amazon | USB-C hub | Stripe |
| March | Expense | Subscriptions | 29.00 | 03/02/2026 | Slack | Pro plan | Stripe |
| March | Expense | Utilities | 85.00 | 03/10/2026 | Comcast | Internet bill | Bank Transfer |

---

## Tab 2: Invoice Log

### Headers (Row 1): Dark Navy bg, Gold text, bold, frozen

| Col | Header | Width (px) | Type | Details |
|---|---|---|---|---|
| A | Invoice # | 100 | Text | e.g. INV-2026-001 |
| B | Client | 160 | Text | Client name |
| C | Description | 220 | Text | Service description |
| D | Issue Date | 110 | Date | MM/DD/YYYY |
| E | Amount | 110 | Currency | $#,##0.00 |
| F | Due Date | 110 | Date | MM/DD/YYYY |
| G | Status | 100 | Dropdown | Source: _Ref!I2:I5, strict |
| H | Paid Date | 110 | Date | MM/DD/YYYY: leave blank until paid |
| I | Notes | 200 | Text | Free text |

### Sample Data (15 invoices)

| A | B | C | D | E | F | G | H | I |
|---|---|---|---|---|---|---|---|---|
| INV-2026-001 | Acme Corp | Brand strategy consulting | 01/05/2026 | 3500.00 | 01/20/2026 | Paid | 01/18/2026 | Early payment |
| INV-2026-002 | Startup XYZ | Logo design package | 01/10/2026 | 1200.00 | 01/25/2026 | Paid | 01/24/2026 | |
| INV-2026-003 | TechFlow | Dashboard development | 01/15/2026 | 2800.00 | 01/30/2026 | Paid | 01/29/2026 | |
| INV-2026-004 | GlobalBrand | January retainer | 01/28/2026 | 1500.00 | 02/05/2026 | Paid | 02/03/2026 | |
| INV-2026-005 | Nexus Ltd | Strategy workshop | 02/03/2026 | 4200.00 | 02/18/2026 | Paid | 02/17/2026 | |
| INV-2026-006 | ContentHub | Blog series x5 | 02/07/2026 | 850.00 | 02/22/2026 | Paid | 02/20/2026 | |
| INV-2026-007 | Startup XYZ | Marketing collateral | 02/12/2026 | 1600.00 | 02/27/2026 | Paid | 02/25/2026 | |
| INV-2026-008 | IndieFounder | Business coaching x3 | 02/19/2026 | 900.00 | 03/05/2026 | Paid | 03/04/2026 | |
| INV-2026-009 | GlobalBrand | February retainer | 02/28/2026 | 1500.00 | 03/07/2026 | Paid | 03/06/2026 | |
| INV-2026-010 | Enterprise Co | Q1 strategy | 03/01/2026 | 5000.00 | 03/16/2026 | Paid | 03/14/2026 | Large project |
| INV-2026-011 | TechFlow | Feature build Sprint 1 | 03/05/2026 | 3200.00 | 03/20/2026 | Sent | | Net 15 |
| INV-2026-012 | LocalBiz | Website refresh | 03/10/2026 | 950.00 | 03/25/2026 | Overdue | | Follow up sent |
| INV-2026-013 | EventCo | Product photography | 03/14/2026 | 600.00 | 03/29/2026 | Sent | | |
| INV-2026-014 | TechConf | Speaking engagement fee | 03/22/2026 | 1200.00 | 04/06/2026 | Sent | | |
| INV-2026-015 | GlobalBrand | March retainer | 03/28/2026 | 1500.00 | 04/12/2026 | Draft | | |

---

## Tab 3: Monthly P&L

### Layout

Row 1: Merged A1:G1: Title "MONTHLY PROFIT & LOSS": Gold on Dark Navy, bold, 16pt

Row 2: Headers: Mid Navy bg, Gold text, bold
Cols: A=Month | B=Total Income | C=Total Expenses | D=Net Profit | E=Profit Margin | F=Income YTD | G=Expenses YTD

Column widths: A=130, B=140, C=140, D=140, E=120, F=140, G=140

Rows 3-14: One row per month (January through December)

Row 3 (January):
- A3: "January"
- B3: `=IFERROR(SUMIFS(Transactions!E:E,Transactions!C:C,"Income",Transactions!B:B,A3),0)`
- C3: `=IFERROR(SUMIFS(Transactions!E:E,Transactions!C:C,"Expense",Transactions!B:B,A3),0)`
- D3: `=B3-C3`
- E3: `=IFERROR(D3/B3,0)`: format as 0.0%
- F3: `=B3` (YTD starts at Jan)
- G3: `=C3`

Row 4 (February):
- A4: "February"
- B4: `=IFERROR(SUMIFS(Transactions!E:E,Transactions!C:C,"Income",Transactions!B:B,A4),0)`
- C4: `=IFERROR(SUMIFS(Transactions!E:E,Transactions!C:C,"Expense",Transactions!B:B,A4),0)`
- D4: `=B4-C4`
- E4: `=IFERROR(D4/B4,0)`
- F4: `=F3+B4`
- G4: `=G3+C4`

Continue pattern through Row 14 (December), each referencing previous row for YTD.

Row 16: Totals row: "TOTAL" label in A16, SUM formulas in B16:G16
- B16: `=SUM(B3:B14)`
- C16: `=SUM(C3:C14)`
- D16: `=B16-C16`
- E16: `=IFERROR(D16/B16,0)`
- F16: (same as F14: full year)
- G16: (same as G14)

Freeze Row 1 and Row 2 only (do not freeze across merged).

---

## Tab 4: Year Overview

### Layout

Row 1: Merged A1:N1: "YEAR AT A GLANCE: 2026": Gold on Dark Navy, bold, 16pt

Row 2: Headers: Mid Navy bg, Gold text
Cols: A=Month | B=Income | C=Expenses | D=Net | E=Margin | F=Sparkline (Income) | G=Sparkline (Expenses) | H=Invoice Count | I=Paid Count

Row 3-14: One row per month

- A3: "January" through A14: "December"
- B3: `=IFERROR('Monthly P&L'!B3,0)` (reference P&L tab: no recalculation)
- C3: `=IFERROR('Monthly P&L'!C3,0)`
- D3: `=B3-C3`
- E3: `=IFERROR(D3/B3,0)`: 0.0%
- F3: `=SPARKLINE(B3:B3,{"charttype","bar";"max",MAX('Monthly P&L'!B3:B14);"color1","#2ECC71"})`: rolling bar sparkline
- G3: `=SPARKLINE(C3:C3,{"charttype","bar";"max",MAX('Monthly P&L'!C3:C14);"color1","#E74C3C"})`
- H3: `=IFERROR(COUNTIFS('Invoice Log'!D:D,">="&DATE(2026,ROW()-2,1),'Invoice Log'!D:D,"<"&DATE(2026,ROW()-1,1)),0)`: invoices issued that month
- I3: `=IFERROR(COUNTIFS('Invoice Log'!D:D,">="&DATE(2026,ROW()-2,1),'Invoice Log'!D:D,"<"&DATE(2026,ROW()-1,1),'Invoice Log'!G:G,"Paid"),0)`

Column widths: A=110, B=130, C=130, D=130, E=100, F=130, G=130, H=120, I=110

---

## Charts

### Chart 1: Income vs Expenses Bar Chart (on Dashboard, sheetId=0)
- Type: COLUMN chart (grouped)
- Title: "Income vs Expenses by Month"
- Data source: Monthly P&L tab (sheetId=3)
  - Domain (X axis): rows 2-14 (header + 12 months), col 0 (Column A, month names): zero-indexed: startRowIndex:2, endRowIndex:15, startColumnIndex:0, endColumnIndex:1
  - Series 1 (Income): startRowIndex:2, endRowIndex:15, startColumnIndex:1, endColumnIndex:2
  - Series 2 (Expenses): startRowIndex:2, endRowIndex:15, startColumnIndex:2, endColumnIndex:3
- Series colors: Income = #2ECC71, Expenses = #E74C3C
- Legend: BOTTOM
- Background: #0D1B2A (dark navy)
- Title color: #C9A84C (gold)
- Position on Dashboard: anchor row 9 (rowIndex:9), col B (columnIndex:1), offsetX:0, offsetY:0, width:500, height:280

### Chart 2: Expense Category Pie Chart (on Dashboard, sheetId=0)
- Type: PIE chart (donut, pieHole: 0.4)
- Title: "Expenses by Category (This Month)"
- Data source: Need helper data: write a summary block on _Ref tab in columns M-N for category totals
  - _Ref!M1: "Category", N1: "Amount"
  - _Ref!M2:M13 = expense category names
  - _Ref!N2: `=SUMIFS(Transactions!E:E,Transactions!D:D,"Software",Transactions!C:C,"Expense",Transactions!B:B,Dashboard!C4)`
  - Continue for all 12 expense categories, rows N3-N13
- Source for pie chart: _Ref sheetId=5, rows 1-13, cols 12-14 (M=col12, N=col13)
  - Domain: startRowIndex:1, endRowIndex:13, startColumnIndex:12, endColumnIndex:13
  - Values: startRowIndex:1, endRowIndex:13, startColumnIndex:13, endColumnIndex:14
- Colors: Cycle through gold shades: #C9A84C, #E8D5A3, #8B6914, #FFD700, #DAA520, #B8860B, #F5DEB3, #D4A017, #C8A951, #BFA043, #A8892A, #967A20
- Legend: RIGHT
- Position: anchor row 9, col H (columnIndex:7), offsetX:0, offsetY:0, width:380, height:280

### Chart 3: Monthly Net Profit Line Chart (on Monthly P&L tab, sheetId=3)
- Type: LINE chart (smooth)
- Title: "Monthly Net Profit Trend"
- Data source: Monthly P&L (sheetId=3)
  - Domain: rows 2-14, col 0 (month names)
  - Series (Net Profit): rows 2-14, col 3 (Column D)
- Series color: #C9A84C (gold)
- Line thickness: 3
- Background: #0D1B2A
- Position: anchor row 18 (rowIndex:18), col A (columnIndex:0), width:600, height:260

---

## Cross-Sheet Formula Logic

**Master control cell:** Dashboard!C4: the Active Month dropdown. All dashboard SUMIFS and QUERY formulas filter by this value.

**Transactions → Dashboard:**
- `=SUMIFS(Transactions!E:E, Transactions!C:C, "Income", Transactions!B:B, Dashboard!C4)`: total income for selected month
- `=SUMIFS(Transactions!E:E, Transactions!C:C, "Expense", Transactions!B:B, Dashboard!C4)`: total expenses

**Invoice Log → Dashboard:**
- `=SUMIFS('Invoice Log'!E:E, 'Invoice Log'!G:G, "Sent") + SUMIFS('Invoice Log'!E:E, 'Invoice Log'!G:G, "Overdue")`: outstanding AR

**Transactions → Monthly P&L:**
- Each P&L row uses SUMIFS filtering by month name in Transactions!B:B

**P&L → Year Overview:**
- Year Overview references P&L via `='Monthly P&L'!B3` etc.: avoids double SUMIFS

**_Ref (helper) → Charts:**
- _Ref!M1:N13 holds live SUMIFS formulas for the expense pie chart, driven by Dashboard!C4

**All cross-sheet formulas:** Wrapped in IFERROR(..., 0) or IFERROR(..., "-")

---

## Conditional Formatting Rules

### Transactions tab (sheetId=1)
1. Column C = "Income": rows 2:1000, col C (index 2): TEXT_EQ "Income" → bg: #162233, text: #2ECC71
2. Column C = "Expense": rows 2:1000, col C (index 2): TEXT_EQ "Expense" → bg: #162233, text: #E74C3C
3. Column E (Amount): NUMBER_GREATER_THAN 1000: bg: #1B2A3B (highlight big transactions)

### Invoice Log tab (sheetId=2)
1. Column G = "Paid": rows 2:50, col G (index 6): TEXT_EQ "Paid" → bg: #0A2E1A, text: #27AE60
2. Column G = "Overdue": TEXT_EQ "Overdue" → bg: #2D0A0A, text: #E74C3C
3. Column G = "Sent": TEXT_EQ "Sent" → bg: #1A1800, text: #F39C12
4. Column G = "Draft": TEXT_EQ "Draft" → bg: #1B2A3B, text: #E8D5A3

### Monthly P&L tab (sheetId=3)
1. Column D (Net Profit): NUMBER_GREATER_THAN 0: rows 3:14, col D (index 3) → text: #2ECC71
2. Column D (Net Profit): NUMBER_LESS_THAN 0: rows 3:14, col D (index 3) → text: #E74C3C

---

## Data Validation

| Sheet | Range | Type | Source | Strict |
|---|---|---|---|---|
| Transactions (sheetId=1) | rows 1-500, col B (month) | ONE_OF_RANGE | _Ref!A2:A13 | Yes |
| Transactions (sheetId=1) | rows 1-500, col C (type) | ONE_OF_RANGE | _Ref!C2:C3 | Yes |
| Transactions (sheetId=1) | rows 1-500, col D (category) | ONE_OF_RANGE | _Ref!E2:G13 | No (warning: combined list) |
| Transactions (sheetId=1) | rows 1-500, col I (payment) | ONE_OF_RANGE | _Ref!K2:K7 | Yes |
| Invoice Log (sheetId=2) | rows 1-100, col G (status) | ONE_OF_RANGE | _Ref!I2:I5 | Yes |
| Dashboard (sheetId=0) | C4 (month selector) | ONE_OF_RANGE | _Ref!A2:A13 | Yes |

Note: ONE_OF_RANGE values use the format: `="'_Ref'!A2:A13"` in userEnteredValue

---

## Frozen Rows / Columns

| Tab | Freeze Rows | Freeze Columns | Notes |
|---|---|---|---|
| Dashboard (sheetId=0) | 4 | 0 | Freeze through month selector row |
| Transactions (sheetId=1) | 1 | 0 | Header row only |
| Invoice Log (sheetId=2) | 1 | 0 | Header row only |
| Monthly P&L (sheetId=3) | 2 | 0 | Title + header row |
| Year Overview (sheetId=4) | 2 | 0 | Title + header row |

Note: Do NOT freeze across merged cells. Dashboard rows 1-3 are merged (A1:L1 and A2:L2): freezing 4 rows is fine since freeze is below the merges.

---

## Tab Colors (updateSheetProperties)

| Tab | Color Hex | RGB Float |
|---|---|---|
| Dashboard | #C9A84C | {red:0.788, green:0.659, blue:0.298} |
| Transactions | #1B2A3B | {red:0.106, green:0.165, blue:0.231} |
| Invoice Log | #1B2A3B | {red:0.106, green:0.165, blue:0.231} |
| Monthly P&L | #1B2A3B | {red:0.106, green:0.165, blue:0.231} |
| Year Overview | #8B6914 | {red:0.545, green:0.412, blue:0.078} |

---

## Column Width Specifications

### Transactions (sheetId=1)
A:45, B:110, C:90, D:150, E:110, F:100, G:160, H:200, I:130

### Invoice Log (sheetId=2)
A:110, B:160, C:220, D:110, E:110, F:110, G:100, H:110, I:200

### Monthly P&L (sheetId=3)
A:130, B:140, C:140, D:140, E:120, F:140, G:140

### Year Overview (sheetId=4)
A:110, B:130, C:130, D:130, E:100, F:130, G:130, H:120, I:110

---

## Row Height Specifications

| Tab | Row(s) | Height (px) |
|---|---|---|
| Dashboard | Row 1 (title) | 52 |
| Dashboard | Row 2 (subtitle) | 30 |
| Dashboard | Rows 6-8 (KPI cards) | 36 |
| All data tabs | Row 1 (header) | 34 |
| All data tabs | Data rows | 26 |

---

## Build Order

1. Create spreadsheet with all 6 sheets (sheetIds 0-5)
2. Write _Ref tab data (columns A, C, E, G, I, K, M-N)
3. Write Transactions tab: headers row 1, then all 35 sample rows
4. Write Invoice Log tab: headers row 1, then all 15 sample rows
5. Write Monthly P&L tab: title row 1, headers row 2, formulas rows 3-16
6. Write Year Overview tab: title row 1, headers row 2, formulas rows 3-14
7. Write Dashboard tab: title/subtitle rows 1-2, month selector row 4, KPI formulas rows 6-8, QUERY formula row 32
8. Apply all formatting via batchUpdate (headers, body rows, column widths, row heights, merges, tab colors, frozen rows)
9. Add data validation (all dropdowns)
10. Add conditional formatting (Transactions, Invoice Log, P&L)
11. Add charts (3 charts)

---

## Final Requirements Checklist

- [ ] All formulas are native Google Sheets: no Apps Script
- [ ] All cross-sheet formulas wrapped in IFERROR
- [ ] Dashboard!C4 is the single active-month control cell
- [ ] Sample data covers 3 months (Jan, Feb, March) with 35 rows in Transactions, 15 in Invoice Log
- [ ] All 3 charts render with data on first open
- [ ] Dropdowns work on Transactions (Month, Type, Category, Payment), Invoice Log (Status), Dashboard (Month selector)
- [ ] No #REF!, #NAME?, #ERROR! cells visible
- [ ] Tab colors set for all 5 visible tabs
- [ ] Frozen rows in place per spec
- [ ] Dark navy / gold color scheme applied throughout
- [ ] Spreadsheet title: "Freelancer Finance Hub: 2026"
- [ ] Output spreadsheet ID and shareable link when build completes

---

## Spreadsheet Title
"Freelancer Finance Hub: 2026"

## Target Etsy Price
$15

## Target Buyer
Freelancers, consultants, independent contractors, solopreneurs
