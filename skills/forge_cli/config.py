import os
import json
from dotenv import load_dotenv

load_dotenv()

NOTION_SECRET = os.getenv("NOTION_SECRET", "")
NOTION_VERSION = "2022-06-28"

# Database IDs
FORGE_PAGE_ID = os.getenv("FORGE_PAGE_ID", "")
TASKS_DB = os.getenv("FORGE_TASKS_DB", "249bcf1a302980739c26c61cad212477")
PIPELINE_DB = os.getenv("FORGE_PIPELINE_DB", "249bcf1a302980f58d84cbbf4fa4dbdb")
REVENUE_DB = os.getenv("FORGE_REVENUE_DB", "24abcf1a3029801f8231d694427dca35")
CONTENT_DB = os.getenv("FORGE_CONTENT_DB", "")
ACTIVITY_LOG_DB = os.getenv("NOTION_DATABASE_ID", "339bcf1a3029818c8f27fb4203b23603")
KPI_BLOCK_IDS = os.getenv("FORGE_KPI_BLOCK_IDS", "").split(",")

# Blotato (Phase 2)
BLOTATO_API_KEY = os.getenv("BLOTATO_API_KEY", "")
BLOTATO_ACCOUNT_IDS = json.loads(os.getenv("BLOTATO_ACCOUNT_IDS", "{}"))
