import json, os

OUT = r"D:\Ai_Sandbox\agentsHQ\Dashboards4Sale\tmp"

# ── COLORS ──────────────────────────────────────────────────────────────────
DARK_BG      = {"red": 0.110, "green": 0.157, "blue": 0.200}  # #1C2833
DARKER_BG    = {"red": 0.078, "green": 0.110, "blue": 0.145}  # #141C25
CARD_BG      = {"red": 0.137, "green": 0.196, "blue": 0.251}  # #233240
SECTION_TEAL = {"red": 0.024, "green": 0.361, "blue": 0.329}  # #065C54
INCOME_CARD  = {"red": 0.039, "green": 0.180, "blue": 0.133}  # #0A2E22
SPEND_CARD   = {"red": 0.196, "green": 0.059, "blue": 0.059}  # #320F0F
REMAIN_CARD  = {"red": 0.059, "green": 0.133, "blue": 0.208}  # #0F2235
SAVINGS_CARD = {"red": 0.196, "green": 0.157, "blue": 0.020}  # #322805
TEAL         = {"red": 0.000, "green": 0.706, "blue": 0.651}  # #00B4A6
CORAL        = {"red": 1.000, "green": 0.420, "blue": 0.420}  # #FF6B6B
GOLD         = {"red": 1.000, "green": 0.820, "blue": 0.400}  # #FFD166
GREEN        = {"red": 0.180, "green": 0.800, "blue": 0.443}  # #2ECC71
WHITE        = {"red": 1.000, "green": 1.000, "blue": 1.000}
SECONDARY    = {"red": 0.584, "green": 0.647, "blue": 0.651}  # #95A5A6
BORDER       = {"red": 0.220, "green": 0.290, "blue": 0.353}  # #384A5A
ALT_ROW      = {"red": 0.094, "green": 0.137, "blue": 0.180}  # #182330
GOLD_DARK    = {"red": 0.500, "green": 0.400, "blue": 0.050}  # dark gold text

# ── HELPERS ─────────────────────────────────────────────────────────────────
def rng(sid, r1, r2, c1, c2):
    return {"sheetId": sid, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}

def repeat(range_d, bg=None, tc=None, bold=False, italic=False, fs=None,
           ha=None, va=None, nf=None, wrap=None):
    fmt = {}
    if bg:  fmt["backgroundColor"] = bg
    tf = {}
    if tc:    tf["foregroundColor"] = tc
    if bold:  tf["bold"] = True
    if italic:tf["italic"] = True
    if fs:    tf["fontSize"] = fs
    if tf:    fmt["textFormat"] = tf
    if ha:    fmt["horizontalAlignment"] = ha
    if va:    fmt["verticalAlignment"] = va
    if nf:    fmt["numberFormat"] = nf
    if wrap:  fmt["wrapStrategy"] = wrap
    fields = "userEnteredFormat(" + ",".join(fmt.keys()) + ")"
    return {"repeatCell": {"range": range_d, "cell": {"userEnteredFormat": fmt}, "fields": fields}}

def merge(sid, r1, r2, c1, c2):
    return {"mergeCells": {"range": rng(sid, r1, r2, c1, c2), "mergeType": "MERGE_ALL"}}

def cw(sid, c1, c2, px):
    return {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": c1, "endIndex": c2}, "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def rh(sid, r1, r2, px):
    return {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": r1, "endIndex": r2}, "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def freeze(sid, rows=0, cols=0):
    return {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": rows, "frozenColumnCount": cols}}, "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}}

def borders(range_d, color=None, outer="SOLID_MEDIUM", inner="SOLID"):
    c = color or BORDER
    return {"updateBorders": {"range": range_d,
        "top": {"style": outer, "color": c}, "bottom": {"style": outer, "color": c},
        "left": {"style": outer, "color": c}, "right": {"style": outer, "color": c},
        "innerHorizontal": {"style": inner, "color": c},
        "innerVertical": {"style": inner, "color": c}}}

def cf_bool(ranges, formula, bg=None, tc=None, bold=False, idx=0):
    fmt = {}
    if bg: fmt["backgroundColor"] = bg
    tf = {}
    if tc: tf["foregroundColor"] = tc
    if bold: tf["bold"] = True
    if tf: fmt["textFormat"] = tf
    return {"addConditionalFormatRule": {"rule": {"ranges": ranges,
        "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": formula}]},
        "format": fmt}}, "index": idx}}

def save(fn, data):
    p = os.path.join(OUT, fn)
    with open(p, "w") as f:
        json.dump(data, f)
    print(f"  OK {fn} ({len(json.dumps(data))//1024}kb)")

# ════════════════════════════════════════════════════════════════════════════
# PHASE 1 — CLEAR ALL SHEETS
# ════════════════════════════════════════════════════════════════════════════
print("Generating phase1_clear.json...")
reqs = []
for sid in range(7):
    reqs.append({"unmergeCells": {"range": rng(sid, 0, 300, 0, 26)}})
    reqs.append(repeat(rng(sid, 0, 300, 0, 26), bg={"red":1,"green":1,"blue":1},
                       tc={"red":0,"green":0,"blue":0}, bold=False, italic=False, fs=10, ha="LEFT", va="BOTTOM"))
    reqs.append({"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": 0, "frozenColumnCount": 0}}, "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}})
save("phase1_clear.json", {"requests": reqs})

# ════════════════════════════════════════════════════════════════════════════
# PHASE 2 — DARK BACKGROUNDS ON ALL SHEETS
# ════════════════════════════════════════════════════════════════════════════
print("Generating phase2_darkbg.json...")
reqs = []
for sid in range(6):  # 0-5 visible tabs
    reqs.append(repeat(rng(sid, 0, 300, 0, 26), bg=DARK_BG, tc=WHITE))
# _Ref stays light (hidden anyway)
save("phase2_darkbg.json", {"requests": reqs})

# ════════════════════════════════════════════════════════════════════════════
# PHASE 3 — SETUP TAB FORMAT (sheetId=5)
# ════════════════════════════════════════════════════════════════════════════
print("Generating phase3_setup_format.json...")
SID = 5
reqs = []

# Title row
reqs.append(merge(SID, 0, 1, 0, 6))
reqs.append(rh(SID, 0, 1, 55))
reqs.append(repeat(rng(SID, 0, 1, 0, 6), bg=DARKER_BG, tc=TEAL, bold=True, fs=16, ha="CENTER", va="MIDDLE"))

# Subtitle
reqs.append(merge(SID, 1, 2, 0, 6))
reqs.append(rh(SID, 1, 2, 24))
reqs.append(repeat(rng(SID, 1, 2, 0, 6), bg=DARK_BG, tc=SECONDARY, italic=True, fs=9, ha="CENTER", va="MIDDLE"))

# Section: INCOME
reqs.append(merge(SID, 3, 4, 0, 6))
reqs.append(repeat(rng(SID, 3, 4, 0, 6), bg=SECTION_TEAL, tc=WHITE, bold=True, fs=10, ha="LEFT", va="MIDDLE"))
reqs.append(rh(SID, 3, 4, 28))

# Income rows 4-7 (rows 5-8)
reqs.append(repeat(rng(SID, 4, 8, 0, 4), bg=CARD_BG, tc=WHITE, va="MIDDLE"))
reqs.append(repeat(rng(SID, 4, 7, 0, 1), bg=CARD_BG, tc=SECONDARY, fs=9))
reqs.append(repeat(rng(SID, 4, 8, 2, 3), bg=INCOME_CARD, tc=GREEN, bold=True,
                   nf={"type":"CURRENCY","pattern":"$#,##0.00"}))
reqs.append(repeat(rng(SID, 7, 8, 0, 1), bg=INCOME_CARD, tc=GREEN, bold=True, fs=10))
reqs.append(repeat(rng(SID, 7, 8, 2, 3), bg=INCOME_CARD, tc=GREEN, bold=True, fs=12,
                   nf={"type":"CURRENCY","pattern":"$#,##0.00"}))
reqs.append(rh(SID, 4, 8, 30))

# Section: SPLIT RATIOS
reqs.append(merge(SID, 9, 10, 0, 6))
reqs.append(repeat(rng(SID, 9, 10, 0, 6), bg=SECTION_TEAL, tc=WHITE, bold=True, fs=10, ha="LEFT", va="MIDDLE"))
reqs.append(rh(SID, 9, 10, 28))

# Ratio rows
reqs.append(repeat(rng(SID, 10, 14, 0, 4), bg=CARD_BG, tc=WHITE, va="MIDDLE"))
reqs.append(repeat(rng(SID, 10, 11, 2, 3), bg={"red":0.039,"green":0.180,"blue":0.133}, tc=TEAL, bold=True, fs=13, ha="CENTER", nf={"type":"NUMBER","pattern":"0"}))
reqs.append(repeat(rng(SID, 11, 12, 2, 3), bg=SPEND_CARD, tc=CORAL, bold=True, fs=13, ha="CENTER", nf={"type":"NUMBER","pattern":"0"}))
reqs.append(repeat(rng(SID, 12, 13, 2, 3), bg=SAVINGS_CARD, tc=GOLD, bold=True, fs=13, ha="CENTER", nf={"type":"NUMBER","pattern":"0"}))
reqs.append(repeat(rng(SID, 13, 14, 0, 1), bg=CARD_BG, tc=SECONDARY, bold=True))
reqs.append(repeat(rng(SID, 13, 14, 2, 3), bg=CARD_BG, tc=WHITE, bold=True, ha="CENTER"))
reqs.append(rh(SID, 10, 14, 34))

# Conditional on total row
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 13, 14, 2, 3)],
    "booleanRule": {"condition": {"type": "NUMBER_EQ", "values": [{"userEnteredValue": "100"}]},
    "format": {"backgroundColor": INCOME_CARD, "textFormat": {"foregroundColor": GREEN, "bold": True}}}}, "index": 0}})
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 13, 14, 2, 3)],
    "booleanRule": {"condition": {"type": "NUMBER_NOT_EQ", "values": [{"userEnteredValue": "100"}]},
    "format": {"backgroundColor": SPEND_CARD, "textFormat": {"foregroundColor": CORAL, "bold": True}}}}, "index": 1}})

# Section: CALCULATED BUDGETS
reqs.append(merge(SID, 15, 16, 0, 6))
reqs.append(repeat(rng(SID, 15, 16, 0, 6), bg=SECTION_TEAL, tc=WHITE, bold=True, fs=10, ha="LEFT", va="MIDDLE"))
reqs.append(rh(SID, 15, 16, 28))

reqs.append(repeat(rng(SID, 16, 19, 0, 4), bg=CARD_BG, tc=WHITE, va="MIDDLE"))
reqs.append(repeat(rng(SID, 16, 17, 2, 3), bg=INCOME_CARD, tc=TEAL, bold=True, nf={"type":"CURRENCY","pattern":"$#,##0.00"}))
reqs.append(repeat(rng(SID, 17, 18, 2, 3), bg=SPEND_CARD, tc=CORAL, bold=True, nf={"type":"CURRENCY","pattern":"$#,##0.00"}))
reqs.append(repeat(rng(SID, 18, 19, 2, 3), bg=SAVINGS_CARD, tc=GOLD, bold=True, nf={"type":"CURRENCY","pattern":"$#,##0.00"}))
reqs.append(rh(SID, 16, 19, 34))

# HOW TO USE section
reqs.append(merge(SID, 21, 22, 0, 6))
reqs.append(repeat(rng(SID, 21, 22, 0, 6), bg=DARKER_BG, tc=TEAL, bold=True, fs=13, ha="CENTER", va="MIDDLE"))
reqs.append(rh(SID, 21, 22, 40))

# Step headers
reqs.append(repeat(rng(SID, 22, 23, 0, 6), bg=CARD_BG, tc=SECONDARY, bold=True, fs=9, ha="CENTER"))
reqs.append(rh(SID, 22, 23, 22))

for i in range(9):  # 9 steps
    row = 23 + i
    reqs.append(repeat(rng(SID, row, row+1, 0, 1), bg=SECTION_TEAL, tc=WHITE, bold=True, fs=12, ha="CENTER", va="MIDDLE"))
    reqs.append(repeat(rng(SID, row, row+1, 1, 2), bg=CARD_BG, tc=WHITE, bold=True, va="MIDDLE"))
    reqs.append(repeat(rng(SID, row, row+1, 2, 4), bg=CARD_BG, tc=SECONDARY, va="MIDDLE", wrap="WRAP"))
    reqs.append(repeat(rng(SID, row, row+1, 4, 6), bg=ALT_ROW, tc=SECONDARY, italic=True, va="MIDDLE", wrap="WRAP"))
reqs.append(rh(SID, 23, 32, 42))

# QUICK TIPS section
reqs.append(merge(SID, 33, 34, 0, 6))
reqs.append(repeat(rng(SID, 33, 34, 0, 6), bg=SAVINGS_CARD, tc=GOLD, bold=True, fs=12, ha="CENTER", va="MIDDLE"))
reqs.append(rh(SID, 33, 34, 36))

for i in range(5):
    row = 34 + i
    reqs.append(repeat(rng(SID, row, row+1, 0, 1), bg=SAVINGS_CARD, tc=GOLD, bold=True, fs=13, ha="CENTER", va="MIDDLE"))
    reqs.append(repeat(rng(SID, row, row+1, 1, 3), bg=CARD_BG, tc=WHITE, bold=True, va="MIDDLE"))
    reqs.append(repeat(rng(SID, row, row+1, 3, 6), bg=ALT_ROW, tc=SECONDARY, italic=True, va="MIDDLE", wrap="WRAP"))
reqs.append(rh(SID, 34, 39, 42))

# Borders
reqs.append(borders(rng(SID, 3, 19, 0, 4), BORDER))
reqs.append(borders(rng(SID, 22, 39, 0, 6), BORDER))

# Column widths
for c,w in [(0,40),(1,200),(2,160),(3,200),(4,240),(5,60)]:
    reqs.append(cw(SID, c, c+1, w))

# Active month dropdown validation
reqs.append({"setDataValidation": {"range": rng(SID, 2, 3, 2, 3),
    "rule": {"condition": {"type": "ONE_OF_RANGE", "values": [{"userEnteredValue": "=_Ref!$A$2:$A$13"}]}, "strict": True, "showCustomUi": True}}})

reqs.append(freeze(SID, 1))
save("phase3_setup_format.json", {"requests": reqs})

# ════════════════════════════════════════════════════════════════════════════
# PHASE 4 — TRANSACTIONS FORMAT (sheetId=1)
# ════════════════════════════════════════════════════════════════════════════
print("Generating phase4_txn_format.json...")
SID = 1
reqs = []

# Header row
reqs.append(repeat(rng(SID, 0, 1, 0, 9), bg=DARKER_BG, tc=TEAL, bold=True, fs=10, ha="CENTER", va="MIDDLE"))
reqs.append(rh(SID, 0, 1, 36))

# Date format col A
reqs.append(repeat(rng(SID, 1, 1000, 0, 1), nf={"type":"DATE","pattern":"MM/dd/yyyy"}))
# Amount format col F
reqs.append(repeat(rng(SID, 1, 1000, 5, 6), nf={"type":"CURRENCY","pattern":"$#,##0.00"}))

# Alternating rows
for i in range(1, 51):
    bg = ALT_ROW if i % 2 == 0 else DARK_BG
    reqs.append(repeat(rng(SID, i, i+1, 0, 9), bg=bg))

# Conditional: Income row = green tint
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 1, 1000, 0, 9)],
    "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": '=$C2="Income"'}]},
    "format": {"backgroundColor": {"red":0.039,"green":0.180,"blue":0.133}}}}, "index": 0}})
# Conditional: Expense row = red tint
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 1, 1000, 0, 9)],
    "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": '=$C2="Expense"'}]},
    "format": {"backgroundColor": SPEND_CARD}}}, "index": 1}})
# Conditional: Amount > 1000 = gold bold
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 1, 1000, 5, 6)],
    "booleanRule": {"condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "1000"}]},
    "format": {"backgroundColor": SAVINGS_CARD, "textFormat": {"foregroundColor": GOLD, "bold": True}}}}, "index": 2}})

# Data validation
reqs.append({"setDataValidation": {"range": rng(SID, 1, 1000, 2, 3), "rule": {"condition": {"type": "ONE_OF_RANGE", "values": [{"userEnteredValue": "=_Ref!$M$2:$M$3"}]}, "strict": True, "showCustomUi": True}}})
reqs.append({"setDataValidation": {"range": rng(SID, 1, 1000, 3, 4), "rule": {"condition": {"type": "ONE_OF_RANGE", "values": [{"userEnteredValue": "=_Ref!$C$2:$C$4"}]}, "strict": True, "showCustomUi": True}}})
reqs.append({"setDataValidation": {"range": rng(SID, 1, 1000, 4, 5), "rule": {"condition": {"type": "ONE_OF_RANGE", "values": [{"userEnteredValue": "=_Ref!$K$2:$K$38"}]}, "strict": True, "showCustomUi": True}}})

# Col widths
for c,w in [(0,115),(1,230),(2,105),(3,135),(4,185),(5,115),(6,115),(7,80),(8,200)]:
    reqs.append(cw(SID, c, c+1, w))
reqs.append(rh(SID, 1, 36, 28))

# Borders on data area
reqs.append(borders(rng(SID, 0, 36, 0, 9), BORDER, "SOLID_MEDIUM", "SOLID"))
reqs.append(freeze(SID, 1))
save("phase4_txn_format.json", {"requests": reqs})

# ════════════════════════════════════════════════════════════════════════════
# PHASE 5 — DASHBOARD FORMAT (sheetId=0)
# ════════════════════════════════════════════════════════════════════════════
print("Generating phase5_dash_format.json...")
SID = 0
reqs = []

# ROW 0 (1): TITLE BANNER
reqs.append(merge(SID, 0, 1, 0, 12))
reqs.append(repeat(rng(SID, 0, 1, 0, 12), bg=DARKER_BG, tc=WHITE, bold=True, fs=20, ha="CENTER", va="MIDDLE"))
reqs.append(rh(SID, 0, 1, 60))

# ROW 1 (2): Info bar
reqs.append(repeat(rng(SID, 1, 2, 0, 12), bg=DARK_BG, tc=SECONDARY, fs=9, ha="CENTER", va="MIDDLE"))
reqs.append(rh(SID, 1, 2, 22))

# ROW 2 (3): Spacer
reqs.append(rh(SID, 2, 3, 10))

# ROW 3 (4): MONTHLY SNAPSHOT header
reqs.append(merge(SID, 3, 4, 0, 12))
reqs.append(repeat(rng(SID, 3, 4, 0, 12), bg=SECTION_TEAL, tc=WHITE, bold=True, fs=10, ha="LEFT", va="MIDDLE"))
reqs.append(rh(SID, 3, 4, 30))

# ROWS 4-6 (5-7): KPI CARDS — 4 cards × 3 cols each
for card_col, card_bg, val_color in [
    (0, INCOME_CARD, GREEN),
    (3, SPEND_CARD, CORAL),
    (6, REMAIN_CARD, WHITE),
    (9, SAVINGS_CARD, GOLD)
]:
    # Label row
    reqs.append(merge(SID, 4, 5, card_col, card_col+3))
    reqs.append(repeat(rng(SID, 4, 5, card_col, card_col+3), bg=card_bg, tc=SECONDARY, bold=True, fs=8, ha="CENTER", va="MIDDLE"))
    # Value row
    reqs.append(merge(SID, 5, 6, card_col, card_col+3))
    reqs.append(repeat(rng(SID, 5, 6, card_col, card_col+3), bg=card_bg, tc=val_color, bold=True, fs=24, ha="CENTER", va="MIDDLE"))
    # Sub-label row
    reqs.append(merge(SID, 6, 7, card_col, card_col+3))
    reqs.append(repeat(rng(SID, 6, 7, card_col, card_col+3), bg=card_bg, tc=SECONDARY, italic=True, fs=8, ha="CENTER", va="MIDDLE"))

# Override remaining card val color conditionally (handled by CF below)
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 5, 6, 6, 9)],
    "booleanRule": {"condition": {"type": "NUMBER_GREATER_THAN_EQ", "values": [{"userEnteredValue": "0"}]},
    "format": {"textFormat": {"foregroundColor": GREEN, "bold": True, "fontSize": 24}}}}, "index": 0}})
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 5, 6, 6, 9)],
    "booleanRule": {"condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "0"}]},
    "format": {"textFormat": {"foregroundColor": CORAL, "bold": True, "fontSize": 24}}}}, "index": 1}})

reqs.append(rh(SID, 4, 5, 26))
reqs.append(rh(SID, 5, 6, 52))
reqs.append(rh(SID, 6, 7, 22))

# ROW 7: Spacer
reqs.append(rh(SID, 7, 8, 12))

# ROW 8 (9): BUDGET VS ACTUAL header
reqs.append(merge(SID, 8, 9, 0, 12))
reqs.append(repeat(rng(SID, 8, 9, 0, 12), bg={"red":0.200,"green":0.082,"blue":0.180}, tc=WHITE, bold=True, fs=10, ha="LEFT", va="MIDDLE"))
reqs.append(rh(SID, 8, 9, 30))

# ROW 9 (10): Table headers
reqs.append(repeat(rng(SID, 9, 10, 0, 12), bg=CARD_BG, tc=SECONDARY, bold=True, fs=9, ha="CENTER", va="MIDDLE"))
reqs.append(rh(SID, 9, 10, 26))

# ROWS 10-13 (11-14): Needs / Wants / Savings / Total
row_colors = [
    (INCOME_CARD, TEAL),
    (SPEND_CARD, CORAL),
    (SAVINGS_CARD, GOLD),
    (DARKER_BG, WHITE),
]
for i, (rbg, rtc) in enumerate(row_colors):
    row = 10 + i
    reqs.append(repeat(rng(SID, row, row+1, 0, 12), bg=rbg, tc=rtc, va="MIDDLE"))
    reqs.append(repeat(rng(SID, row, row+1, 0, 1), bg=rbg, tc=rtc, bold=True, va="MIDDLE"))
    # currency cols
    for col in [2, 4, 6]:
        reqs.append(repeat(rng(SID, row, row+1, col, col+1), bg=rbg, tc=rtc, bold=(i==3),
                           nf={"type":"CURRENCY","pattern":"$#,##0.00"}))
    # % col
    reqs.append(repeat(rng(SID, row, row+1, 8, 9), bg=rbg, tc=rtc, nf={"type":"PERCENT","pattern":"0%"}))

# CF: Difference column green/red
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 10, 13, 6, 7)],
    "booleanRule": {"condition": {"type": "NUMBER_GREATER_THAN_EQ", "values": [{"userEnteredValue": "0"}]},
    "format": {"textFormat": {"foregroundColor": GREEN}}}}, "index": 2}})
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 10, 13, 6, 7)],
    "booleanRule": {"condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "0"}]},
    "format": {"textFormat": {"foregroundColor": CORAL}}}}, "index": 3}})

reqs.append(rh(SID, 10, 14, 32))

# ROW 14: Spacer
reqs.append(rh(SID, 14, 15, 12))

# ROW 15 (16): TOP TRANSACTIONS header
reqs.append(merge(SID, 15, 16, 0, 12))
reqs.append(repeat(rng(SID, 15, 16, 0, 12), bg={"red":0.024,"green":0.157,"blue":0.361}, tc=WHITE, bold=True, fs=10, ha="LEFT", va="MIDDLE"))
reqs.append(rh(SID, 15, 16, 30))

# ROW 16 (17): Transaction table headers
reqs.append(repeat(rng(SID, 16, 17, 0, 12), bg=CARD_BG, tc=SECONDARY, bold=True, fs=9, ha="CENTER"))
reqs.append(rh(SID, 16, 17, 26))

# ROWS 17-26: Transaction data rows (alt colors)
for i in range(10):
    row = 17 + i
    bg = DARK_BG if i % 2 == 0 else ALT_ROW
    reqs.append(repeat(rng(SID, row, row+1, 0, 12), bg=bg, tc=WHITE, va="MIDDLE"))
    # Amount col formatting
    reqs.append(repeat(rng(SID, row, row+1, 4, 5), bg=bg, tc=TEAL, bold=True,
                       nf={"type":"CURRENCY","pattern":"$#,##0.00"}))
reqs.append(rh(SID, 17, 27, 26))

# ROW 27: Spacer
reqs.append(rh(SID, 27, 28, 12))

# ROW 28 (29): SPENDING BREAKDOWN header
reqs.append(merge(SID, 28, 29, 0, 12))
reqs.append(repeat(rng(SID, 28, 29, 0, 12), bg=SECTION_TEAL, tc=WHITE, bold=True, fs=10, ha="LEFT", va="MIDDLE"))
reqs.append(rh(SID, 28, 29, 30))

# ROW 29 (30): Bucket sub-headers
reqs.append(repeat(rng(SID, 29, 30, 0, 12), bg=CARD_BG, tc=SECONDARY, bold=True, fs=9, ha="CENTER"))
reqs.append(rh(SID, 29, 30, 26))

# ROWS 30-32: Bucket rows
bucket_colors = [TEAL, CORAL, GOLD]
for i, bc in enumerate(bucket_colors):
    row = 30 + i
    bg = INCOME_CARD if i==0 else (SPEND_CARD if i==1 else SAVINGS_CARD)
    reqs.append(repeat(rng(SID, row, row+1, 0, 12), bg=bg, tc=bc, va="MIDDLE"))
    reqs.append(repeat(rng(SID, row, row+1, 0, 1), bg=bg, tc=bc, bold=True))
    reqs.append(repeat(rng(SID, row, row+1, 2, 4), bg=bg, tc=WHITE, nf={"type":"CURRENCY","pattern":"$#,##0.00"}))
    reqs.append(repeat(rng(SID, row, row+1, 4, 5), bg=bg, tc=bc, nf={"type":"PERCENT","pattern":"0%"}))
reqs.append(rh(SID, 30, 33, 34))

# ROW 33: Spacer before charts
reqs.append(rh(SID, 33, 34, 16))

# Borders on tables
reqs.append(borders(rng(SID, 4, 7, 0, 12), BORDER))
reqs.append(borders(rng(SID, 9, 14, 0, 12), BORDER))
reqs.append(borders(rng(SID, 16, 27, 0, 12), BORDER))
reqs.append(borders(rng(SID, 29, 33, 0, 12), BORDER))

# Column widths
for c,w in [(0,160),(1,30),(2,130),(3,30),(4,130),(5,30),(6,130),(7,30),(8,80),(9,80),(10,160),(11,140)]:
    reqs.append(cw(SID, c, c+1, w))

reqs.append(freeze(SID, 2))
save("phase5_dash_format.json", {"requests": reqs})

# ════════════════════════════════════════════════════════════════════════════
# PHASE 6 — DEBT TRACKER FORMAT (sheetId=2)
# ════════════════════════════════════════════════════════════════════════════
print("Generating phase6_debt_format.json...")
SID = 2
reqs = []

reqs.append(merge(SID, 0, 1, 0, 10))
reqs.append(repeat(rng(SID, 0, 1, 0, 10), bg=DARKER_BG, tc=CORAL, bold=True, fs=18, ha="CENTER", va="MIDDLE"))
reqs.append(rh(SID, 0, 1, 55))

reqs.append(merge(SID, 1, 2, 0, 10))
reqs.append(repeat(rng(SID, 1, 2, 0, 10), bg=CARD_BG, tc=SECONDARY, italic=True, fs=9, ha="CENTER", va="MIDDLE", wrap="WRAP"))
reqs.append(rh(SID, 1, 2, 28))

# Section: Snowball order tip
reqs.append(merge(SID, 2, 3, 0, 10))
reqs.append(repeat(rng(SID, 2, 3, 0, 10), bg=SPEND_CARD, tc=CORAL, bold=True, fs=9, ha="LEFT", va="MIDDLE"))
reqs.append(rh(SID, 2, 3, 24))

# Headers
reqs.append(repeat(rng(SID, 3, 4, 0, 10), bg=SECTION_TEAL, tc=WHITE, bold=True, fs=9, ha="CENTER", va="MIDDLE"))
reqs.append(rh(SID, 3, 4, 32))

# Data rows
for i in range(8):
    row = 4 + i
    bg = DARK_BG if i % 2 == 0 else ALT_ROW
    reqs.append(repeat(rng(SID, row, row+1, 0, 10), bg=bg, tc=WHITE, va="MIDDLE"))
    reqs.append(repeat(rng(SID, row, row+1, 2, 3), bg=bg, tc=WHITE, nf={"type":"CURRENCY","pattern":"$#,##0.00"}))
    reqs.append(repeat(rng(SID, row, row+1, 3, 4), bg=bg, tc=SECONDARY, nf={"type":"PERCENT","pattern":"0.00%"}))
    for c in [4, 5, 6, 8]:
        reqs.append(repeat(rng(SID, row, row+1, c, c+1), bg=bg, tc=WHITE, nf={"type":"CURRENCY","pattern":"$#,##0.00"}))
reqs.append(rh(SID, 4, 12, 32))

# Totals row
reqs.append(repeat(rng(SID, 12, 13, 0, 10), bg=DARKER_BG, tc=TEAL, bold=True, va="MIDDLE"))
reqs.append(repeat(rng(SID, 12, 13, 2, 3), bg=DARKER_BG, tc=TEAL, bold=True, nf={"type":"CURRENCY","pattern":"$#,##0.00"}))
for c in [4, 5, 6, 8]:
    reqs.append(repeat(rng(SID, 12, 13, c, c+1), bg=DARKER_BG, tc=TEAL, bold=True, nf={"type":"CURRENCY","pattern":"$#,##0.00"}))
reqs.append(rh(SID, 12, 13, 32))

# Debt-free date row
reqs.append(merge(SID, 14, 15, 0, 5))
reqs.append(repeat(rng(SID, 14, 15, 0, 5), bg=CARD_BG, tc=GOLD, bold=True, fs=10, va="MIDDLE"))
reqs.append(repeat(rng(SID, 14, 15, 5, 7), bg=INCOME_CARD, tc=GREEN, bold=True, fs=12, ha="CENTER", va="MIDDLE",
                   nf={"type":"DATE","pattern":"mmmm yyyy"}))
reqs.append(rh(SID, 14, 15, 36))

# CF: Status column
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 4, 12, 9, 10)],
    "booleanRule": {"condition": {"type": "TEXT_CONTAINS", "values": [{"userEnteredValue": "PAID OFF"}]},
    "format": {"backgroundColor": INCOME_CARD, "textFormat": {"foregroundColor": GREEN, "bold": True}}}}, "index": 0}})
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 4, 12, 9, 10)],
    "booleanRule": {"condition": {"type": "TEXT_CONTAINS", "values": [{"userEnteredValue": "In Progress"}]},
    "format": {"backgroundColor": SAVINGS_CARD, "textFormat": {"foregroundColor": GOLD}}}}, "index": 1}})
# Balance gradient
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 4, 12, 2, 3)],
    "gradientRule": {"minpoint": {"color": GREEN, "type": "MIN"}, "maxpoint": {"color": CORAL, "type": "MAX"}}}, "index": 2}})

# Col widths
for c,w in [(0,165),(1,130),(2,130),(3,115),(4,120),(5,120),(6,130),(7,120),(8,120),(9,130)]:
    reqs.append(cw(SID, c, c+1, w))

reqs.append(borders(rng(SID, 3, 15, 0, 10), BORDER))
reqs.append(freeze(SID, 4))
save("phase6_debt_format.json", {"requests": reqs})

# ════════════════════════════════════════════════════════════════════════════
# PHASE 7 — SAVINGS GOALS FORMAT (sheetId=3)
# ════════════════════════════════════════════════════════════════════════════
print("Generating phase7_savings_format.json...")
SID = 3
reqs = []

reqs.append(merge(SID, 0, 1, 0, 8))
reqs.append(repeat(rng(SID, 0, 1, 0, 8), bg=DARKER_BG, tc=GOLD, bold=True, fs=18, ha="CENTER", va="MIDDLE"))
reqs.append(rh(SID, 0, 1, 55))

reqs.append(repeat(rng(SID, 2, 3, 0, 8), bg=SECTION_TEAL, tc=WHITE, bold=True, fs=9, ha="CENTER", va="MIDDLE"))
reqs.append(rh(SID, 2, 3, 30))

for i in range(7):
    row = 3 + i
    bg = DARK_BG if i % 2 == 0 else ALT_ROW
    reqs.append(repeat(rng(SID, row, row+1, 0, 8), bg=bg, tc=WHITE, va="MIDDLE"))
    reqs.append(repeat(rng(SID, row, row+1, 0, 1), bg=bg, tc=GOLD, bold=True))
    for c in [1, 2, 3]:
        reqs.append(repeat(rng(SID, row, row+1, c, c+1), bg=bg, tc=WHITE, nf={"type":"CURRENCY","pattern":"$#,##0.00"}))
    reqs.append(repeat(rng(SID, row, row+1, 5, 6), bg=bg, tc=SECONDARY, nf={"type":"DATE","pattern":"mmmm yyyy"}))
    reqs.append(repeat(rng(SID, row, row+1, 6, 7), bg=bg, tc=TEAL, bold=True, nf={"type":"PERCENT","pattern":"0.0%"}))

reqs.append(rh(SID, 3, 10, 34))

# Totals
reqs.append(repeat(rng(SID, 10, 11, 0, 8), bg=DARKER_BG, tc=GOLD, bold=True, va="MIDDLE"))
for c in [1, 2, 3]:
    reqs.append(repeat(rng(SID, 10, 11, c, c+1), bg=DARKER_BG, tc=GOLD, bold=True, nf={"type":"CURRENCY","pattern":"$#,##0.00"}))
reqs.append(repeat(rng(SID, 10, 11, 6, 7), bg=DARKER_BG, tc=GOLD, bold=True, nf={"type":"PERCENT","pattern":"0.0%"}))
reqs.append(rh(SID, 10, 11, 32))

# CF on % complete
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 3, 10, 6, 7)],
    "booleanRule": {"condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "0.25"}]},
    "format": {"backgroundColor": SPEND_CARD, "textFormat": {"foregroundColor": CORAL}}}}, "index": 0}})
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 3, 10, 6, 7)],
    "booleanRule": {"condition": {"type": "NUMBER_BETWEEN", "values": [{"userEnteredValue": "0.25"}, {"userEnteredValue": "0.74"}]},
    "format": {"backgroundColor": SAVINGS_CARD, "textFormat": {"foregroundColor": GOLD}}}}, "index": 1}})
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 3, 10, 6, 7)],
    "booleanRule": {"condition": {"type": "NUMBER_GREATER_THAN_EQ", "values": [{"userEnteredValue": "0.75"}]},
    "format": {"backgroundColor": INCOME_CARD, "textFormat": {"foregroundColor": GREEN}}}}, "index": 2}})

for c,w in [(0,185),(1,140),(2,140),(3,160),(4,145),(5,155),(6,110),(7,210)]:
    reqs.append(cw(SID, c, c+1, w))
reqs.append(borders(rng(SID, 2, 11, 0, 8), BORDER))
reqs.append(freeze(SID, 3))
save("phase7_savings_format.json", {"requests": reqs})

# ════════════════════════════════════════════════════════════════════════════
# PHASE 8 — ANNUAL OVERVIEW FORMAT (sheetId=4)
# ════════════════════════════════════════════════════════════════════════════
print("Generating phase8_annual_format.json...")
SID = 4
reqs = []

reqs.append(merge(SID, 0, 1, 0, 15))
reqs.append(repeat(rng(SID, 0, 1, 0, 15), bg=DARKER_BG, tc=TEAL, bold=True, fs=16, ha="CENTER", va="MIDDLE"))
reqs.append(rh(SID, 0, 1, 50))

reqs.append(merge(SID, 2, 3, 1, 13))
reqs.append(repeat(rng(SID, 2, 3, 0, 15), bg=CARD_BG, tc=SECONDARY, bold=True, fs=9, ha="CENTER", va="MIDDLE"))
reqs.append(rh(SID, 2, 3, 28))

row_styles = [
    (3, INCOME_CARD, GREEN),
    (4, INCOME_CARD, TEAL),
    (5, SPEND_CARD, CORAL),
    (6, SAVINGS_CARD, GOLD),
    (7, DARKER_BG, WHITE),
    (8, ALT_ROW, WHITE),
    (9, SAVINGS_CARD, GOLD),
]
for row, rbg, rtc in row_styles:
    reqs.append(repeat(rng(SID, row, row+1, 0, 15), bg=rbg, tc=rtc, va="MIDDLE"))
    reqs.append(repeat(rng(SID, row, row+1, 0, 1), bg=rbg, tc=rtc, bold=True))
    if row <= 7:
        reqs.append(repeat(rng(SID, row, row+1, 1, 15), bg=rbg, tc=rtc, nf={"type":"CURRENCY","pattern":"$#,##0"}))
    elif row == 9:
        reqs.append(repeat(rng(SID, row, row+1, 1, 15), bg=rbg, tc=rtc, nf={"type":"PERCENT","pattern":"0%"}))

# CF on NET row
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 8, 9, 1, 14)],
    "booleanRule": {"condition": {"type": "NUMBER_GREATER_THAN_EQ", "values": [{"userEnteredValue": "0"}]},
    "format": {"backgroundColor": INCOME_CARD, "textFormat": {"foregroundColor": GREEN}}}}, "index": 0}})
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 8, 9, 1, 14)],
    "booleanRule": {"condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "0"}]},
    "format": {"backgroundColor": SPEND_CARD, "textFormat": {"foregroundColor": CORAL}}}}, "index": 1}})
# CF savings rate
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 9, 10, 1, 14)],
    "booleanRule": {"condition": {"type": "NUMBER_GREATER_THAN_EQ", "values": [{"userEnteredValue": "0.2"}]},
    "format": {"backgroundColor": INCOME_CARD, "textFormat": {"foregroundColor": GREEN}}}}, "index": 2}})
reqs.append({"addConditionalFormatRule": {"rule": {"ranges": [rng(SID, 9, 10, 1, 14)],
    "booleanRule": {"condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "0.1"}]},
    "format": {"backgroundColor": SPEND_CARD, "textFormat": {"foregroundColor": CORAL}}}}, "index": 3}})

# Trend row
reqs.append(merge(SID, 11, 12, 1, 13))
reqs.append(repeat(rng(SID, 11, 12, 0, 15), bg=CARD_BG, tc=TEAL, bold=True, va="MIDDLE"))
reqs.append(rh(SID, 11, 12, 50))

reqs.append(rh(SID, 3, 11, 30))
reqs.append(cw(SID, 0, 1, 160))
for c in range(1, 14):
    reqs.append(cw(SID, c, c+1, 88))
reqs.append(cw(SID, 13, 14, 100))
reqs.append(cw(SID, 14, 15, 100))

reqs.append(borders(rng(SID, 2, 12, 0, 15), BORDER))
reqs.append(freeze(SID, 3))
save("phase8_annual_format.json", {"requests": reqs})

# ════════════════════════════════════════════════════════════════════════════
# PHASE 9 — TAB COLORS + HIDE _REF
# ════════════════════════════════════════════════════════════════════════════
print("Generating phase9_tabs.json...")
tab_colors = [
    (0, DARKER_BG),
    (1, SECTION_TEAL),
    (2, {"red":0.600,"green":0.200,"blue":0.200}),
    (3, {"red":0.500,"green":0.400,"blue":0.050}),
    (4, {"red":0.100,"green":0.450,"blue":0.400}),
    (5, {"red":0.200,"green":0.350,"blue":0.500}),
]
reqs = []
for sid, color in tab_colors:
    reqs.append({"updateSheetProperties": {"properties": {"sheetId": sid, "tabColorStyle": {"rgbColor": color}}, "fields": "tabColorStyle"}})
reqs.append({"updateSheetProperties": {"properties": {"sheetId": 6, "hidden": True}, "fields": "hidden"}})
save("phase9_tabs.json", {"requests": reqs})

print("\nAll files generated successfully!")
