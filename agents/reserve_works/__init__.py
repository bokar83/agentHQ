"""
reserve_works — Reserve Works wheel strategy research agent.

Produces candidate trade lists for manual review. Does not place trades.
Does not select strikes. Does not execute on assignment. All outputs
route to Telegram for Boubacar's manual review and approval.

Kill switch: set RW_ENABLED=false in environment to disable all RW activity.
"""

import os

RW_ENABLED = os.environ.get("RW_ENABLED", "false").lower() == "true"
RW_PAPER_MODE = os.environ.get("RW_PAPER_MODE", "true").lower() == "true"
