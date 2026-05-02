# Freelancer Financial Tracker: Planning Document

## Product Overview
A sellable Google Sheets template for freelancers to manage their business finances.
**Target Price:** $15 on Etsy
**Color Scheme:** Dark Navy (#1B2A4A) and Gold (#D4AF37)

---

## Sheet Structure

### 1. Dashboard (Tab 1)
- KPI summary cards: Total Income YTD, Total Expenses YTD, Net Profit YTD, Outstanding Invoices
- Monthly Income vs Expenses bar/column chart (using SPARKLINE)
- Top clients by revenue (mini table)
- Current month snapshot: Income, Expenses, Profit, Profit Margin %
- Quick stats: Paid invoices count, Unpaid invoices count

### 2. Monthly P&L (Tab 2)
- Rows: Jan through Dec, plus a Totals row
- Columns: Month, Income, Expenses, Net Profit, Profit Margin %, Running Total
- Income and Expense breakdowns by category (subtables)
- All values pull via SUMIFS from Income and Expenses sheets

### 3. Invoice Log (Tab 3)
- Columns: Invoice #, Date Issued, Client, Description, Amount, Tax %, Tax Amount, Total, Due Date, Status, Date Paid, Notes
- Status dropdown: Draft / Sent / Paid / Overdue / Cancelled
- Auto-calculated Tax Amount and Total
- Conditional color: Paid = green, Overdue = red, Sent = yellow

### 4. Income (Tab 4: raw data entry)
- Columns: Date, Client, Project/Description, Category, Invoice #, Amount, Currency, Notes
- Category dropdown: Web Design, Branding, Consulting, UI/UX, Copywriting, Photography, Development, Other

### 5. Expenses (Tab 5: raw data entry)
- Columns: Date, Vendor/Payee, Description, Category, Payment Method, Amount, Currency, Receipt/Notes
- Category dropdown: Software, Hardware, Marketing, Travel, Office, Professional Services, Education, Taxes, Other

---

## Formulas Architecture

### Dashboard pulls from:
- Income!F:F → SUM for total income
- Expenses!F:F → SUM for total expenses
- Invoice Log → COUNTIF for paid/unpaid counts
- Monthly P&L → current month values

### Monthly P&L formulas (example for January income):
```
=SUMPRODUCT((MONTH(Income!$A$2:$A$200)=1)*(YEAR(Income!$A$2:$A$200)=YEAR(TODAY()))*(Income!$F$2:$F$200))
```

### Invoice Log auto-calculations:
- Tax Amount: =E2*(F2/100)
- Total: =E2+G2
- Days overdue: =IF(J2="Paid","",IF(TODAY()>I2,TODAY()-I2,""))

---

## Color Palette (RGB values for Sheets API)
- Dark Navy: R=27, G=42, B=74  → {red: 0.106, green: 0.165, blue: 0.290}
- Gold: R=212, G=175, B=55  → {red: 0.831, green: 0.686, blue: 0.216}
- Light Gold (headers on navy): R=255, G=223, B=128 → {red: 1.0, green: 0.875, blue: 0.502}
- White text: {red: 1, green: 1, blue: 1}
- Light navy (alternating rows): R=235, G=240, B=252 → {red: 0.922, green: 0.941, blue: 0.988}
- Success green: R=52, G=168, B=83 → {red: 0.204, green: 0.659, blue: 0.325}
- Warning red: R=234, G=67, B=53 → {red: 0.918, green: 0.263, blue: 0.208}
- Warning yellow: R=251, G=188, B=4 → {red: 0.984, green: 0.737, blue: 0.016}

---

## Sample Data (to be included for Etsy buyers)
- 6 income entries across Jan-Mar 2026 from 4 fictional clients
- 8 expense entries across the same period
- 5 invoice records with mixed statuses (Paid, Sent, Overdue)

---

## Etsy Listing Copy (suggested)
**Title:** Freelancer Finance Tracker | Google Sheets Template | Income, Expenses & Invoice Log | Dark Navy Gold

**Tags:** freelancer budget, invoice tracker, google sheets template, self employed finances, income tracker, expense log, profit and loss, small business template

**Description excerpt:**
"Stay on top of your freelance finances with this beautifully designed Google Sheets template. Track income, log expenses, manage invoices, and see your profitability at a glance: all in one professional dashboard."
