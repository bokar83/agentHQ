"""
apollo_tool.py — Apollo.io Lead Discovery Logic
==============================================
This skill identifies high-quality leads in the Utah niche using the Apollo.io API.
It prioritizes searching over revealing lead contact details to preserve credits.
"""

import os
import logging
import httpx
from typing import List, Optional

logger = logging.getLogger(__name__)

APOLLO_API_URL = "https://api.apollo.io/v1"
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY")

def search_utah_leads(query: str = "") -> List[dict]:
    """
    Search for professional service SMBs in Utah (SLC/Utah County).
    Prioritizes Legal, Accounting, Agencies, and Home Services.
    - query: optional text search
    - location: Salt Lake City, Utah County
    No credits are spent for searching.
    """
    if not APOLLO_API_KEY:
        logger.warning("APOLLO_API_KEY not found in environment.")
        return []

    try:
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": APOLLO_API_KEY,
            "Cache-Control": "no-cache"
        }
        data = {
            "q_keywords": query if query else "Legal, Accounting, Marketing Agency, HVAC, Plumbing",
            "person_locations": ["Salt Lake City, Utah", "Provo, Utah", "Orem, Utah", "Lehi, Utah"],
            "person_titles": ["Owner", "Founder", "CEO", "President", "Managing Partner"],
            "organization_num_employees_range": [10, 80], # 10-75 employees target
            "page": 1,
            "per_page": 10
        }

        with httpx.Client() as client:
            response = client.post(f"{APOLLO_API_URL}/mixed_people/api_search", json=data, headers=headers)
            response.raise_for_status()
            results = response.json()

        leads = []
        for person in results.get("people", []):
            leads.append({
                "name": person.get("name"),
                "company": person.get("organization", {}).get("name"),
                "title": person.get("title"),
                "location": person.get("organization", {}).get("primary_location", {}).get("city"),
                "linkedin_url": person.get("linkedin_url"),
                "source": "apollo"
            })
        
        return leads[:5] # Return top 5 prospects
    except Exception as e:
        logger.error(f"Apollo search failed: {e}")
        return []

def reveal_lead_email(linkedin_url: str) -> Optional[str]:
    """
    Exchanges 1 credit to reveal the email of a specific individual.
    Only triggered if the owner authorizes the lead outreach.
    Returns: email string or None.
    """
    if not APOLLO_API_KEY:
        return None

    try:
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": APOLLO_API_KEY,
            "Cache-Control": "no-cache"
        }
        data = {
            "linkedin_url": linkedin_url
        }

        with httpx.Client() as client:
            response = client.post(f"{APOLLO_API_URL}/people/match", json=data, headers=headers)
            response.raise_for_status()
            result = response.json()

        person = result.get("person", {})
        email = person.get("email")
        
        if email:
            logger.info(f"Revealed email for {linkedin_url}: {email}")
        return email
    except Exception as e:
        logger.error(f"Apollo reveal failed: {e}")
        return None
