"""
Premium Dashboard Upgrade:
1. Delete all existing charts
2. Add big month display row
3. Large donut chart RIGHT SIDE (split panel layout)
4. SPARKLINE progress bars in budget table
5. Full-width column + line charts below
"""
import json, os, subprocess

SHEET_ID = "1pkO1G5q_qDe0nLCm7W12O3-jurzYKH16bcw8X5AOmQ0"
GIT_BASH  = r"C:\Program Files\Git\bin\bash.exe"
OUT       = r"D:\Ai_Sandbox\agentsHQ\Dashboards4Sale\tmp"

def to_unix(p):
    p = p.replace("\\", "/")
    if len(p) > 1 and p[1] == ":": p = "/" + p[0].lower() + p[2:]
    return p

def run_batch(reqs, label):
    fname = os.path.join(OUT, "_pu_tmp.json")
    with open(fname, "w") as f: json.dump({"requests": reqs}, f)
    unix = to_unix(fname)
    cmd = (f"gws sheets spreadsheets batchUpdate "
           f"--params '{{\"spreadsheetId\":\"{SHEET_ID}\"}}' "
           f"--json \"$(cat '{unix}')\"")
    r = subprocess.run([GIT_BASH, "-c", cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    os.remove(fname)
    out = r.stdout + r.stderr
    if '"replies"' in out:
        print(f"  OK  {label}")
    else:
        print(f"  ERR {label}: {out[:200]}")

def run_values(data_list, label):
    payload = {"valueInputOption": "USER_ENTERED", "data": data_list}
    fname = os.path.join(OUT, "_pu_vtmp.json")
    with open(fname, "w", encoding="utf-8") as f: json.dump(payload, f)
    unix = to_unix(fname)
    cmd = (f"gws sheets spreadsheets values batchUpdate "
           f"--params '{{\"spreadsheetId\":\"{SHEET_ID}\"}}' "
           f"--json \"$(cat '{unix}')\"")
    r = subprocess.run([GIT_BASH, "-c", cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    os.remove(fname)
    out = r.stdout + r.stderr
    if "updatedCells" in out:
        print(f"  OK  {label}")
    else:
        print(f"  ERR {label}: {out[:200]}")

def rng(sid, r1, r2, c1, c2):
    return {"sheetId": sid, "startRowIndex": r1, "endRowIndex": r2,
            "startColumnIndex": c1, "endColumnIndex": c2}

def repeat(range_d, **kw):
    f = {}
    if "bg" in kw: f["backgroundColor"] = kw["bg"]
    tf = {}
    if "tc" in kw: tf["foregroundColor"] = kw["tc"]
    if kw.get("bold"): tf["bold"] = True
    if kw.get("italic"): tf["italic"] = True
    if "fs" in kw: tf["fontSize"] = kw["fs"]
    if tf: f["textFormat"] = tf
    if "ha" in kw: f["horizontalAlignment"] = kw["ha"]
    if "va" in kw: f["verticalAlignment"] = kw["va"]
    if "nf" in kw: f["numberFormat"] = kw["nf"]
    fields = "userEnteredFormat(" + ",".join(f.keys()) + ")"
    return {"repeatCell": {"range": range_d, "cell": {"userEnteredFormat": f}, "fields": fields}}

def cw(sid, c1, c2, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": c1, "endIndex": c2},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def rh(sid, r1, r2, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": r1, "endIndex": r2},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def anchor(row, col):
    return {"sheetId": 0, "rowIndex": row, "columnIndex": col}

# ── Colors ────────────────────────────────────────────────────────────────────
DARK_BG  = {"red":0.110,"green":0.157,"blue":0.200}
DARKER   = {"red":0.078,"green":0.110,"blue":0.145}
CARD_BG  = {"red":0.137,"green":0.196,"blue":0.251}
ALT_ROW  = {"red":0.094,"green":0.137,"blue":0.180}
TEAL     = {"red":0.000,"green":0.706,"blue":0.651}
CORAL    = {"red":1.000,"green":0.420,"blue":0.420}
GOLD     = {"red":1.000,"green":0.820,"blue":0.400}
GREEN    = {"red":0.180,"green":0.800,"blue":0.443}
WHITE    = {"red":1.0,  "green":1.0,  "blue":1.0}
SECONDARY= {"red":0.584,"green":0.647,"blue":0.651}
SECTION_T= {"red":0.024,"green":0.361,"blue":0.329}
SID = 0

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: Delete all 4 existing charts
# ═══════════════════════════════════════════════════════════════════════════════
print("Step 1: Deleting existing charts...")
run_batch([
    {"deleteEmbeddedObject": {"objectId": 913973707}},
    {"deleteEmbeddedObject": {"objectId": 1925197316}},
    {"deleteEmbeddedObject": {"objectId": 1541557739}},
    {"deleteEmbeddedObject": {"objectId": 1469714517}},
], "delete 4 charts")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: Layout improvements — column widths, row heights, month banner
# ═══════════════════════════════════════════════════════════════════════════════
print("Step 2: Layout improvements...")
run_batch([
    # Widen columns for premium spacing
    cw(SID, 0, 1, 195),   # A: labels
    cw(SID, 1, 2, 14),    # B: spacer
    cw(SID, 2, 3, 140),   # C
    cw(SID, 3, 4, 14),    # D: spacer
    cw(SID, 4, 5, 140),   # E
    cw(SID, 5, 6, 14),    # F: spacer
    cw(SID, 6, 7, 140),   # G
    cw(SID, 7, 8, 14),    # H: spacer
    cw(SID, 8, 9, 135),   # I: Progress bars — wider
    cw(SID, 9, 10, 72),   # J: % number
    cw(SID, 10, 11, 175), # K: Status text
    cw(SID, 11, 12, 110), # L

    # Row heights
    rh(SID, 0, 1, 68),    # Title banner
    rh(SID, 1, 2, 28),    # Info bar
    rh(SID, 2, 3, 70),    # Month banner (NEW)
    rh(SID, 3, 4, 34),    # Section header
    rh(SID, 4, 5, 28),    # KPI label
    rh(SID, 5, 6, 68),    # KPI value — bigger
    rh(SID, 6, 7, 24),    # KPI sub
    rh(SID, 7, 8, 12),    # Spacer
    rh(SID, 8, 9, 34),    # Budget header
    rh(SID, 9, 10, 28),   # Table col headers
    rh(SID, 10, 14, 38),  # Budget data rows
    rh(SID, 14, 15, 12),  # Spacer
    rh(SID, 15, 16, 34),  # Top txn header
    rh(SID, 16, 17, 28),  # Txn col headers
    rh(SID, 17, 27, 28),  # Txn data rows
    rh(SID, 27, 28, 12),  # Spacer
    rh(SID, 28, 29, 34),  # Breakdown header
    rh(SID, 29, 30, 28),  # Breakdown sub-headers
    rh(SID, 30, 33, 38),  # Breakdown rows
    rh(SID, 33, 35, 14),  # Spacer before charts

    # Month banner: merge and format row 2 as big month display
    {"mergeCells": {"range": rng(SID, 2, 3, 0, 12), "mergeType": "MERGE_ALL"}},
    repeat(rng(SID, 2, 3, 0, 12), bg=DARKER, tc=TEAL, bold=True, fs=32, ha="CENTER", va="MIDDLE"),

    # Title row: slightly bigger font
    repeat(rng(SID, 0, 1, 0, 12), bg=DARKER, tc=WHITE, bold=True, fs=22, ha="CENTER", va="MIDDLE"),

    # KPI value row: ensure large font
    repeat(rng(SID, 5, 6, 0, 3),  bg={"red":0.039,"green":0.180,"blue":0.133}, tc=GREEN,  bold=True, fs=26, ha="CENTER", va="MIDDLE"),
    repeat(rng(SID, 5, 6, 3, 6),  bg={"red":0.196,"green":0.059,"blue":0.059}, tc=CORAL,  bold=True, fs=26, ha="CENTER", va="MIDDLE"),
    repeat(rng(SID, 5, 6, 6, 9),  bg={"red":0.059,"green":0.133,"blue":0.208}, tc=WHITE,  bold=True, fs=26, ha="CENTER", va="MIDDLE"),
    repeat(rng(SID, 5, 6, 9, 12), bg={"red":0.196,"green":0.157,"blue":0.020}, tc=GOLD,   bold=True, fs=26, ha="CENTER", va="MIDDLE"),

    # Number format on KPI values
    repeat(rng(SID, 5, 6, 0, 12), nf={"type":"CURRENCY","pattern":"$#,##0.00"}),

    # Progress bar background in budget table
    repeat(rng(SID, 10, 14, 8, 9), bg=ALT_ROW),
    repeat(rng(SID, 10, 14, 9, 10), bg=DARK_BG, tc=WHITE,
           nf={"type":"PERCENT","pattern":"0%"}, ha="CENTER"),
    repeat(rng(SID, 29, 33, 8, 9), bg=ALT_ROW),
    repeat(rng(SID, 29, 33, 9, 10), bg=DARK_BG, tc=WHITE,
           nf={"type":"PERCENT","pattern":"0%"}, ha="CENTER"),
], "column widths + row heights + banner format")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: Month banner + progress bar values
# ═══════════════════════════════════════════════════════════════════════════════
print("Step 3: Adding month banner and progress bars...")

# SPARKLINE formula builder
def spark(pct_formula):
    return (f'=IFERROR(SPARKLINE(MIN({pct_formula},1.15),'
            f'{{"charttype","bar";'
            f'"color1",IF({pct_formula}>1,"#FF6B6B",IF({pct_formula}>0.8,"#FFD166","#00B4A6"));'
            f'"color2","#182330";"max",1.15}}),"")')

run_values([
    # Big month banner
    {"range": "Dashboard!A3",  "values": [['=UPPER(Setup!$C$3)&"  —  YOUR MONTHLY BUDGET"']]},

    # Table headers update: I=PROGRESS, J=% USED
    {"range": "Dashboard!I10:J10", "values": [["PROGRESS", "%"]]},
    {"range": "Dashboard!I30:J30", "values": [["PROGRESS", "%"]]},

    # Budget table progress bars (rows 11-14)
    {"range": "Dashboard!I11", "values": [[spark("E11/C11")]]},
    {"range": "Dashboard!I12", "values": [[spark("E12/C12")]]},
    {"range": "Dashboard!I13", "values": [[spark("E13/C13")]]},
    {"range": "Dashboard!I14", "values": [[spark("E14/C14")]]},
    {"range": "Dashboard!J11", "values": [["=IFERROR(E11/C11,0)"]]},
    {"range": "Dashboard!J12", "values": [["=IFERROR(E12/C12,0)"]]},
    {"range": "Dashboard!J13", "values": [["=IFERROR(E13/C13,0)"]]},
    {"range": "Dashboard!J14", "values": [["=IFERROR(E14/C14,0)"]]},

    # Spending breakdown progress bars (rows 31-33)
    {"range": "Dashboard!I31", "values": [[spark("E31/C31")]]},
    {"range": "Dashboard!I32", "values": [[spark("E32/C32")]]},
    {"range": "Dashboard!I33", "values": [[spark("E33/C33")]]},
    {"range": "Dashboard!J31", "values": [["=IFERROR(E31/C31,0)"]]},
    {"range": "Dashboard!J32", "values": [["=IFERROR(E32/C32,0)"]]},
    {"range": "Dashboard!J33", "values": [["=IFERROR(E33/C33,0)"]]},
], "month banner + progress bars")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4: Three premium charts
# ═══════════════════════════════════════════════════════════════════════════════
print("Step 4: Adding 3 premium charts...")

# Chart 1: Large donut — RIGHT PANEL beside KPI cards + budget table
# Anchored at row 3 (below month banner), col 7 (right half)
# 600px wide × 460px tall → spans rows 3-18 visually
donut = {
    "addChart": {
        "chart": {
            "spec": {
                "title": "Spending by Bucket",
                "titleTextFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 11},
                "backgroundColor": DARKER,
                "pieChart": {
                    "legendPosition": "BOTTOM_LEGEND",
                    "pieHole": 0.45,
                    "domain": {
                        "sourceRange": {"sources": [{
                            "sheetId": SID,
                            "startRowIndex": 30, "endRowIndex": 33,
                            "startColumnIndex": 0, "endColumnIndex": 1
                        }]}
                    },
                    "series": {
                        "sourceRange": {"sources": [{
                            "sheetId": SID,
                            "startRowIndex": 30, "endRowIndex": 33,
                            "startColumnIndex": 4, "endColumnIndex": 5
                        }]}
                    },

                },
                "fontName": "Arial",
            },
            "position": {
                "overlayPosition": {
                    "anchorCell": anchor(3, 7),
                    "widthPixels":  612,
                    "heightPixels": 470,
                }
            }
        }
    }
}

# Chart 2: Budget vs Actual — left side below section
bar_chart = {
    "addChart": {
        "chart": {
            "spec": {
                "title": "Budget vs Actual by Category",
                "titleTextFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 11},
                "backgroundColor": DARKER,
                "basicChart": {
                    "chartType": "COLUMN",
                    "legendPosition": "BOTTOM_LEGEND",
                    "stackedType": "NOT_STACKED",
                    "axis": [
                        {"position": "BOTTOM_AXIS",
                         "format": {"foregroundColor": SECONDARY, "fontSize": 9}},
                        {"position": "LEFT_AXIS", "title": "Amount ($)",
                         "format": {"foregroundColor": SECONDARY, "fontSize": 9}},
                    ],
                    "domains": [{
                        "domain": {
                            "sourceRange": {"sources": [{
                                "sheetId": SID,
                                "startRowIndex": 9, "endRowIndex": 13,
                                "startColumnIndex": 0, "endColumnIndex": 1
                            }]}
                        }
                    }],
                    "series": [
                        {
                            "series": {"sourceRange": {"sources": [{
                                "sheetId": SID,
                                "startRowIndex": 9, "endRowIndex": 13,
                                "startColumnIndex": 2, "endColumnIndex": 3}]}},
                            "targetAxis": "LEFT_AXIS",
                            "color": TEAL,
                            "dataLabel": {"type": "VALUE",
                                "textFormat": {"foregroundColor": WHITE, "fontSize": 9}}
                        },
                        {
                            "series": {"sourceRange": {"sources": [{
                                "sheetId": SID,
                                "startRowIndex": 9, "endRowIndex": 13,
                                "startColumnIndex": 4, "endColumnIndex": 5}]}},
                            "targetAxis": "LEFT_AXIS",
                            "color": CORAL,
                            "dataLabel": {"type": "VALUE",
                                "textFormat": {"foregroundColor": WHITE, "fontSize": 9}}
                        }
                    ]
                },
                "fontName": "Arial",
            },
            "position": {
                "overlayPosition": {
                    "anchorCell": anchor(35, 0),
                    "widthPixels":  640,
                    "heightPixels": 320,
                }
            }
        }
    }
}

# Chart 3: Monthly trend line (Income vs Spending across 12 months)
trend = {
    "addChart": {
        "chart": {
            "spec": {
                "title": "Monthly Income vs Total Spend",
                "titleTextFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 11},
                "backgroundColor": DARKER,
                "basicChart": {
                    "chartType": "LINE",
                    "legendPosition": "BOTTOM_LEGEND",
                    "stackedType": "NOT_STACKED",
                    "axis": [
                        {"position": "BOTTOM_AXIS",
                         "format": {"foregroundColor": SECONDARY, "fontSize": 8}},
                        {"position": "LEFT_AXIS",
                         "format": {"foregroundColor": SECONDARY, "fontSize": 8}},
                    ],
                    "domains": [{
                        "domain": {
                            "sourceRange": {"sources": [{
                                "sheetId": 4,
                                "startRowIndex": 2, "endRowIndex": 3,
                                "startColumnIndex": 1, "endColumnIndex": 13
                            }]}
                        }
                    }],
                    "series": [
                        {
                            "series": {"sourceRange": {"sources": [{
                                "sheetId": 4,
                                "startRowIndex": 3, "endRowIndex": 4,
                                "startColumnIndex": 1, "endColumnIndex": 13}]}},
                            "targetAxis": "LEFT_AXIS",
                            "color": TEAL,
                        },
                        {
                            "series": {"sourceRange": {"sources": [{
                                "sheetId": 4,
                                "startRowIndex": 7, "endRowIndex": 8,
                                "startColumnIndex": 1, "endColumnIndex": 13}]}},
                            "targetAxis": "LEFT_AXIS",
                            "color": CORAL,
                        }
                    ],
                    "lineSmoothing": True,
                },
                "fontName": "Arial",
            },
            "position": {
                "overlayPosition": {
                    "anchorCell": anchor(35, 7),
                    "widthPixels":  600,
                    "heightPixels": 320,
                }
            }
        }
    }
}

run_batch([donut, bar_chart, trend], "add 3 premium charts")

print("\nPremium upgrade complete!")
