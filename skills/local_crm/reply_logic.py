"""
reply_logic.py — Catalyst Growth Engine Reply Handling
======================================================
This skill enforces the direct "Move-to-Call" protocol for incoming replies.
Goal: Minimize chatter. Maximize conversions to 15-minute Strategy Calls.
"""

from .crm_tool import update_lead_status, log_interaction

def process_reply(lead_id: int, incoming_msg: str) -> str:
    """
    Handle an incoming message from a lead.
    Enforces the 'Reply -> Reply -> Call' rule.
    """
    log_interaction(lead_id, 'reply', incoming_msg)
    update_lead_status(lead_id, 'replied')
    
    # Logic to decide the reply response (to be connected to leGriot or BouB AI Voice)
    # The prompt for the agent should be: 
    # "A lead just replied with: {incoming_msg}. Your goal is to move to a 15-minute call."
    
    return "✅ Reply logged. Ready for Agent Response (Goal: Book call)."

if __name__ == "__main__":
    print(process_reply(1, "Interesting. Tell me more."))
    # Expected output: Confirmation that the CRM was updated.
