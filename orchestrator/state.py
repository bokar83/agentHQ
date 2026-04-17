"""
state.py — In-memory system state trackers.
"""

# In-memory tracker: chat_id -> last completed job metadata
# Used by praise/critique detector to pair feedback with prior output.
_last_completed_job: dict = {}

# In-memory project context: chat_id -> active project name
# Set via /switch <project-name>; used as session_key prefix for crews
_active_project: dict = {}
