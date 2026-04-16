# Design Spec: Budget Template — Etsy Digital Product (EN / FR / AR)

**Date:** 2026-04-15
**Owner:** Boubacar Barry (bokar83@gmail.com)
**Reference:** prettyarrow.com clone · Clone Targets DB score 38/40
**Etsy price:** $9 / 9 € / 9 $ per listing (3 separate listings)

---

## Overview

A clean, premium Google Sheets monthly budget template built in the Warm Terracotta visual style. Sold as 3 separate Etsy listings — one per language (EN, FR, AR) — each with its own SEO-optimized title, tags, and description targeting that market's actual search terms.

This is a v1 "build your muscles" product. Scope is deliberately minimal: 3 tabs, beautiful design, pre-loaded sample data. Ship fast, collect reviews, then expand.

**What failed last time:** Dark navy background, neon teal text, clashing donut chart colors. It looked like a developer tool. The buyer is a woman 25–45 managing household finances. She buys with her eyes.

---

## Visual Design System

### Color Palette

| Role | Color | Hex |
|------|-------|-----|
| Background | Warm cream | `#FDF6F0` |
| Header / accent | Terracotta | `#C8956C` |
| Danger / overspend | Coral | `#E07A5F` |
| Savings / positive | Sage green | `#81B29A` |
| Card background | White | `#FFFFFF` |
| Progress bar bg | Pale terracotta | `#FDF0E8` |
| Savings bar bg | Pale sage | `#EEF5F1` |
| Body text | Dark charcoal | `#333333` |
| Muted text | Light gray | `#999999` |
| Input cells | Pale yellow | `#FFF9C4` |

**Hard rule:** No dark backgrounds. No neon colors. No default Google Sheets chart colors (blue/red/yellow/green primary set). Every chart uses the palette above only.

### Typography

- **Tab banners:** 12pt, bold, white text on terracotta (`#C8956C`) background
- **Section headers:** 10pt, bold, terracotta text on white
- **KPI values:** 14pt, bold, color-coded by role (terracotta/coral/sage)
- **Labels:** 8pt, uppercase, letter-spacing 0.5px, muted gray
- **Body / data rows:** 10pt, regular, dark charcoal
- **Input cells:** 10pt, pale yellow background (`#FFF9C4`)
- **Progress bars:** Courier New or similar monospace (`=REPT("█",...) & REPT("░",...)`)

### Card Style

Every section is a "card": white background, 4–6px border-radius, subtle shadow via borders (`border: 1px solid #F5E6D8`). No thick dark borders. No full-row color fills except the header banner.

### Column Widths

- Label columns: 160px
- Currency columns: 110px
- Date columns: 100px
- Progress bar columns: 130px
- Status columns: 150px

---

## Tab Structure (3 tabs)

| # | Tab Name (EN) | Tab Name (FR) | Tab Name (AR) | Visible |
|---|---------------|---------------|---------------|---------|
| 0 | BUDGET | BUDGET | الميزانية | ✅ |
| 1 | SAVINGS | ÉPARGNE | الادخار | ✅ |
| 2 | DASHBOARD | TABLEAU DE BORD | لوحة التحكم | ✅ |

Tab colors: all use terracotta tab color (`#C8956C` text or tab background where Google Sheets allows).

---

## Tab 0: BUDGET

### Purpose
Monthly income and expense tracker. The source of truth. All numbers feed into the Dashboard.

### Layout

- **Row 1:** Merged banner — tab name in bold white on terracotta, full width
- **Row 2:** 3 KPI summary cells (Income / Spent / Remaining) — auto-calculated, color-coded
- **Row 3:** Empty spacer
- **Row 4:** Column headers (frozen rows 1–4)
- **Rows 5–54:** 50 transaction rows (enough for any month)

### Row 2 KPI Cells

| Cell | Label | Formula | Color |
|------|-------|---------|-------|
| B2 | Income / Revenus / الدخل | `=SUMIF(D5:D54,"Income",E5:E54)` | Terracotta `#C8956C` |
| D2 | Spent / Dépenses / المصروف | `=SUMIF(D5:D54,"Expense",E5:E54)` | Coral `#E07A5F` |
| F2 | Remaining / Solde / المتبقي | `=B2-D2` | Sage green `#81B29A` (positive) / Coral (negative) |

### Transaction Columns

| Col | Header (EN/FR/AR) | Type | Details |
|-----|-------------------|------|---------|
| A | Date / Date / التاريخ | Date | MM/DD/YYYY |
| B | Description | Text | Free text |
| C | Category / Catégorie / الفئة | Dropdown | From named range CATEGORIES |
| D | Type | Dropdown | "Income" / "Expense" (hidden from AR version — use Arabic equivalents) |
| E | Amount / Montant / المبلغ | Currency | Always positive |

### Categories

**EN:** Housing, Food, Transport, Utilities, Subscriptions, Dining Out, Health, Shopping, Entertainment, Personal Care, Education, Savings Transfer, Income, Other

**FR:** Logement, Alimentation, Transport, Factures, Abonnements, Restaurants, Santé, Shopping, Loisirs, Soins personnels, Éducation, Virement épargne, Revenu, Autre

**AR:** السكن, الطعام, المواصلات, الفواتير, الاشتراكات, المطاعم, الصحة, التسوق, الترفيه, العناية الشخصية, التعليم, تحويل للادخار, دخل, أخرى

### Conditional Formatting

- Remaining (F2): green bg `#EEF5F1` if positive, coral bg `#FDE8E4` if negative
- Amount column (E): terracotta text for Income rows, coral text for Expense rows

### Sample Data (pre-loaded, 15 rows — April 2026)

**EN version (USD):**
1. 04/01, Paycheck, Income, $3,500
2. 04/03, Rent, Housing, Expense, $1,200
3. 04/05, Groceries, Food, Expense, $187
4. 04/08, Electric bill, Utilities, Expense, $94
5. 04/10, Netflix, Subscriptions, Expense, $16
6. 04/12, Gas, Transport, Expense, $52
7. 04/15, Paycheck, Income, $3,500
8. 04/17, Dinner out, Dining Out, Expense, $67
9. 04/20, Groceries, Food, Expense, $143
10. 04/22, Internet, Utilities, Expense, $60
11. 04/24, Amazon, Shopping, Expense, $35
12. 04/26, Coffee, Dining Out, Expense, $23
13. 04/28, Car insurance, Transport, Expense, $120
14. 04/29, Gym, Health, Expense, $35
15. 04/30, Savings transfer, Savings Transfer, Expense, $500

**FR version (EUR, Côte d'Ivoire context):**
Same structure, amounts in EUR, categories in French, descriptions localized (e.g., "Loyer" not "Rent", "Orange Money" for telecom).

**AR version (MAD — Moroccan dirham):**
Same structure, amounts in MAD, RTL layout (`dir="rtl"` equivalent in sheet — right-align all text, reverse column order A→E becomes right-to-left visually).

---

## Tab 1: SAVINGS

### Purpose
Up to 5 savings goals with progress bars. Shows how close the user is to each goal and how much to save per month.

### Layout

- **Row 1:** Banner
- **Row 2:** Summary — Total saved across all goals / Total target / Overall % funded
- **Row 3:** Spacer
- **Row 4:** Column headers (frozen rows 1–4)
- **Rows 5–9:** 5 savings goal rows
- **Row 11:** Overall progress bar (full width merged cell, REPT formula)

### Columns

| Col | Header (EN) | Type | Formula |
|-----|-------------|------|---------|
| A | Goal | Text | User input |
| B | Target | Currency | User input |
| C | Saved | Currency | User input |
| D | Target Date | Date | User input |
| E | % Funded | % | `=IFERROR(C5/B5,0)` |
| F | Monthly Needed | Currency | `=IFERROR((B5-C5)/MAX(1,DATEDIF(TODAY(),D5,"M")),0)` |
| G | Progress | Text (bar) | `=REPT("█",MIN(10,ROUND(E5*10,0)))&REPT("░",MAX(0,10-MIN(10,ROUND(E5*10,0))))` |
| H | Status | Text | `=IF(E5>=1,"✓ Funded!",IF(F5<=0,"✓ On track","→ "&TEXT(F5,"$#,##0")&"/mo"))` |

### Conditional Formatting

- % Funded ≥ 100%: row bg `#EEF5F1` (light sage)
- % Funded 50–99%: row bg `#FDF6F0` (light cream)
- % Funded < 50%: no fill (white)

### Sample Goals (EN, pre-loaded)

1. Emergency Fund | $5,000 | $1,800 | 2026-12-31
2. Vacation | $2,000 | $650 | 2026-08-01
3. New Laptop | $1,200 | $400 | 2026-07-01
(Rows 4–5 empty)

---

## Tab 2: DASHBOARD

### Purpose
Visual summary that serves as the Etsy listing thumbnail. 2-column layout: KPI cards on the left, CSS donut + savings progress on the right.

### Layout

- **Row 1:** Banner — "DASHBOARD · [Month] [Year]" (auto-populated with `=TEXT(TODAY(),"MMMM YYYY")`)
- **Rows 2–10:** Left column — 3 stacked KPI cards
- **Rows 2–6:** Right column — Donut-style % breakdown (REPT-based, not a chart object)
- **Rows 7–10:** Right column — Top savings goal progress

**No Google Sheets chart objects.** All visuals are built from cell formatting, REPT bars, and conditional formatting. This prevents the ugly default chart colors that ruined the last build.

### Left Column — KPI Cards (rows 2–10, cols A–D)

Each card spans 2 rows, merged cells, card-style border:

**Card 1 — Income**
- Label: "INCOME / REVENUS / الدخل" (8pt, uppercase, muted)
- Value: `=BUDGET!B2` (14pt bold, terracotta)
- Sub-label: "This month" (8pt, muted)

**Card 2 — Spent**
- Label: "SPENT / DÉPENSES / المصروف"
- Value: `=BUDGET!D2` (14pt bold, coral if > 80% of income, sage if ≤ 80%)
- Sub-label: `=TEXT(BUDGET!D2/BUDGET!B2*100,"0")&"% of income"` (8pt, muted)

**Card 3 — Remaining**
- Label: "REMAINING / SOLDE / المتبقي"
- Value: `=BUDGET!F2` (14pt bold, sage if positive, coral if negative)
- Sub-label: `=IF(BUDGET!F2>=0,"✓ Under budget","⚠ Over budget")` (8pt)

### Right Column — Spending Split (rows 2–6, cols F–J)

REPT-based visual showing spending vs savings split. No chart object.

```
Spending   ████████░░  62%
Savings    ████░░░░░░  38%
```

Formulas:
- Spending %: `=BUDGET!D2/BUDGET!B2`
- Savings %: `=1-(BUDGET!D2/BUDGET!B2)`
- Bar: `=REPT("█",ROUND(pct*10,0))&REPT("░",10-ROUND(pct*10,0))`

### Right Column — Top Savings Goal (rows 7–10, cols F–J)

Shows the first savings goal from the SAVINGS tab:
- Goal name: `=SAVINGS!A5`
- Progress bar: `=SAVINGS!G5`
- Amount: `=SAVINGS!C5&" / "&SAVINGS!B5&" · "&TEXT(SAVINGS!E5,"0%")`

---

## Language Localization Rules

### FR (French)

- Currency format: `# ##0,00 €` (European style — space as thousands separator, comma as decimal)
- Market context: France uses Euro. Ivory Coast / Senegal use FCFA (XOF) — offer FCFA as an alternative in the sample data note in the listing description.
- Tone: informal "tu" (consumer product, personal finance)
- Date format: `DD/MM/YYYY`
- All labels, headers, dropdown values, status messages, and sample data descriptions in French

### AR (Arabic)

- RTL layout: Sheet direction right-to-left. Column A is rightmost visually.
- Currency: Moroccan dirham (MAD) as default in sample data. Note in listing: works for any Arab country currency.
- All text in Modern Standard Arabic (MSA) — not dialect
- Numbers: Western Arabic numerals (1 2 3, not ١ ٢ ٣) — easier for spreadsheet formulas
- Date format: `DD/MM/YYYY` (universal)
- Progress bar characters: same REPT formula — Unicode blocks render LTR even in RTL sheets, which is acceptable

---

## Etsy Listings

### EN Listing

**Title:** `Monthly Budget Planner Google Sheets Template | Budget Tracker Spreadsheet | Instant Download 2026`

**Tags (13):** budget planner, google sheets budget, monthly budget template, budget spreadsheet, expense tracker, spending tracker, budget tracker 2026, personal finance spreadsheet, google sheets template, budget worksheet, income expense tracker, financial planner, printable budget

**Price:** $9

**Description excerpt:**
```
Take control of your money with this clean, easy-to-use Google Sheets budget template.

✅ WHAT'S INCLUDED (3 tabs):
📋 BUDGET — Log income and expenses by category. Balance calculates automatically.
🎯 SAVINGS — Track up to 5 savings goals with visual progress bars.
📊 DASHBOARD — Beautiful visual summary: income vs. spending at a glance.

✨ FEATURES:
• Pre-loaded with sample data — works immediately after download
• Color-coded: green = on track, orange = watch out
• No formulas to edit — just fill in your numbers
• Works in Google Sheets (free) — no Excel needed
• Instant access via Google Sheets link after purchase
```

### FR Listing

**Title:** `Modèle Budget Mensuel Google Sheets | Tableau de Bord Finances Personnelles | Téléchargement Immédiat`

**Tags (13):** modele budget mensuel, budget mensuel google sheets, tableau de bord budget, suivi depenses, planificateur budget, feuille de calcul budget, budget familial, gestion budget personnel, modele google sheets, tracker depenses, budget 2026, finance personnelle, suivi finances

**Price:** 9 €

### AR Listing

**Title:** `نموذج ميزانية شهرية Google Sheets | متابعة المصروفات | تحميل فوري`

**Tags (13):** ميزانية شهرية, نموذج ميزانية, متابعة مصروفات, تخطيط مالي, جدول بيانات, google sheets عربي, ادارة المال, توفير المال, نموذج مالي, تتبع النفقات, ميزانية 2026, تخطيط ميزانية, مصاريف شهرية

**Price:** $9 (USD — Etsy does not support MAD)

---

## Deliverables

1. **3 Google Sheets files** — one per language, shared as "view only" links
2. **3 Etsy listings** — EN, FR, AR — each with title, description, 13 tags, price
3. **3 Etsy thumbnail images** — screenshot of Dashboard tab, cropped to 2000×2000px, annotated with product name overlay

---

## Build Order

1. Build EN version fully (all 3 tabs, sample data, formatting, conditional formatting)
2. Verify EN: check all formulas work with sample data, dashboard looks clean
3. Duplicate EN → FR: translate all strings, update sample data to EUR/French context
4. Duplicate EN → AR: translate all strings, flip to RTL, update sample data to MAD
5. Screenshot each Dashboard tab for Etsy thumbnail
6. Run `seo-strategy` skill on each listing draft to validate keyword choices
7. Create 3 Etsy listings
8. Update Notion Clone Targets record: Status → Building

---

## What NOT to build in v1

- No debt tracker tab
- No net worth tracker
- No annual overview
- No chart objects (use REPT bars only)
- No currency switcher dropdown
- No password protection
- No print formatting
- No PDF export

All of the above are v2 features, after the first sale proves the design.
