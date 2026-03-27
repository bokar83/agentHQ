"""
Splits a large batchUpdate JSON into small chunk files, then runs gws for each.
Usage: python split_and_run.py <json_file> [chunk_size]
"""
import json, sys, os, subprocess

SHEET_ID = "1pkO1G5q_qDe0nLCm7W12O3-jurzYKH16bcw8X5AOmQ0"
CHUNK = int(sys.argv[2]) if len(sys.argv) > 2 else 10
BASE = os.path.dirname(os.path.abspath(__file__))

GIT_BASH = r"C:\Program Files\Git\bin\bash.exe"

def to_git_bash_path(p):
    """Convert Windows path like D:\foo\bar to /d/foo/bar for Git Bash."""
    p = p.replace("\\", "/")
    if len(p) > 1 and p[1] == ":":
        p = "/" + p[0].lower() + p[2:]
    return p

def gws_batch(chunk_file):
    unix_path = to_git_bash_path(chunk_file)
    cmd = (
        f'gws sheets spreadsheets batchUpdate '
        f"--params '{{\"spreadsheetId\":\"{SHEET_ID}\"}}' "
        f"--json \"$(cat '{unix_path}')\""
    )
    r = subprocess.run([GIT_BASH, "-c", cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = r.stdout + r.stderr
    return '"replies"' in out, out

def main():
    fname = sys.argv[1]
    with open(fname, encoding="utf-8") as f:
        data = json.load(f)
    reqs = data.get("requests", [])
    total = len(reqs)
    print(f"{os.path.basename(fname)}: {total} requests, chunk={CHUNK}")

    ok = failed = 0
    chunk_files = []
    # Write all chunk files first
    for i in range(0, total, CHUNK):
        chunk = reqs[i:i+CHUNK]
        cpath = os.path.join(BASE, f"_c{i//CHUNK:03d}.json")
        with open(cpath, "w", encoding="utf-8") as f:
            json.dump({"requests": chunk}, f)
        chunk_files.append((cpath, len(chunk)))

    # Run each chunk
    for idx, (cpath, n) in enumerate(chunk_files):
        size = os.path.getsize(cpath)
        success, out = gws_batch(cpath)
        os.remove(cpath)
        if success:
            ok += n
            print(f"  chunk {idx+1}/{len(chunk_files)}: {n} reqs ({size}b) OK  [{ok}/{total}]")
        else:
            failed += n
            print(f"  chunk {idx+1}/{len(chunk_files)}: FAILED ({size}b) -> {out[:150]}")

    print(f"DONE: {ok}/{total} OK, {failed} failed")

main()
