"""
constants.py — System-wide configuration tokens and task classifications.
"""

SAVE_REQUIRED_TASK_TYPES = {
    "research_report",
    "consulting_deliverable",
    "website_build",
    "app_build",
    "3d_website_build",
    "code_task",
    "general_writing",
    "social_content",
    "linkedin_x_campaign",
    "voice_polishing",
    "crm_outreach",
    "hunter_task",
    "content_push_to_drive",
    "skill_build",
    "nlm_artifact",
}

# Task types that produce publishable content -- after Drive save, also log to
# the Notion content board with the Drive URL.
CONTENT_TASK_TYPES = {
    "social_content",
    "linkedin_x_campaign",
    "general_writing",
    "voice_polishing",
    "content_push_to_drive",
}

MEMORY_GATED_TASK_TYPES = {
    "research_report",
    "consulting_deliverable",
    "website_build",
    "web_builder",
    "3d_web_builder",
    "notion_architect",
    "copywriting",
    "cold_outreach",
    "email_draft",
}
