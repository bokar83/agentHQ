# Wedding Budget Planner: Full Spreadsheet Specification

## Design Brief
- **Product**: Etsy digital download, $18
- **Theme**: Blush pink (#F4C2C2) and rose gold (#B76E79 / #C9A27C)
- **Sheets**: 5 tabs

---

## Color Palette

| Role | Hex | Usage |
|------|-----|-------|
| Blush Pink (light) | #FFF0F3 | Row backgrounds, header fills |
| Blush Pink (medium) | #F4C2C2 | Section headers, borders |
| Rose Gold (primary) | #B76E79 | Title text, accent headers |
| Rose Gold (warm) | #C9A27C | Dashboard highlights |
| Ivory White | #FFFDF9 | Data entry cells |
| Charcoal | #3D3D3D | Body text |
| Soft Gold | #E8C99A | Total/summary rows |

---

## Sheet 1: DASHBOARD

### Layout (rows x columns)
- **A1:G1**: Merged title: "Our Wedding Budget" (rose gold, large font, centered)
- **A2:G2**: Subtitle: wedding date placeholder, italic blush

**Budget Summary Card (A4:D10)**
| Cell | Label | Formula/Value |
|------|-------|---------------|
| A4 | Total Budget | manual input |
| A5 | Total Estimated | =SUM(Vendors!E:E) |
| A6 | Total Actual Spend | =SUM(Vendors!F:F) |
| A7 | Total Deposits Paid | =SUM(Vendors!G:G) |
| A8 | Total Balance Due | =SUM(Vendors!H:H) |
| A9 | Remaining Budget | =B4-B6 |
| A10 | Over/Under Budget | =B4-B6 (conditional format: red if negative) |

**Guest Summary Card (F4:G8)**
| Cell | Label | Formula |
|------|-------|---------|
| F4 | Total Invited | =SUM(Guests!C:C) |
| F5 | Confirmed | =COUNTIF(Guests!D:D,"Yes") |
| F6 | Declined | =COUNTIF(Guests!D:D,"No") |
| F7 | Awaiting Reply | =COUNTIF(Guests!D:D,"Pending") |
| F8 | Meal Choices | =COUNTIF(Guests!E:E,"<>") |

**Category Spend Bar (A12:G22)**
- Table showing spend per vendor category vs budget allocation
- Columns: Category | Budget Allocated | Estimated | Actual | Variance

---

## Sheet 2: VENDORS

### Headers (Row 1: rose gold fill, white text, bold)
| Col | Header |
|-----|--------|
| A | # |
| B | Vendor Name |
| C | Category |
| D | Contact / Phone |
| E | Estimated Cost |
| F | Actual Cost |
| G | Deposit Paid |
| H | Balance Due |
| I | Due Date |
| J | Contract Signed? |
| K | Paid in Full? |
| L | Notes |

### Formula: Balance Due (H column)
`=IF(F2<>"", F2-G2, E2-G2)`

### Categories (dropdown validation for column C)
Venue, Catering, Photography, Videography, Florals, Music/DJ, Hair & Makeup, Cake/Desserts, Stationery, Officiant, Transport, Attire, Honeymoon, Miscellaneous

### Pre-filled sample rows (rows 2-16, 15 vendor rows)
Row 2: 1 | Venue Name | Venue | | 5000 | | 1000 | =H formula | | No | No |
Row 3: 2 | Photographer | Photography | | 3000 | | 500 | =H formula | | No | No |
Row 4: 3 | Florist | Florals | | 1500 | | 300 | =H formula | | No | No |
... (continues for all 15 rows)

### Conditional Formatting
- "Paid in Full? = Yes" → entire row light green
- Balance Due > 0 and Due Date < TODAY() → row highlight orange (overdue)
- Contract Signed = No → column J cell pink

---

## Sheet 3: DEPOSITS TRACKER

### Headers (Row 1: blush pink fill, rose gold text)
| Col | Header |
|-----|--------|
| A | Vendor |
| B | Category |
| C | Total Contract |
| D | Deposit Amount |
| E | Deposit Date |
| F | Payment Method |
| G | Remaining Balance |
| H | Next Payment Date |
| I | Final Payment Due |
| J | Status |

### Formula: Remaining Balance (G)
`=C2-D2`

### Status dropdown validation
Deposit Pending | Deposit Paid | Partially Paid | Paid in Full

### Auto-pulls from Vendors sheet
`=Vendors!B2` for vendor name
`=Vendors!C2` for category

---

## Sheet 4: GUESTS

### Headers (Row 1: rose gold fill, white text)
| Col | Header |
|-----|--------|
| A | # |
| B | Guest Name |
| C | Party Size |
| D | RSVP Status |
| E | Meal Choice |
| F | Dietary Restrictions |
| G | Table Assignment |
| H | Gift Received? |
| I | Thank You Sent? |
| J | Address (for invites) |
| K | Email |
| L | Phone |
| M | Notes |

### Dropdown validations
- D (RSVP): Yes | No | Pending | Maybe
- E (Meal): Chicken | Fish | Beef | Vegetarian | Vegan | Kids Meal
- H (Gift): Yes | No | Pending
- I (Thank You): Yes | No

### Pre-filled sample rows: 20 guest placeholder rows

---

## Sheet 5: PAYMENTS TIMELINE

### Headers (Row 1)
| Col | Header |
|-----|--------|
| A | Payment # |
| B | Vendor |
| C | Payment Type |
| D | Amount Due |
| E | Due Date |
| F | Date Paid |
| G | Payment Method |
| H | Confirmation # |
| I | Status |

### Conditional formatting
- Status = "Paid" → green row
- Due Date < TODAY() and Status != "Paid" → red row (overdue)
- Due Date within 14 days → yellow row (due soon)

### Status dropdown
Upcoming | Due Soon | Overdue | Paid

---

## gws API Calls Required

### Step 1: Create Spreadsheet
```
gws sheets spreadsheets create --json '{
  "properties": {
    "title": "Wedding Budget Planner"
  },
  "sheets": [
    {"properties": {"title": "DASHBOARD", "index": 0}},
    {"properties": {"title": "VENDORS", "index": 1}},
    {"properties": {"title": "DEPOSITS", "index": 2}},
    {"properties": {"title": "GUESTS", "index": 3}},
    {"properties": {"title": "PAYMENTS", "index": 4}}
  ]
}'
```

### Step 2: Write Headers (batchUpdate values)
```
gws sheets spreadsheets values batchUpdate --params '{"spreadsheetId": "<ID>"}' --json '{
  "valueInputOption": "USER_ENTERED",
  "data": [
    {
      "range": "VENDORS!A1:L1",
      "values": [["#","Vendor Name","Category","Contact / Phone","Estimated Cost","Actual Cost","Deposit Paid","Balance Due","Due Date","Contract Signed?","Paid in Full?","Notes"]]
    },
    {
      "range": "GUESTS!A1:M1",
      "values": [["#","Guest Name","Party Size","RSVP Status","Meal Choice","Dietary Restrictions","Table Assignment","Gift Received?","Thank You Sent?","Address","Email","Phone","Notes"]]
    },
    {
      "range": "DEPOSITS!A1:J1",
      "values": [["Vendor","Category","Total Contract","Deposit Amount","Deposit Date","Payment Method","Remaining Balance","Next Payment Date","Final Payment Due","Status"]]
    },
    {
      "range": "PAYMENTS!A1:I1",
      "values": [["Payment #","Vendor","Payment Type","Amount Due","Due Date","Date Paid","Payment Method","Confirmation #","Status"]]
    },
    {
      "range": "DASHBOARD!A1",
      "values": [["Our Wedding Budget"]]
    }
  ]
}'
```

### Step 3: Apply Formatting (batchUpdate spreadsheet)
Full spreadsheetsBatchUpdate JSON for colors, fonts, borders is detailed below.

---

## Formatting JSON (Key Sections)

### Rose gold header fill = RGB(183, 110, 121) → red:0.718, green:0.431, blue:0.475
### Blush pink fill = RGB(244, 194, 194) → red:0.957, green:0.761, blue:0.761
### Light blush row = RGB(255, 240, 243) → red:1.0, green:0.941, blue:0.953

```json
{
  "repeatCell": {
    "range": {"sheetId": 1, "startRowIndex": 0, "endRowIndex": 1},
    "cell": {
      "userEnteredFormat": {
        "backgroundColor": {"red": 0.718, "green": 0.431, "blue": 0.475},
        "textFormat": {
          "foregroundColor": {"red": 1, "green": 1, "blue": 1},
          "bold": true,
          "fontSize": 11,
          "fontFamily": "Lato"
        },
        "horizontalAlignment": "CENTER",
        "verticalAlignment": "MIDDLE"
      }
    },
    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
  }
}
```
