import json, os

requests = []
for i in range(1, 36):
    color = {"red": 0.969, "green": 0.980, "blue": 0.980} if i % 2 == 0 else {"red": 1.0, "green": 1.0, "blue": 1.0}
    requests.append({
        "repeatCell": {
            "range": {"sheetId": 1, "startRowIndex": i, "endRowIndex": i+1, "startColumnIndex": 0, "endColumnIndex": 9},
            "cell": {"userEnteredFormat": {"backgroundColor": color}},
            "fields": "userEnteredFormat.backgroundColor"
        }
    })

out = os.path.join(os.path.dirname(__file__), "txn_alt_rows.json")
with open(out, "w") as f:
    json.dump({"requests": requests}, f)
print("done", len(requests), "->", out)
