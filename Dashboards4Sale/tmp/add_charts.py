"""
Adds two embedded charts to the Dashboard:
1. Donut chart — Spending by bucket (Needs / Wants / Savings)
2. Column chart — Budget vs Actual comparison
Both anchored below row 33 (after the spending breakdown section).
"""
import json, os, subprocess

SHEET_ID = "1pkO1G5q_qDe0nLCm7W12O3-jurzYKH16bcw8X5AOmQ0"
GIT_BASH  = r"C:\Program Files\Git\bin\bash.exe"
OUT       = r"D:\Ai_Sandbox\agentsHQ\Dashboards4Sale\tmp"

def to_unix(p):
    p = p.replace("\\", "/")
    if len(p) > 1 and p[1] == ":": p = "/" + p[0].lower() + p[2:]
    return p

def apply_batch(reqs, label):
    fname = os.path.join(OUT, "_chart_tmp.json")
    with open(fname, "w", encoding="utf-8") as f:
        json.dump({"requests": reqs}, f)
    unix = to_unix(fname)
    cmd = (f"gws sheets spreadsheets batchUpdate "
           f"--params '{{\"spreadsheetId\":\"{SHEET_ID}\"}}' "
           f"--json \"$(cat '{unix}')\"")
    r = subprocess.run([GIT_BASH, "-c", cmd],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    os.remove(fname)
    out = r.stdout + r.stderr
    if '"replies"' in out:
        print(f"  OK  {label}")
    else:
        print(f"  ERR {label}: {out[:200]}")

DASH_SID = 0

# ── Color palette ─────────────────────────────────────────────────────────────
TEAL   = {"red": 0.000, "green": 0.706, "blue": 0.651}
CORAL  = {"red": 1.000, "green": 0.420, "blue": 0.420}
GOLD   = {"red": 1.000, "green": 0.820, "blue": 0.400}
DARK   = {"red": 0.078, "green": 0.110, "blue": 0.145}
WHITE  = {"red": 1.0, "green": 1.0, "blue": 1.0}

# ── Anchor helpers ────────────────────────────────────────────────────────────
def anchor(row, col, row_offset=0, col_offset=0):
    return {"sheetId": DASH_SID, "rowIndex": row, "columnIndex": col,
            "offsetYPixels": row_offset, "offsetXPixels": col_offset}

# ── Chart 1: Donut — Spending by Bucket ──────────────────────────────────────
# Data: Dashboard!A31:A33 (bucket labels) and Dashboard!E31:E33 (actual spend)
# Anchor: row 35, col 0 (below spending breakdown, left side)
donut_chart = {
    "addChart": {
        "chart": {
            "spec": {
                "title": "Spending by Bucket",
                "titleTextFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 12},
                "backgroundColor": DARK,
                "pieChart": {
                    "legendPosition": "LABELED_LEGEND",
                    "pieHole": 0.5,
                    "series": {
                        "dataLabel": {
                            "type": "PERCENT",
                            "textFormat": {"foregroundColor": WHITE, "fontSize": 10}
                        }
                    },
                    "domain": {
                        "sourceRange": {
                            "sources": [{"sheetId": DASH_SID,
                                         "startRowIndex": 30, "endRowIndex": 33,
                                         "startColumnIndex": 0, "endColumnIndex": 1}]
                        }
                    },
                    "data": [
                        {
                            "sourceRange": {
                                "sources": [{"sheetId": DASH_SID,
                                             "startRowIndex": 30, "endRowIndex": 33,
                                             "startColumnIndex": 4, "endColumnIndex": 5}]
                            }
                        }
                    ]
                },
                "fontName": "Arial",
            },
            "position": {
                "overlayPosition": {
                    "anchorCell": anchor(35, 0),
                    "widthPixels": 420,
                    "heightPixels": 280,
                }
            }
        }
    }
}

# ── Chart 2: Column — Budget vs Actual by Bucket ─────────────────────────────
# Labels: A11:A13, Budget: C11:C13, Actual: E11:E13
# Anchor: row 35, col 6 (right side, beside the donut)
bar_chart = {
    "addChart": {
        "chart": {
            "spec": {
                "title": "Budget vs Actual",
                "titleTextFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 12},
                "backgroundColor": DARK,
                "basicChart": {
                    "chartType": "COLUMN",
                    "legendPosition": "BOTTOM_LEGEND",
                    "stackedType": "NOT_STACKED",
                    "axis": [
                        {"position": "BOTTOM_AXIS", "title": "",
                         "format": {"foregroundColor": WHITE}},
                        {"position": "LEFT_AXIS", "title": "Amount ($)",
                         "format": {"foregroundColor": WHITE}},
                    ],
                    "domains": [
                        {
                            "domain": {
                                "sourceRange": {
                                    "sources": [{"sheetId": DASH_SID,
                                                 "startRowIndex": 10, "endRowIndex": 13,
                                                 "startColumnIndex": 0, "endColumnIndex": 1}]
                                }
                            }
                        }
                    ],
                    "series": [
                        {
                            "series": {
                                "sourceRange": {
                                    "sources": [{"sheetId": DASH_SID,
                                                 "startRowIndex": 10, "endRowIndex": 13,
                                                 "startColumnIndex": 2, "endColumnIndex": 3}]
                                }
                            },
                            "targetAxis": "LEFT_AXIS",
                            "color": TEAL,
                            "dataLabel": {"type": "VALUE", "textFormat": {"foregroundColor": WHITE, "fontSize": 9}}
                        },
                        {
                            "series": {
                                "sourceRange": {
                                    "sources": [{"sheetId": DASH_SID,
                                                 "startRowIndex": 10, "endRowIndex": 13,
                                                 "startColumnIndex": 4, "endColumnIndex": 5}]
                                }
                            },
                            "targetAxis": "LEFT_AXIS",
                            "color": CORAL,
                            "dataLabel": {"type": "VALUE", "textFormat": {"foregroundColor": WHITE, "fontSize": 9}}
                        }
                    ]
                },
                "fontName": "Arial",
            },
            "position": {
                "overlayPosition": {
                    "anchorCell": anchor(35, 6),
                    "widthPixels": 500,
                    "heightPixels": 280,
                }
            }
        }
    }
}

print("Adding Dashboard charts...")
apply_batch([donut_chart, bar_chart], "Dashboard charts (donut + column)")
print("Done!")
