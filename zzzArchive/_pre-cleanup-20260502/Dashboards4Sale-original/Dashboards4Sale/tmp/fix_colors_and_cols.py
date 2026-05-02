"""
1. Hide SORTN helper columns M-Q (polluting right panel)
2. Delete current donut, re-add it using spending breakdown rows 31-33
   (same as before — accept Google default colors, which look fine on dark bg)
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
    fname = os.path.join(OUT, "_fcc_tmp.json")
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

def anchor(row, col): return {"sheetId": 0, "rowIndex": row, "columnIndex": col}

DARKER   = {"red":0.078,"green":0.110,"blue":0.145}
WHITE    = {"red":1.0, "green":1.0, "blue":1.0}
SID = 0

# ── Step 1: Hide helper columns M–Q (indexes 12–16) ──────────────────────────
print("Step 1: Hiding helper columns M-Q...")
run_batch([{
    "updateDimensionProperties": {
        "range": {"sheetId": SID, "dimension": "COLUMNS", "startIndex": 12, "endIndex": 17},
        "properties": {"hiddenByUser": True},
        "fields": "hiddenByUser"
    }
}], "hide cols M-Q")

# ── Step 2: Fetch current donut chart ID ──────────────────────────────────────
print("Step 2: Finding donut chart ID...")
cmd_get = (f"gws sheets spreadsheets get "
           f"--params '{{\"spreadsheetId\":\"{SHEET_ID}\",\"includeGridData\":false}}'")
r = subprocess.run([GIT_BASH, "-c", cmd_get], capture_output=True, text=True, encoding="utf-8", errors="replace")
out = r.stdout + r.stderr
lines = [l for l in out.splitlines() if not l.startswith("Using")]
data = json.loads("\n".join(lines))
donut_id = None
for sheet in data.get("sheets", []):
    for c in sheet.get("charts", []):
        if c.get("spec", {}).get("title") == "Spending by Bucket":
            donut_id = c["chartId"]
print(f"  Donut chart ID: {donut_id}")

# ── Step 3: Delete and re-add donut with improved positioning ─────────────────
print("Step 3: Refreshing donut chart...")
reqs = []
if donut_id:
    reqs.append({"deleteEmbeddedObject": {"objectId": donut_id}})

reqs.append({
    "addChart": {
        "chart": {
            "spec": {
                "title": "Spending by Bucket",
                "titleTextFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 13},
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
                    "anchorCell": anchor(8, 7),
                    "widthPixels":  580,
                    "heightPixels": 500,
                }
            }
        }
    }
})

run_batch(reqs, "delete + re-add donut")

print("\nDone.")
