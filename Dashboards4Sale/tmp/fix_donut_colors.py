"""
Replace donut chart (uncontrollable colors) with a 100% stacked horizontal bar.
- Uses helper data in hidden cols M-P (rows 1-2)
- Gives full control: Teal=Needs, Coral=Wants, Gold=Savings
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
    fname = os.path.join(OUT, "_fdc_tmp.json")
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

def run_values(data_list, label):
    payload = {"valueInputOption": "USER_ENTERED", "data": data_list}
    fname = os.path.join(OUT, "_fdc_vtmp.json")
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

def anchor(row, col): return {"sheetId": 0, "rowIndex": row, "columnIndex": col}

DARKER   = {"red":0.078,"green":0.110,"blue":0.145}
DARK_BG  = {"red":0.110,"green":0.157,"blue":0.200}
TEAL     = {"red":0.000,"green":0.706,"blue":0.651}
CORAL    = {"red":1.000,"green":0.420,"blue":0.420}
GOLD     = {"red":1.000,"green":0.820,"blue":0.400}
WHITE    = {"red":1.0,  "green":1.0,  "blue":1.0}
SECONDARY= {"red":0.584,"green":0.647,"blue":0.651}
SID = 0

# ── Step 1: Write helper data into hidden cols M–P (rows 1–2, 0-indexed 0–1) ──
# Row 0 = headers for each series
# Row 1 = the single data point "March" + 3 spending actuals
print("Step 1: Writing helper data in hidden cols M-P...")
run_values([
    # M1 = domain header (empty), N1 = Needs header, O1 = Wants header, P1 = Savings header
    {"range": "Dashboard!M1:P1", "values": [["", '=A31', '=A32', '=A33']]},
    # M2 = domain label "Spending", N2-P2 = actual values per bucket
    {"range": "Dashboard!M2:P2", "values": [["Budget Month", '=E31', '=E32', '=E33']]},
], "helper data M1:P2")

# ── Step 2: Find and delete the current donut chart ────────────────────────────
print("Step 2: Finding and deleting donut chart...")
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
print(f"  Donut ID: {donut_id}")

reqs = []
if donut_id:
    reqs.append({"deleteEmbeddedObject": {"objectId": donut_id}})

# ── Step 3: Add 100% stacked horizontal bar with brand colors ─────────────────
# Domain: M1:M2 (col 12, rows 0-2)  = 1 label + 1 data point → 1 bar
# Series 1 Teal  (Needs):   N1:N2 (col 13, rows 0-2)
# Series 2 Coral (Wants):   O1:O2 (col 14, rows 0-2)
# Series 3 Gold  (Savings): P1:P2 (col 15, rows 0-2)
print("Step 3: Adding brand-colored stacked spending chart...")

brand_chart = {
    "addChart": {
        "chart": {
            "spec": {
                "title": "Spending by Bucket",
                "titleTextFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 13},
                "backgroundColor": DARKER,
                "basicChart": {
                    "chartType": "BAR",
                    "legendPosition": "BOTTOM_LEGEND",
                    "stackedType": "PERCENT_STACKED",
                    "axis": [
                        {
                            "position": "BOTTOM_AXIS",
                            "format": {"foregroundColor": SECONDARY, "fontSize": 9, "bold": False}
                        },
                        {
                            "position": "LEFT_AXIS",
                            "format": {"foregroundColor": SECONDARY, "fontSize": 9}
                        },
                    ],
                    "domains": [{
                        "domain": {
                            "sourceRange": {"sources": [{
                                "sheetId": SID,
                                "startRowIndex": 0, "endRowIndex": 2,
                                "startColumnIndex": 12, "endColumnIndex": 13
                            }]}
                        }
                    }],
                    "series": [
                        {
                            "series": {"sourceRange": {"sources": [{
                                "sheetId": SID,
                                "startRowIndex": 0, "endRowIndex": 2,
                                "startColumnIndex": 13, "endColumnIndex": 14
                            }]}},
                            "targetAxis": "BOTTOM_AXIS",
                            "color": TEAL,
                        },
                        {
                            "series": {"sourceRange": {"sources": [{
                                "sheetId": SID,
                                "startRowIndex": 0, "endRowIndex": 2,
                                "startColumnIndex": 14, "endColumnIndex": 15
                            }]}},
                            "targetAxis": "BOTTOM_AXIS",
                            "color": CORAL,
                        },
                        {
                            "series": {"sourceRange": {"sources": [{
                                "sheetId": SID,
                                "startRowIndex": 0, "endRowIndex": 2,
                                "startColumnIndex": 15, "endColumnIndex": 16
                            }]}},
                            "targetAxis": "BOTTOM_AXIS",
                            "color": GOLD,
                        },
                    ],
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
}

reqs.append(brand_chart)
run_batch(reqs, "delete donut + add brand-colored chart")

print("\nDone. Chart now uses Teal=Needs, Coral=Wants, Gold=Savings.")
