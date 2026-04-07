"""
test_growth_engine.py — CRM & Apollo Verification
==================================================
Run this to verify that the local CRM and Apollo skills are correctly 
integrated and the database connection is functional.
"""

import os
import sys
import logging

import sys
import logging
from dotenv import load_dotenv

# Ensure orchestrator is in path for imports
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

# Load environment variables
env_path = os.path.join(base_dir, "infrastructure", ".env")
load_dotenv(env_path)

from skills.local_crm.crm_tool import add_lead, get_daily_scoreboard
from skills.serper_skill.prospecting_tool import discover_utah_leads

logging.basicConfig(level=logging.INFO)

def run_test():
    print("🚀 Starting Growth Engine Verification (Serper Pivot)...")

    # 1. Test Serper Search (Dry Run)
    print("\n[1/3] Testing Serper Lead Discovery...")
    leads = discover_utah_leads("Founder Marketing Agency Salt Lake City")
    if leads:
        print(f"✅ Found {len(leads)} leads via Serper/LinkedIn.")
        for l in leads[:3]:  # Show first 3
            print(f"   - {l['name']} ({l['linkedin_url']})")
    else:
        print("⚠️ No leads found (Check Serper API Key or Query).")

    # 2. Test CRM Addition (Postgres)
    print("\n[2/3] Testing CRM Addition...")
    test_lead = {
        "name": "Boubacar Test",
        "company": "Catalyst Works",
        "title": "Owner",
        "location": "SLC, UT",
        "linkedin_url": "https://linkedin.com/in/bdiallo",
        "source": "test_script"
    }
    lead_id = add_lead(test_lead)
    if lead_id > 0:
        print(f"✅ Lead added to Postgres CRM. ID: {lead_id}")
    else:
        print("❌ CRM Add failed (Check Postgres connection and schema_v2.sql).")

    # 3. Test Scoreboard Logic
    print("\n[3/3] Testing Daily Scoreboard...")
    stats = get_daily_scoreboard()
    if stats:
        print(f"✅ Scoreboard Stats: {stats}")
    else:
        print("❌ Scoreboard Retrieval failed.")

    print("\n🏁 Verification Complete.")

if __name__ == "__main__":
    run_test()
