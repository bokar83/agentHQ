import json, os, subprocess

SHEET_ID = "1pkO1G5q_qDe0nLCm7W12O3-jurzYKH16bcw8X5AOmQ0"
GIT_BASH  = r"C:\Program Files\Git\bin\bash.exe"
OUT       = r"D:\Ai_Sandbox\agentsHQ\Dashboards4Sale\tmp"

def to_unix(p):
    p = p.replace("\\", "/")
    if len(p) > 1 and p[1] == ":": p = "/" + p[0].lower() + p[2:]
    return p

def anchor(row, col):
    return {"sheetId": 0, "rowIndex": row, "columnIndex": col}

WHITE = {"red":1,"green":1,"blue":1}
TEAL  = {"red":0,"green":0.706,"blue":0.651}
CORAL = {"red":1,"green":0.42,"blue":0.42}
DARK  = {"red":0.078,"green":0.11,"blue":0.145}

donut = {"addChart": {"chart": {"spec": {
    "title": "Spending by Bucket",
    "titleTextFormat": {"bold":True,"foregroundColor":WHITE,"fontSize":12},
    "backgroundColor": DARK,
    "pieChart": {
        "legendPosition": "LABELED_LEGEND",
        "pieHole": 0.5,
        "domain": {"sourceRange": {"sources": [{"sheetId":0,"startRowIndex":30,"endRowIndex":33,"startColumnIndex":0,"endColumnIndex":1}]}},
        "series": {"sourceRange": {"sources": [{"sheetId":0,"startRowIndex":30,"endRowIndex":33,"startColumnIndex":4,"endColumnIndex":5}]}}
    }
}, "position": {"overlayPosition": {"anchorCell": anchor(35,0), "widthPixels":420,"heightPixels":280}}}}}

bar = {"addChart": {"chart": {"spec": {
    "title": "Budget vs Actual",
    "titleTextFormat": {"bold":True,"foregroundColor":WHITE,"fontSize":12},
    "backgroundColor": DARK,
    "basicChart": {
        "chartType": "COLUMN",
        "legendPosition": "BOTTOM_LEGEND",
        "axis": [{"position":"BOTTOM_AXIS"},{"position":"LEFT_AXIS","title":"Amount ($)"}],
        "domains": [{"domain": {"sourceRange": {"sources": [{"sheetId":0,"startRowIndex":10,"endRowIndex":13,"startColumnIndex":0,"endColumnIndex":1}]}}}],
        "series": [
            {"series": {"sourceRange": {"sources": [{"sheetId":0,"startRowIndex":10,"endRowIndex":13,"startColumnIndex":2,"endColumnIndex":3}]}}, "targetAxis":"LEFT_AXIS", "color":TEAL},
            {"series": {"sourceRange": {"sources": [{"sheetId":0,"startRowIndex":10,"endRowIndex":13,"startColumnIndex":4,"endColumnIndex":5}]}}, "targetAxis":"LEFT_AXIS", "color":CORAL}
        ]
    }
}, "position": {"overlayPosition": {"anchorCell": anchor(35,6), "widthPixels":500,"heightPixels":280}}}}}

payload = {"requests": [donut, bar]}
fname = os.path.join(OUT, "_charts2.json")
with open(fname, "w") as f:
    json.dump(payload, f)
unix = to_unix(fname)
cmd = (f"gws sheets spreadsheets batchUpdate "
       f"--params '{{\"spreadsheetId\":\"{SHEET_ID}\"}}' "
       f"--json \"$(cat '{unix}')\"")
r = subprocess.run([GIT_BASH, "-c", cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
os.remove(fname)
out = r.stdout + r.stderr
if '"replies"' in out:
    print("OK: Charts added")
else:
    print(f"ERR: {out[:300]}")
