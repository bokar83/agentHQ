# Design Spec: All-in-One Budget + Debt + Savings Dashboard (Etsy Template #5)

**Date:** 2026-03-25
**Owner:** Boubacar (bokar83@gmail.com)
**Sell Price Target:** $16–$22 on Etsy
**Delivery:** Google Sheets link via ListingView

---

## Overview

A premium Google Sheets bundle that combines six financial management tools into one cohesive workbook: monthly budget tracking, debt payoff planning (snowball + avalanche), savings goal tracking, sinking funds management, net worth tracking, and digital cash envelopes. The centerpiece is a Financial Health Score dashboard that auto-rates the user's finances across 5 categories and shows year-to-date performance at a glance. Built with Navy Slate color theme for broadest demographic appeal (couples, families, business owners). Sample data pre-loaded so it works out of the box.

---

## Tab Structure

21 sheets total: 8 visible + 12 hidden monthly summaries + 1 hidden lookup.

| sheetId | Tab Name | Visible | Purpose |
|---------|----------|---------|---------|
| 0 | START HERE | ✅ | Onboarding guide, color legend, what each tab does |
| 1 | HEALTH SCORE | ✅ | YTD Financial Health Score dashboard — 5 category cards + overall score |
| 2 | BUDGET LOG | ✅ | Single transaction input table — source of truth for all budget data |
| 3 | DEBT PAYOFF | ✅ | Snowball/Avalanche toggle, up to 10 debts, payoff ranking + date calculator |
| 4 | SAVINGS GOALS | ✅ | Up to 8 goals with monthly contribution calculator + progress bars |
| 5 | SINKING FUNDS | ✅ | Up to 12 funds with goal calculator + visual runway bars |
| 6 | NET WORTH | ✅ | 12-month asset/liability tracker + net worth line chart |
| 7 | CASH ENVELOPES | ✅ | 10 digital envelopes — budget vs. spent, color-coded status |
| 8 | JAN | ❌ | Auto-aggregates BUDGET LOG transactions for January |
| 9 | FEB | ❌ | Auto-aggregates BUDGET LOG transactions for February |
| 10 | MAR | ❌ | Auto-aggregates BUDGET LOG transactions for March |
| 11 | APR | ❌ | Auto-aggregates BUDGET LOG transactions for April |
| 12 | MAY | ❌ | Auto-aggregates BUDGET LOG transactions for May |
| 13 | JUN | ❌ | Auto-aggregates BUDGET LOG transactions for June |
| 14 | JUL | ❌ | Auto-aggregates BUDGET LOG transactions for July |
| 15 | AUG | ❌ | Auto-aggregates BUDGET LOG transactions for August |
| 16 | SEP | ❌ | Auto-aggregates BUDGET LOG transactions for September |
| 17 | OCT | ❌ | Auto-aggregates BUDGET LOG transactions for October |
| 18 | NOV | ❌ | Auto-aggregates BUDGET LOG transactions for November |
| 19 | DEC | ❌ | Auto-aggregates BUDGET LOG transactions for December |
| 20 | LOOKUP | ❌ | Reference data: categories, bucket mappings, score thresholds |

---

## Tab 0: START HERE (sheetId: 0)

### Layout
- Row 1: Merged title banner — "💙 Your All-in-One Financial Dashboard — Welcome!" (navy bg, white text, 18pt bold)
- Row 2: Subtitle — "Complete setup in 5 minutes. Follow the steps below." (light bg, 11pt)
- Rows 4–8: 3-column setup steps table (Step #, What To Do, Where To Go)
- Rows 10–17: Tab directory — icon, tab name, one-line description, color-coded by category
- Rows 19–24: Color legend — what green/amber/red means across the workbook
- Row 26: "You're all set! Head to HEALTH SCORE to see your dashboard →"

### Setup Steps
1. Enter your monthly income in BUDGET LOG (cell B3)
2. Log your first transactions in BUDGET LOG starting at row 7
3. Add your debts in DEBT PAYOFF tab
4. Add your savings goals in SAVINGS GOALS tab
5. Set up your sinking funds in SINKING FUNDS tab

---

## Tab 1: HEALTH SCORE (sheetId: 1)

### Layout
- Row 1: Merged banner — "📊 FINANCIAL HEALTH SCORE — 2026 Year-to-Date" (navy bg, white, 16pt bold)
- Row 2: Overall score display — large merged cell, auto-calculated 0–100, color-coded background
- Row 3: Score label — "GREAT / GOOD / NEEDS ATTENTION" based on score range
- Rows 5–10: 5 category score cards (2-column layout: left card + right card, 5th card spans full width or paired with a summary)
- Row 12: "Last updated" note (auto-populated with TODAY())
- Rows 14–20: YTD summary stats — total income, total expenses, net savings, surplus/deficit

### Overall Score Formula
```
=IFERROR(ROUND((BudgetScore + SavingsScore + DebtScore + NetWorthScore + SinkingFundsScore) / 5, 0), 0)
```
Each category scores 0–100. Weighted equally.

### 5 Category Cards (each card shows: category name, score, status label, progress bar)

**Card 1 — Budget Health**
- Metric: YTD expenses / YTD income (pulled from hidden monthly summary tabs)
- Score: IF(ratio ≤ 0.85, 100, IF(ratio ≤ 0.95, 85, IF(ratio ≤ 1.0, 70, IF(ratio ≤ 1.10, 45, 10))))
- Status: ≤95% → "✅ On Track", ≤110% → "⚠️ Watch Spending", >110% → "🔴 Over Budget"

**Card 2 — Savings Rate**
- Metric: YTD amount saved / YTD income
- Score: IF(rate ≥ 0.20, 100, IF(rate ≥ 0.15, 85, IF(rate ≥ 0.10, 70, IF(rate ≥ 0.05, 45, 10))))
- Status: ≥15% → "✅ Strong Saver", ≥5% → "⚠️ Building Habit", <5% → "🔴 Save More"

**Card 3 — Debt Progress**
- Metric: Total debt paid YTD / Total minimum payments due YTD
- Score: IF(ratio ≥ 1.5, 100, IF(ratio ≥ 1.2, 85, IF(ratio ≥ 1.0, 70, IF(ratio ≥ 0.8, 45, 10))))
- Status: ≥120% of minimums → "✅ Ahead of Schedule", ≥100% → "⚠️ Meeting Minimums", <100% → "🔴 Missed Payments"

**Card 4 — Net Worth Trend**
- Metric: Current net worth vs. Jan 1 net worth (from NET WORTH tab)
- Score: IF(growth > 0.05, 100, IF(growth > 0, 75, IF(growth = 0, 50, IF(growth > -0.05, 30, 10))))
- Status: Growing → "✅ Building Wealth", Flat → "⚠️ Holding Steady", Declining → "🔴 Net Worth Dropping"

**Card 5 — Sinking Funds**
- Metric: Sum of all fund current balances / Sum of all fund target amounts (from SINKING FUNDS tab)
- Score: IF(pct ≥ 0.75, 100, IF(pct ≥ 0.50, 75, IF(pct ≥ 0.30, 50, IF(pct ≥ 0.10, 25, 10))))
- Status: ≥75% → "✅ Well Prepared", ≥40% → "⚠️ Getting There", <40% → "🔴 Build Your Buffer"

### Progress Bars (REPT-based)
```
=REPT("█", ROUND(score/10, 0)) & REPT("░", 10-ROUND(score/10, 0))
```

### Conditional Formatting on Score Cell
- Score ≥ 80: background #27AE60, white text
- Score 60–79: background #E67E22, white text
- Score < 60: background #E74C3C, white text

---

## Tab 2: BUDGET LOG (sheetId: 2)

### Layout
- Row 1: Banner — "💰 BUDGET LOG — All Transactions" (navy)
- Rows 2–4: Input panel — Monthly Income Target (B3, yellow input cell — user enters expected monthly take-home pay; used by HEALTH SCORE for savings rate and budget health calculations), YTD Income (auto-SUMPRODUCT of all Income-type transactions), YTD Expenses (auto-SUMPRODUCT of all Expense-type transactions), YTD Surplus/Deficit (YTD Income minus YTD Expenses)
- Row 6: Column headers (frozen)
- Rows 7–200: Transaction rows (194 rows of data entry space)

### Columns
| Col | Header | Type | Details |
|-----|--------|------|---------|
| A | Date | Date | User enters date; format MM/DD/YYYY |
| B | Description | Text | Free text description |
| C | Category | Dropdown | From LOOKUP!A:A — 20 expense + 3 income categories |
| D | Type | Dropdown | "Income" or "Expense" — strict validation |
| E | Amount | Currency ($#,##0.00) | Always positive; Type determines direction |
| F | Month | Formula | `=IF(A7="","",TEXT(A7,"MMM"))` — auto-populated, hidden from user editing |
| G | Month# | Formula | `=IF(A7="","",MONTH(A7))` — numeric month, used by summary tabs |

Column F and G: light gray text, locked appearance (not editable — formula cells).

### Sample Data (pre-loaded, 42 rows)
**January 2026 (15 rows):**
- 2026-01-01, Paycheck, Salary, Income, $3,500
- 2026-01-03, Rent, Housing, Expense, $1,200
- 2026-01-05, Groceries - Walmart, Groceries, Expense, $187.43
- 2026-01-08, Electric Bill, Utilities, Expense, $94.20
- 2026-01-10, Netflix, Subscriptions, Expense, $15.99
- 2026-01-10, Spotify, Subscriptions, Expense, $10.99
- 2026-01-12, Gas - Shell, Transportation, Expense, $52.30
- 2026-01-15, Paycheck, Salary, Income, $3,500
- 2026-01-18, Dinner out - Olive Garden, Dining Out, Expense, $67.45
- 2026-01-20, Groceries - Kroger, Groceries, Expense, $143.22
- 2026-01-22, Internet Bill, Utilities, Expense, $59.99
- 2026-01-25, Amazon purchase, Shopping, Expense, $34.99
- 2026-01-26, Coffee shop, Dining Out, Expense, $23.40
- 2026-01-28, Car Insurance, Auto, Expense, $120.00
- 2026-01-30, Gym membership, Health & Fitness, Expense, $35.00

**February 2026 (14 rows):**
- 2026-02-01, Paycheck, Salary, Income, $3,500
- 2026-02-03, Rent, Housing, Expense, $1,200
- 2026-02-06, Groceries - Walmart, Groceries, Expense, $204.17
- 2026-02-08, Electric Bill, Utilities, Expense, $87.50
- 2026-02-10, Netflix, Subscriptions, Expense, $15.99
- 2026-02-10, Spotify, Subscriptions, Expense, $10.99
- 2026-02-14, Valentine's Dinner, Dining Out, Expense, $112.80
- 2026-02-15, Paycheck, Salary, Income, $3,500
- 2026-02-17, Gas - Shell, Transportation, Expense, $48.60
- 2026-02-20, Groceries - Target, Groceries, Expense, $167.34
- 2026-02-22, Internet Bill, Utilities, Expense, $59.99
- 2026-02-24, New shoes, Clothing, Expense, $79.99
- 2026-02-26, Coffee shop, Dining Out, Expense, $31.20
- 2026-02-28, Gym membership, Health & Fitness, Expense, $35.00

**March 2026 (13 rows — Dining Out over budget to trigger amber/red conditional formatting):**
- 2026-03-01, Paycheck, Salary, Income, $3,500
- 2026-03-03, Rent, Housing, Expense, $1,200
- 2026-03-05, Groceries - Walmart, Groceries, Expense, $221.88
- 2026-03-07, Electric Bill, Utilities, Expense, $101.40
- 2026-03-10, Netflix, Subscriptions, Expense, $15.99
- 2026-03-10, Spotify, Subscriptions, Expense, $10.99
- 2026-03-12, Gas - Shell, Transportation, Expense, $61.40
- 2026-03-15, Paycheck, Salary, Income, $3,500
- 2026-03-16, Birthday dinner - group, Dining Out, Expense, $89.50
- 2026-03-19, Lunch - work meeting, Dining Out, Expense, $43.20
- 2026-03-22, Groceries - Kroger, Groceries, Expense, $188.65
- 2026-03-25, Coffee + snacks, Dining Out, Expense, $28.75
- 2026-03-28, Internet Bill, Utilities, Expense, $59.99

---

## Tab 3: DEBT PAYOFF (sheetId: 3)

### Layout
- Row 1: Banner — "💳 DEBT PAYOFF PLANNER" (navy)
- Row 2: Strategy selector — "Payoff Method:" label + B2 dropdown cell (Snowball / Avalanche), prominent styling
- Row 3: Extra Monthly Payment input — "Extra $/ month toward debt:" label + B3 input cell (yellow)
- Row 4: Summary — Total Debt, Est. Debt-Free Date, Total Interest Remaining
- Row 6: Column headers (frozen)
- Rows 7–16: 10 debt rows
- Rows 18–22: "What If" extra payment simulator — user enters a hypothetical extra amount → shows new payoff date and interest saved

### Columns (rows 7–16)
| Col | Header | Type | Details |
|-----|--------|------|---------|
| A | Debt Name | Text | e.g., "Credit Card - Chase" |
| B | Current Balance | Currency | User inputs |
| C | Interest Rate | Percentage (0.00%) | User inputs (e.g., 0.22 for 22%) |
| D | Minimum Payment | Currency | User inputs |
| E | Payoff Order | Formula | Rank based on strategy in B2. Snowball: RANK by balance ascending. Avalanche: RANK by interest rate descending. `=IF(B7="","",IF($B$2="Snowball", RANK(B7,B$7:B$16,1), RANK(C7,C$7:C$16,0)))` |
| F | Monthly Payment | Formula | `=IF(B7="","",IF(E7=1, D7+$B$3, D7))` — extra payment goes to #1 priority debt |
| G | Months to Payoff | Formula | `=IF(B7="","",IFERROR(NPER(C7/12, -F7, B7),0))` |
| H | Payoff Date | Formula | `=IF(G7="","",EDATE(TODAY(), ROUND(G7,0)))` formatted as MMM YYYY |
| I | Total Interest | Formula | `=IF(B7="","",IFERROR((F7*G7)-B7, 0))` |
| J | Progress Bar | Formula | `=IF(B7="","",REPT("█",MIN(10,ROUND((1-B7/MAX(B$7:B$16))*10,0)))&REPT("░",MAX(0,10-MIN(10,ROUND((1-B7/MAX(B$7:B$16))*10,0)))))` |

### Sample Debts (pre-loaded)
1. Credit Card - Chase | $4,200 | 22% | $105/mo
2. Car Loan | $8,500 | 6.5% | $245/mo
3. Student Loan | $18,000 | 4.5% | $195/mo
(Rows 4–10 left empty for user to fill)

### What If Simulator (rows 18–22)
- B19: "Extra payment amount" input (yellow cell)
- Shows: New payoff date for debt #1, Months saved, Interest saved
- Formula: `=IFERROR(NPER(C7/12, -(D7+B19), B7),0)`

---

## Tab 4: SAVINGS GOALS (sheetId: 4)

### Layout
- Row 1: Banner — "🎯 SAVINGS GOALS" (navy)
- Row 2: Summary — Total saved across all goals, Total target across all goals, Overall % funded
- Row 4: Column headers (frozen)
- Rows 5–12: 8 savings goal rows
- Row 14: Overall progress bar (spans full width)

### Columns (rows 5–12)
| Col | Header | Type | Details |
|-----|--------|------|---------|
| A | Goal Name | Text | e.g., "Emergency Fund" |
| B | Target Amount | Currency | User inputs |
| C | Current Amount | Currency | User inputs — update as they save |
| D | Target Date | Date | User inputs |
| E | % Funded | Formula | `=IF(B5="","",IFERROR(C5/B5,0))` formatted as 0% |
| F | Monthly Needed | Formula | `=IF(OR(B5="",D5=""),"",IFERROR((B5-C5)/MAX(1,DATEDIF(TODAY(),D5,"M")),0))` |
| G | On Track? | Formula | `=IF(E5="","",IF(E5>=1,"✅ Funded!",IF(F5<=0,"✅ On Track","⚠️ "&TEXT(F5,"$#,##0")&"/mo needed")))` |
| H | Progress Bar | Formula | `=IF(B5="","",REPT("█",MIN(10,ROUND(E5*10,0)))&REPT("░",MAX(0,10-MIN(10,ROUND(E5*10,0)))))` |

### Sample Goals (pre-loaded)
1. Emergency Fund | $10,000 | $3,400 | 2026-12-31
2. Vacation Fund | $3,500 | $1,200 | 2026-07-01
3. Down Payment | $25,000 | $8,750 | 2028-01-01
(Rows 4–8 empty for user)

### Conditional Formatting
- % Funded ≥ 100%: green background
- % Funded 50–99%: amber background
- % Funded < 50%: light red background

---

## Tab 5: SINKING FUNDS (sheetId: 5)

### Layout
- Row 1: Banner — "🪣 SINKING FUNDS" (navy)
- Row 2: Master summary — Total across all funds: budgeted vs. saved vs. % funded
- Row 4: Column headers (frozen)
- Rows 5–16: 12 sinking fund rows
- Row 18: Overall "all funds % funded" progress bar

### Columns (rows 5–16)
| Col | Header | Type | Details |
|-----|--------|------|---------|
| A | Fund Name | Text | e.g., "Car Insurance" |
| B | Target Amount | Currency | Total amount needed |
| C | Current Balance | Currency | Amount saved so far |
| D | Target Date | Date | When the money is needed |
| E | Monthly Contribution | Formula | `=IF(OR(B5="",D5=""),"",IFERROR((B5-C5)/MAX(1,DATEDIF(TODAY(),D5,"M")),0))` — how much to save per month |
| F | % Funded | Formula | `=IF(B5="","",IFERROR(C5/B5,0))` |
| G | Runway Bar | Formula | `=IF(B5="","",REPT("█",MIN(10,ROUND(F5*10,0)))&REPT("░",MAX(0,10-MIN(10,ROUND(F5*10,0)))))` |

### Sample Funds (pre-loaded)
1. Car Insurance (Semi-Annual) | $720 | $360 | 2026-07-01
2. Christmas Gifts | $1,200 | $300 | 2026-12-01
3. Home Repairs | $2,000 | $650 | 2026-12-31
4. Medical Deductible | $1,500 | $500 | 2026-12-31
5. Gifts & Birthdays | $600 | $150 | 2026-12-31
(Rows 10–16 empty)

---

## Tab 6: NET WORTH (sheetId: 6)

### Layout
- Row 1: Banner — "📈 NET WORTH TRACKER" (navy)
- Row 2: Current net worth (latest month), YTD change, YTD % change
- Rows 4–5: Month header row + column labels
- Rows 6–15: Asset rows (10 asset categories)
- Row 16: Total Assets (auto-sum)
- Rows 18–24: Liability rows (7 liability categories)
- Row 25: Total Liabilities (auto-sum)
- Row 27: NET WORTH = Total Assets − Total Liabilities (bold, colored)
- Row 28: Month-over-Month Change (formula)
- Row 29: MoM Change % (formula)
- Rows 31–50: Embedded line chart

### Columns (A = category label, B–M = Jan–Dec)
**Asset rows:**
- Checking Account(s)
- Savings Account(s)
- Investment/Brokerage
- Retirement (401k/IRA)
- Home Value
- Vehicle(s) Value
- Cash
- Crypto / Other Investments
- Other Assets 1
- Other Assets 2

**Liability rows:**
- Credit Card Balances
- Car Loan(s)
- Student Loan(s)
- Mortgage
- Personal Loan(s)
- Medical Debt
- Other Debt

### Sample Data (pre-loaded, 12 months trending upward)
Net worth starts at ~$28,000 in Jan 2026 and rises to ~$34,500 by Dec 2026.

### Chart
- Line chart — Net Worth over 12 months
- Data: Row 27, columns B–M
- Colors: Navy line (#2C3E6B), green fill below line
- Position: Anchored at A31, ~600×300px
- Title: "Net Worth Trend — 2026"

### Conditional Formatting
- MoM Change row: positive = green bg, negative = red bg

---

## Tab 7: CASH ENVELOPES (sheetId: 7)

### Layout
- Row 1: Banner — "💵 DIGITAL CASH ENVELOPES" (navy)
- Row 2: Summary — Total budgeted, total spent, total remaining
- Row 4: Column headers (frozen)
- Rows 5–14: 10 envelope rows
- Row 16: Totals row

### Columns
| Col | Header | Type | Details |
|-----|--------|------|---------|
| A | Envelope Name | Text | e.g., "Groceries" |
| B | Budget | Currency | How much allocated this month |
| C | Spent | Currency | User updates as they spend |
| D | Remaining | Formula | `=IF(B5="","",B5-C5)` |
| E | % Used | Formula | `=IF(B5="","",IFERROR(C5/B5,0))` |
| F | Status Bar | Formula | `=IF(B5="","",REPT("█",MIN(10,ROUND(E5*10,0)))&REPT("░",MAX(0,10-MIN(10,ROUND(E5*10,0)))))` |
| G | Status | Formula | `=IF(D5="","",IF(D5>=0,"✅ "&TEXT(D5,"$#,##0.00")&" left","🔴 Over by "&TEXT(ABS(D5),"$#,##0.00")))` |

### Sample Envelopes (pre-loaded)
1. Groceries | $500 | $324.65
2. Dining Out | $200 | $190.85
3. Entertainment | $150 | $47.00
4. Gas / Transportation | $180 | $92.30
5. Personal Care | $100 | $38.50
(Rows 10–14 empty)

### Conditional Formatting
- Remaining ≥ 0: row background white
- Remaining < 0: row background light red (#FADBD8)
- % Used ≥ 90%: % cell amber (#FAD7A0)
- % Used ≥ 100%: % cell red (#E74C3C), white text

---

## Tabs 8–19: Monthly Summaries — JAN through DEC (sheetIds: 8–19)

Each hidden tab follows identical structure. Example shown for JAN (sheetId: 8):

### Columns / Rows
- B1: Month name ("January")
- B2: Total Income for month: `=SUMPRODUCT(('BUDGET LOG'!G$7:G$200=1)*('BUDGET LOG'!D$7:D$200="Income")*('BUDGET LOG'!E$7:E$200))`
- B3: Total Expenses for month: `=SUMPRODUCT(('BUDGET LOG'!G$7:G$200=1)*('BUDGET LOG'!D$7:D$200="Expense")*('BUDGET LOG'!E$7:E$200))`
- B4: Surplus/Deficit: `=B2-B3`
- B5: Savings Amount: `=SUMPRODUCT(('BUDGET LOG'!G$7:G$200=1)*('BUDGET LOG'!C$7:C$200="Savings Transfer")*('BUDGET LOG'!E$7:E$200))`
- Rows 7+: Category breakdown using SUMPRODUCT per category from LOOKUP tab

The number `1` in `G$7:G$200=1` is the month number (1 for JAN, 2 for FEB, etc., up to 12 for DEC).

HEALTH SCORE tab pulls from these hidden tabs:
- `=SUM(JAN!B2, FEB!B2, MAR!B2, ...)` for YTD income
- `=SUM(JAN!B3, FEB!B3, MAR!B3, ...)` for YTD expenses

---

## Tab 20: LOOKUP (sheetId: 20) — Hidden

### Column A: Expense Categories (20 categories)
Housing, Utilities, Groceries, Dining Out, Transportation, Auto, Health & Fitness, Subscriptions, Shopping, Entertainment, Personal Care, Clothing, Education, Gifts & Donations, Travel, Insurance, Savings Transfer, Investments, Other Expense, Salary

### Column B: Budget Bucket Mapping
Maps each category to: Needs / Wants / Savings (for potential 50/30/20 display)

### Column C: Score Thresholds
Labels for Health Score conditional formatting reference

---

## Visual Design

### Color Palette
| Use | Hex | RGB (0–1 float for API) |
|-----|-----|------------------------|
| Navy primary | `#2C3E6B` | (0.173, 0.243, 0.420) |
| Success green | `#27AE60` | (0.153, 0.682, 0.376) |
| Warning amber | `#E67E22` | (0.902, 0.494, 0.133) |
| Danger red | `#E74C3C` | (0.906, 0.298, 0.235) |
| Light background | `#F7F8FA` | (0.969, 0.973, 0.980) |
| Card background | `#EEF1F8` | (0.933, 0.945, 0.973) |
| Input cell yellow | `#FFF9C4` | (1.0, 0.976, 0.769) |
| White | `#FFFFFF` | (1.0, 1.0, 1.0) |
| Body text | `#2C3E50` | (0.173, 0.243, 0.314) |

### Typography
- Banner rows: 14–16pt, bold, white text on navy background
- Section headers: 11pt, bold, navy text on card-bg
- Body data: 10pt, regular, body text color
- Input cells: 10pt, body text, yellow background
- Progress bars: Courier New or similar monospace for consistent bar width

### Number Formats
- Currency: `$#,##0.00`
- Percentage: `0.0%`
- Date: `MMM D, YYYY`
- Month-year: `MMM YYYY`
- Score (integer): `0`

### Column Widths (key columns)
- Name/label columns: 180px
- Currency columns: 120px
- Date columns: 110px
- Progress bar columns: 140px
- Status columns: 160px
- Month columns (NET WORTH): 80px each

### Frozen Rows
- All tabs: Freeze row 1 (banner) + row with column headers
- BUDGET LOG: Freeze rows 1–6 (banner + input panel + headers)
- NET WORTH: Freeze column A (category labels) + row 5 (month headers)

---

## Charts

### Chart 1 — Net Worth Trend (NET WORTH tab)
- Type: Line chart
- Data: Row 27, columns B–M (Jan–Dec net worth values)
- Header row: Row 5 (month names)
- Series color: `#2C3E6B`
- Background fill under line: light navy at 20% opacity (use area chart style)
- Position: Anchored at A31, 600×300px
- Title: "Net Worth — 2026"
- Y-axis: Currency format
- Legend: None (single series)

### Chart 2 — Health Score Trend (HEALTH SCORE tab, optional inline)
- Type: SPARKLINE formula per category card row — `=SPARKLINE(range, {"charttype","line";"color","#2C3E6B"})`
- Shows the trend of each category score across available months
- Inline in the card, not a standalone chart object

---

## Conditional Formatting Rules (priority order)

### BUDGET LOG (column E — Amount)
1. Type = "Income": green text `#27AE60`
2. Type = "Expense": no special formatting (default)

### HEALTH SCORE (score cell)
1. Value ≥ 80: bg `#27AE60`, white text
2. Value 60–79: bg `#E67E22`, white text
3. Value < 60: bg `#E74C3C`, white text

### SAVINGS GOALS (column E — % Funded)
1. Value ≥ 1: bg `#D5F5E3` (light green)
2. Value ≥ 0.5: bg `#FAD7A0` (light amber)
3. Value < 0.5: bg `#FADBD8` (light red)

### SINKING FUNDS (column F — % Funded)
Same rules as Savings Goals.

### CASH ENVELOPES (column D — Remaining)
1. Value < 0: entire row bg `#FADBD8`
2. Column E (% Used) ≥ 1.0: cell bg `#E74C3C`, white text
3. Column E (% Used) ≥ 0.9: cell bg `#FAD7A0`

### NET WORTH (row 28 — MoM Change)
1. Value > 0: bg `#D5F5E3`
2. Value < 0: bg `#FADBD8`
3. Value = 0: bg `#EEF1F8`

### DEBT PAYOFF (column I — Total Interest)
1. Color scale: low interest = green, high interest = red (gradient)

---

## Data Validation (Dropdowns)

### BUDGET LOG Column C (Category) — from LOOKUP!A2:A21
- Type: ONE_OF_RANGE
- Strict: true (reject invalid input)
- Applied to: C7:C200

### BUDGET LOG Column D (Type)
- Type: ONE_OF_LIST — ["Income", "Expense"]
- Strict: true
- Applied to: D7:D200

### DEBT PAYOFF B2 (Strategy)
- Type: ONE_OF_LIST — ["Snowball", "Avalanche"]
- Strict: true
- Single cell

---

## Etsy Listing

### Title (140 chars max)
`Budget Spreadsheet Google Sheets | All-in-One Budget Planner Debt Tracker Savings Dashboard Net Worth Template 2026`

### 13 SEO Tags
1. budget spreadsheet
2. google sheets budget
3. debt payoff tracker
4. savings goal tracker
5. net worth tracker
6. sinking funds spreadsheet
7. cash envelope system
8. budget planner 2026
9. debt snowball spreadsheet
10. financial dashboard
11. budget template google sheets
12. personal finance spreadsheet
13. all in one budget planner

### Listing Description (full)
```
💙 ALL-IN-ONE FINANCIAL DASHBOARD — Google Sheets Template

Take control of your money with ONE powerful spreadsheet that replaces 6 separate tools. Whether you're budgeting paycheck to paycheck, crushing debt, or building wealth — this dashboard does it all.

✅ WHAT'S INCLUDED (8 Tabs):

📊 FINANCIAL HEALTH SCORE — Your personal finance report card. Auto-calculates a score from 0–100 across 5 categories so you know exactly where you stand at a glance.

💰 BUDGET LOG — Log every transaction once. Your entire budget updates automatically. No duplicating data across tabs.

💳 DEBT PAYOFF PLANNER — Choose Snowball (Dave Ramsey method) OR Avalanche strategy with one click. Automatically ranks your debts, calculates payoff dates, and shows total interest saved.

🎯 SAVINGS GOALS — Up to 8 goals with auto-calculated monthly contribution targets. Visual progress bars show how close you are.

🪣 SINKING FUNDS — Never be surprised by irregular expenses again. Set a target + date → get the exact monthly amount to save.

📈 NET WORTH TRACKER — Watch your wealth grow month by month with a beautiful chart. Track all assets and liabilities in one place.

💵 CASH ENVELOPES — Digital version of the cash stuffing method. Set budgets per category, track spending, see what's left.

🚀 EASY TO USE:
• Pre-loaded with sample data so you can see it working immediately
• Color-coded: green = on track, amber = watch out, red = needs attention
• Step-by-step START HERE tab — set up in 5 minutes
• No formulas to edit — just fill in your numbers

📋 DETAILS:
• Works in Google Sheets (free) — no Excel or paid software needed
• Instant access via Google Sheets link after purchase
• 2026 ready — use for any year
• Desktop + laptop optimized

⭐ PERFECT FOR:
• Anyone living paycheck to paycheck who wants a plan
• Couples managing shared finances
• Dave Ramsey Baby Steps followers
• Anyone working toward debt freedom or their first $10K saved

💬 Questions? Message me — I respond within 24 hours.
```

---

## Mockup Image Style

**Recommended Freepik mockup:** MacBook Pro + iPad side-by-side flat lay on a clean white desk with subtle shadows.

**What to show on screen:**
- MacBook: HEALTH SCORE tab (the 5 category cards, overall score badge)
- iPad: DEBT PAYOFF tab (the ranked debt list with progress bars visible)

**Overlay text on mockup:**
- "All-in-One Budget Dashboard"
- "Google Sheets • Instant Download"

**Additional listing images (5 total):**
1. Hero: MacBook + iPad mockup (HEALTH SCORE visible)
2. Close-up: BUDGET LOG tab
3. Close-up: DEBT PAYOFF tab with snowball/avalanche toggle visible
4. Feature grid: 6 icons showing each tab with one-line description
5. "Before/After": messy spreadsheet vs. clean dashboard (text-based graphic)

---

## Build Order for GWS CLI

1. Create spreadsheet with all 21 sheets (named, hidden where applicable)
2. Populate LOOKUP tab (categories, mappings)
3. Write all cell data and formulas to each visible tab
4. Write formulas to all 12 hidden monthly summary tabs
5. Apply all formatting (colors, fonts, borders, column widths)
6. Add data validation (dropdowns, checkboxes)
7. Add conditional formatting rules
8. Add net worth line chart
9. Freeze rows/columns on all tabs
10. Add sample data to BUDGET LOG (triggers all formula chains)
11. Add sample data to DEBT PAYOFF, SAVINGS GOALS, SINKING FUNDS, NET WORTH, CASH ENVELOPES
