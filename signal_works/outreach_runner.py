"""
signal_works/outreach_runner.py
Standalone daily runner for Catalyst Works cold outreach.
Mirrors the Signal Works morning_runner.py pattern.

Creates up to 10 Gmail drafts per day in boubacar@catalystworks.consulting
for CRM leads that have not yet been contacted.

Called by: morning_runner.py (step 4 of daily sequence)
           Or standalone: python -m signal_works.outreach_runner
"""
import logging
import os
import socket
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Ensure agentsHQ root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Also add /app alias for the outreach_tool's internal imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "orchestrator"))


def run() -> int:
    """Run CW cold outreach drafts. Returns number of drafts created."""
    from skills.coordination import claim, complete

    holder = f"{socket.gethostname()}/pid={os.getpid()}/outreach_runner"
    task = claim(resource="task:outreach-runner-cw", holder=holder, ttl_seconds=900)
    if task is None:
        logger.warning(
            "Another outreach_runner is already running. Exiting cleanly. "
            "Check skills.coordination.list_running()."
        )
        return 0

    try:
        try:
            from skills.outreach.outreach_tool import run_outreach
            result = run_outreach(contact_all=False)  # default: 10 leads per run
            drafted = result.get("drafted", 0)
            skipped = result.get("skipped", 0)
            error = result.get("error")
            if error:
                logger.error(f"CW outreach error: {error}")
            logger.info(f"CW outreach: {drafted} drafted, {skipped} skipped.")
            return drafted
        except Exception as e:
            logger.error(f"CW outreach runner failed: {e}")
            return 0
    finally:
        complete(task["id"])


if __name__ == "__main__":
    count = run()
    sys.exit(0 if count > 0 else 1)
