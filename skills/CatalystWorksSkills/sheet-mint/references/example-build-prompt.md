# Smart 50/30/20 Monthly Budget Planner — GWS CLI Build Prompt

Build me a complete, production-ready "Smart 50/30/20 Monthly Budget Planner" in Google Sheets using the GWS CLI. This spreadsheet is a sellable digital product. Every formula, format, chart, and dropdown must be fully functional on first open — no placeholders, no empty dashboards.

---

## Overview

A modern personal budgeting system based on the 50/30/20 rule (50% Needs, 30% Wants, 20% Savings & Debt). The user sets their monthly income, customizes their split ratios, logs transactions, and the dashboard auto-updates. Includes a Debt Snowball Tracker and Savings Goals tab. Color scheme: deep teal headers, coral Wants, sage green Needs, golden Savings. Clean, minimal, and professional.

---

## Tab Structure

| sheetId | Name              | Visible | Purpose                                      |
|---------|-------------------|---------|----------------------------------------------|
| 0       | Dashboard         | Yes     | Monthly overview: KPIs, charts, summaries    |
| 1       | Transactions      | Yes     | Daily income & expense log                   |
| 2       | Debt Tracker      | Yes     | Debt snowball payoff calculator              |
| 3       | Savings Goals     | Yes     | Goal progress tracker                        |
| 4       | Annual Overview   | Yes     | Year-at-a-glance monthly summary table       |
| 5       | Setup             | Yes     | User inputs: income, ratios, category names  |
| 6       | _Ref              | Hidden  | Lookup tables: categories, months, buckets   |

---

## Color Palette

| Semantic Role      | Hex Code  | RGB Float (R, G, B)     |
|--------------------|-----------|--------------------------|
| Header background  | #264653   | 0.149, 0.275, 0.325      |
| Header text        | #FFFFFF   | 1.0, 1.0, 1.0            |
| Needs (50%)        | #2A9D8F   | 0.165, 0.616, 0.561      |
| Wants (30%)        | #E76F51   | 0.906, 0.435, 0.318      |
| Savings/Debt (20%) | #E9C46A   | 0.914, 0.769, 0.416      |
| Income / Positive  | #52B788   | 0.322, 0.718, 0.533      |
| Danger / Over      | #D62828   | 0.839, 0.157, 0.157      |
| Warning            | #F4A261   | 0.957, 0.635, 0.380      |
| Section bg light   | #EAF4F4   | 0.918, 0.957, 0.957      |
| Alternating row    | #F7FAFA   | 0.969, 0.980, 0.980      |
| White              | #FFFFFF   | 1.0, 1.0, 1.0            |
| Border / subtle    | #CDD8D8   | 0.804, 0.847, 0.847      |

---

## Tab 6 (Hidden): _Ref (sheetId: 6)

Populate this tab first. It is the lookup source for all dropdowns.

### Range A1:A3 — Month list (label: "MONTHS")
January, February, March, April, May, June, July, August, September, October, November, December

### Range C1:C3 — Bucket list (label: "BUCKETS")
Needs, Wants, Savings & Debt

### Range E1:E20 — Needs categories (label: "NEEDS_CATS")
Rent/Mortgage, Utilities, Groceries, Insurance, Car Payment, Gas/Transport, Phone Bill, Internet, Medical, Childcare, Subscriptions (Essential), Minimum Debt Payment, Other Needs

### Range G1:G15 — Wants categories (label: "WANTS_CATS")
Dining Out, Entertainment, Shopping, Travel, Personal Care, Hobbies, Gifts, Alcohol/Bars, Streaming Services, Clothing, Gym, Social Life, Other Wants

### Range I1:I8 — Savings categories (label: "SAVINGS_CATS")
Emergency Fund, Retirement (401k/IRA), House Down Payment, Vacation Fund, Sinking Fund, Extra Debt Payment, Investment, Other Savings

### Range K1:K13 — All transaction types combined (label: "ALL_CATS")
List: Income, then all Needs, Wants, and Savings categories combined (pull from E and G and I columns).

### Range M1:M2 — Transaction types (label: "TYPES")
Income, Expense

---

## Tab 5: Setup (sheetId: 5)

This is the user's control panel. Style it clearly with section headers.

### Layout

Row 1: Merged A1:F1 — Title: "BUDGET SETUP & CONFIGURATION" — Header style (#264653 bg, white text, bold, 14pt, centered)

Row 3: Label in A3: "YOUR NAME" — Value in C3: "Alex Johnson" (editable)
Row 4: Label in A4: "CURRENCY SYMBOL" — Value in C4: "$" (editable)
Row 5: Label in A5: "ACTIVE MONTH" — Dropdown in C5: source from _Ref!A1:A12, default: "January"
Row 6: Label in A6: "ACTIVE YEAR" — Value in C6: 2025 (editable number)

Row 8: Merged A8:F8 — Section header: "MONTHLY INCOME" — bg #2A9D8F, white text, bold
Row 9: Label in A9: "Primary Income" — Value in C9: 4500 (number)
Row 10: Label in A10: "Secondary Income" — Value in C10: 800 (number)
Row 11: Label in A11: "Other Income" — Value in C11: 200 (number)
Row 12: Label in A12: "TOTAL INCOME" — Formula in C12: =SUM(C9:C11) — bold, #264653 bg, white text

Row 14: Merged A14:F14 — Section header: "50/30/20 SPLIT RATIOS" — bg #264653, white text, bold
Row 15: Label in A15: "Needs %" — Value in C15: 50 — format as 0"%" — note in D15: "(Recommended: 50)"
Row 16: Label in A16: "Wants %" — Value in C16: 30 — note in D16: "(Recommended: 30)"
Row 17: Label in A17: "Savings & Debt %" — Value in C17: 20 — note in D17: "(Recommended: 20)"
Row 18: Label in A18: "TOTAL (must = 100)" — Formula in C18: =C15+C16+C17 — conditional format: green if =100, red if ≠100

Row 20: Merged A20:F20 — Section header: "CALCULATED BUDGETS" — bg #2A9D8F, white text, bold
Row 21: Label in A21: "Needs Budget" — Formula in C21: =C12*(C15/100) — currency format
Row 22: Label in A22: "Wants Budget" — Formula in C22: =C12*(C16/100) — currency format
Row 23: Label in A23: "Savings & Debt Budget" — Formula in C23: =C12*(C17/100) — currency format

Column widths: A=220, B=20, C=160, D=200

Freeze row 1.

---

## Tab 1: Transactions (sheetId: 1)

The data entry hub. Every row is one transaction.

### Headers (Row 1) — bg #264653, white text, bold, 11pt

| Col | Header       | Width | Type                          |
|-----|--------------|-------|-------------------------------|
| A   | DATE         | 110   | Date (MM/DD/YYYY)             |
| B   | DESCRIPTION  | 220   | Text (free entry)             |
| C   | TYPE         | 100   | Dropdown: Income / Expense    |
| D   | BUCKET       | 130   | Dropdown: Needs/Wants/Savings |
| E   | CATEGORY     | 180   | Dropdown: all categories      |
| F   | AMOUNT       | 110   | Currency $#,##0.00            |
| G   | MONTH        | 110   | Formula: =TEXT(A2,"mmmm")     |
| H   | YEAR         | 80    | Formula: =YEAR(A2)            |
| I   | NOTES        | 200   | Text (free entry)             |

### Data Validation
- C2:C1000: Dropdown from _Ref!M1:M2, strict
- D2:D1000: Dropdown from _Ref!C1:C3, strict
- E2:E1000: Dropdown from _Ref!K1:K30 (all categories combined), strict

### Formulas (auto-populate, don't require user input)
- G2: =IF(A2="","",TEXT(A2,"mmmm")) — copy down to G1000
- H2: =IF(A2="","",YEAR(A2)) — copy down to H1000

### Conditional Formatting on Column C
- If C = "Income": row background #EBF7F0 (light green tint)
- If C = "Expense": row background #FFF8F6 (light coral tint)

### Conditional Formatting on Column F (Amount)
- If F > 500: bold text
- If F > 1000: bold + #FFF3CD background (golden highlight)

### Sample Data — 35 rows across January–March 2025

Include the following (use realistic dates spread across Jan, Feb, Mar 2025):

**January (15 rows):**
| Date       | Description         | Type    | Bucket         | Category            | Amount   |
|------------|---------------------|---------|----------------|---------------------|----------|
| 01/01/2025 | Opening Balance     | Income  | Savings & Debt | Emergency Fund      | 500.00   |
| 01/03/2025 | Paycheck            | Income  | —              | Income              | 2250.00  |
| 01/05/2025 | Rent                | Expense | Needs          | Rent/Mortgage       | 1200.00  |
| 01/06/2025 | Electricity Bill    | Expense | Needs          | Utilities           | 85.00    |
| 01/07/2025 | Whole Foods         | Expense | Needs          | Groceries           | 142.50   |
| 01/10/2025 | Netflix             | Expense | Wants          | Streaming Services  | 15.99    |
| 01/12/2025 | Chipotle            | Expense | Wants          | Dining Out          | 18.75    |
| 01/15/2025 | Paycheck            | Income  | —              | Income              | 2250.00  |
| 01/16/2025 | Car Insurance       | Expense | Needs          | Insurance           | 120.00   |
| 01/18/2025 | Amazon Shopping     | Expense | Wants          | Shopping            | 67.89    |
| 01/20/2025 | Gas Station         | Expense | Needs          | Gas/Transport       | 55.00    |
| 01/22/2025 | Gym Membership      | Expense | Wants          | Gym                 | 40.00    |
| 01/25/2025 | Savings Transfer    | Expense | Savings & Debt | Emergency Fund      | 300.00   |
| 01/28/2025 | Phone Bill          | Expense | Needs          | Phone Bill          | 75.00    |
| 01/30/2025 | Side Hustle Income  | Income  | —              | Income              | 800.00   |

**February (10 rows):**
| Date       | Description         | Type    | Bucket         | Category            | Amount   |
|------------|---------------------|---------|----------------|---------------------|----------|
| 02/03/2025 | Paycheck            | Income  | —              | Income              | 2250.00  |
| 02/05/2025 | Rent                | Expense | Needs          | Rent/Mortgage       | 1200.00  |
| 02/07/2025 | Trader Joes         | Expense | Needs          | Groceries           | 110.00   |
| 02/10/2025 | Valentine Dinner    | Expense | Wants          | Dining Out          | 95.00    |
| 02/14/2025 | Flowers/Gift        | Expense | Wants          | Gifts               | 45.00    |
| 02/15/2025 | Paycheck            | Income  | —              | Income              | 2250.00  |
| 02/18/2025 | Internet Bill       | Expense | Needs          | Internet            | 59.99    |
| 02/20/2025 | Retirement          | Expense | Savings & Debt | Retirement (401k/IRA)| 400.00  |
| 02/25/2025 | Spotify             | Expense | Wants          | Streaming Services  | 9.99     |
| 02/28/2025 | Side Hustle         | Income  | —              | Income              | 800.00   |

**March (10 rows):**
| Date       | Description         | Type    | Bucket         | Category            | Amount   |
|------------|---------------------|---------|----------------|---------------------|----------|
| 03/03/2025 | Paycheck            | Income  | —              | Income              | 2250.00  |
| 03/05/2025 | Rent                | Expense | Needs          | Rent/Mortgage       | 1200.00  |
| 03/08/2025 | Costco              | Expense | Needs          | Groceries           | 188.42   |
| 03/12/2025 | Concert Tickets     | Expense | Wants          | Entertainment       | 120.00   |
| 03/15/2025 | Paycheck            | Income  | —              | Income              | 2250.00  |
| 03/18/2025 | Car Payment         | Expense | Needs          | Car Payment         | 350.00   |
| 03/20/2025 | New Shoes           | Expense | Wants          | Clothing            | 89.00    |
| 03/22/2025 | Doctor Visit        | Expense | Needs          | Medical             | 40.00    |
| 03/25/2025 | Investment          | Expense | Savings & Debt | Investment          | 200.00   |
| 03/30/2025 | Side Hustle         | Income  | —              | Income              | 800.00   |

Freeze row 1. Alternate row colors: white / #F7FAFA starting row 2.

---

## Tab 0: Dashboard (sheetId: 0)

The main visual hub. Driven by Setup!C5 (Active Month) and Setup!C6 (Active Year).

All SUMIFS formulas filter Transactions by MONTH (col G) = active month AND YEAR (col H) = active year.

### Row 1 — Title Banner
Merged A1:L1 — Formula: =UPPER(Setup!C5)&" "&Setup!C6&" — BUDGET DASHBOARD"
Style: #264653 bg, white text, bold, 18pt, centered, row height 50px

### Row 2 — Subtitle
Merged A2:L2 — Text: "Smart 50/30/20 Budget Planner"
Style: #2A9D8F bg, white text, 10pt italic, centered

### Row 4-6 — Budget Period Info (left panel)
A4: "BUDGET PERIOD" bold, #264653 text
B4: =Setup!C5&" 1 — "&Setup!C5&" 30, "&Setup!C6
A5: "ACTIVE MONTH" bold
B5: =Setup!C5
A6: "CURRENCY" bold
B6: =Setup!C4

### Row 8 — KPI Section Header
Merged A8:L8 — "MONTHLY SNAPSHOT" — bg #264653, white, bold, 11pt

### Row 9-11 — KPI Cards (3 columns of 4 cards each)

**Card 1: TOTAL INCOME (A9:C11)**
- Label row 9: "TOTAL INCOME" — bg #264653, white, bold, centered
- Value row 10: =SUMIFS(Transactions!F:F, Transactions!C:C, "Income", Transactions!G:G, Setup!C5, Transactions!H:H, Setup!C6) — large font 20pt, bold, #52B788 text, centered
- Sub-label row 11: "This month's earnings" — small 9pt, italic

**Card 2: TOTAL SPENT (D9:F11)**
- Label: "TOTAL SPENT" — bg #264653, white, bold
- Value: =SUMIFS(Transactions!F:F, Transactions!C:C, "Expense", Transactions!G:G, Setup!C5, Transactions!H:H, Setup!C6) — 20pt, bold, #E76F51 text
- Sub-label: "Total outflow this month"

**Card 3: REMAINING (G9:I11)**
- Label: "AMOUNT LEFT" — bg #264653, white, bold
- Value: =D10-G10 (income minus spent) — 20pt, bold — conditional: green if ≥0, red if <0
- Sub-label: "Available to spend/save"

**Card 4: SAVINGS RATE (J9:L11)**
- Label: "SAVINGS RATE" — bg #264653, white, bold
- Value: =IFERROR(SUMIFS(Transactions!F:F,Transactions!D:D,"Savings & Debt",Transactions!G:G,Setup!C5,Transactions!H:H,Setup!C6)/SUMIFS(Transactions!F:F,Transactions!C:C,"Income",Transactions!G:G,Setup!C5,Transactions!H:H,Setup!C6),0) — 20pt, bold, format as 0.0%, #E9C46A text
- Sub-label: "% of income saved"

### Row 13-20 — Budget vs Actual Comparison Table

Row 13: Merged A13:L13 — "BUDGET VS. ACTUAL" — bg #2A9D8F, white, bold, 11pt

Row 14 headers (bg #264653, white, bold):
A14: CATEGORY | C14: BUDGET | E14: ACTUAL | G14: DIFFERENCE | I14: % USED | K14: STATUS

Row 15 — Needs:
A15: "🟢 NEEDS (50%)" — bold
C15: =Setup!C21 — currency
E15: =SUMIFS(Transactions!F:F,Transactions!D:D,"Needs",Transactions!G:G,Setup!C5,Transactions!H:H,Setup!C6) — currency
G15: =C15-E15 — currency, green if >0 red if <0
I15: =IFERROR(E15/C15,0) — 0% format
K15: =IF(I15<=1,"✅ On Track","⚠️ Over Budget")

Row 16 — Wants:
A16: "🟠 WANTS (30%)" — bold
C16: =Setup!C22
E16: =SUMIFS(Transactions!F:F,Transactions!D:D,"Wants",Transactions!G:G,Setup!C5,Transactions!H:H,Setup!C6)
G16: =C16-E16
I16: =IFERROR(E16/C16,0)
K16: =IF(I16<=1,"✅ On Track","⚠️ Over Budget")

Row 17 — Savings:
A17: "🟡 SAVINGS & DEBT (20%)" — bold
C17: =Setup!C23
E17: =SUMIFS(Transactions!F:F,Transactions!D:D,"Savings & Debt",Transactions!G:G,Setup!C5,Transactions!H:H,Setup!C6)
G17: =C17-E17
I17: =IFERROR(E17/C17,0)
K17: =IF(I17<=1,"✅ On Track","⚠️ Over Budget")

Row 18 — Total:
A18: "TOTAL" — bold, bg #264653, white
C18: =SUM(C15:C17)
E18: =SUM(E15:E17)
G18: =C18-E18
I18: =IFERROR(E18/C18,0)
K18: =IF(I18<=1,"✅ On Track","⚠️ Over Budget")

### Row 22-35 — Top Expenses This Month (left side A22:F35)

Row 22: Merged A22:F22 — "TOP TRANSACTIONS THIS MONTH" — bg #264653, white, bold

Row 23 headers: Date | Description | Bucket | Category | Amount

Rows 24-33: Use LARGE/INDEX/MATCH or QUERY to pull top 10 expense rows for the active month:
=IFERROR(QUERY(Transactions!A:I,"SELECT A,B,D,E,F WHERE C='Expense' AND G='"&Setup!C5&"' AND H="&Setup!C6&" ORDER BY F DESC LIMIT 10",0),"")

### Row 22-35 — Category Breakdown (right side H22:L35)

Row 22: Merged H22:L22 — "SPENDING BY BUCKET" — bg #2A9D8F, white, bold

Rows 23-26:
H23: "Bucket" | I23: "Budget" | J23: "Spent" | K23: "Remaining" | L23: "Bar"
H24: Needs | I24: =Setup!C21 | J24: =E15 | K24: =G15 | L24: =SPARKLINE(J24/I24,{"charttype","bar";"max",1;"color1","#2A9D8F";"color2","#EAF4F4"})
H25: Wants | I25: =Setup!C22 | J25: =E16 | K25: =G16 | L25: =SPARKLINE(J25/I25,{"charttype","bar";"max",1;"color1","#E76F51";"color2","#FFF8F6"})
H26: Savings | I26: =Setup!C23 | J26: =E17 | K26: =G17 | L26: =SPARKLINE(J26/I26,{"charttype","bar";"max",1;"color1","#E9C46A";"color2","#FFFDF0"})

Freeze rows 1-2.

Column widths: A=140, B=30, C=130, D=30, E=130, F=30, G=130, H=30, I=130, J=130, K=100, L=140

---

## Charts on Dashboard

### Chart 1 — Donut: Actual Spending Allocation
- Type: PIE with pieHole: 0.4 (donut)
- Title: "Actual Allocation"
- Data source: Dashboard rows 15-17, columns E (Actual)
- Labels: Needs, Wants, Savings & Debt
- Colors: #2A9D8F, #E76F51, #E9C46A
- Position: Anchored at Dashboard row 9, column D area (overlaid/beside KPI cards)
- Size: 340 wide × 240 high
- Legend: BOTTOM

### Chart 2 — Column: Budget vs Actual by Bucket
- Type: BAR (vertical column, grouped)
- Title: "Budget vs. Actual"
- Data source: Dashboard rows 15-17 — two series: column C (Budget) and column E (Actual)
- Series 1 (Budget): #264653
- Series 2 (Actual): #2A9D8F
- Position: Anchored below row 19 on Dashboard
- Size: 480 wide × 260 high
- Legend: BOTTOM

---

## Tab 2: Debt Tracker (sheetId: 2)

### Row 1 — Title Banner
Merged A1:J1 — "DEBT SNOWBALL TRACKER" — bg #264653, white, bold, 16pt, centered

### Row 2 — Instructions
Merged A2:J2 — "List your debts smallest to largest. Pay minimums on all, attack the smallest with extra payments. (Snowball Method)" — italic, 10pt

### Row 4 — Headers (bg #264653, white, bold)
A4: DEBT NAME | B4: LENDER | C4: TOTAL BALANCE | D4: INTEREST RATE | E4: MIN PAYMENT | F4: EXTRA PAYMENT | G4: MONTHLY PAYMENT | H4: MONTHS TO PAYOFF | I4: TOTAL INTEREST | J4: STATUS

### Rows 5-12 — Debt Entries (8 debt slots)

Pre-fill sample debts in rows 5-8:
Row 5: Credit Card A | Chase | 1850.00 | 22.99% | 45.00 | 200.00 | =E5+F5 | =IFERROR(NPER(D5/12,-(G5),C5),0) formatted as integer | =IFERROR(G5*H5-C5,0) | =IF(C5=0,"✅ PAID OFF","⏳ In Progress")
Row 6: Medical Bill | Hospital | 620.00 | 0% | 50.00 | 100.00 | (same formulas)
Row 7: Car Loan | Toyota Fin | 8400.00 | 6.9% | 280.00 | 0.00 | (same formulas)
Row 8: Student Loan | Navient | 14200.00 | 4.5% | 175.00 | 0.00 | (same formulas)
Rows 9-12: empty with formulas ready

### Row 14 — Totals Row (bg #264653, white, bold)
A14: "TOTALS" | C14: =SUM(C5:C12) | E14: =SUM(E5:E12) | F14: =SUM(F5:F12) | G14: =SUM(G5:G12) | I14: =SUM(I5:I12)

### Row 16 — Debt-Free Date Estimate
A16: "Estimated Debt-Free Month:" | C16: =EDATE(TODAY(), MAX(H5:H12)) formatted as MMMM YYYY

Column widths: A=160, B=130, C=130, D=120, E=120, F=120, G=130, H=130, I=120, J=130

Conditional formatting:
- J column: "✅ PAID OFF" → bg #D4EDDA (light green), text #155724
- J column: "⏳ In Progress" → bg #FFF3CD (light yellow), text #856404
- C column: gradient color scale from green (low balance) to red (high balance)

Freeze row 4.

---

## Tab 3: Savings Goals (sheetId: 3)

### Row 1 — Title
Merged A1:H1 — "SAVINGS GOALS TRACKER" — bg #264653, white, bold, 16pt

### Row 3 — Headers (bg #2A9D8F, white, bold)
A3: GOAL NAME | B3: TARGET AMOUNT | C3: CURRENT SAVED | D3: MONTHLY CONTRIBUTION | E3: MONTHS REMAINING | F3: TARGET DATE | G3: % COMPLETE | H3: PROGRESS BAR

### Rows 4-10 — Goal Entries (7 slots)

Pre-fill sample goals:
Row 4: Emergency Fund | 10000 | 3200 | 300 | =IFERROR(CEILING((B4-C4)/D4,1),0) | =EDATE(TODAY(),E4) formatted MMMM YYYY | =IFERROR(C4/B4,0) as 0.0% | =SPARKLINE(G4,{"charttype","bar";"max",1;"color1","#2A9D8F";"color2","#EAF4F4"})
Row 5: Vacation Fund | 3000 | 750 | 150 | (same) | (same) | (same) | (same with color1 #E9C46A)
Row 6: House Down Payment | 40000 | 8500 | 500 | (same) | (same) | (same) | (same)
Row 7: New Car Fund | 15000 | 1200 | 200 | (same) | (same) | (same) | (same)
Rows 8-10: Empty with formulas ready

### Row 12 — Totals
A12: "TOTALS" bold | B12: =SUM(B4:B10) | C12: =SUM(C4:C10) | D12: =SUM(D4:D10) | G12: =IFERROR(C12/B12,0) as 0.0%

Conditional formatting on G column (% Complete):
- G < 25%: bg #F8D7DA (light red)
- G 25%-74%: bg #FFF3CD (light yellow)
- G >= 75%: bg #D4EDDA (light green)

Column widths: A=180, B=140, C=140, D=160, E=150, F=150, G=110, H=200

Freeze row 3.

---

## Tab 4: Annual Overview (sheetId: 4)

### Row 1
Merged A1:P1 — Formula: =Setup!C6&" ANNUAL BUDGET OVERVIEW" — bg #264653, white, bold, 16pt

### Row 3 — Column Headers (bg #264653, white, bold)
A3: METRIC | B3: JAN | C3: FEB | D3: MAR | E3: APR | F3: MAY | G3: JUN | H3: JUL | I3: AUG | J3: SEP | K3: OCT | L3: NOV | M3: DEC | N3: TOTAL | O3: AVG

### Rows 4-9 — Metric Rows

For each month column (B=January, C=February etc), use SUMIFS filtering Transactions by G column (month name) and H column (year = Setup!C6).

Row 4: INCOME — =SUMIFS(Transactions!F:F,Transactions!C:C,"Income",Transactions!G:G,"January",Transactions!H:H,Setup!C6) ... across all months. N4=SUM(B4:M4), O4=AVERAGE(B4:M4). Style: bg #EBF7F0, #52B788 text, bold.

Row 5: NEEDS SPENT — same pattern filtering D column = "Needs". Style: bg #EAF4F4, #2A9D8F text.

Row 6: WANTS SPENT — filtering D = "Wants". Style: bg #FFF8F6, #E76F51 text.

Row 7: SAVINGS SPENT — filtering D = "Savings & Debt". Style: bg #FFFDF0, #E9C46A text.

Row 8: TOTAL SPENT — =SUM(B5:B7) per month. N8=SUM(B8:M8). Bold.

Row 9: NET (Income - Spent) — =B4-B8 per month. N9=SUM(B9:M9). Conditional: green bg if >0, red bg if <0.

Row 10: SAVINGS RATE — =IFERROR(B7/B4,0) per month. Format as 0%. Conditional: green if >=20%, yellow if 10-19%, red if <10%.

### Row 12 onwards — Mini sparkline row
A12: "TREND" | B12:M12 — For each month col, show SPARKLINE of Net (row 9 across months):
B12: =SPARKLINE(B9:M9,{"charttype","line";"color","#2A9D8F";"linewidth",2}) — Merge B12:M12 and show one sparkline across all months.

Column widths: A=160, B:M=90 each, N=100, O=100

Freeze rows 1-3.

---

## Final Requirements

1. Build order: _Ref → Setup → Transactions (with sample data) → Dashboard → Debt Tracker → Savings Goals → Annual Overview
2. All formulas must be native Google Sheets — no Apps Script
3. Every SUMIFS/QUERY must reference Setup!C5 for the active month and Setup!C6 for the year
4. Wrap all cross-sheet formulas in IFERROR(..., 0) or IFERROR(..., "") to prevent errors on empty months
5. Apply thin borders (#CDD8D8) around all data tables
6. Tab colors: Dashboard=#264653, Transactions=#2A9D8F, Debt Tracker=#E76F51, Savings Goals=#E9C46A, Annual Overview=#52B788, Setup=#A8DADC
7. After creating the spreadsheet, output the shareable link and the spreadsheet ID
8. The spreadsheet title should be: "Smart 50/30/20 Monthly Budget Planner"
