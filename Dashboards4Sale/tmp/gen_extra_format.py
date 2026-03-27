import json, os, subprocess

SHEET_ID = "1pkO1G5q_qDe0nLCm7W12O3-jurzYKH16bcw8X5AOmQ0"
GIT_BASH  = r"C:\Program Files\Git\bin\bash.exe"
OUT       = r"D:\Ai_Sandbox\agentsHQ\Dashboards4Sale\tmp"

def to_unix(p):
    p = p.replace("\\", "/")
    if len(p) > 1 and p[1] == ":": p = "/" + p[0].lower() + p[2:]
    return p

def rng(sid,r1,r2,c1,c2): return {"sheetId":sid,"startRowIndex":r1,"endRowIndex":r2,"startColumnIndex":c1,"endColumnIndex":c2}
def repeat(range_d,**fmt):
    f = {}
    if "bg" in fmt: f["backgroundColor"] = fmt["bg"]
    tf = {}
    if "tc" in fmt: tf["foregroundColor"] = fmt["tc"]
    if fmt.get("bold"): tf["bold"] = True
    if tf: f["textFormat"] = tf
    if "ha" in fmt: f["horizontalAlignment"] = fmt["ha"]
    if "nf" in fmt: f["numberFormat"] = fmt["nf"]
    fields = "userEnteredFormat(" + ",".join(f.keys()) + ")"
    return {"repeatCell": {"range":range_d,"cell":{"userEnteredFormat":f},"fields":fields}}

CURR = {"type":"CURRENCY","pattern":"$#,##0.00"}
PCT  = {"type":"PERCENT","pattern":"0%"}
DATE_FMT = {"type":"DATE","pattern":"MM/DD/YYYY"}
SID_DASH = 0

reqs = []
# Dashboard: KPI value rows (row 5 = index 5) - already formatted by repeat but set number format on formula cells
reqs.append(repeat(rng(SID_DASH,5,6,0,3),  nf=CURR, ha="CENTER"))  # Income KPI
reqs.append(repeat(rng(SID_DASH,5,6,3,6),  nf=CURR, ha="CENTER"))  # Spending KPI
reqs.append(repeat(rng(SID_DASH,5,6,6,9),  nf=CURR, ha="CENTER"))  # Remaining KPI
reqs.append(repeat(rng(SID_DASH,5,6,9,12), nf=CURR, ha="CENTER"))  # Savings KPI

# Budget vs Actual: Budget, Actual, Difference cols (cols 2, 4, 6)
for c in [2, 4, 6]:
    reqs.append(repeat(rng(SID_DASH,10,14,c,c+1), nf=CURR))
# % col (col 8) 
reqs.append(repeat(rng(SID_DASH,10,14,8,9), nf=PCT))

# Top 10 transactions: Date col (A=0) and Amount col (E=4)
reqs.append(repeat(rng(SID_DASH,17,27,0,1), nf=DATE_FMT, ha="CENTER"))
reqs.append(repeat(rng(SID_DASH,17,27,4,5), nf=CURR, ha="RIGHT"))

# Spending breakdown: Budget(C=2), Actual(E=4), Remaining(G=6) cols, % col (I=8)
for c in [2, 4, 6]:
    reqs.append(repeat(rng(SID_DASH,30,33,c,c+1), nf=CURR))
reqs.append(repeat(rng(SID_DASH,30,33,8,9), nf=PCT))

# Annual Overview: number formats
SID_ANN = 4
# Rows 4-9 (currency), row 10 (percent)
for row in range(3, 9):
    reqs.append(repeat(rng(SID_ANN,row,row+1,1,15), nf={"type":"CURRENCY","pattern":"$#,##0"}))
reqs.append(repeat(rng(SID_ANN,9,10,1,15), nf={"type":"PERCENT","pattern":"0%"}))

payload = {"requests": reqs}
fname = os.path.join(OUT, "_extra_fmt.json")
with open(fname, "w") as f: json.dump(payload, f)
unix = to_unix(fname)
cmd = (f"gws sheets spreadsheets batchUpdate "
       f"--params '{{\"spreadsheetId\":\"{SHEET_ID}\"}}' "
       f"--json \"$(cat '{unix}')\"")
r = subprocess.run([GIT_BASH, "-c", cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
os.remove(fname)
out = r.stdout + r.stderr
if '"replies"' in out:
    print("OK: extra number formats applied")
else:
    print(f"ERR: {out[:200]}")
