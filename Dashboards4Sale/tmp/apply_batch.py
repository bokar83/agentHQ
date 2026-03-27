"""
Reads a batchUpdate JSON file, splits into chunks, writes each chunk to a tiny
temp file, then calls gws via shell for each chunk.
Usage: python apply_batch.py <json_file> [chunk_size]
"""
import json, sys, os, subprocess

SHEET_ID = "1pkO1G5q_qDe0nLCm7W12O3-jurzYKH16bcw8X5AOmQ0"
CHUNK = int(sys.argv[2]) if len(sys.argv) > 2 else 20
BASE = os.path.dirname(os.path.abspath(__file__))

def run_chunk(chunk_requests, idx):
    tmp_path = os.path.join(BASE, f"_chunk_{idx}.json")
    payload = {"requests": chunk_requests}
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    # Use powershell to avoid bash arg-length limits
    ps_cmd = (
        f'$j = Get-Content "{tmp_path}" -Raw -Encoding UTF8; '
        f'gws sheets spreadsheets batchUpdate '
        f'--params \'{{"spreadsheetId":"{SHEET_ID}"}}\' '
        f'--json $j'
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_cmd],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    os.remove(tmp_path)
    out = result.stdout + result.stderr
    if '"replies"' in out:
        return True
    if "error" in out.lower():
        print(f"    ERR chunk {idx}: {out[:300]}")
        return False
    return True

def main():
    fname = sys.argv[1]
    with open(fname, encoding="utf-8") as f:
        data = json.load(f)
    reqs = data.get("requests", [])
    total = len(reqs)
    print(f"  {os.path.basename(fname)}: {total} requests in chunks of {CHUNK}")
    ok = 0
    failed = 0
    for i in range(0, total, CHUNK):
        chunk = reqs[i:i+CHUNK]
        if run_chunk(chunk, i // CHUNK):
            ok += len(chunk)
        else:
            failed += len(chunk)
        print(f"    [{ok}/{total}] applied, {failed} failed")
    print(f"  DONE: {ok} OK, {failed} failed")

main()
