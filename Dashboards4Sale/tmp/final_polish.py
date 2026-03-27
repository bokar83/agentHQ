"""
Final polish: freeze rows on remaining tabs, add script install note to Setup.
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
    fname = os.path.join(OUT, "_polish_tmp.json")
    with open(fname, "w") as f: json.dump({"requests": reqs}, f)
    unix = to_unix(fname)
    cmd = (f"gws sheets spreadsheets batchUpdate "
           f"--params '{{\"spreadsheetId\":\"{SHEET_ID}\"}}' "
           f"--json \"$(cat '{unix}')\"")
    r = subprocess.run([GIT_BASH, "-c", cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    os.remove(fname)
    out = r.stdout + r.stderr
    print(f"  {'OK' if '\"replies\"' in out else 'ERR'}: {label}" + (f" -> {out[:150]}" if '"replies"' not in out else ""))

def run_values(data_list, label):
    payload = {"valueInputOption": "USER_ENTERED", "data": data_list}
    fname = os.path.join(OUT, "_polish_vtmp.json")
    with open(fname, "w", encoding="utf-8") as f: json.dump(payload, f)
    unix = to_unix(fname)
    cmd = (f"gws sheets spreadsheets values batchUpdate "
           f"--params '{{\"spreadsheetId\":\"{SHEET_ID}\"}}' "
           f"--json \"$(cat '{unix}')\"")
    r = subprocess.run([GIT_BASH, "-c", cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    os.remove(fname)
    out = r.stdout + r.stderr
    print(f"  {'OK' if 'updatedCells' in out else 'ERR'}: {label}" + (f" -> {out[:150]}" if 'updatedCells' not in out else ""))

def freeze(sid, rows=0, cols=0):
    return {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {
        "frozenRowCount": rows, "frozenColumnCount": cols}},
        "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}}

def rng(sid,r1,r2,c1,c2): return {"sheetId":sid,"startRowIndex":r1,"endRowIndex":r2,"startColumnIndex":c1,"endColumnIndex":c2}
def repeat(range_d, **fmt):
    f = {}
    if "bg" in fmt: f["backgroundColor"] = fmt["bg"]
    tf = {}
    if "tc" in fmt: tf["foregroundColor"] = fmt["tc"]
    if fmt.get("bold"): tf["bold"] = True
    if fmt.get("italic"): tf["italic"] = True
    if "fs" in fmt: tf["fontSize"] = fmt["fs"]
    if tf: f["textFormat"] = tf
    if "ha" in fmt: f["horizontalAlignment"] = fmt["ha"]
    if "va" in fmt: f["verticalAlignment"] = fmt["va"]
    if "wrap" in fmt: f["wrapStrategy"] = fmt["wrap"]
    fields = "userEnteredFormat(" + ",".join(f.keys()) + ")"
    return {"repeatCell": {"range":range_d,"cell":{"userEnteredFormat":f},"fields":fields}}

TEAL = {"red":0,"green":0.706,"blue":0.651}
GREEN = {"red":0.18,"green":0.8,"blue":0.443}
GOLD  = {"red":1,"green":0.82,"blue":0.4}
WHITE = {"red":1,"green":1,"blue":1}
SECONDARY = {"red":0.584,"green":0.647,"blue":0.651}
SAVINGS_CARD = {"red":0.196,"green":0.157,"blue":0.020}
CARD_BG = {"red":0.137,"green":0.196,"blue":0.251}
DARK_BG = {"red":0.110,"green":0.157,"blue":0.200}

# ── Freeze rows ───────────────────────────────────────────────────────────────
print("Freezing rows on all tabs...")
run_batch([
    freeze(0, 2),   # Dashboard: freeze top 2 rows (title + info bar)
    freeze(1, 1),   # Transactions: freeze header row
    freeze(2, 4),   # Debt Tracker: freeze through row 4 (headers)
    freeze(3, 3),   # Savings Goals: freeze through row 3
    freeze(4, 3),   # Annual Overview: freeze through row 3
    freeze(5, 1),   # Setup: freeze title row
], "freeze rows on all tabs")

# ── Debt Tracker: bold totals row, debt-free date styling ────────────────────
print("Styling Debt Tracker totals...")
run_batch([
    repeat(rng(2,12,13,0,10), bold=True, va="MIDDLE"),
    repeat(rng(2,14,15,0,7),  va="MIDDLE"),
], "Debt Tracker styling")

# ── Savings Goals: progress bar formatting ────────────────────────────────────
# The % complete column (G = col 6) already has CF rules.
# Add a note row below with quick-start text.

# ── Annual Overview: bold INCOME row and NET row ──────────────────────────────
print("Styling Annual Overview key rows...")
run_batch([
    repeat(rng(4,3,4,0,15),  bold=True, va="MIDDLE"),    # header row
    repeat(rng(4,3,4,0,1),   bold=True, va="MIDDLE"),    # INCOME label
    repeat(rng(4,7,8,0,15),  bold=True, va="MIDDLE"),    # TOTAL SPEND row
    repeat(rng(4,8,9,0,15),  bold=True, va="MIDDLE"),    # NET CASH row
], "Annual Overview bold rows")

# ── Add Apps Script install note to Setup tab ─────────────────────────────────
print("Adding Apps Script install note to Setup...")
script_note = (
    "OPTIONAL AUTOMATION  —  Add the Budget Tools menu (clear data + theme toggle)\n\n"
    "1. In this spreadsheet, click Extensions > Apps Script\n"
    "2. Delete any existing code in the editor\n"
    "3. Open the file APPS_SCRIPT.js (included in your download)\n"
    "4. Paste the code into the Apps Script editor\n"
    "5. Press Ctrl+S to save, then click Run > Run function > onOpen\n"
    "6. Approve the permissions request\n"
    "7. Reload the spreadsheet — a 'Budget Tools' menu will appear!\n\n"
    "The Budget Tools menu lets you:\n"
    "  - Clear all 35 sample rows with one click (with confirmation)\n"
    "  - Toggle between dark and light theme\n"
    "  - View the About panel"
)

run_values([
    {"range": "Setup!A41", "values": [["  AUTOMATION (OPTIONAL)"]]},
    {"range": "Setup!A42:E42", "values": [["Step", "Action", "Where", "Details", "Note"]]},
    {"range": "Setup!A43:E43", "values": [["1","Open Apps Script editor","Extensions > Apps Script","A new browser tab will open with the code editor.","Only do this once"]]},
    {"range": "Setup!A44:E44", "values": [["2","Paste script code","Paste APPS_SCRIPT.js content","Delete any existing code, paste the full APPS_SCRIPT.js file.","Included in download"]]},
    {"range": "Setup!A45:E45", "values": [["3","Save & run onOpen","Ctrl+S, then Run > onOpen","Approve the permission request that appears.","One-time setup"]]},
    {"range": "Setup!A46:E46", "values": [["4","Reload spreadsheet","Close & reopen","A new 'Budget Tools' menu will appear in the menu bar.","Done!"]]},
], "Setup automation instructions")

# ── Format the automation section ─────────────────────────────────────────────
run_batch([
    # Section header
    {"mergeCells": {"range": rng(5,40,41,0,6), "mergeType": "MERGE_ALL"}},
    repeat(rng(5,40,41,0,6), bg=SAVINGS_CARD, tc=GOLD, bold=True, fs=12, ha="CENTER", va="MIDDLE"),
    {"updateDimensionProperties": {"range": {"sheetId":5,"dimension":"ROWS","startIndex":40,"endIndex":41},"properties":{"pixelSize":36},"fields":"pixelSize"}},
    # Column headers
    repeat(rng(5,41,42,0,6), bg=CARD_BG, tc=SECONDARY, bold=True, fs=9, ha="CENTER"),
    {"updateDimensionProperties": {"range": {"sheetId":5,"dimension":"ROWS","startIndex":41,"endIndex":42},"properties":{"pixelSize":22},"fields":"pixelSize"}},
    # Step rows
    repeat(rng(5,42,46,0,6), bg=DARK_BG, tc=WHITE, va="MIDDLE"),
    repeat(rng(5,42,46,0,1), bg=SAVINGS_CARD, tc=GOLD, bold=True, fs=12, ha="CENTER", va="MIDDLE"),
    {"updateDimensionProperties": {"range": {"sheetId":5,"dimension":"ROWS","startIndex":42,"endIndex":46},"properties":{"pixelSize":38},"fields":"pixelSize"}},
], "Automation section formatting")

print("\nFinal polish complete!")
