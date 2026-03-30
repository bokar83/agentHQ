"""
prospecting_tool.py — Serper-Based Lead Discovery
=================================================
This skill identifies high-quality leads in the Utah niche using Google/Serper.
Focuses on LinkedIn profiling of Founders/Owners in Salt Lake & Utah County.
"""

import os
import json
import logging
import httpx
from typing import List

logger = logging.getLogger(__name__)

SERPER_API_KEY = os.environ.get("SERPER_API_KEY")
SERPER_URL = "https://google.serper.dev/search"

def discover_utah_leads(query: str = "") -> List[dict]:
    """
    Search for professional service SMBs in Utah (SLC/Utah County).
    Targets Owners/Founders on LinkedIn.
    Returns: List of lead dictionaries.
    """
    if not SERPER_API_KEY:
        logger.warning("SERPER_API_KEY not found in environment.")
        return []

    # Construct a high-intent LinkedIn dorking query
    # e.g. site:linkedin.com/in/ "Founder" "Salt Lake City" "Marketing Agency"
    base_query = query if query else "Founder Owner Salt Lake City Utah County Marketing Agency Legal Accounting HVAC"
    search_query = f'site:linkedin.com/in/ {base_query}'

    try:
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        payload = json.dumps({"q": search_query, "num": 10})

        with httpx.Client() as client:
            response = client.post(SERPER_URL, headers=headers, data=payload)
            response.raise_for_status()
            results = response.json()

        leads = []
        for result in results.get("organic", []):
            # Extract basic info from snippet/title
            # Title usually looks like "Name - Title - Company | LinkedIn"
            title_parts = result.get("title", "").split(" - ")
            name = title_parts[0] if len(title_parts) > 0 else "Unknown Name"
            
            leads.append({
                "name": name,
                "company": "See LinkedIn Snippet", # Serper doesn't have structured company fields like Apollo
                "title": "Founder/Owner", # Assumed by search query
                "location": "Utah",
                "linkedin_url": result.get("link"),
                "source": "serper_discovery"
            })
        
        return leads[:5] # Return top 5
    except Exception as e:
        logger.error(f"Serper prospecting failed: {e}")
        return []

if __name__ == "__main__":
    # Test script
    test_leads = discover_utah_leads("Marketing Agency SLC")
    print(json.dumps(test_leads, indent=2))
