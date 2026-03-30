"""
scoreboard.py — Daily Revenue Scoreboard Logic
==============================================
This skill generates the 9:00 AM awareness and 5:00 PM accountability
reports for Boubacar. It pulls live stats from the Postgres CRM.
"""

from .crm_tool import get_daily_scoreboard

def format_daily_scoreboard() -> str:
    """
    Returns a formatted string representing the daily progress.
    Used for WhatsApp broadcasts/replies.
    """
    stats = get_daily_scoreboard()
    if not stats:
        return "⚠️ CRM Scoreboard Unavailable (Check Postgres Connection)"
        
    indicator = "✅" if stats['messages_sent'] >= 5 else "⏳"
    
    return (
        f"📊 *DAILY REVENUE SCOREBOARD*\n\n"
        f"{indicator} *Outreach Goal: 5 / 5*\n"
        f"- Leads found today: {stats['leads_found']}\n"
        f"- Messages sent today: {stats['messages_sent']}\n"
        f"--------------------------\n"
        f"📬 *Pipeline Health:*\n"
        f"- Replies received: {stats['replies']}\n"
        f"- Strategy Calls booked: {stats['booked']}\n"
        f"--------------------------\n"
        f"*Status:* {indicator if stats['messages_sent'] >= 5 else '⚠️ ACTION NEEDED — Reach out to 5 now.'}"
    )

if __name__ == "__main__":
    print(format_daily_scoreboard())
