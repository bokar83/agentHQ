# BUILD_PROMPT: The Blush Wedding Budget Planner

Build a **Wedding Budget Planner** in Google Sheets. Sellable digital product priced at $18 on Etsy.
Every formula, chart, dropdown, and conditional formatting rule must be fully functional on first open.

---

## Overview

A beautifully designed wedding budget planner for couples planning their big day. Tracks every vendor,
deposit paid, balance due, total budget vs actual spend with a live dashboard, and a complete guest
count tracker. The differentiating feature is a dedicated Payments tab that gives a clear timeline of
what's been paid, what's still owed, and due dates: so nothing falls through the cracks. Color scheme
is elegant blush pink and rose gold: Etsy-ready and immediately usable.

---

## Tab Structure

| sheetId | Name            | Visible | Purpose                                                         |
|---------|-----------------|---------|------------------------------------------------------------------|
| 0       | Dashboard       | Yes     | KPI cards, budget vs actual chart, category breakdown chart      |
| 1       | Vendors         | Yes     | Master vendor list with category, contact, contract amount      |
| 2       | Payments        | Yes     | Deposit/balance tracker with due dates and paid status          |
| 3       | Budget vs Actual| Yes     | Category-level budget allocation vs actual spend               |
| 4       | Guest Tracker   | Yes     | Guest list with RSVP status, meal choice, table assignment      |
| 5       | _Ref            | No      | Hidden lookup/dropdown source data                              |

---

## Color Palette

| Role               | Hex      | RGB Float (R, G, B)              |
|--------------------|----------|-----------------------------------|
| Header BG          | #8B3A52  | {red: 0.545, green: 0.227, blue: 0.322} |
| Header Text        | #FFF8F0  | {red: 1.0, green: 0.973, blue: 0.941}   |
| Rose Gold Accent   | #C9956C  | {red: 0.788, green: 0.584, blue: 0.424} |
| Blush BG           | #F9E0E5  | {red: 0.976, green: 0.878, blue: 0.898} |
| Ivory BG           | #FFF8F0  | {red: 1.0, green: 0.973, blue: 0.941}   |
| Warm Gray          | #9E8E8E  | {red: 0.620, green: 0.557, blue: 0.557} |
| Deep Text          | #3D1A26  | {red: 0.239, green: 0.102, blue: 0.149} |
| Paid Green         | #6B9E78  | {red: 0.420, green: 0.620, blue: 0.471} |
| Unpaid Red         | #C96C6C  | {red: 0.788, green: 0.424, blue: 0.424} |
| Alt Row BG         | #FDF0F3  | {red: 0.992, green: 0.941, blue: 0.953} |

---

## Tab 5 (Hidden): _Ref

Populate this tab FIRST before all other tabs.

```
_Ref!A1:A13 : VENDOR CATEGORIES header + 12 values
A1: VENDOR CATEGORY
A2: Venue
A3: Catering
A4: Photography
A5: Videography
A6: Florals
A7: Music / DJ
A8: Hair & Makeup
A9: Cake & Desserts
A10: Transportation
A11: Officiant
A12: Invitations & Stationery
A13: Other

_Ref!C1:C5 : PAYMENT STATUS
C1: PAYMENT STATUS
C2: Deposit Paid
C3: Paid in Full
C4: Pending
C5: Overdue

_Ref!E1:E6 : RSVP STATUS
E1: RSVP STATUS
E2: Attending
E3: Declined
E4: Awaiting Reply
E5: Maybe
E6: Plus One Confirmed

_Ref!G1:G5 : MEAL CHOICE
G1: MEAL CHOICE
G2: Chicken
G3: Fish
G4: Vegetarian
G5: Vegan

_Ref!I1:I20: TABLE ASSIGNMENTS
I1: TABLE
I2: Head Table
I3: Table 1
I4: Table 2
I5: Table 3
I6: Table 4
I7: Table 5
I8: Table 6
I9: Table 7
I10: Table 8
I11: Table 9
I12: Table 10
I13: Cocktail Hour
I14: Kids Table
I15: Unassigned
```

---

## Tab 1: Vendors

### Column Definitions

| Col | Header           | Width | Type     | Formula / Dropdown Source             |
|-----|------------------|-------|----------|---------------------------------------|
| A   | #                | 40    | Auto-num | =IF(B2="","",ROW()-1)                 |
| B   | Vendor Name      | 200   | Text     | Manual entry                          |
| C   | Category         | 160   | Dropdown | _Ref!A2:A13                           |
| D   | Contact Name     | 160   | Text     | Manual entry                          |
| E   | Phone            | 130   | Text     | Manual entry                          |
| F   | Email            | 200   | Text     | Manual entry                          |
| G   | Contract Amount  | 120   | Currency | Manual entry, format $#,##0.00        |
| H   | Deposit Amount   | 120   | Currency | Manual entry, format $#,##0.00        |
| I   | Balance Due      | 120   | Formula  | =IFERROR(IF(G2="","",G2-H2),"")       |
| J   | Due Date         | 110   | Date     | Manual entry                          |
| K   | Notes            | 250   | Text     | Manual entry                          |

### Sample Data (30 rows: 3 months of planning activity)

Row 2: Rosewood Estate | Venue | Sarah Mitchell | 555-0101 | venue@rosewood.com | 8500 | 2550 | | 2026-06-15 | Outdoor ceremony + reception hall
Row 3: Bloom & Co Catering | Catering | James Park | 555-0102 | james@bloomco.com | 12000 | 3600 | | 2026-07-01 | $120/head x 100 guests, tasting April
Row 4: Aurora Photography | Photography | Lisa Chen | 555-0103 | lisa@aurora.photo | 4200 | 1260 | | 2026-05-01 | 10-hour coverage, 2 photographers
Row 5: Reel Moments Video | Videography | Tom Davis | 555-0104 | tom@reelmoments.com | 2800 | 840 | | 2026-05-15 | Cinematic highlight reel + full edit
Row 6: The Floral Studio | Florals | Maria Santos | 555-0105 | maria@floralstudio.com | 3500 | 1050 | | 2026-06-01 | Ceremony arch, 10 centerpieces, bouquets
Row 7: Harmony Strings DJ | Music / DJ | Kevin Lee | 555-0106 | kevin@harmonydj.com | 2200 | 660 | | 2026-06-01 | Cocktail hour + 4-hour reception
Row 8: Glow Beauty Co | Hair & Makeup | Priya Nair | 555-0107 | priya@glowbeauty.com | 1800 | 540 | | 2026-07-15 | Bride + 4 bridesmaids trial included
Row 9: Sugar Petals Bakery | Cake & Desserts | Anne Wu | 555-0108 | anne@sugarpetals.com | 950 | 285 | | 2026-07-20 | 5-tier floral cake + 50 mini desserts
Row 10: Luxury Car Hire | Transportation | Matt Brown | 555-0109 | matt@luxurycarhire.com | 750 | 225 | | 2026-08-01 | Rolls Royce + limo for wedding party
Row 11: Rev. Grace Turner | Officiant | Grace Turner | 555-0110 | grace@ceremonies.com | 600 | 180 | | 2026-07-01 | Custom ceremony script, rehearsal incl.
Row 12: Paperie & Co | Invitations & Stationery | Claire Fox | 555-0111 | claire@paperie.com | 1200 | 360 | | 2026-04-15 | 120 invites, RSVP cards, menus, programs
Row 13: Venue Coordinator | Other | Dana Rich | 555-0112 | dana@rosewood.com | 800 | 240 | | 2026-06-15 | Day-of coordination, 8 hrs

---

## Tab 2: Payments

### Column Definitions

| Col | Header           | Width | Type     | Formula / Details                                              |
|-----|------------------|-------|----------|----------------------------------------------------------------|
| A   | #                | 40    | Auto-num | =IF(B2="","",ROW()-1)                                          |
| B   | Vendor Name      | 200   | Text     | Manual entry (matches Vendors tab)                            |
| C   | Category         | 160   | Dropdown | _Ref!A2:A13                                                    |
| D   | Contract Total   | 120   | Currency | Manual entry, $#,##0.00                                       |
| E   | Deposit Amount   | 120   | Currency | Manual entry, $#,##0.00                                       |
| F   | Deposit Due Date | 110   | Date     | Manual entry                                                   |
| G   | Deposit Paid?    | 100   | Checkbox | Checkbox validation                                            |
| H   | Balance Due      | 120   | Formula  | =IFERROR(IF(D2="","",D2-E2),"")                                |
| I   | Balance Due Date | 110   | Date     | Manual entry                                                   |
| J   | Balance Paid?    | 100   | Checkbox | Checkbox validation                                            |
| K   | Payment Status   | 140   | Formula  | =IFERROR(IF(D2="","",IF(AND(G2=TRUE,J2=TRUE),"Paid in Full",IF(AND(G2=TRUE,J2=FALSE),IF(I2<TODAY(),"Overdue","Deposit Paid"),IF(G2=FALSE,IF(F2<TODAY(),"Overdue","Pending"),"Pending")))),"") |
| L   | Notes            | 200   | Text     | Manual entry                                                   |

### Sample Data (12 vendors)

Row 2: Rosewood Estate | Venue | 8500 | 2550 | 2026-01-15 | TRUE | | 2026-07-15 | FALSE | | Balance due July
Row 3: Bloom & Co Catering | Catering | 12000 | 3600 | 2026-02-01 | TRUE | | 2026-08-01 | FALSE | | Final headcount confirmed 60 days out
Row 4: Aurora Photography | Photography | 4200 | 1260 | 2026-01-20 | TRUE | | 2026-07-20 | FALSE | | Final payment before wedding date
Row 5: Reel Moments Video | Videography | 2800 | 840 | 2026-02-10 | TRUE | | 2026-07-20 | FALSE |
Row 6: The Floral Studio | Florals | 3500 | 1050 | 2026-02-20 | TRUE | | 2026-07-25 | FALSE |
Row 7: Harmony Strings DJ | Music / DJ | 2200 | 660 | 2026-03-01 | FALSE | | 2026-07-01 | FALSE |
Row 8: Glow Beauty Co | Hair & Makeup | 1800 | 540 | 2026-03-15 | FALSE | | 2026-07-20 | FALSE |
Row 9: Sugar Petals Bakery | Cake & Desserts | 950 | 285 | 2026-03-20 | FALSE | | 2026-07-25 | FALSE |
Row 10: Luxury Car Hire | Transportation | 750 | 225 | 2026-04-01 | FALSE | | 2026-07-25 | FALSE |
Row 11: Rev. Grace Turner | Officiant | 600 | 180 | 2026-03-01 | FALSE | | 2026-07-01 | FALSE |
Row 12: Paperie & Co | Invitations & Stationery | 1200 | 360 | 2026-02-15 | TRUE | | 2026-05-15 | TRUE | | Fully paid
Row 13: Venue Coordinator | Other | 800 | 240 | 2026-03-15 | FALSE | | 2026-07-15 | FALSE |

---

## Tab 3: Budget vs Actual

### Column Definitions

| Col | Header            | Width | Type     | Formula / Details                                              |
|-----|-------------------|-------|----------|----------------------------------------------------------------|
| A   | Category          | 180   | Text     | Pre-filled with all 12 vendor categories                       |
| B   | Budgeted Amount   | 130   | Currency | Manual entry per category, $#,##0.00                          |
| C   | Actual Spend      | 130   | Formula  | =IFERROR(SUMIF(Vendors!C:C,A2,Vendors!G:G),0)                  |
| D   | Difference        | 120   | Formula  | =IFERROR(B2-C2,0)                                              |
| E   | % of Budget Used  | 120   | Formula  | =IFERROR(IF(B2=0,"",C2/B2),"")  format: 0%                   |
| F   | Status            | 120   | Formula  | =IFERROR(IF(B2="","",IF(C2>B2,"Over Budget",IF(C2/B2>=0.9,"Near Limit","On Track"))),"") |
| G   | Sparkline         | 120   | Formula  | =IFERROR(IF(B2="","",SPARKLINE(C2/B2,{"charttype","bar";"max",1;"color1","#C9956C";"color2","#F9E0E5"})),"") |

### Pre-filled Category Rows (A2:A13)
A2: Venue
A3: Catering
A4: Photography
A5: Videography
A6: Florals
A7: Music / DJ
A8: Hair & Makeup
A9: Cake & Desserts
A10: Transportation
A11: Officiant
A12: Invitations & Stationery
A13: Other

### Sample Budget Data (B column):
B2: 9000, B3: 13000, B4: 4500, B5: 3000, B6: 4000, B7: 2500, B8: 2000, B9: 1000, B10: 800, B11: 700, B12: 1500, B13: 1000

### Row 15: Totals Row
A15: TOTAL
B15: =SUM(B2:B13)
C15: =SUM(C2:C13)
D15: =SUM(D2:D13)
E15: =IFERROR(C15/B15,"")

---

## Tab 4: Guest Tracker

### Column Definitions

| Col | Header         | Width | Type     | Formula / Dropdown                              |
|-----|----------------|-------|----------|--------------------------------------------------|
| A   | #              | 40    | Auto-num | =IF(B2="","",ROW()-1)                            |
| B   | First Name     | 130   | Text     | Manual entry                                     |
| C   | Last Name      | 130   | Text     | Manual entry                                     |
| D   | Group / Party  | 150   | Text     | Manual entry (e.g. "Smith Family")               |
| E   | Side           | 90    | Dropdown | ONE_OF_LIST: Bride's Side, Groom's Side, Mutual  |
| F   | RSVP Status    | 140   | Dropdown | _Ref!E2:E6                                       |
| G   | Meal Choice    | 130   | Dropdown | _Ref!G2:G5                                       |
| H   | Table          | 120   | Dropdown | _Ref!I2:I15                                      |
| I   | Plus One?      | 90    | Checkbox | Checkbox                                         |
| J   | Gift Received? | 110   | Checkbox | Checkbox                                         |
| K   | Thank You Sent?| 120   | Checkbox | Checkbox                                         |
| L   | Notes          | 200   | Text     | Manual entry                                     |

### Summary Rows (rows 2-4 above header, placed at top as a mini-dashboard in rows 1-4)
Actually place summary stats in row 1 of a separate section at top (rows 2-5), then headers in row 7, data from row 8.

Guest Tracker Layout:
- Row 1: Title banner "GUEST TRACKER" (merged A1:L1)
- Row 2: "Total Invited:" B2 formula =COUNTA(B8:B500)
- Row 3: "Attending:" B3 formula =COUNTIF(F8:F500,"Attending")
- Row 4: "Declined:" B4 formula =COUNTIF(F8:F500,"Declined")
- Row 5: "Awaiting Reply:" B5 formula =COUNTIF(F8:F500,"Awaiting Reply")
- Row 6: "Total Meals - Chicken:" D6 =COUNTIF(G8:G500,"Chicken") | "Fish:" F6 =COUNTIF(G8:G500,"Fish") | "Veg:" H6 =COUNTIF(G8:G500,"Vegetarian") | "Vegan:" J6 =COUNTIF(G8:G500,"Vegan")
- Row 7: Column headers
- Rows 8+: Guest data

### Sample Guest Data (30 guests, row 8 onward)

8: Emma | Johnson | Johnson Family | Bride's Side | Attending | Chicken | Table 1 | FALSE | TRUE | TRUE |
9: Liam | Johnson | Johnson Family | Bride's Side | Attending | Fish | Table 1 | TRUE | TRUE | FALSE |
10: Olivia | Williams | Williams Family | Groom's Side | Attending | Vegetarian | Table 2 | FALSE | FALSE | FALSE |
11: Noah | Williams | Williams Family | Groom's Side | Attending | Chicken | Table 2 | TRUE | FALSE | FALSE |
12: Ava | Brown | Brown Family | Bride's Side | Attending | Chicken | Table 3 | FALSE | TRUE | TRUE |
13: Isabella | Brown | Brown Family | Bride's Side | Attending | Vegan | Table 3 | FALSE | TRUE | TRUE |
14: Sophia | Davis | Davis Family | Groom's Side | Awaiting Reply | | Unassigned | FALSE | FALSE | FALSE |
15: Mason | Davis | Davis Family | Groom's Side | Attending | Fish | Table 4 | TRUE | FALSE | FALSE |
16: Logan | Miller | Miller Family | Mutual | Attending | Chicken | Table 4 | FALSE | FALSE | FALSE |
17: Charlotte | Miller | Miller Family | Mutual | Attending | Chicken | Table 4 | FALSE | FALSE | FALSE |
18: Elijah | Wilson | Wilson Family | Bride's Side | Declined | | Unassigned | FALSE | FALSE | FALSE |
19: Amelia | Moore | Moore Family | Groom's Side | Attending | Vegetarian | Table 5 | FALSE | TRUE | FALSE |
20: James | Taylor | Taylor Family | Mutual | Attending | Chicken | Table 5 | TRUE | FALSE | FALSE |
21: Harper | Anderson | Anderson Family | Bride's Side | Attending | Fish | Table 5 | FALSE | FALSE | FALSE |
22: Evelyn | Thomas | Thomas Family | Groom's Side | Awaiting Reply | | Unassigned | FALSE | FALSE | FALSE |
23: Alexander | Jackson | Jackson Family | Mutual | Attending | Chicken | Table 6 | FALSE | TRUE | TRUE |
24: Abigail | White | White Family | Bride's Side | Attending | Vegetarian | Table 6 | FALSE | FALSE | FALSE |
25: Benjamin | Harris | Harris Family | Groom's Side | Attending | Chicken | Table 6 | TRUE | FALSE | FALSE |
26: Ella | Martin | Martin Family | Mutual | Declined | | Unassigned | FALSE | FALSE | FALSE |
27: William | Garcia | Garcia Family | Groom's Side | Attending | Fish | Table 7 | FALSE | TRUE | FALSE |
28: Scarlett | Martinez | Martinez Family | Bride's Side | Attending | Chicken | Table 7 | FALSE | FALSE | FALSE |
29: Henry | Robinson | Robinson Family | Mutual | Attending | Vegan | Table 7 | FALSE | FALSE | FALSE |
30: Luna | Clark | Clark Family | Bride's Side | Attending | Chicken | Table 8 | TRUE | TRUE | TRUE |
31: Sebastian | Rodriguez | Rodriguez Family | Groom's Side | Attending | Fish | Table 8 | FALSE | FALSE | FALSE |
32: Mia | Lewis | Lewis Family | Mutual | Awaiting Reply | | Unassigned | FALSE | FALSE | FALSE |
33: Jack | Lee | Lee Family | Bride's Side | Attending | Chicken | Table 8 | FALSE | TRUE | FALSE |
34: Aria | Walker | Walker Family | Groom's Side | Attending | Chicken | Table 9 | FALSE | FALSE | FALSE |
35: Julian | Hall | Hall Family | Mutual | Attending | Vegetarian | Table 9 | FALSE | FALSE | FALSE |
36: Chloe | Allen | Allen Family | Bride's Side | Attending | Chicken | Table 9 | FALSE | TRUE | TRUE |
37: Owen | Young | Young Family | Groom's Side | Attending | Fish | Table 10 | TRUE | FALSE | FALSE |

---

## Tab 0: Dashboard

### Layout

Row 1: Merged A1:L1: Title banner "THE BLUSH WEDDING BUDGET PLANNER"
Row 2: Merged A2:L2: subtitle "Your complete wedding finance & guest overview"
Row 3: Empty spacer

Row 4-5: KPI Cards (merged pairs of cells, 6 KPI cards across)
- KPI 1 (A4:B5): "TOTAL BUDGET" / =IFERROR('Budget vs Actual'!B15,0) / format $#,##0
- KPI 2 (C4:D5): "TOTAL SPENT" / =IFERROR('Budget vs Actual'!C15,0) / format $#,##0
- KPI 3 (E4:F5): "REMAINING" / =IFERROR('Budget vs Actual'!B15-'Budget vs Actual'!C15,0) / format $#,##0
- KPI 4 (G4:H5): "VENDORS BOOKED" / =COUNTA(Vendors!B2:B500) / format 0
- KPI 5 (I4:J5): "GUESTS ATTENDING" / =COUNTIF('Guest Tracker'!F8:F500,"Attending") / format 0
- KPI 6 (K4:L5): "DEPOSITS PAID" / =COUNTIF(Payments!G2:G500,TRUE) / format 0

Row 6: Empty spacer

Row 7: Section header "BUDGET OVERVIEW" (merged A7:F7)
Row 7 continued: Section header "PAYMENT SUMMARY" (merged G7:L7)

Rows 8-20: Chart placeholder area: charts will overlay this region

Row 22: Section header "CATEGORY BREAKDOWN" (merged A22:L22)
Rows 23-35: Second chart area

Row 37: Section header "BALANCE DUE SUMMARY" (merged A37:L37)
Row 38 headers: Vendor | Category | Contract | Deposit | Balance | Status
Rows 39-50: =IFERROR(INDEX(Payments!B:B,ROW()-37),"") style references pulling top unpaid vendors

Actually use simpler direct pull for balance due summary:
Row 38: Headers: A38=Vendor | B38=Category | C38=Contract Total | D38=Deposits Paid | E38=Balance Due | F38=Status
Rows 39-50: Pull from Payments tab:
A39: =IFERROR(INDEX(Payments!B:B,ROW()-37),"")
B39: =IFERROR(INDEX(Payments!C:C,ROW()-37),"")
C39: =IFERROR(INDEX(Payments!D:D,ROW()-37),"")
D39: =IFERROR(INDEX(Payments!E:E,ROW()-37),"")
E39: =IFERROR(INDEX(Payments!H:H,ROW()-37),"")
F39: =IFERROR(INDEX(Payments!K:K,ROW()-37),"")

---

## Charts

### Chart 1: Budget vs Actual Column Chart (on Dashboard)
- Type: Column chart (COLUMN)
- Source tab: Budget vs Actual (sheetId 3)
- Domain: A2:A13 (category names)
- Series 1: B2:B13 (Budgeted): color #8B3A52
- Series 2: C2:C13 (Actual Spend): color #C9956C
- Title: "Budget vs Actual by Category"
- Legend: BOTTOM
- Position: anchor Dashboard row 7, col A (0,6), offset 0px, 0px, width 550px, height 300px

### Chart 2: Payment Status Donut Chart (on Dashboard)
- Type: Pie chart (PIE) with pieHole: 0.5
- Source: Must compute on _Ref or directly. Use a small helper section on _Ref for chart source.
  Add to _Ref!K1:L5:
  K1: STATUS | L1: COUNT
  K2: Paid in Full | L2: =COUNTIF(Payments!K:K,"Paid in Full")
  K3: Deposit Paid | L3: =COUNTIF(Payments!K:K,"Deposit Paid")
  K4: Pending | L4: =COUNTIF(Payments!K:K,"Pending")
  K5: Overdue | L5: =COUNTIF(Payments!K:K,"Overdue")
- Domain: _Ref!K2:K5
- Series: _Ref!L2:L5
- Colors: ["#6B9E78","#C9956C","#F9E0E5","#C96C6C"]
- Title: "Payment Status"
- Position: anchor Dashboard row 7, col G (6,6), offset 0px, 0px, width 400px, height 300px

### Chart 3: Guest RSVP Pie Chart (on Dashboard)
- Add helper to _Ref!K7:L11:
  K7: RSVP | L7: COUNT
  K8: Attending | L8: =COUNTIF('Guest Tracker'!F:F,"Attending")
  K9: Declined | L9: =COUNTIF('Guest Tracker'!F:F,"Declined")
  K10: Awaiting Reply | L10: =COUNTIF('Guest Tracker'!F:F,"Awaiting Reply")
  K11: Maybe | L11: =COUNTIF('Guest Tracker'!F:F,"Maybe")
- Type: Pie chart
- Domain: _Ref!K8:K11
- Series: _Ref!L8:L11
- Colors: ["#8B3A52","#C96C6C","#F9E0E5","#C9956C"]
- Title: "Guest RSVPs"
- Position: anchor Dashboard row 22, col A (0,21), offset 0px, 0px, width 400px, height 260px

---

## Conditional Formatting Rules

### Payments Tab: Column K (Payment Status)
1. Range: K2:K500 | TEXT_EQ "Paid in Full" → BG #6B9E78, text #FFF8F0
2. Range: K2:K500 | TEXT_EQ "Deposit Paid" → BG #C9956C, text #FFF8F0
3. Range: K2:K500 | TEXT_EQ "Pending" → BG #F9E0E5, text #3D1A26
4. Range: K2:K500 | TEXT_EQ "Overdue" → BG #C96C6C, text #FFF8F0

### Budget vs Actual Tab: Column F (Status)
5. Range: F2:F13 | TEXT_EQ "Over Budget" → BG #C96C6C, text #FFF8F0
6. Range: F2:F13 | TEXT_EQ "Near Limit" → BG #C9956C, text #FFF8F0
7. Range: F2:F13 | TEXT_EQ "On Track" → BG #6B9E78, text #FFF8F0

### Budget vs Actual Tab: Column D (Difference)
8. Range: D2:D13 | NUMBER_LESS 0 → text color #C96C6C, bold
9. Range: D2:D13 | NUMBER_GREATER_THAN_EQ 0 → text color #6B9E78, bold

### Dashboard Tab: KPI cards
10. Range: E4:F5 (Remaining) | custom formula =E5<0 → BG #C96C6C, text #FFF8F0

---

## Data Validation Dropdowns

1. Vendors!C2:C500 → ONE_OF_RANGE: _Ref!A2:A13 (Vendor Category), strict
2. Payments!C2:C500 → ONE_OF_RANGE: _Ref!A2:A13 (Vendor Category), strict
3. 'Guest Tracker'!E8:E500 → ONE_OF_LIST: ["Bride's Side","Groom's Side","Mutual"], strict
4. 'Guest Tracker'!F8:F500 → ONE_OF_RANGE: _Ref!E2:E6 (RSVP Status), strict
5. 'Guest Tracker'!G8:G500 → ONE_OF_RANGE: _Ref!G2:G5 (Meal Choice), strict
6. 'Guest Tracker'!H8:H500 → ONE_OF_RANGE: _Ref!I2:I15 (Table), strict
7. 'Guest Tracker'!I8:I500 → Checkbox
8. 'Guest Tracker'!J8:J500 → Checkbox
9. 'Guest Tracker'!K8:K500 → Checkbox
10. Payments!G2:G500 → Checkbox (Deposit Paid?)
11. Payments!J2:J500 → Checkbox (Balance Paid?)

---

## Frozen Rows / Columns

| Tab              | Freeze Rows | Freeze Cols |
|------------------|-------------|-------------|
| Dashboard        | 3           | 0           |
| Vendors          | 1           | 1           |
| Payments         | 1           | 1           |
| Budget vs Actual | 1           | 1           |
| Guest Tracker    | 7           | 0           |

---

## Tab Colors (updateSheetProperties)

| Tab              | Tab Color |
|------------------|-----------|
| Dashboard        | #8B3A52   |
| Vendors          | #C9956C   |
| Payments         | #C96C6C   |
| Budget vs Actual | #6B9E78   |
| Guest Tracker    | #F9E0E5   |

---

## Cross-Sheet Formula Logic

- Dashboard KPI cells pull from: 'Budget vs Actual'!B15, 'Budget vs Actual'!C15, Vendors!, Payments!, 'Guest Tracker'!
- Budget vs Actual!C column uses SUMIF on Vendors!C:C (category) and Vendors!G:G (contract amount)
- Payments!K (Payment Status) uses checkbox state + date comparison with TODAY()
- All cross-sheet formulas wrapped in IFERROR

---

## Final Requirements Checklist

- [ ] Spreadsheet title: "The Blush Wedding Budget Planner"
- [ ] All formulas use USER_ENTERED valueInputOption so they parse correctly
- [ ] All cross-sheet formulas wrapped in IFERROR
- [ ] _Ref tab built first, hidden, all dropdown sources populated
- [ ] Sample data must populate all chart series (not empty)
- [ ] Tab colors set per table above
- [ ] Frozen rows/columns per table above
- [ ] Conditional formatting applied to Payments!K and Budget vs Actual!F and D columns
- [ ] All dropdowns functional on first open
- [ ] Output: spreadsheet ID + shareable link https://docs.google.com/spreadsheets/d/[ID]/edit
- [ ] Price point: $18 Etsy
