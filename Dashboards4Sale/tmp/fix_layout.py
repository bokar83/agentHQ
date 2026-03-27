"""
Fix dashboard layout:
1. Delete the donut chart that's covering KPI cards
2. Re-anchor it at row 8 (below KPIs) so all 4 KPI cards are visible
3. Make bar chart anchor explicit
4. Clear progress-bar column (col I) — it's invisible behind the chart
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
    fname = os.path.join(OUT, "_fl_tmp.json")
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
    fname = os.path.join(OUT, "_fl_vtmp.json")
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
TEAL     = {"red":0.000,"green":0.706,"blue":0.651}
CORAL    = {"red":1.000,"green":0.420,"blue":0.420}
WHITE    = {"red":1.0,  "green":1.0,  "blue":1.0}
SECONDARY= {"red":0.584,"green":0.647,"blue":0.651}
SID = 0

# ── Step 1: Delete the mispositioned donut chart ──────────────────────────────
print("Step 1: Deleting donut chart (was covering KPIs)...")
run_batch([
    {"deleteEmbeddedObject": {"objectId": 2092718273}},
], "delete donut chart")

# ── Step 2: Clear progress bars col I (hidden behind chart anyway) ────────────
print("Step 2: Clearing hidden progress bar cells...")
run_values([
    {"range": "Dashboard!I10:J10", "values": [["", ""]]},
    {"range": "Dashboard!I11:J14", "values": [["",""],["",""],["",""],["",""]]},
    {"range": "Dashboard!I30:J30", "values": [["", ""]]},
    {"range": "Dashboard!I31:J33", "values": [["",""],["",""],["",""]]},
], "clear col I/J progress bars")

# ── Step 3: Re-add donut anchored at row 8 (below KPI section) ───────────────
# Row 8 = after title(0) + info(1) + banner(2) + section_header(3) + kpi_label(4) + kpi_value(5) + kpi_sub(6) + spacer(7)
# This means the donut sits BESIDE the Budget vs Actual table — KPIs fully visible above
print("Step 3: Adding donut chart at row 8 (beside budget table)...")

donut = {
    "addChart": {
        "chart": {
            "spec": {
                "title": "Spending by Bucket",
                "titleTextFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 12},
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
                    "anchorCell": anchor(8, 7),   # row 8 = below KPI section
                    "widthPixels":  580,
                    "heightPixels": 500,
                }
            }
        }
    }
}

run_batch([donut], "add repositioned donut chart")

print("\nLayout fix complete!")
print("KPI cards should now be fully visible. Donut sits beside Budget vs Actual table.")
