import json, os

SHEET_ID = "1pkO1G5q_qDe0nLCm7W12O3-jurzYKH16bcw8X5AOmQ0"
GIT_BASH = r"C:\Program Files\Git\bin\bash.exe"
OUT = r"D:\Ai_Sandbox\agentsHQ\Dashboards4Sale\tmp"

def rng(sid, r1, r2, c1, c2):
    return {"sheetId": sid, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}

GREEN  = {"red": 0.180, "green": 0.800, "blue": 0.443}
CORAL  = {"red": 1.000, "green": 0.420, "blue": 0.420}

# Fix the 2 KPI "remaining" card CF rules (fontSize not allowed in CF textFormat)
reqs = [
    # Remove old rules at index 0 and 1 first (delete highest index first)
    {"deleteConditionalFormatRule": {"sheetId": 0, "index": 1}},
    {"deleteConditionalFormatRule": {"sheetId": 0, "index": 0}},
    # Re-add without fontSize
    {"addConditionalFormatRule": {"rule": {"ranges": [rng(0, 5, 6, 6, 9)],
        "booleanRule": {"condition": {"type": "NUMBER_GREATER_THAN_EQ", "values": [{"userEnteredValue": "0"}]},
        "format": {"textFormat": {"foregroundColor": GREEN, "bold": True}}}}, "index": 0}},
    {"addConditionalFormatRule": {"rule": {"ranges": [rng(0, 5, 6, 6, 9)],
        "booleanRule": {"condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "0"}]},
        "format": {"textFormat": {"foregroundColor": CORAL, "bold": True}}}}, "index": 1}},
]

p = os.path.join(OUT, "fix_cf.json")
with open(p, "w") as f:
    json.dump({"requests": reqs}, f)
print(f"Wrote {p}")
