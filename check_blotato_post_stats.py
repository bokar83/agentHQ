import os
import sys
import json

def load_env(path=".env"):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    val = val.strip().strip("'").strip('"')
                    os.environ[key.strip()] = val

load_env()
sys.path.append("orchestrator")

from blotato_publisher import BlotatoPublisher

# Live Submission IDs from your Content Board
submission_ids = [
    "4dbb1d17-e7a3-4103-b294-46c808770ab5",
    "67121407-d3c1-488f-b572-42e69fa99e57",
    "4e198ff1-f762-4202-bb90-6ce051976186",
    "bfc19cbf-69b6-4dbc-b4b4-82509a1a2710"
]

try:
    publisher = BlotatoPublisher()
    
    for sid in submission_ids:
        print(f"\n========================================\nQuerying Blotato for Submission ID: {sid}")
        try:
            status_data = publisher.get_status(sid)
            print(json.dumps(status_data, indent=2))
        except Exception as err:
            print(f"Error querying {sid}: {err}")
            
    publisher.close()
except Exception as e:
    print(f"General Error: {e}")
