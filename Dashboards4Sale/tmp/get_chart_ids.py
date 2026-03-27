"""Fetch all chart IDs from the Dashboard sheet"""
import json, subprocess

SHEET_ID = "1pkO1G5q_qDe0nLCm7W12O3-jurzYKH16bcw8X5AOmQ0"
GIT_BASH  = r"C:\Program Files\Git\bin\bash.exe"

cmd = (f"gws sheets spreadsheets get "
       f"--params '{{\"spreadsheetId\":\"{SHEET_ID}\",\"includeGridData\":false}}'")

r = subprocess.run([GIT_BASH, "-c", cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
out = r.stdout + r.stderr
lines = [l for l in out.splitlines() if not l.startswith("Using")]
try:
    data = json.loads("\n".join(lines))
    for sheet in data.get("sheets", []):
        title = sheet["properties"]["title"]
        charts = sheet.get("charts", [])
        if charts:
            print(f"\n=== {title} ===")
            for c in charts:
                cid = c.get("chartId")
                ctitle = c.get("spec", {}).get("title", "?")
                pos = c.get("position", {}).get("overlayPosition", {})
                anchor = pos.get("anchorCell", {})
                print(f"  ID={cid}  title='{ctitle}'  anchor=row{anchor.get('rowIndex')},col{anchor.get('columnIndex')}  size={pos.get('widthPixels')}x{pos.get('heightPixels')}")
except Exception as e:
    print(f"Parse error: {e}")
    print(out[:1000])
