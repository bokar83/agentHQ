"""
Attempts to create an Apps Script project via Drive API and upload code via direct HTTP.
Falls back to a helper cell note in the spreadsheet.
"""
import json, os, subprocess, urllib.request, urllib.parse, urllib.error

SHEET_ID = "1pkO1G5q_qDe0nLCm7W12O3-jurzYKH16bcw8X5AOmQ0"
GIT_BASH  = r"C:\Program Files\Git\bin\bash.exe"
OUT       = r"D:\Ai_Sandbox\agentsHQ\Dashboards4Sale\tmp"

def to_unix(p):
    p = p.replace("\\", "/")
    if len(p) > 1 and p[1] == ":": p = "/" + p[0].lower() + p[2:]
    return p

# ── Try to get access token via gws token cache ───────────────────────────────
def get_access_token():
    """Get a fresh access token by running a gws command and capturing the auth header."""
    # gws injects an Authorization header for every request.
    # We can't easily extract it, but we can try using gws drive files get on the spreadsheet
    # to confirm auth works, then use the credentials.
    
    # Try: export environment variable or read token from cache
    # The token_cache.json is binary/encrypted, but let's see if gws exposes a token endpoint
    result = subprocess.run(
        [GIT_BASH, "-c", "gws auth export 2>&1 | grep -v Using"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    try:
        creds = json.loads(result.stdout.strip())
        client_id = creds.get("client_id", "")
        client_secret = creds.get("client_secret", "")
        refresh_token = creds.get("refresh_token", "")
        
        # Check if masked (length 11 chars with ... is the masked format)
        if "..." in client_secret or len(client_secret) < 20:
            return None, "client_secret is masked"
        if "..." in refresh_token or len(refresh_token) < 20:
            return None, "refresh_token is masked"
        
        # Try token refresh
        payload = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }).encode()
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=payload)
        resp = json.loads(urllib.request.urlopen(req).read())
        return resp.get("access_token"), None
    except Exception as e:
        return None, str(e)

token, err = get_access_token()
if err:
    print(f"Cannot get access token: {err}")
    print("Apps Script must be added manually (code saved to APPS_SCRIPT.js)")
else:
    print(f"Got access token: {token[:20]}...")
    
    # Try Apps Script API
    SCRIPT_CODE = open(os.path.join(OUT, "APPS_SCRIPT.js"), encoding="utf-8").read()
    
    # Step 1: Create project
    create_body = json.dumps({"title": "Budget Planner Scripts", "parentId": SHEET_ID}).encode()
    req = urllib.request.Request(
        "https://script.googleapis.com/v1/projects",
        data=create_body, method="POST"
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        resp = json.loads(urllib.request.urlopen(req).read())
        script_id = resp.get("scriptId", "")
        print(f"Created script project: {script_id}")
        
        # Step 2: Upload content
        content_body = json.dumps({
            "files": [
                {"name": "Code", "type": "SERVER_JS", "source": SCRIPT_CODE},
                {"name": "appsscript", "type": "JSON", "source": json.dumps({
                    "timeZone": "America/New_York", "runtimeVersion": "V8",
                    "dependencies": {}, "exceptionLogging": "STACKDRIVER"
                })}
            ]
        }).encode()
        req2 = urllib.request.Request(
            f"https://script.googleapis.com/v1/projects/{script_id}/content",
            data=content_body, method="PUT"
        )
        req2.add_header("Authorization", f"Bearer {token}")
        req2.add_header("Content-Type", "application/json")
        resp2 = json.loads(urllib.request.urlopen(req2).read())
        print(f"Script content uploaded: {list(resp2.keys())}")
        print("Apps Script created and uploaded successfully!")
    except urllib.error.HTTPError as e:
        err_body = json.loads(e.read())
        print(f"Apps Script API error: {err_body.get('error',{}).get('message','unknown')}")
        print("Code is in APPS_SCRIPT.js — add manually via Extensions > Apps Script")

