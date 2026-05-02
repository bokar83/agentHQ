"""Add 3 premium charts (fixed - no invalid slices field)"""
import json, os, subprocess

SHEET_ID = "1pkO1G5q_qDe0nLCm7W12O3-jurzYKH16bcw8X5AOmQ0"
GIT_BASH  = r"C:\Program Files\Git\bin\bash.exe"
OUT       = r"D:\Ai_Sandbox\agentsHQ\Dashboards4Sale\tmp"

def to_unix(p):
    p = p.replace("\\", "/")
    if len(p) > 1 and p[1] == ":": p = "/" + p[0].lower() + p[2:]
    return p

def run_batch(reqs, label):
    fname = os.path.join(OUT, "_ac3_tmp.json")
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
        print(f"  ERR {label}: {out[:400]}")

def anchor(row, col):
    return {"sheetId": 0, "rowIndex": row, "columnIndex": col}

DARKER   = {"red":0.078,"green":0.110,"blue":0.145}
TEAL     = {"red":0.000,"green":0.706,"blue":0.651}
CORAL    = {"red":1.000,"green":0.420,"blue":0.420}
GOLD     = {"red":1.000,"green":0.820,"blue":0.400}
WHITE    = {"red":1.0,  "green":1.0,  "blue":1.0}
SECONDARY= {"red":0.584,"green":0.647,"blue":0.651}
SID = 0

# Chart 1: Large donut — right panel beside KPI cards
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

# Chart 2: Budget vs Actual column chart
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
                        },
                        {
                            "series": {"sourceRange": {"sources": [{
                                "sheetId": SID,
                                "startRowIndex": 9, "endRowIndex": 13,
                                "startColumnIndex": 4, "endColumnIndex": 5}]}},
                            "targetAxis": "LEFT_AXIS",
                            "color": CORAL,
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

# Chart 3: Monthly trend line
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
print("Done.")
