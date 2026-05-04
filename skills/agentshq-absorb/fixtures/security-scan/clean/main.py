import os
import requests

API_KEY = os.environ.get("API_KEY")

def fetch_data(url):
    response = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
    return response.json()
