"""
Direct Google Sheets API caller. Handles large JSON without shell arg limits.
Usage: python sheets_api.py <json_file> [chunk_size]
       python sheets_api.py --values <json_file>
"""
import json, sys, os, urllib.request, urllib.parse, subprocess

SHEET_ID = "1pkO1G5q_qDe0nLCm7W12O3-jurzYKH16bcw8X5AOmQ0"
CHUNK = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] != "--values" else 40

def get_token():
    creds_raw = subprocess.run(["gws", "auth", "export"], capture_output=True, text=True, shell=True).stdout
    # Parse from output (skip "Using keyring" line)
    lines = [l for l in creds_raw.strip().splitlines() if not l.startswith("Using")]
    creds = json.loads("\n".join(lines))
    payload = urllib.parse.urlencode({
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=payload)
    resp = json.loads(urllib.request.urlopen(req).read())
    return resp["access_token"]

def api_call(url, body, token, method="POST"):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        return None, json.loads(e.read())

def batch_update(requests_list, token):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}:batchUpdate"
    return api_call(url, {"requests": requests_list}, token)

def values_batch_update(data, token):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values:batchUpdate"
    return api_call(url, data, token)

def main():
    values_mode = "--values" in sys.argv
    fname = sys.argv[2] if values_mode else sys.argv[1]

    print(f"Getting access token...")
    token = get_token()
    print(f"Token OK")

    with open(fname, encoding="utf-8") as f:
        data = json.load(f)

    if values_mode:
        resp, err = values_batch_update(data, token)
        if err:
            print(f"ERROR: {json.dumps(err)[:300]}")
        else:
            cells = sum(r.get("updatedCells", 0) for r in resp.get("responses", []))
            print(f"OK: {cells} cells updated")
        return

    reqs = data.get("requests", [])
    total = len(reqs)
    print(f"{os.path.basename(fname)}: {total} requests, chunk={CHUNK}")
    ok = failed = 0
    for i in range(0, total, CHUNK):
        chunk = reqs[i:i+CHUNK]
        resp, err = batch_update(chunk, token)
        if err:
            print(f"  ERR chunk {i//CHUNK+1}: {json.dumps(err)[:200]}")
            failed += len(chunk)
        else:
            ok += len(chunk)
        print(f"  [{ok}/{total}] OK  [{failed} failed]")
    print(f"DONE: {ok} OK, {failed} failed")

main()
