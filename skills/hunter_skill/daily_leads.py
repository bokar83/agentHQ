"""
daily_leads.py — Daily Prospecting Orchestrator
==============================================
This skill coordinates the discovery of 20 high-intent Utah leads,
logs them to the PostgreSQL CRM, and formats a report for email delivery.
"""

import os
import logging
import json
from datetime import datetime
from typing import List, Dict

# Import existing tools if available, else placeholders
try:
    from skills.serper_skill.prospecting_tool import discover_utah_leads
    from skills.local_crm.crm_tool import add_lead, get_daily_scoreboard
except ImportError:
    # Log that we are using mock tools for testing if imports fail
    def discover_utah_leads(query: str = ""): return []
    def add_lead(data: dict): return 0
    def get_daily_scoreboard(): return {}

logger = logging.getLogger(__name__)

def harvest_daily_leads() -> Dict:
    """
    1. Search for 20 leads across ICP niches.
    2. Add to CRM.
    3. Return a formatted report.
    """
    niches = [
        "Law Firm Managing Partner Salt Lake City",
        "Accounting Practice Owner Utah County",
        "Creative Marketing Agency Founder SLC",
        "HVAC Plumbing Electrical Company Owner Utah"
    ]
    
    all_found_leads = []
    
    # We want 20 total, so 5 per niche
    for niche in niches:
        logger.info(f"Harvesting leads for niche: {niche}")
        leads = discover_utah_leads(niche)
        # In a real scenario, discover_utah_leads would be updated to return more or called multiple times
        all_found_leads.extend(leads)

    added_count = 0
    report_lines = [f"# Catalyst Daily Lead Report — {datetime.now().strftime('%Y-%m-%d')}\n"]
    
    for lead in all_found_leads:
        # Add to CRM
        lead_id = add_lead(lead)
        if lead_id:
            added_count += 1
            report_lines.append(f"### {lead['name']} ({lead.get('company', 'Unknown Company')})")
            report_lines.append(f"- **Title:** {lead.get('title', 'Founder/Owner')}")
            report_lines.append(f"- **Email:** {lead.get('email', 'pending@verification.com')}")
            report_lines.append(f"- **LinkedIn:** {lead.get('linkedin_url', 'N/A')}")
            report_lines.append(f"- **Niche:** {lead.get('source', 'Serper Harvest')}")
            report_lines.append("")

    report_lines.append(f"\n**TOTAL LEADS HARVESTED:** {added_count}")
    
    return {
        "count": added_count,
        "report": "\n".join(report_lines)
    }

if __name__ == "__main__":
    result = harvest_daily_leads()
    print(result['report'])
