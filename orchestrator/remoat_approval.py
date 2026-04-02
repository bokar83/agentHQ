import sys
import time
from notifier import log_for_remoat

def await_remoat_approval(prompt: str, timeout_seconds: int = 3600) -> str:
    """
    Pauses execution, pings Telegram via Remoat, and waits for a terminal response.
    Remoat handles the 'input' part by piping Telegram replies back into the stdin.
    """
    log_for_remoat(f"🤔 APPROVAL REQUIRED:\n{prompt}\n\n(Reply directly to the Telegram message to approve or reject)", "APPROVAL")
    
    print(f"\n[REMOAT:WAITING] Waiting for input for: {prompt}")
    
    # In Remoat mode, the reply from Telegram is piped into standard input (stdin)
    # We use a simple input() call which will block until Remoat feeds it the reply.
    try:
        user_response = input("REMOAT_INPUT> ").strip()
        log_for_remoat(f"✅ Received Choice: {user_response}", "NOTIFICATION")
        return user_response
    except EOFError:
        log_for_remoat("❌ Remoat input stream closed unexpectedly.", "ERROR")
        return "error: stream closed"
    except Exception as e:
        log_for_remoat(f"❌ Error waiting for approval: {e}", "ERROR")
        return f"error: {str(e)}"

if __name__ == "__main__":
    # Quick Test
    print("Testing Remoat Approval Utility...")
    choice = await_remoat_approval("Should I proceed with the Supabase migration?")
    print(f"User decided: {choice}")
