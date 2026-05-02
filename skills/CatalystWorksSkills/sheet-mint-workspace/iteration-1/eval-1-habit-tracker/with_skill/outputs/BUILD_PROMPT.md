# BUILD_PROMPT.md: Bloom Habit Tracker: 30-Day Monthly Planner

Build a habit tracker in Google Sheets. Sellable digital product targeting Etsy buyers.
Every formula, chart, dropdown, and conditional formatting rule must be functional on first open.

---

## Overview

The Bloom Habit Tracker is a clean, minimal 30-day monthly habit planner for personal growth
enthusiasts. It tracks 10 daily habits across a full month, auto-calculates streak counters
(current and longest), shows a weekly summary of completion rates, and features a dashboard
with sparkline progress bars. The differentiating feature is a REPT-based visual streak bar
on the Dashboard showing habit momentum at a glance. Designed for Etsy buyers in the
productivity/self-improvement niche. Estimated price: $12-$15.

---

## Tab Structure

| sheetId | Name             | Visible | Purpose                                              |
|---------|------------------|---------|------------------------------------------------------|
| 0       | Dashboard        | Yes     | Monthly overview, streak counters, sparkline bars    |
| 1       | March Tracker    | Yes     | 31-row daily check grid for 10 habits (checkboxes)   |
| 2       | Habit Setup      | Yes     | User enters 10 habit names + weekly goals            |
| 3       | Weekly Summary   | Yes     | Auto-calculated week-by-week completion stats        |
| 4       | _Ref             | No      | Hidden: dropdown source data, month list             |

---

## Color Palette

| Semantic Role          | Hex Code | RGB Float (R, G, B)              |
|------------------------|----------|----------------------------------|
| Page background        | #F0F7F0  | {red:0.941, green:0.969, blue:0.941} |
| Header background      | #A8D5A2  | {red:0.659, green:0.835, blue:0.635} |
| Header text            | #2E7D52  | {red:0.180, green:0.490, blue:0.322} |
| Accent / streak        | #4CAF7D  | {red:0.298, green:0.686, blue:0.490} |
| Deep green (titles)    | #2E7D52  | {red:0.180, green:0.490, blue:0.322} |
| White (primary bg)     | #FFFFFF  | {red:1.0,   green:1.0,   blue:1.0  } |
| Alternating row tint   | #E8F5E9  | {red:0.910, green:0.961, blue:0.914} |
| Completed cell fill    | #C8E6C9  | {red:0.784, green:0.902, blue:0.788} |
| Missed cell fill       | #FFCDD2  | {red:1.0,   green:0.804, blue:0.824} |
| Streak bar color       | #4CAF7D  | {red:0.298, green:0.686, blue:0.490} |
| Border / divider       | #B2DFDB  | {red:0.698, green:0.875, blue:0.859} |

---

## Tab 4 (Hidden): _Ref

Build this tab FIRST. All dropdown sources live here.

| Range       | Content                                          |
|-------------|--------------------------------------------------|
| A1:A13      | MONTHS header + Jan-Dec                          |
| C1:C5       | COMPLETION_BAND: Excellent, Good, Fair, Low, None|
| E1:E11      | HABITS (default names): Morning Water, Exercise, Read 20 min, Meditate, No Sugar, Sleep 8h, Journaling, Walk 10k Steps, No Phone 1h, Gratitude |
| G1:G2       | BOOL_OPTIONS: TRUE, FALSE                        |

Write these values:
- A1: MONTHS, A2: January, A3: February, A4: March, A5: April, A6: May, A7: June, A8: July, A9: August, A10: September, A11: October, A12: November, A13: December
- C1: COMPLETION_BAND, C2: Excellent (≥80%), C3: Good (60-79%), C4: Fair (40-59%), C5: Low (<40%), C6: None
- E1: HABITS, E2: Morning Water, E3: Exercise, E4: Read 20 min, E5: Meditate, E6: No Sugar, E7: Sleep 8h, E8: Journaling, E9: Walk 10k Steps, E10: No Phone 1h, E11: Gratitude

---

## Tab 2: Habit Setup

This is where the user configures their 10 habits.

### Layout (write values first, then formatting)

| Row | Col A          | Col B         | Col C (formula/value)    |
|-----|----------------|---------------|--------------------------|
| 1   | HABIT SETUP    | (merged A1:C1)|:                        |
| 2   | Active Month   | March         | (user input cell B2)     |
| 3   | Year           | 2026          | (user input cell B3)     |
| 4   |:              |:             |:                        |
| 5   | #   | Habit Name     | Daily Goal (times/day)   |
| 6   | 1   | Morning Water  | 1                        |
| 7   | 2   | Exercise       | 1                        |
| 8   | 3   | Read 20 min    | 1                        |
| 9   | 4   | Meditate       | 1                        |
| 10  | 5   | No Sugar       | 1                        |
| 11  | 6   | Sleep 8h       | 1                        |
| 12  | 7   | Journaling     | 1                        |
| 13  | 8   | Walk 10k Steps | 1                        |
| 14  | 9   | No Phone 1h    | 1                        |
| 15  | 10  | Gratitude      | 1                        |

Column widths: A=50, B=220, C=160

Freeze row 1 (title banner only: do NOT freeze merged row when freezing rows 1+).
Actually: freeze rows 1-5 (header block).

---

## Tab 1: March Tracker

This is the main daily check grid. 31 rows of data (days 1-31) + 1 header row.

### Headers (Row 1)

| Col | Header          | Width | Notes                                           |
|-----|-----------------|-------|-------------------------------------------------|
| A   | Day             | 50    | Day number 1-31                                 |
| B   | Date            | 90    | =DATE('Habit Setup'!B3, MATCH('Habit Setup'!B2,'_Ref'!A2:A13,0), A2) |
| C   | Habit 1 (Morning Water) | 110 | ='Habit Setup'!B6                         |
| D   | Habit 2 (Exercise)      | 110 | ='Habit Setup'!B7                         |
| E   | Habit 3 (Read 20 min)   | 110 | ='Habit Setup'!B8                         |
| F   | Habit 4 (Meditate)      | 110 | ='Habit Setup'!B9                         |
| G   | Habit 5 (No Sugar)      | 110 | ='Habit Setup'!B10                        |
| H   | Habit 6 (Sleep 8h)      | 110 | ='Habit Setup'!B11                        |
| I   | Habit 7 (Journaling)    | 110 | ='Habit Setup'!B12                        |
| J   | Habit 8 (Walk 10k)      | 110 | ='Habit Setup'!B13                        |
| K   | Habit 9 (No Phone 1h)   | 110 | ='Habit Setup'!B14                        |
| L   | Habit 10 (Gratitude)    | 110 | ='Habit Setup'!B15                        |
| M   | Daily Total     | 80    | =COUNTIF(C2:L2,TRUE)                            |
| N   | % Done          | 70    | =M2/10                                          |

Row 1 is the header. Header labels in C1:L1 pull from Habit Setup via formula.

### Data Rows (Rows 2-32 = Days 1-31)

Column A: Day numbers 1 through 31 (static values)
Columns C:L: Checkboxes (TRUE/FALSE via setDataValidation with checkbox type)
Column M: =COUNTIF(C2:L2,TRUE): drag down for all 31 rows
Column N: =M2/10: format as percentage: drag down for all 31 rows

Column B formula for row 2: =DATE('Habit Setup'!B3,MATCH('Habit Setup'!B2,'_Ref'!A2:A13,0),A2)
Drag down through row 32 (changes A2 reference to A3, A4, ... A32).

### Sample Data (pre-filled checkboxes as TRUE/FALSE)

Write these as TRUE/FALSE values (USER_ENTERED so checkboxes render):

| Row | Day | C    | D    | E     | F    | G    | H    | I    | J    | K    | L    |
|-----|-----|------|------|-------|------|------|------|------|------|------|------|
| 2   | 1   | TRUE | TRUE | TRUE  | TRUE | TRUE | TRUE | TRUE | TRUE | FALSE| TRUE |
| 3   | 2   | TRUE | TRUE | TRUE  | TRUE | FALSE| TRUE | TRUE | FALSE| FALSE| TRUE |
| 4   | 3   | TRUE | FALSE| TRUE  | TRUE | TRUE | TRUE | FALSE| TRUE | TRUE | TRUE |
| 5   | 4   | TRUE | TRUE | FALSE | TRUE | TRUE | FALSE| TRUE | TRUE | TRUE | TRUE |
| 6   | 5   | TRUE | TRUE | TRUE  | FALSE| TRUE | TRUE | TRUE | TRUE | TRUE | TRUE |
| 7   | 6   | FALSE| TRUE | TRUE  | TRUE | TRUE | TRUE | TRUE | TRUE | FALSE| FALSE|
| 8   | 7   | TRUE | FALSE| TRUE  | TRUE | TRUE | TRUE | FALSE| TRUE | TRUE | TRUE |
| 9   | 8   | TRUE | TRUE | TRUE  | TRUE | TRUE | TRUE | TRUE | TRUE | TRUE | TRUE |
| 10  | 9   | TRUE | TRUE | TRUE  | TRUE | FALSE| TRUE | TRUE | FALSE| TRUE | TRUE |
| 11  | 10  | TRUE | TRUE | FALSE | TRUE | TRUE | TRUE | FALSE| TRUE | TRUE | TRUE |
| 12  | 11  | TRUE | TRUE | TRUE  | TRUE | TRUE | FALSE| TRUE | TRUE | TRUE | TRUE |
| 13  | 12  | FALSE| TRUE | TRUE  | FALSE| TRUE | TRUE | TRUE | TRUE | TRUE | TRUE |
| 14  | 13  | TRUE | TRUE | TRUE  | TRUE | TRUE | TRUE | FALSE| TRUE | FALSE| TRUE |
| 15  | 14  | TRUE | FALSE| TRUE  | TRUE | TRUE | TRUE | TRUE | TRUE | TRUE | FALSE|
| 16  | 15  | TRUE | TRUE | TRUE  | TRUE | TRUE | TRUE | TRUE | FALSE| TRUE | TRUE |
| 17  | 16  | TRUE | TRUE | FALSE | TRUE | FALSE| TRUE | TRUE | TRUE | TRUE | TRUE |
| 18  | 17  | TRUE | TRUE | TRUE  | TRUE | TRUE | FALSE| TRUE | TRUE | TRUE | TRUE |
| 19  | 18  | FALSE| TRUE | TRUE  | TRUE | TRUE | TRUE | FALSE| TRUE | FALSE| TRUE |
| 20  | 19  | TRUE | TRUE | TRUE  | FALSE| TRUE | TRUE | TRUE | TRUE | TRUE | TRUE |
| 21  | 20  | TRUE | TRUE | TRUE  | TRUE | TRUE | TRUE | TRUE | TRUE | TRUE | TRUE |
| 22  | 21  | TRUE | FALSE| TRUE  | TRUE | TRUE | TRUE | FALSE| FALSE| TRUE | TRUE |
| 23  | 22  | TRUE | TRUE | TRUE  | TRUE | FALSE| TRUE | TRUE | TRUE | TRUE | FALSE|
| 24  | 23  | TRUE | TRUE | FALSE | TRUE | TRUE | TRUE | TRUE | TRUE | TRUE | TRUE |
| 25  | 24  | TRUE | TRUE | TRUE  | TRUE | TRUE | FALSE| TRUE | TRUE | FALSE| TRUE |
| 26  | 25  | TRUE | TRUE | TRUE  | TRUE | TRUE | TRUE | TRUE | TRUE | TRUE | TRUE |
| 27  | 26  | FALSE| TRUE | TRUE  | TRUE | TRUE | TRUE | FALSE| TRUE | TRUE | TRUE |
| 28  | 27  | TRUE | TRUE | TRUE  | FALSE| TRUE | TRUE | TRUE | TRUE | TRUE | TRUE |
| 29  | 28  | TRUE | TRUE | FALSE | TRUE | TRUE | TRUE | TRUE | FALSE| TRUE | TRUE |
| 30  | 29  | TRUE | FALSE| TRUE  | TRUE | FALSE| TRUE | FALSE| TRUE | TRUE | TRUE |
| 31  | 30  | TRUE | TRUE | TRUE  | TRUE | TRUE | TRUE | TRUE | TRUE | TRUE | FALSE|
| 32  | 31  | TRUE | TRUE | TRUE  | TRUE | TRUE | FALSE| TRUE | TRUE | TRUE | TRUE |

Freeze row 1. Column widths as specified above.

---

## Tab 3: Weekly Summary

Auto-calculated from March Tracker data. 5 weeks (W1-W5) × 10 habits.

### Layout

Row 1: Title banner "WEEKLY SUMMARY: MARCH 2026" (merged A1:M1)
Row 2: Column headers

| Col | Header          | Width |
|-----|-----------------|-------|
| A   | Week            | 60    |
| B   | Dates           | 130   |
| C   | Habit 1         | 100   | (pulls from Habit Setup)
| D   | Habit 2         | 100   |
| E   | Habit 3         | 100   |
| F   | Habit 4         | 100   |
| G   | Habit 5         | 100   |
| H   | Habit 6         | 100   |
| I   | Habit 7         | 100   |
| J   | Habit 8         | 100   |
| K   | Habit 9         | 100   |
| L   | Habit 10        | 100   |
| M   | Weekly %        | 80    |

Headers C2:L2 pull from Habit Setup: ='Habit Setup'!B6, ='Habit Setup'!B7, etc.

### Weekly Data Rows (Rows 3-7)

Each cell formula uses COUNTIFS on March Tracker to count TRUE values within each week's day range.

Week 1 (Days 1-7): Row 3
- A3: Week 1
- B3: Mar 1-7
- C3: =IFERROR(COUNTIFS('March Tracker'!A$2:A$32,">="&1,'March Tracker'!A$2:A$32,"<="&7,'March Tracker'!C$2:C$32,TRUE),0)
- D3: =IFERROR(COUNTIFS('March Tracker'!A$2:A$32,">="&1,'March Tracker'!A$2:A$32,"<="&7,'March Tracker'!D$2:D$32,TRUE),0)
- E3: =IFERROR(COUNTIFS('March Tracker'!A$2:A$32,">="&1,'March Tracker'!A$2:A$32,"<="&7,'March Tracker'!E$2:E$32,TRUE),0)
- F3: =IFERROR(COUNTIFS('March Tracker'!A$2:A$32,">="&1,'March Tracker'!A$2:A$32,"<="&7,'March Tracker'!F$2:F$32,TRUE),0)
- G3: =IFERROR(COUNTIFS('March Tracker'!A$2:A$32,">="&1,'March Tracker'!A$2:A$32,"<="&7,'March Tracker'!G$2:G$32,TRUE),0)
- H3: =IFERROR(COUNTIFS('March Tracker'!A$2:A$32,">="&1,'March Tracker'!A$2:A$32,"<="&7,'March Tracker'!H$2:H$32,TRUE),0)
- I3: =IFERROR(COUNTIFS('March Tracker'!A$2:A$32,">="&1,'March Tracker'!A$2:A$32,"<="&7,'March Tracker'!I$2:I$32,TRUE),0)
- J3: =IFERROR(COUNTIFS('March Tracker'!A$2:A$32,">="&1,'March Tracker'!A$2:A$32,"<="&7,'March Tracker'!J$2:J$32,TRUE),0)
- K3: =IFERROR(COUNTIFS('March Tracker'!A$2:A$32,">="&1,'March Tracker'!A$2:A$32,"<="&7,'March Tracker'!K$2:K$32,TRUE),0)
- L3: =IFERROR(COUNTIFS('March Tracker'!A$2:A$32,">="&1,'March Tracker'!A$2:A$32,"<="&7,'March Tracker'!L$2:L$32,TRUE),0)
- M3: =IFERROR((C3+D3+E3+F3+G3+H3+I3+J3+K3+L3)/(7*10),0): format as %

Week 2 (Days 8-14): Row 4
- A4: Week 2, B4: Mar 8-14
- C4:L4: Same COUNTIFS pattern with ">="&8 and "<="&14
- M4: =(C4+D4+E4+F4+G4+H4+I4+J4+K4+L4)/(7*10): format as %

Week 3 (Days 15-21): Row 5
- A5: Week 3, B5: Mar 15-21
- C5:L5: ">="&15, "<="&21
- M5: sum/70

Week 4 (Days 22-28): Row 6
- A6: Week 4, B6: Mar 22-28
- C6:L6: ">="&22, "<="&28
- M6: sum/70

Week 5 (Days 29-31): Row 7
- A7: Week 5, B7: Mar 29-31
- C7:L7: ">="&29, "<="&31
- M7: =IFERROR((C7+D7+E7+F7+G7+H7+I7+J7+K7+L7)/(3*10),0): format as %

Row 8: Monthly Total row
- A8: TOTAL, B8: Full Month
- C8: =IFERROR(COUNTIF('March Tracker'!C2:C32,TRUE),0): through L8 for each habit col
- M8: =IFERROR(SUM(C8:L8)/(31*10),0): format as %

Freeze row 2.

---

## Tab 0: Dashboard

Build this tab LAST so all cross-references resolve.

### Layout

Row 1: Title banner "BLOOM HABIT TRACKER" (merged A1:N1)
Row 2: Subtitle "March 2026: Monthly Overview" (merged A2:N2)
Row 3: blank spacer
Row 4: Section header "HABIT PERFORMANCE" (A4:F4 merged)
Row 5: Column headers for habit table

| Col | Header           | Width |
|-----|------------------|-------|
| A   | #                | 40    |
| B   | Habit            | 200   |
| C   | Days Done        | 90    |
| D   | % Complete       | 90    |
| E   | Current Streak   | 100   |
| F   | Longest Streak   | 110   |
| G   | Trend            | 120   | (SPARKLINE)
| H   | Streak Bar       | 200   | (REPT visual)

Rows 6-15: One row per habit (10 habits)

#### Habit 1 row (Row 6):
- A6: 1
- B6: ='Habit Setup'!B6
- C6: =IFERROR(COUNTIF('March Tracker'!C2:C32,TRUE),0)
- D6: =IFERROR(C6/31,0): format as %
- E6: =IFERROR(LET(vals,'March Tracker'!C2:C32,n,COUNTA(vals),streak,0,i,n,REDUCE(0,SEQUENCE(n,1,n,-1),LAMBDA(acc,j,IF(INDEX(vals,j)=TRUE,acc+1,0)))),0)

  SIMPLER current streak formula (counts from last day backwards until FALSE):
  E6: =IFERROR(COUNTIF(OFFSET('March Tracker'!C$32,0,0,-MATCH(FALSE,IF(OFFSET('March Tracker'!C$2,MATCH(TRUE,'March Tracker'!C$2:C$32,0)-1,0,31-MATCH(TRUE,'March Tracker'!C$2:C$32,0)+1,1)=FALSE,TRUE,FALSE),0),1),TRUE),0)

  USE THIS SIMPLER ALTERNATIVE for current streak:
  E6: =IFERROR(SUMPRODUCT((MMULT(--(OFFSET('March Tracker'!C$2,31-ROW(INDIRECT("A1:A31")),0,1,1)=TRUE),ROW(INDIRECT("A1:A31"))^0)>0)*((MMULT(--(OFFSET('March Tracker'!C$2,31-ROW(INDIRECT("A1:A31")),0,1,1)=FALSE),ROW(INDIRECT("A1:A31"))^0)=0))),0)

  BEST SIMPLE current streak (from bottom, count consecutive TRUEs):
  E6: =IFERROR(MATCH(FALSE,ARRAYFORMULA(OFFSET('March Tracker'!C$2,SEQUENCE(31,1,30,-1),0,1,1)=TRUE),0)-1,31)

- F6: Longest streak formula:
  F6: =IFERROR(MAX(MMULT(--(OFFSET('March Tracker'!C$2,ROW(INDIRECT("A0:A30"))-1,0,1,1)=TRUE),TRANSPOSE(ISNUMBER(MATCH(ROW(INDIRECT("A1:A31")),SEQUENCE(31),0))))),0)

  USE THIS SIMPLER ALTERNATIVE for longest streak:
  F6: =IFERROR(LET(d,ARRAYFORMULA(IF('March Tracker'!C2:C32=TRUE,1,0)),n,31,groups,ARRAYFORMULA(d*MMULT(TRANSPOSE(SEQUENCE(n,n,0)>=SEQUENCE(n,1,0))*TRANSPOSE(SEQUENCE(n,n,0)<SEQUENCE(n,1)),SEQUENCE(n,1,0)^0)),MAX(groups)),0)

  PRACTICAL longest streak (works without LET complexity):
  F6: =IFERROR(MAX(FREQUENCY(IF('March Tracker'!C2:C32=TRUE,ROW('March Tracker'!C2:C32)),IF('March Tracker'!C2:C32=FALSE,ROW('March Tracker'!C2:C32)))),0)

- G6 (SPARKLINE: weekly trend line):
  =IFERROR(SPARKLINE({'Weekly Summary'!C3,'Weekly Summary'!C4,'Weekly Summary'!C5,'Weekly Summary'!C6,'Weekly Summary'!C7},{"charttype","line";"lineWidth",2;"color","#4CAF7D";"empty","ignore"}),)

- H6 (REPT streak bar):
  =IFERROR(REPT("█",E6)&REPT("░",MAX(0,10-E6)),"")

Rows 7-15: Same formulas as Row 6, but shift column references:
- Row 7 (Habit 2): uses column D in March Tracker, Weekly Summary col D
- Row 8 (Habit 3): column E
- Row 9 (Habit 4): column F
- Row 10 (Habit 5): column G
- Row 11 (Habit 6): column H
- Row 12 (Habit 7): column I
- Row 13 (Habit 8): column J
- Row 14 (Habit 9): column K
- Row 15 (Habit 10): column L

Row 16: blank spacer

Row 17: Section header "MONTH AT A GLANCE" (merged A17:H17)
Row 18:
- A18: "Total Completions"
- B18: =IFERROR(SUM('March Tracker'!M2:M32),0)
- C18: "Overall %"
- D18: =IFERROR(SUM('March Tracker'!M2:M32)/(31*10),0): format as %
- E18: "Best Day"
- F18: =IFERROR(INDEX('March Tracker'!A2:A32,MATCH(MAX('March Tracker'!M2:M32),'March Tracker'!M2:M32,0)),0)
- G18: "Best Habit"
- H18: =IFERROR(INDEX('Habit Setup'!B6:B15,MATCH(MAX(C6,C7,C8,C9,C10,C11,C12,C13,C14,C15),C6:C15,0)),"")

Freeze rows 1-5.

---

## Charts

### Chart 1: Weekly Completion % Bar Chart
- Type: COLUMN chart
- Title: "Weekly Completion Rate"
- Source: Weekly Summary tab (sheetId 3)
  - Domain (X-axis labels): rows 2-7, col 0 (column A = Week)
  - Series: rows 2-7, col 12 (column M = Weekly %)
- Colors: series fill #4CAF7D
- Position: anchor at Dashboard row 20, col A (row index 19, col index 0)
  offsetX: 10, offsetY: 10, width: 500, height: 280
- Legend: BOTTOM

### Chart 2: Habit Completion Count Bar Chart
- Type: BAR chart (horizontal)
- Title: "Habits Completed (Days in Month)"
- Source: Dashboard tab (sheetId 0)
  - Domain: rows 5-15, col 1 (col B = Habit names), row indices 5-14
  - Series: rows 5-15, col 2 (col C = Days Done), row indices 5-14
- Colors: #A8D5A2
- Position: anchor at Dashboard row 20, col F (row index 19, col index 5)
  offsetX: 10, offsetY: 10, width: 500, height: 280
- Legend: NONE

---

## Conditional Formatting

### On March Tracker (sheetId 1):

1. Checkbox TRUE → green fill
   - Range: C2:L32 (rows 1-31, cols 2-11 zero-indexed)
   - Condition: CUSTOM_FORMULA =C2=TRUE
   - Background: #C8E6C9 {red:0.784, green:0.902, blue:0.788}

2. Checkbox FALSE on filled rows → light red fill
   - Range: C2:L32
   - Condition: CUSTOM_FORMULA =AND(C2=FALSE,$A2<>"")
   - Background: #FFCDD2 {red:1.0, green:0.804, blue:0.824}

### On Dashboard (sheetId 0):

3. % Complete ≥ 80% → dark green text
   - Range: D6:D15 (col 3, rows 5-14 zero-indexed)
   - Condition: NUMBER_GREATER_THAN_EQ 0.8
   - Text color: #2E7D52

4. % Complete < 50% → orange text
   - Range: D6:D15
   - Condition: NUMBER_LESS_THAN 0.5
   - Text color: #E65100 {red:0.902, green:0.318, blue:0.0}

### On Weekly Summary (sheetId 3):

5. Weekly % ≥ 0.8 → green fill on M col
   - Range: M3:M8 (col 12, rows 2-7 zero-indexed)
   - Condition: NUMBER_GREATER_THAN_EQ 0.8
   - Background: #C8E6C9

6. Weekly % < 0.5 → yellow fill on M col
   - Range: M3:M8
   - Condition: NUMBER_LESS_THAN 0.5
   - Background: #FFF9C4 {red:1.0, green:0.976, blue:0.769}

---

## Data Validation

### March Tracker (sheetId 1):

1. Checkboxes on C2:L32
   - Type: boolean (checkbox)
   - Use setDataValidation with condition type BOOLEAN
   - Strict: true

---

## Frozen Rows / Columns

| Tab              | Freeze Rows | Freeze Cols |
|------------------|-------------|-------------|
| Dashboard        | 5           | 0           |
| March Tracker    | 1           | 2           |
| Habit Setup      | 5           | 0           |
| Weekly Summary   | 2           | 0           |
| _Ref             | 1           | 0           |

Note: Do NOT freeze across merged cells. Dashboard title rows 1-2 are merged but freeze is set to row 5 (below the merges).

---

## Cross-Sheet Formula Logic

Key reference cells:
- 'Habit Setup'!B2 = Active Month (text: "March")
- 'Habit Setup'!B3 = Active Year (number: 2026)
- '_Ref'!A2:A13 = Month names list (used in MATCH for month number)

March Tracker date formula:
  =DATE('Habit Setup'!B3, MATCH('Habit Setup'!B2,'_Ref'!A2:A13,0), A2)
  This converts "March" + 2026 + day number → actual date value.

Dashboard Days Done (e.g., Habit 1):
  =COUNTIF('March Tracker'!C2:C32,TRUE)
  No month filter needed: tracker is one month per sheet.

Weekly Summary COUNTIFS:
  Uses 'March Tracker'!A column (day numbers) as the date filter dimension,
  filtering rows where day >= week_start AND day <= week_end.

---

## Number Formats

- Column D (% Complete) on Dashboard: format as "0%"
- Column N (% Done) on March Tracker: format as "0%"
- Column M (Weekly %) on Weekly Summary: format as "0%"
- Column D18 on Dashboard: format as "0%"
- Column B on March Tracker: format as "MMM D" (e.g., Mar 1)

---

## Build Order

1. Create spreadsheet with all 5 sheets (sheetIds 0-4, sheet 4 hidden)
2. Write _Ref data (sheetId 4)
3. Write Habit Setup data (sheetId 2): static values first, then formatting
4. Write March Tracker headers and sample data (sheetId 1)
5. Write Weekly Summary formulas (sheetId 3)
6. Write Dashboard formulas (sheetId 0): LAST
7. Apply all formatting (one batchUpdate per tab)
8. Set data validation (checkboxes on March Tracker)
9. Add conditional formatting
10. Add charts (Chart 1 weekly bars, Chart 2 habit comparison)
11. Set frozen rows/columns

---

## Final Requirements Checklist

- [ ] All formulas are native Google Sheets (no Apps Script)
- [ ] All cross-sheet formulas wrapped in IFERROR
- [ ] Dashboard pulls from Habit Setup and March Tracker
- [ ] Checkboxes are functional (boolean data validation)
- [ ] Sample data covers all 31 days with variety to trigger all conditional formatting
- [ ] Charts render with data on first open
- [ ] Tab colors set: Dashboard=#4CAF7D, MarchTracker=#A8D5A2, HabitSetup=#2E7D52, WeeklySummary=#A8D5A2
- [ ] Frozen rows in place per table above
- [ ] No #REF!, #NAME?, or #ERROR! cells visible
- [ ] Spreadsheet title: "Bloom Habit Tracker: 30-Day Monthly Planner"
- [ ] Output spreadsheet ID and shareable link when done
- [ ] Etsy-ready: clean, minimal, soft greens and whites throughout
