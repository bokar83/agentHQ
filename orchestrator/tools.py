"""
tools.py — Tool Registry
=========================
All tools available to agentsHQ agents are defined and
registered here. Agents import what they need from this file.

Tool categories:
  1. Search & Research (Serper, web scraping)
  2. File Operations (read, write, save outputs)
  3. Code Execution
  4. MCP Server Adapters (external services)
  5. Memory Tools (Qdrant queries)
  6. Communication Tools (n8n webhooks)

Adding a new tool:
  1. Define it here
  2. Create skills/[tool-name]/SKILL.md
  3. Import in agents.py for relevant agents
  4. Register in AGENTS.md
"""

import os
import sys
import json
import logging
import subprocess
import sys

# Subprocess creation flags to suppress console window flashing on Windows
SUBPROCESS_FLAGS = 0x08000000 if sys.platform == "win32" else 0
import httpx
from datetime import datetime
from typing import Any, Optional
from crewai_tools import (
    SerperDevTool,
    FileWriterTool,
    FileReadTool,
)
try:
    from crewai_tools import CodeInterpreterTool
    _code_interpreter_available = True
except ImportError:
    CodeInterpreterTool = None  # type: ignore
    _code_interpreter_available = False
from crewai.tools import BaseTool
from pydantic import Field

from firecrawl_tools import FirecrawlScrapeTool, FirecrawlCrawlTool, FirecrawlSearchTool

try:
    from kie_media import (
        generate_image as _kie_generate_image,
        generate_video as _kie_generate_video,
        generate_promo_video as _kie_generate_promo_video,
        list_models as _kie_list_models,
        check_credits as _kie_check_credits,
        KieMediaError,
    )
    _kie_available = True
except ImportError as _kie_import_err:
    _kie_available = False
    _kie_import_error_msg = str(_kie_import_err)

from health import health_registry

# Core hunter + CRM imports — must not fail silently
try:
    from skills.local_crm.crm_tool import add_lead, log_interaction, update_lead_status, get_daily_scoreboard, update_lead_email, get_lead_by_name, get_uncontacted_leads, mark_outreach_sent
    health_registry.register("CRM", "healthy")
except ImportError as e:
    health_registry.register("CRM", "unhealthy", message=str(e))
    def add_lead(*args, **kwargs): return "ERROR: CRM Skill not ready. Dependency issue: " + str(e)
    def log_interaction(*args, **kwargs): return "ERROR: CRM Skill not ready. Dependency issue: " + str(e)
    def update_lead_status(*args, **kwargs): return "ERROR: CRM Skill not ready."
    def get_daily_scoreboard(*args, **kwargs): return "ERROR: CRM Skill not ready."
    def update_lead_email(*args, **kwargs): return "ERROR: CRM Skill not ready."
    def get_lead_by_name(*args, **kwargs): return "ERROR: CRM Skill not ready."
    def mark_outreach_sent(*args, **kwargs): return {"marked": 0, "leads": [], "error": "CRM_OFFLINE"}

try:
    from skills.serper_skill.hunter_tool import discover_leads, reveal_email_for_lead
    health_registry.register("Prospecting", "healthy")
except ImportError as e:
    health_registry.register("Prospecting", "unhealthy", message=str(e))
    def discover_leads(*args, **kwargs): return "ERROR: Discovery Skill not ready. Dependency issue: " + str(e)
    def reveal_email_for_lead(*args, **kwargs): return "ERROR: Hunter Skill not ready."

try:
    from skills.cli_hub.cli_hub_tool import execute_cli_hub_action
    health_registry.register("CLI Hub", "healthy")
except ImportError as e:
    health_registry.register("CLI Hub", "unhealthy", message=str(e))
    def execute_cli_hub_action(*args, **kwargs): return "ERROR: CLI Hub Skill not ready. Dependency issue: " + str(e)

# GitHub & Notion Skill Imports
try:
    from skills.github_skill.github_tool import create_repo, create_issue, create_file
    health_registry.register("GitHub", "healthy")
except ImportError as e:
    health_registry.register("GitHub", "unhealthy", message=str(e))
    def create_repo(*args, **kwargs): return "ERROR: GitHub Skill not ready. Dependency issue: " + str(e)
    def create_issue(*args, **kwargs): return "ERROR: GitHub Skill not ready."
    def create_file(*args, **kwargs): return "ERROR: GitHub Skill not ready."

try:
    from skills.notion_cli.notion_cli import NotionCLI
    from skills.notion_stylist.notion_stylist import NotionStylist
    from skills.notion_skill.notion_tool import search_databases, create_page, append_block
    health_registry.register("Notion", "healthy")
except ImportError as e:
    health_registry.register("Notion", "unhealthy", message=str(e))
    def search_databases(*args, **kwargs): return "ERROR: Notion Skill not ready: " + str(e)
    def create_page(*args, **kwargs): return "ERROR: Notion Skill not ready."
    def append_block(*args, **kwargs): return "ERROR: Notion Skill not ready."
    NotionStylist = None
    NotionCLI = None

try:
    from skills.mermaid_diagrammer.skill import mermaid_tool
except ImportError as e:
    logger_pre = __import__("logging").getLogger(__name__)
    logger_pre.warning(f"mermaid_diagrammer import failed: {e}")
    mermaid_tool = None

# Hyperframes video production skill
try:
    from skills.hyperframes.skill import get_hyperframes_tool
    hyperframes_tool = get_hyperframes_tool()
except ImportError as e:
    logger_pre = __import__("logging").getLogger(__name__)
    logger_pre.warning(f"hyperframes skill import failed: {e}")
    hyperframes_tool = None

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# SEARCH & RESEARCH TOOLS
# ══════════════════════════════════════════════════════════════

class LaunchVercelAppTool(BaseTool):
    name: str = "launch_vercel_app"
    description: str = "Launches a web application to Vercel and GitHub. Synchronizes with a GitHub repo (bokar83/<app_name>) and triggers a Vercel deployment. Parameters: app_name (string), is_prod (boolean)."

    def _run(self, app_name: str, is_prod: bool = False) -> str:
        # Normalize: strip trailing -app suffix if provided (the script re-adds it).
        clean_name = app_name.replace("-app", "")

        # Validate against a strict allowlist. app_name ends up as the GitHub
        # repo slug, the Vercel project name, and a local directory, so it must
        # only contain characters safe in all three contexts. Previously this
        # value was interpolated into a shell string with shell=True, which
        # allowed arbitrary command execution via crafted app_name input.
        import re
        if not re.match(r"^[a-zA-Z0-9_-]{1,60}$", clean_name):
            return (
                f"Invalid app_name {clean_name!r}. "
                "Use alphanumeric, dash, or underscore only (1-60 chars)."
            )

        base_dir = os.getcwd()
        script_path = os.path.join("skills", "vercel-launch", "scripts", "launch.sh")

        # Argument list, no shell. bash is invoked directly and receives the
        # script path + name + flag as separate argv entries. No interpolation.
        args = ["bash", script_path, clean_name]
        if is_prod:
            args.append("--prod")
        logger.info(f"Executing Vercel Launch: {args} in {base_dir}")

        try:
            result = subprocess.run(
                args,
                shell=False,
                capture_output=True,
                text=True,
                cwd=base_dir,
                timeout=300,
                creationflags=SUBPROCESS_FLAGS,
            )
            if result.returncode != 0:
                error_msg = f"Error launching app:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
                logger.error(f"Vercel Launch Failed: {error_msg}")
                return error_msg
            return result.stdout
        except subprocess.TimeoutExpired:
            logger.error("Vercel Launch timed out after 300s")
            return "Vercel launch timed out (300s). Check Vercel dashboard for deploy status."
        except Exception as e:
            logger.error(f"Vercel Launch Exception: {e}")
            return f"System exception during launch: {str(e)}"

# Instantiate core tools
search_tool = SerperDevTool()
launch_vercel_tool = LaunchVercelAppTool()

# File operations
file_writer = FileWriterTool()
file_reader = FileReadTool()

# Code execution (sandboxed — only available if crewai_tools supports it)
code_interpreter = CodeInterpreterTool() if _code_interpreter_available else None


# ── Notion Styling & Branding Tools ──────────────────────────
class SetNotionStyleTool(BaseTool):
    """Sets the cover and icon for a Notion page."""
    name: str = "set_notion_style"
    description: str = (
        "Set the premium cover image and icon for a Notion page. "
        "Inputs: 'page_id' (string), 'cover' (string URL), 'icon' (emoji or URL)."
    )
    def _run(self, page_id: str, cover: str = None, icon: str = None) -> str:
        if NotionStylist is None:
            return "NotionStylist not available — skill not installed"
        stylist = NotionStylist()
        return stylist.set_premium_style(page_id, cover, icon)

class AddNotionNavTool(BaseTool):
    """Adds a multi-column navigation grid to a Notion page."""
    name: str = "add_notion_nav_grid"
    description: str = (
        "Add a multi-column navigation grid to a Notion page. "
        "Inputs: 'page_id' (string), 'items_json' (JSON list of dicts with 'title' and 'url')."
    )
    def _run(self, page_id: str, items_json: str) -> str:
        if NotionStylist is None:
            return "NotionStylist not available — skill not installed"
        import json
        stylist = NotionStylist()
        try:
            items = json.loads(items_json) if isinstance(items_json, str) else items_json
            return stylist.create_navigation_grid(page_id, items)
        except Exception as e:
            return f"Error: {e}"

set_notion_style_tool = SetNotionStyleTool()
add_notion_nav_tool = AddNotionNavTool()

class ArchitectNotionPageTool(BaseTool):
    """Converts Markdown text to Notion blocks and appends them to a page."""
    name: str = "architect_notion_page"
    description: str = (
        "Architect a full Notion page from Markdown text. "
        "Inputs: 'page_id' (string), 'markdown_text' (string), "
        "optional 'set_style' (bool), 'cover_key' (string), 'icon_emoji' (string)."
    )
    def _run(self, page_id: str, markdown_text: str, set_style: bool = False, cover_key: str = "dark_geometry", icon_emoji: str = "🏗️") -> str:
        if NotionStylist is None:
            return "NotionStylist not available — skill not installed"
        stylist = NotionStylist()
        try:
            result = stylist.architect_page(page_id, markdown_text, set_style=set_style, cover_key=cover_key, icon_emoji=icon_emoji)
            return f"Architected page {page_id} successfully. Added {result.get('appended')} blocks."
        except Exception as e:
            return f"Error architecting page: {e}"

class ApplyNotionTemplateTool(BaseTool):
    """Applies a branded template to a Notion page."""
    name: str = "apply_notion_template"
    description: str = (
        "Apply a branded template to a Notion page. Clears existing content. "
        "Inputs: 'page_id' (string), 'template_name' (string). "
        "Available templates: project_command_center, client_portal, knowledge_hub."
    )
    def _run(self, page_id: str, template_name: str) -> str:
        if NotionStylist is None:
            return "NotionStylist not available — skill not installed"
        stylist = NotionStylist()
        try:
            result = stylist.apply_template(page_id, template_name)
            return f"Successfully applied template '{result.get('template')}' to page {page_id}."
        except Exception as e:
            return f"Error applying template: {e}"

class AddNotionCalloutTool(BaseTool):
    """Adds a callout block to a Notion page."""
    name: str = "add_notion_callout"
    description: str = "Adds a callout block. Inputs: 'page_id', 'text', optional 'emoji' and 'color'."
    def _run(self, page_id: str, text: str, emoji: str = "🔥", color: str = "default") -> str:
        if NotionStylist is None:
            return "NotionStylist not available — skill not installed"
        stylist = NotionStylist()
        return str(stylist.add_callout(page_id, text, emoji, color))

class AddNotionHeadingTool(BaseTool):
    """Adds a heading to a Notion page."""
    name: str = "add_notion_heading"
    description: str = "Adds a heading. Inputs: 'page_id', 'text', optional 'level' (1-3) and 'color'."
    def _run(self, page_id: str, text: str, level: int = 2, color: str = "default") -> str:
        if NotionStylist is None:
            return "NotionStylist not available — skill not installed"
        stylist = NotionStylist()
        return str(stylist.add_heading(page_id, text, level, color))

class AddNotionDividerTool(BaseTool):
    """Adds a divider to a Notion page."""
    name: str = "add_notion_divider"
    description: str = "Adds a full-width divider. Inputs: 'page_id'."
    def _run(self, page_id: str) -> str:
        if NotionStylist is None:
            return "NotionStylist not available — skill not installed"
        stylist = NotionStylist()
        return str(stylist.add_divider(page_id))

class AddNotionToggleTool(BaseTool):
    """Adds a toggle block to a Notion page."""
    name: str = "add_notion_toggle"
    description: str = "Adds a toggle block. Inputs: 'page_id', 'text'."
    def _run(self, page_id: str, text: str) -> str:
        if NotionStylist is None:
            return "NotionStylist not available — skill not installed"
        stylist = NotionStylist()
        return str(stylist.add_toggle(page_id, text))

class CreateNotionColumnLayoutTool(BaseTool):
    """Creates a multi-column layout."""
    name: str = "create_notion_column_layout"
    description: str = "Creates columns. Inputs: 'page_id', 'columns_content' (JSON string — list of lists of Notion block dicts)."
    def _run(self, page_id: str, columns_content: str) -> str:
        if NotionStylist is None:
            return "NotionStylist not available — skill not installed"
        import json
        stylist = NotionStylist()
        try:
            content = json.loads(columns_content) if isinstance(columns_content, str) else columns_content
            stylist.create_column_layout(page_id, content)
            return f"Column layout with {len(content)} columns added to page {page_id}."
        except Exception as e:
            return f"Error: {e}"

class ClearNotionPageTool(BaseTool):
    """Clears all content from a Notion page."""
    name: str = "clear_notion_page"
    description: str = (
        "Delete all child blocks from a Notion page. "
        "Inputs: 'page_id' (string), 'preserve_databases' (bool, default True)."
    )
    def _run(self, page_id: str, preserve_databases: bool = True) -> str:
        if NotionStylist is None:
            return "NotionStylist not available — skill not installed"
        stylist = NotionStylist()
        try:
            stylist.clear_page_content(page_id, preserve_databases=preserve_databases)
            return f"Page {page_id} cleared (preserve_databases={preserve_databases})."
        except Exception as e:
            return f"Error: {e}"

architect_notion_page_tool = ArchitectNotionPageTool()
apply_notion_template_tool = ApplyNotionTemplateTool()
add_notion_callout_tool = AddNotionCalloutTool()
add_notion_heading_tool = AddNotionHeadingTool()
add_notion_divider_tool = AddNotionDividerTool()
add_notion_toggle_tool = AddNotionToggleTool()
create_notion_column_layout_tool = CreateNotionColumnLayoutTool()
clear_notion_page_tool = ClearNotionPageTool()

NOTION_STYLING_TOOLS = [
    set_notion_style_tool,
    add_notion_nav_tool,
    architect_notion_page_tool,
    apply_notion_template_tool,
    add_notion_callout_tool,
    add_notion_heading_tool,
    add_notion_divider_tool,
    add_notion_toggle_tool,
    create_notion_column_layout_tool,
    clear_notion_page_tool,
]


# ── Forge CLI Tools ────────────────────────────────────────
class ForgeLogTool(BaseTool):
    """Logs an agent action to The Forge 2.0 Activity Log."""
    name: str = "forge_log"
    description: str = (
        "Log an agent action to The Forge 2.0 dashboard. "
        "Input: JSON with 'message', optional 'agent' and 'status'."
    )
    def _run(self, input_data: str) -> str:
        try:
            from skills.forge_cli.databases import ForgeDB
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            db = ForgeDB()
            result = db.log_action(
                data.get("message", "Agent action"),
                agent=data.get("agent", "System"),
                status=data.get("status", "Success"),
            )
            return f"Logged to Forge: {result.get('url', result.get('id'))}"
        except Exception as e:
            return f"Forge log failed: {e}"


class ForgePipelineTool(BaseTool):
    """Adds a lead to The Forge 2.0 Consulting Pipeline."""
    name: str = "forge_pipeline_add"
    description: str = (
        "Add a lead to the consulting pipeline. "
        "Input: JSON with 'company', optional 'contact', 'email', 'value', 'status', 'source'."
    )
    def _run(self, input_data: str) -> str:
        try:
            from skills.forge_cli.databases import ForgeDB
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            db = ForgeDB()
            result = db.add_pipeline_lead(
                data["company"],
                contact=data.get("contact", ""),
                email=data.get("email", ""),
                value=data.get("value", 0),
                status=data.get("status", "Discovery"),
                source=data.get("source", "Hunter Agent"),
            )
            return f"Lead added: {result.get('url', result.get('id'))}"
        except Exception as e:
            return f"Pipeline add failed: {e}"


class ForgeContentTool(BaseTool):
    """Adds a content draft to The Forge 2.0 Content Board."""
    name: str = "forge_content_draft"
    description: str = (
        "Add a content draft to the Content Board. "
        "Input: JSON with 'title', 'content', optional 'platforms' (list), 'topics' (list), 'type'."
    )
    def _run(self, input_data: str) -> str:
        try:
            from skills.forge_cli.databases import ForgeDB
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            db = ForgeDB()
            result = db.add_content_idea(
                data["title"],
                platforms=data.get("platforms", ["LinkedIn"]),
                topics=data.get("topics", []),
                content_type=data.get("type", "Post"),
                content=data.get("content", ""),
                agent=data.get("agent", "Social Crew"),
            )
            if data.get("content"):
                db.update_content_status(result["id"], status="Draft")
            return f"Content added: {result.get('url', result.get('id'))}"
        except Exception as e:
            return f"Content add failed: {e}"


forge_log_tool = ForgeLogTool()
forge_pipeline_tool = ForgePipelineTool()
forge_content_tool = ForgeContentTool()

FORGE_TOOLS = [forge_log_tool, forge_pipeline_tool, forge_content_tool]


class InboundLeadTool(BaseTool):
    """Runs the inbound lead routine end-to-end for a webhook payload.

    Triggered by n8n on Calendly/Formspree events. Handles idempotency,
    research, voice drafting, Notion logging, and Gmail draft creation.
    Returns the serialized InboundRoutineResult as a JSON string.
    """
    name: str = "inbound_lead_run"
    description: str = (
        "Run the inbound lead routine on a webhook payload. "
        "Input: JSON with 'name', 'email', 'booking_id', 'source' "
        "('calendly'|'formspree'), and optionally 'company', 'meeting_time' "
        "(ISO8601), 'raw_company_url', 'notion_row_id'. "
        "Returns JSON with status (enriched|rebook_update|partial|failed), "
        "brief, email draft, notion + gmail pointers."
    )

    def _run(self, input_data: str) -> str:
        try:
            from skills.inbound_lead.runner import run_inbound_lead
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            result = run_inbound_lead(data)
            return result.model_dump_json()
        except Exception as e:
            return json.dumps({"status": "failed", "error": f"Tool dispatch failed: {e}"})


inbound_lead_tool = InboundLeadTool()

INBOUND_TOOLS = [inbound_lead_tool]


# ══════════════════════════════════════════════════════════════
# GOOGLE WORKSPACE TOOLS (Calendar + Gmail)
# Supports multiple accounts via separate credentials files:
#   bokar83@gmail.com                    → GOOGLE_OAUTH_CREDENTIALS_JSON (default)
#   boubacar@catalystworks.consulting    → GOOGLE_OAUTH_CREDENTIALS_JSON_CW (outreach account)
#   catalystworks.ai@gmail.com           → GOOGLE_OAUTH_CREDENTIALS_JSON_CW (legacy alias)
# ══════════════════════════════════════════════════════════════

# Dynamic credentials pathing for cross-platform support
def _get_default_creds_path(filename: str) -> str:
    """Resolve credentials path based on environment."""
    # Try /app/secrets first (Docker/Production)
    docker_path = os.path.join("/", "app", "secrets", filename)
    if os.path.exists(docker_path):
        return docker_path
    
    # Fallback to local secrets directory in the workspace
    local_path = os.path.abspath(os.path.join(os.getcwd(), "secrets", filename))
    return local_path

_GWS_CREDS_MAP = {
    "bokar83@gmail.com": os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON", _get_default_creds_path("gws-oauth-credentials.json")),
    "boubacar@catalystworks.consulting": os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON_CW", _get_default_creds_path("gws-oauth-credentials-cw.json")),
    "catalystworks.ai@gmail.com": os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON_CW", _get_default_creds_path("gws-oauth-credentials-cw.json")),
}
_GWS_DEFAULT_ACCOUNT = "bokar83@gmail.com"


def _gws_creds_path(account: str | None = None) -> str:
    """Return the credentials file path for the given account (default: bokar83)."""
    return _GWS_CREDS_MAP.get(account or _GWS_DEFAULT_ACCOUNT, _GWS_CREDS_MAP[_GWS_DEFAULT_ACCOUNT])


def _gws_request(method: str, url: str, account: str | None = None, **kwargs) -> dict:
    """Make an authenticated Google API request using the stored OAuth token."""
    import json as _json
    creds_path = _gws_creds_path(account)
    try:
        with open(creds_path) as f:
            creds = _json.load(f)
    except Exception as e:
        raise RuntimeError(f"Cannot load GWS credentials from {creds_path}: {e}")

    token_resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"],
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    token_resp.raise_for_status()
    access_token = token_resp.json()["access_token"]

    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {access_token}"
    resp = getattr(httpx, method)(url, headers=headers, timeout=30, **kwargs)
    resp.raise_for_status()
    return resp.json() if resp.content else {}


class GWSCalendarListTool(BaseTool):
    name: str = "calendar_list_events"
    description: str = (
        "List events from Google Calendar for a given date range. "
        "Input: JSON with 'date' (YYYY-MM-DD) for a single day, or 'start' and 'end' (YYYY-MM-DD). "
        "Optional: 'calendar_id' (default: primary)."
    )
    def _run(self, input_data: str) -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            cal_id = data.get("calendar_id", "primary")
            if "date" in data:
                from datetime import date, timedelta
                d = data["date"]
                time_min = f"{d}T00:00:00-06:00"
                time_max = f"{d}T23:59:59-06:00"
            else:
                time_min = f"{data['start']}T00:00:00-06:00"
                time_max = f"{data['end']}T23:59:59-06:00"
            result = _gws_request(
                "get",
                f"https://www.googleapis.com/calendar/v3/calendars/{cal_id}/events",
                params={"timeMin": time_min, "timeMax": time_max, "singleEvents": "true", "orderBy": "startTime"},
            )
            events = result.get("items", [])
            if not events:
                return "No events found."
            lines = []
            for e in events:
                start = e.get("start", {}).get("dateTime", e.get("start", {}).get("date", ""))
                lines.append(f"- {e.get('summary','Untitled')} @ {start}")
            return "\n".join(lines)
        except Exception as e:
            return f"calendar_list_events failed: {e}"


class GWSCalendarCreateTool(BaseTool):
    name: str = "calendar_create_event"
    description: str = (
        "Create an event in Google Calendar. "
        "Input: JSON with 'summary', 'start' (ISO datetime), 'end' (ISO datetime). "
        "Optional: 'description', 'color_id' (1-11), 'calendar_id' (default: primary)."
    )
    def _run(self, input_data: str) -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            cal_id = data.get("calendar_id", "primary")
            body = {
                "summary": data["summary"],
                "start": {"dateTime": data["start"], "timeZone": "America/Denver"},
                "end": {"dateTime": data["end"], "timeZone": "America/Denver"},
            }
            if "description" in data:
                body["description"] = data["description"]
            if "color_id" in data:
                body["colorId"] = str(data["color_id"])
            result = _gws_request(
                "post",
                f"https://www.googleapis.com/calendar/v3/calendars/{cal_id}/events",
                json=body,
            )
            return f"Event created: {result.get('summary')} (id: {result.get('id')})"
        except Exception as e:
            return f"calendar_create_event failed: {e}"


class GWSCalendarDeleteTool(BaseTool):
    name: str = "calendar_delete_event"
    description: str = (
        "Delete an event from Google Calendar by event ID. "
        "Input: JSON with 'event_id'. Optional: 'calendar_id' (default: primary)."
    )
    def _run(self, input_data: str) -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            cal_id = data.get("calendar_id", "primary")
            httpx.delete(
                f"https://www.googleapis.com/calendar/v3/calendars/{cal_id}/events/{data['event_id']}",
                headers={"Authorization": f"Bearer {_get_gws_token(data.get('account'))}"},
                timeout=15,
            )
            return f"Event {data['event_id']} deleted."
        except Exception as e:
            return f"calendar_delete_event failed: {e}"


def _get_gws_token(account: str | None = None) -> str:
    """Helper to get a fresh access token for the given account (default: bokar83)."""
    creds_path = _gws_creds_path(account)
    with open(creds_path) as f:
        creds = json.load(f)
    token_resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"],
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    token_resp.raise_for_status()
    return token_resp.json()["access_token"]


class GWSGmailCreateDraftTool(BaseTool):
    name: str = "gmail_create_draft"
    description: str = (
        "Create a Gmail draft. "
        "Input: JSON with 'to' (email), 'subject', 'body' (plain text). "
        "Optional: 'cc', 'account' (email address to send from — defaults to bokar83@gmail.com; "
        "use 'boubacar@catalystworks.consulting' for Catalyst Works outreach)."
    )
    def _run(self, input_data: str) -> str:
        try:
            import base64
            from email.mime.text import MIMEText
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            account = data.get("account")
            msg = MIMEText(data["body"])
            msg["to"] = data["to"]
            msg["subject"] = data["subject"]
            if "cc" in data:
                msg["cc"] = data["cc"]
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            result = _gws_request(
                "post",
                "https://gmail.googleapis.com/gmail/v1/users/me/drafts",
                account=account,
                json={"message": {"raw": raw}},
            )
            draft_id = result.get("id", "")
            from_label = account or _GWS_DEFAULT_ACCOUNT
            return f"Draft created (id: {draft_id}): '{data['subject']}' to {data['to']} from {from_label}"
        except Exception as e:
            return f"gmail_create_draft failed: {e}"


class GWSGmailSearchTool(BaseTool):
    name: str = "gmail_search"
    description: str = (
        "Search Gmail messages. Returns sender, subject, and snippet for each result. "
        "Input: JSON with 'query' (Gmail search syntax, e.g. 'from:someone subject:hello'). "
        "Optional: 'max_results' (default 10), 'account' (email address to search — defaults to bokar83@gmail.com)."
    )
    def _run(self, input_data: str) -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            account = data.get("account")
            max_results = data.get("max_results", 10)
            result = _gws_request(
                "get",
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                account=account,
                params={"q": data["query"], "maxResults": max_results},
            )
            messages = result.get("messages", [])
            if not messages:
                return "No messages found."
            lines = [f"Found {len(messages)} message(s):\n"]
            for msg in messages:
                msg_id = msg["id"]
                try:
                    detail = _gws_request(
                        "get",
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
                        account=account,
                        params={"format": "metadata", "metadataHeaders": ["From", "Subject", "Date"]},
                    )
                    headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
                    sender = headers.get("From", "Unknown sender")
                    subject = headers.get("Subject", "(no subject)")
                    date = headers.get("Date", "")
                    snippet = detail.get("snippet", "")[:120]
                    lines.append(f"- From: {sender}\n  Subject: {subject}\n  Date: {date}\n  Preview: {snippet}")
                except Exception:
                    lines.append(f"- ID: {msg_id} (could not fetch details)")
            return "\n".join(lines)
        except Exception as e:
            return f"gmail_search failed: {e}"


class GWSGmailSendHTMLMeTool(BaseTool):
    name: str = "gmail_send_html_me"
    description: str = (
        "Directly send a beautifully formatted HTML email to Boubacar Barry "
        "(to BOTH boubacar@catalystworks.consulting and bokar83@gmail.com) without creating a draft. "
        "Input: JSON with 'subject' (str), 'body' (plain text or markdown representation of the content), "
        "and 'html_body' (HTML representation with proper styling, headers, and paragraphs). "
        "Optional: 'account' (email address to send from — defaults to bokar83@gmail.com; "
        "can use 'boubacar@catalystworks.consulting' for business-toned notifications)."
    )
    def _run(self, input_data: str) -> str:
        try:
            import base64
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            account = data.get("account")
            
            subject = data.get("subject", "agentsHQ Notification")
            body_text = data.get("body", "Please view this email in an HTML-compatible client.")
            html_content = data.get("html_body") or data.get("body") or ""
            
            # If html_content does not look like raw HTML, wrap it in a beautiful, premium design template
            is_raw_html = (
                html_content.strip().startswith("<")
                and ("<html>" in html_content.lower() or "<body" in html_content.lower() or "<div" in html_content.lower() or "<p" in html_content.lower())
            )
            
            if not is_raw_html:
                # Convert basic linebreaks to HTML
                formatted_html = html_content.replace("\r\n", "\n").replace("\n", "<br>")
                html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        line-height: 1.6;
        color: #334155;
        background-color: #f8fafc;
        margin: 0;
        padding: 40px 20px;
    }}
    .container {{
        max-width: 600px;
        margin: 0 auto;
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        overflow: hidden;
    }}
    .header {{
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 32px 24px;
        text-align: left;
        border-bottom: 1px solid #e2e8f0;
    }}
    .header h1 {{
        color: #ffffff;
        font-size: 20px;
        font-weight: 600;
        margin: 0;
        letter-spacing: -0.025em;
    }}
    .content {{
        padding: 32px 24px;
        font-size: 15px;
    }}
    .content p {{
        margin-top: 0;
        margin-bottom: 16px;
    }}
    .footer {{
        background-color: #f1f5f9;
        padding: 20px 24px;
        font-size: 12px;
        color: #64748b;
        border-top: 1px solid #e2e8f0;
        text-align: center;
    }}
</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>agentsHQ Notification</h1>
        </div>
        <div class="content">
            <p>{formatted_html}</p>
        </div>
        <div class="footer">
            Sent automatically by agentsHQ to Boubacar Barry.<br>
            © 2026 Catalyst Works Consulting.
        </div>
    </div>
</body>
</html>"""

            recipients = ["boubacar@catalystworks.consulting", "bokar83@gmail.com"]
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["To"] = ", ".join(recipients)
            if account:
                msg["From"] = account
            
            msg.attach(MIMEText(body_text, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            
            result = _gws_request(
                "post",
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                account=account,
                json={"raw": raw},
            )
            msg_id = result.get("id", "")
            from_label = account or _GWS_DEFAULT_ACCOUNT
            return f"HTML Email sent directly to {', '.join(recipients)} (id: {msg_id}) from {from_label} with subject '{subject}'"
        except Exception as e:
            return f"gmail_send_html_me failed: {e}"


gws_calendar_list_tool = GWSCalendarListTool()
gws_calendar_create_tool = GWSCalendarCreateTool()
gws_calendar_delete_tool = GWSCalendarDeleteTool()
gws_gmail_draft_tool = GWSGmailCreateDraftTool()
gws_gmail_search_tool = GWSGmailSearchTool()
gws_gmail_send_html_me_tool = GWSGmailSendHTMLMeTool()

class GWSDriveSearchTool(BaseTool):
    """Search for files in the agentsHQ Google Drive folder."""
    name: str = "search_drive_files"
    description: str = (
        "Search for files in the agentsHQ Google Drive. "
        "Input: JSON with 'query' (filename or keyword to search for) "
        "and optional 'folder' (deliverables, leads, research, social, code, websites). "
        "Returns a list of matching files with names and shareable links."
    )

    def _run(self, input_data: str = "{}") -> str:
        try:
            data = {}
            if input_data:
                try:
                    data = json.loads(input_data) if isinstance(input_data, str) else input_data
                except Exception:
                    pass
            query_str = data.get("query", "")

            folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
            oauth_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON", "")
            if not folder_id or not oauth_path:
                return "Drive not configured — GOOGLE_DRIVE_FOLDER_ID or GOOGLE_OAUTH_CREDENTIALS_JSON missing."

            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            import json as _json
            with open(oauth_path) as f:
                info = _json.load(f)
            creds = Credentials(
                token=None,
                refresh_token=info["refresh_token"],
                client_id=info["client_id"],
                client_secret=info["client_secret"],
                token_uri="https://oauth2.googleapis.com/token",
            )
            service = build("drive", "v3", credentials=creds)

            q_parts = [f"'{folder_id}' in parents or parents in (select id from files where '{folder_id}' in parents)"]
            if query_str:
                q_parts = [f"name contains '{query_str}' and trashed=false"]
            q = " and ".join(q_parts)
            results = service.files().list(
                q=q,
                fields="files(id,name,webViewLink,mimeType,createdTime)",
                orderBy="createdTime desc",
                pageSize=10,
            ).execute()
            files = results.get("files", [])
            if not files:
                return f"No files found matching '{query_str}' in Drive."
            lines = [f"Drive search results for '{query_str}':\n"]
            for f_item in files:
                lines.append(f"- {f_item['name']}")
                lines.append(f"  {f_item.get('webViewLink', 'no link')}")
            return "\n".join(lines)
        except Exception as e:
            return f"Drive search failed: {e}"


class GWSDriveListRecentTool(BaseTool):
    """List the most recent files saved to Google Drive by agentsHQ."""
    name: str = "list_recent_drive_files"
    description: str = (
        "List the most recent files saved to the agentsHQ Google Drive folder. "
        "Input: optional JSON with 'limit' (default 10) and 'folder' "
        "(deliverables, leads, research, social, code, websites — omit for all). "
        "Returns file names and shareable links."
    )

    def _run(self, input_data: str = "{}") -> str:
        try:
            data = {}
            if input_data:
                try:
                    data = json.loads(input_data) if isinstance(input_data, str) else input_data
                except Exception:
                    pass
            limit = int(data.get("limit", 10))
            folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
            oauth_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON", "")
            if not folder_id or not oauth_path:
                return "Drive not configured."

            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            import json as _json
            with open(oauth_path) as f:
                info = _json.load(f)
            creds = Credentials(
                token=None,
                refresh_token=info["refresh_token"],
                client_id=info["client_id"],
                client_secret=info["client_secret"],
                token_uri="https://oauth2.googleapis.com/token",
            )
            service = build("drive", "v3", credentials=creds)
            results = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="files(id,name,webViewLink,mimeType,createdTime)",
                orderBy="createdTime desc",
                pageSize=limit,
            ).execute()
            files = results.get("files", [])
            if not files:
                return "No files found in the agentsHQ Drive folder."
            lines = [f"Recent Drive files ({len(files)}):\n"]
            for f_item in files:
                lines.append(f"- {f_item['name']}")
                lines.append(f"  {f_item.get('webViewLink', 'no link')}")
            return "\n".join(lines)
        except Exception as e:
            return f"Drive list failed: {e}"


class GWSDriveCreateFileTool(BaseTool):
    """Create a new Google Doc in a Drive folder and return its webViewLink."""
    name: str = "create_drive_doc"
    description: str = (
        "Create a new Google Doc in a specified Google Drive folder. "
        "Input: JSON with 'name' (filename) and optional 'folder_id' (Drive folder ID, "
        "defaults to CONTENT_DRIVE_FOLDER_ID env var). "
        "Returns the file ID and webViewLink on success."
    )

    def _run(self, input_data: str = "{}") -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            name = data.get("name", "Untitled")
            folder_id = data.get("folder_id") or os.environ.get(
                "CONTENT_DRIVE_FOLDER_ID", "1lS7VT4aMfo7eQc-zVdOfFfvWvevytwNs"
            )
            result = _gws_request(
                "post",
                "https://www.googleapis.com/drive/v3/files?fields=id,webViewLink",
                json={
                    "name": name,
                    "mimeType": "application/vnd.google-apps.document",
                    "parents": [folder_id],
                },
            )
            file_id = result.get("id", "")
            web_link = result.get(
                "webViewLink", f"https://docs.google.com/document/d/{file_id}/edit"
            )
            return json.dumps({"id": file_id, "webViewLink": web_link})
        except Exception as e:
            return f"create_drive_doc failed: {e}"


gws_drive_search_tool = GWSDriveSearchTool()
gws_drive_list_tool = GWSDriveListRecentTool()
gws_drive_create_tool = GWSDriveCreateFileTool()

GWS_TOOLS = [
    gws_calendar_list_tool,
    gws_calendar_create_tool,
    gws_calendar_delete_tool,
    gws_gmail_draft_tool,
    gws_gmail_search_tool,
    gws_gmail_send_html_me_tool,
    gws_drive_search_tool,
    gws_drive_list_tool,
    gws_drive_create_tool,
]


# ══════════════════════════════════════════════════════════════
# CUSTOM TOOLS
# ══════════════════════════════════════════════════════════════

class SaveOutputTool(BaseTool):
    """
    Saves agent output to the /outputs directory with metadata.
    All agent deliverables should be saved via this tool.
    """
    name: str = "save_output"
    description: str = (
        "Save a deliverable to the outputs directory. "
        "Use this to save websites, reports, code, and any other "
        "final deliverables produced for the user. "
        "Input: JSON with 'filename', 'content', and optional 'task_type'."
    )

    def _run(self, input_data: str) -> str:
        try:
            if isinstance(input_data, str):
                data = json.loads(input_data)
            else:
                data = input_data
                
            filename = data.get("filename", f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            content = data.get("content", "")
            
            output_dir = "/app/outputs"
            os.makedirs(output_dir, exist_ok=True)
            
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"Output saved: {filepath}")
            return f"File saved successfully: {filename}"
            
        except Exception as e:
            logger.error(f"SaveOutputTool failed: {e}")
            return f"Error saving output: {e}"

class QueryMemoryTool(BaseTool):
    """
    Queries Qdrant vector memory for relevant past tasks and outputs.
    Use this at the start of any task to surface related prior work.
    """
    name: str = "query_memory"
    description: str = (
        "Search the agent memory for relevant past tasks, outputs, "
        "and learnings. Use this before starting any task to avoid "
        "reinventing work that's already been done. "
        "Input: a natural language search query string."
    )

    def _run(self, query: str) -> str:
        try:
            from memory import query_memory
            results = query_memory(query, top_k=3)
            if not results:
                return "No relevant memory found for this query."

            output = "Relevant past work found:\n\n"
            for i, r in enumerate(results, 1):
                output += f"{i}. {r.get('summary', 'No summary')}\n"
                output += f"   Task type: {r.get('task_type', 'unknown')}\n"
                output += f"   Date: {r.get('date', 'unknown')}\n\n"
            return output

        except Exception as e:
            logger.warning(f"Memory query failed (non-fatal): {e}")
            return "Memory unavailable — proceeding without past context."


class SaveLearningTool(BaseTool):
    """
    Saves a lesson or pattern to the agent learning memory.
    Use this when you identify a reusable approach, pattern, or preference
    that should be remembered for future runs of this task type.
    """
    name: str = "save_learning"
    description: str = (
        "Save a lesson or reusable pattern to long-term agent memory. "
        "Use when you identify an approach that worked well and should be "
        "remembered for future tasks of this type. "
        "Input: JSON string with fields: task_type (str), lesson (str), "
        "learning_type (str, one of: pattern, preference, lesson)."
    )

    def _run(self, input_str: str) -> str:
        try:
            import json as _json
            data = _json.loads(input_str) if isinstance(input_str, str) else input_str
            task_type = data.get("task_type", "unknown")
            lesson = data.get("lesson", "")
            learning_type = data.get("learning_type", "pattern")
            if not lesson:
                return "No lesson text provided — nothing saved."
            from memory import extract_and_save_learnings
            ok = extract_and_save_learnings(
                task_request=lesson,
                task_type=task_type,
                result_summary=lesson,
                learning_type=learning_type,
            )
            return "Lesson saved to memory." if ok else "Learning save skipped (MEMORY_LEARNING_ENABLED not set or extraction failed)."
        except Exception as e:
            logger.warning(f"SaveLearningTool failed: {e}")
            return f"Save failed: {e}"


class VoicePolisherTool(BaseTool):
    """
    Programmatically removes AI markers and polishes the voice.
    """
    name: str = "voice_polisher"
    description: str = (
        "Strip common AI markers (em-dashes, filler phrases) "
        "and polish the text to sound more human. "
        "Input: the text string to polish."
    )

    def _run(self, text: str) -> str:
        try:
            # Add root to path if needed to find skills
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if root_dir not in sys.path:
                sys.path.append(root_dir)
            
            from skills.boub_voice_mastery.voice_polisher import polish_voice
            return polish_voice(text)
        except Exception as e:
            logger.error(f"VoicePolisherTool failed: {e}")
            return text


class ValidateOutputTool(BaseTool):
    """LLM-side validation for structured outputs and voice guardrails."""
    name: str = "validate_output"
    description: str = (
        "LLM check of task output for JSON schema compliance, tone drift, completeness, and no em-dashes. "
        "Input: output text, optional schema text, optional extra rules. Returns PASS or FAIL: <reason>."
    )

    def _run(self, output: str, schema: str = "", rules: str = "") -> str:
        try:
            from llm_helpers import call_llm

            prompt = (
                "Validate the output against the required rules.\n"
                "Return exactly one line.\n"
                "If the output passes, return: PASS\n"
                "If it fails, return: FAIL: <brief reason>\n\n"
                "Validation rules:\n"
                "1. If a schema is provided, the output must comply with it.\n"
                "2. Output must be complete and usable, not partial.\n"
                "3. Tone must not drift from the requested constraints.\n"
                "4. Output must not contain em-dashes.\n"
                "5. Keep the verdict strict and concise.\n\n"
                f"Schema:\n{schema or '[none provided]'}\n\n"
                f"Additional rules:\n{rules or '[none provided]'}\n\n"
                f"Output to validate:\n{output}"
            )
            resp = call_llm(
                [{"role": "user", "content": prompt}],
                model="anthropic/claude-haiku-4.5",
                temperature=0.0,
                max_tokens=120,
            )
            verdict = (resp.choices[0].message.content or "").strip()
            if verdict == "PASS" or verdict.startswith("FAIL:"):
                return verdict
            return f"FAIL: Invalid validator response: {verdict[:120]}"
        except Exception as e:
            logger.error(f"ValidateOutputTool failed: {e}")
            return f"FAIL: validator error: {e}"


class EscalateTool(BaseTool):
    """
    Sends an escalation message to Boubacar when an agent is blocked,
    uncertain, or encounters an unknown task type.
    Triggers an n8n webhook that delivers a Telegram message.
    """
    name: str = "escalate_to_owner"
    description: str = (
        "Send an escalation message to Boubacar when you are blocked, "
        "uncertain, or encounter a request you cannot handle. "
        "NEVER hallucinate — escalate instead. "
        "Input: JSON with 'reason', 'original_request', and 'recommendation'."
    )

    def _run(self, input_data: str) -> str:
        try:
            if isinstance(input_data, str):
                data = json.loads(input_data)
            else:
                data = input_data
                
            reason = data.get("reason", "Unknown reason")
            original = data.get("original_request", "")
            recommendation = data.get("recommendation", "")
            
            message = (
                f"🚨 *Agent Escalation*\n\n"
                f"*Reason:* {reason}\n\n"
                f"*Original request:* {original}\n\n"
                f"*My recommendation:* {recommendation}"
            )
            
            # Send via n8n webhook if configured
            webhook_url = os.environ.get("N8N_ESCALATION_WEBHOOK")
            if webhook_url:
                httpx.post(webhook_url, json={"message": message}, timeout=10)
                return f"Escalation sent to owner: {reason}"
            else:
                logger.warning(f"Escalation (no webhook configured): {message}")
                return f"Escalation logged (webhook not configured): {reason}"
                
        except Exception as e:
            logger.error(f"EscalateTool failed: {e}")
            return f"Escalation failed: {str(e)}"


class ProposeNewAgentTool(BaseTool):
    """
    When a task type is unknown, this tool drafts a new agent spec
    and sends it to Boubacar for approval before creating it.
    This is how the system teaches itself new skills.
    """
    name: str = "propose_new_agent"
    description: str = (
        "When you encounter a task type that no existing agent can handle, "
        "use this tool to draft a specification for a new agent and send "
        "it to Boubacar for approval. "
        "Input: JSON with 'agent_name', 'role', 'goal', 'backstory', "
        "'tools_needed', 'task_type_key', 'trigger_keywords'."
    )

    def _run(self, input_data: str) -> str:
        try:
            if isinstance(input_data, str):
                data = json.loads(input_data)
            else:
                data = input_data
            
            agent_name = data.get("agent_name", "unnamed_agent")
            
            proposal = (
                f"🤖 *New Agent Proposal*\n\n"
                f"*Name:* {agent_name}\n"
                f"*Role:* {data.get('role', '')}\n"
                f"*Goal:* {data.get('goal', '')}\n"
                f"*Task type key:* {data.get('task_type_key', '')}\n"
                f"*Triggers:* {', '.join(data.get('trigger_keywords', []))}\n"
                f"*Tools needed:* {', '.join(data.get('tools_needed', []))}\n\n"
                f"Reply YES to approve and I will create this agent."
            )
            
            # Save proposal to disk for review
            proposal_dir = "/app/outputs/proposals"
            os.makedirs(proposal_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f"{proposal_dir}/agent_proposal_{agent_name}_{timestamp}.json", "w") as f:
                json.dump(data, f, indent=2)
            
            # Send to owner via n8n webhook
            webhook_url = os.environ.get("N8N_ESCALATION_WEBHOOK")
            if webhook_url:
                httpx.post(webhook_url, json={"message": proposal}, timeout=10)
            
            logger.info(f"New agent proposal submitted: {agent_name}")
            return f"Agent proposal submitted for {agent_name}. Awaiting Boubacar's approval."
            
        except Exception as e:
            logger.error(f"ProposeNewAgentTool failed: {e}")
            return f"Proposal failed: {str(e)}"


class CLIHubSearchTool(BaseTool):
    """
    Searches the HKUDS CLI-Anything Hub for pre-built agent-native CLIs.
    """
    name: str = "search_cli_hub"
    description: str = (
        "Search the CLI-Anything community hub for stateful CLI wrappers. "
        "Use this before building a new tool from scratch. "
        "Input: JSON with 'action' (list/search/install) and 'query' or 'name'."
    )

    def _run(self, input_data: str) -> str:
        try:
            import asyncio
            if isinstance(input_data, str):
                data = json.loads(input_data)
            else:
                data = input_data
            
            action = data.get("action", "search")
            query = data.get("query", data.get("name", ""))

            # Run the async function safely from a sync context.
            # If an event loop is already running (FastAPI background task),
            # run_until_complete() would deadlock — use a fresh thread instead.
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, execute_cli_hub_action(action, query=query, name=query))
                result = future.result(timeout=30)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"CLIHubSearchTool failed: {e}")
            return f"Error searching Hub: {e}"


# ══════════════════════════════════════════════════════════════
# FIRECRAWL TOOLS
# Imported from firecrawl_tools.py (shared module).
# FirecrawlScrapeTool, FirecrawlCrawlTool, FirecrawlSearchTool
# are available via the import at the top of this file.
# ══════════════════════════════════════════════════════════════


class UtahProspectingTool(BaseTool):
    """
    Unified lead discovery: Serper LinkedIn dork → Serper local business →
    Firecrawl website scrape → Hunter.io email → Apollo fallback.
    """
    name: str = "discover_leads"
    description: str = (
        "Discover Utah SMB leads (owners, founders, CEOs) across Legal, "
        "Accounting, Marketing Agency, HVAC, Plumbing, and Roofing industries. "
        "Optional input: a query string to override the default ICP "
        "(e.g. 'HVAC Park City'). Returns up to 20 leads with name, company, "
        "title, phone, email, linkedin_url, and source."
    )
    def _run(self, query: str = "") -> str:
        results = discover_leads(query)
        return json.dumps(results, indent=2)


class ApolloLeadHarvestTool(BaseTool):
    """Apollo-based primary lead harvest for Growth Hunter."""
    name: str = "harvest_apollo_leads"
    description: str = (
        "Primary Apollo paid-plan lead discovery. "
        "Inputs: target int, pipeline string ('sw', 'cw', or 'studio'). "
        "Runs the matching Signal Works topup harvester and returns a compact summary."
    )

    def _run(self, target: int = 20, pipeline: str = "sw") -> str:
        try:
            target = int(target or 20)
        except (TypeError, ValueError):
            target = 20

        key = (pipeline or "sw").strip().lower()
        harvesters = {
            "sw": ("Signal Works", "signal_works.topup_leads", "topup"),
            "cw": ("Catalyst Works", "signal_works.topup_cw_leads", "topup_cw_leads"),
            "studio": ("Studio", "signal_works.topup_studio_leads", "topup_studio_leads"),
        }
        if key not in harvesters:
            return f"Error: unknown Apollo pipeline '{pipeline}'. Use 'sw', 'cw', or 'studio'."

        label, module_name, function_name = harvesters[key]
        try:
            module = __import__(module_name, fromlist=[function_name])
            topup_fn = getattr(module, function_name)
            count = topup_fn(minimum=target)
            return json.dumps(
                {
                    "tool": "harvest_apollo_leads",
                    "pipeline": key,
                    "pipeline_label": label,
                    "target": target,
                    "count": count,
                    "summary": [
                        f"{label} Apollo harvest returned {count} email lead(s) for target {target}."
                    ],
                },
                indent=2,
            )
        except Exception as e:
            return f"Error running Apollo harvest for pipeline '{key}': {e}"


class CRMRevealEmailTool(BaseTool):
    """On-demand email reveal for a named lead via Hunter.io then Apollo."""
    name: str = "reveal_email"
    description: str = (
        "Reveal the email address for a specific named lead. "
        "Tries Hunter.io first (free), then Apollo (1 credit). "
        "Input: JSON with 'name' (required), 'company' (optional), "
        "'linkedin_url' (optional). "
        "After finding the email, update the CRM with add_lead or log_interaction."
    )
    def _run(self, input_data: str) -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            name = data.get("name", "")
            company = data.get("company", "")
            linkedin_url = data.get("linkedin_url", "")
            if not name:
                return "Error: 'name' is required."
            email = reveal_email_for_lead(name, company, linkedin_url)
            if email:
                # Update CRM if we can look up the lead
                lead = get_lead_by_name(name, company)
                if lead.get("id"):
                    update_lead_email(lead["id"], email)
                    log_interaction(lead["id"], "email_revealed", f"Email revealed: {email}")
                return f"Email found for {name}: {email}"
            return f"No email found for {name}."
        except Exception as e:
            return f"Error: {e}"


class CRMAddLeadTool(BaseTool):
    """Adds a newly discovered lead to Supabase."""
    name: str = "add_lead"
    description: str = (
        "Add a discovered lead to the Supabase CRM. "
        "Input: JSON dict with name, company, title, location, linkedin_url, industry, source. "
        "Also logs a discovery interaction in lead_interactions automatically."
    )
    def _run(self, input_data: str) -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            lead_id = add_lead(data)
            return f"Lead added to CRM. ID: {lead_id}"
        except Exception as e:
            return f"Error: {e}"


class CRMLogInteractionTool(BaseTool):
    """Logs an outreach attempt or discovery note for a lead."""
    name: str = "log_interaction"
    description: str = (
        "Log an outreach attempt or note for a specific lead. "
        "Input: JSON dict with lead_id, interaction_type (outreach/note), and content."
    )
    def _run(self, input_data: str) -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            success = log_interaction(data.get("lead_id"), data.get("interaction_type"), data.get("content"))
            return "Interaction logged." if success else "Failed to log."
        except Exception as e:
            return f"Error: {e}"


class CRMGetUncontactedTool(BaseTool):
    """Returns all CRM leads who have never been contacted."""
    name: str = "get_uncontacted_leads"
    description: str = (
        "Get all leads in the Supabase CRM who have never been contacted "
        "(status = 'new' and last_contacted_at is null). "
        "Returns a JSON list with id, name, company, title, email, phone, linkedin_url, industry. "
        "Use this at the start of any outreach run to know who needs to be reached."
    )
    def _run(self, _=None) -> str:
        leads = get_uncontacted_leads()
        return json.dumps(leads, indent=2, default=str)


class DailyScoreboardTool(BaseTool):
    """Reports daily sales velocity (leGriot's dashboard)."""
    name: str = "get_daily_scoreboard"
    description: str = "Get today's stats: leads found, messages sent, replies, booked calls, and revenue."
    def _run(self, _=None) -> str:
        stats = get_daily_scoreboard()
        return (
            f"📊 *DAILY REVENUE SCOREBOARD*\n"
            f"- Leads found: {stats.get('leads_found', 0)} / 5\n"
            f"- Messages sent: {stats.get('messages_sent', 0)} / 5\n"
            f"- Replies: {stats.get('replies', 0)}\n"
            f"- Calls booked: {stats.get('booked', 0)}\n"
            f"- Revenue: ${stats.get('revenue', 0)}"
        )


# ══════════════════════════════════════════════════════════════
# MCP SERVER ADAPTERS
# Uncomment and configure as MCP servers become available.
# See: https://docs.crewai.com/en/concepts/mcp-server-adapter
# ══════════════════════════════════════════════════════════════

def get_mcp_tools(server_url: str, headers: Optional[dict] = None) -> list:
    """
    Connect to an MCP server and return its tools as CrewAI tools.
    Usage: tools = get_mcp_tools("http://mcp-server-url/sse")
    """
    try:
        from crewai_tools import MCPServerAdapter
        # Pass headers if provided (e.g. for Vercel Bearer token)
        adapter = MCPServerAdapter({"url": server_url, "headers": headers or {}})
        tools = adapter.tools
        logger.info(f"Loaded {len(tools)} tools from MCP server: {server_url}")
        return tools
    except Exception as e:
        logger.warning(f"MCP server unavailable ({server_url}): {e}")
        return []


# ── Vercel Integration ────────────────────────────────────────
# Load Vercel tools via official MCP server
VERCEL_TOKEN = os.environ.get("VERCEL_TOKEN")
VERCEL_TOOLS = []
# Temporarily disabled to avoid 'mcp' package prompts during Notion overhaul
# if VERCEL_TOKEN:
#     # Standard Vercel MCP server at https://mcp.vercel.com
#     # Requires Authorization: Bearer <token>
#     VERCEL_TOOLS = get_mcp_tools(
#         "https://mcp.vercel.com/sse", 
#         headers={"Authorization": f"Bearer {VERCEL_TOKEN}"}
#     )


# ── GitHub Tools ─────────────────────────────────────────────

class GitHubRepoTool(BaseTool):
    """Creates a new GitHub repository."""
    name: str = "create_github_repo"
    description: str = "Create a new private or public GitHub repository. Input: JSON with 'name' and optional 'description'."
    def _run(self, input_data: str) -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            result = create_repo(data["name"], data.get("description", ""))
            return f"GitHub Repo Created: {result['url']}"
        except Exception as e:
            return f"Error: {e}"

class GitHubIssueTool(BaseTool):
    """Creates a new GitHub issue."""
    name: str = "create_github_issue"
    description: str = "Create a new issue in a GitHub repository. Input: JSON with 'repo_name', 'title', and 'body'."
    def _run(self, input_data: str) -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            result = create_issue(data["repo_name"], data["title"], data.get("body", ""))
            return f"GitHub Issue Created: {result['url']}"
        except Exception as e:
            return f"Error: {e}"

class GitHubFileTool(BaseTool):
    """Creates or updates a file in a GitHub repository."""
    name: str = "upsert_github_file"
    description: str = "Create or update a file in a GitHub repository. Input: JSON with 'repo_name', 'path', 'content', and 'message'."
    def _run(self, input_data: str) -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            result = create_file(data["repo_name"], data["path"], data["content"], data.get("message", "Update via agent"))
            return result
        except Exception as e:
            return f"Error: {e}"

# ── Notion Tools ─────────────────────────────────────────────

class NotionSearchTool(BaseTool):
    """Searches for Notion databases."""
    name: str = "search_notion_databases"
    description: str = "Search for available Notion databases to find target IDs. Input: optional query string."
    def _run(self, query: str = "") -> str:
        try:
            results = search_databases(query)
            if not results: return "No databases found."
            output = "Available Notion Databases:\n"
            for r in results:
                title = r.get("title", [{}])[0].get("plain_text", "Untitled")
                output += f"- {title} (ID: {r['id']})\n"
            return output
        except Exception as e:
            return f"Error: {e}"

class NotionPageTool(BaseTool):
    """Creates a new Notion page in a database."""
    name: str = "create_notion_page"
    description: str = "Create a new page in a Notion database. Input: JSON with 'database_id', 'title', and 'content'."
    def _run(self, input_data: str) -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            url = create_page(data["database_id"], data["title"], data.get("content", ""))
            return f"Notion Page Created: {url}"
        except Exception as e:
            return f"Error: {e}"


class NotionCreateIdeaTool(BaseTool):
    """Creates a new idea record in the agentsHQ Ideas Notion database."""
    name: str = "create_notion_idea"
    description: str = (
        "Save a new idea or brain dump to the agentsHQ Ideas database in Notion. "
        "Input: JSON with 'title' (string, short name for the idea), "
        "'content' (string, full description), "
        "'impact' (High|Medium|Low, REQUIRED: score based on value to Boubacar/CW), "
        "'effort' (High|Medium|Low, REQUIRED: score based on build complexity), "
        "and optional 'category' (Tool|Agent|Feature|Business|Personal, default: Feature). "
        "ALWAYS provide impact and effort -- every idea must be scored on save."
    )

    def _run(self, input_data: str) -> str:
        db_id = os.environ.get("IDEAS_DB_ID", "")
        if not db_id:
            return "Error: IDEAS_DB_ID env var not set. Run scripts/bootstrap_ideas_db.py first."
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            title = data.get("title", "Untitled Idea")
            content = data.get("content", "")
            category = data.get("category", "Feature")
            impact = data.get("impact", "")
            effort = data.get("effort", "")
            from skills.notion_skill.notion_tool import create_idea_page
            url = create_idea_page(db_id, title, content, category, impact=impact, effort=effort)
            scored = f" [Impact: {impact}, Effort: {effort}]" if impact and effort else " [WARNING: impact/effort not scored]"
            return f"Idea saved to Notion: '{title}'{scored} {url}"
        except Exception as e:
            return f"Error saving idea: {e}"


class NotionQueryIdeasTool(BaseTool):
    """Queries the agentsHQ Ideas Notion database and returns recent entries."""
    name: str = "query_notion_ideas"
    description: str = (
        "Read ideas from the agentsHQ Ideas database. "
        "Input: optional JSON with 'status' filter (New|Reviewed|Archived) "
        "and 'limit' (default 20). Returns formatted list of ideas."
    )

    def _run(self, input_data: str = "{}") -> str:
        db_id = os.environ.get("IDEAS_DB_ID", "")
        if not db_id:
            return "Error: IDEAS_DB_ID env var not set. Run scripts/bootstrap_ideas_db.py first."
        try:
            data = {}
            if input_data:
                try:
                    data = json.loads(input_data) if isinstance(input_data, str) else input_data
                except Exception:
                    pass
            from skills.notion_skill.notion_tool import query_database
            filter_obj = None
            if data.get("status"):
                filter_obj = {
                    "property": "Status",
                    "select": {"equals": data["status"]},
                }
            results = query_database(db_id, filter_body=filter_obj)
            if not results:
                return "No ideas found in the database."
            limit = int(data.get("limit", 20))
            lines = [f"agentsHQ Ideas ({len(results[:limit])} entries):\n"]
            for r in results[:limit]:
                props = r.get("properties", {})
                name = ""
                name_prop = props.get("Name", {}).get("title", [])
                if name_prop:
                    name = name_prop[0].get("plain_text", "Untitled")
                content_prop = props.get("Content", {}).get("rich_text", [])
                content_text = content_prop[0].get("plain_text", "")[:200] if content_prop else ""
                status = props.get("Status", {}).get("select", {})
                status_name = status.get("name", "New") if status else "New"
                category = props.get("Category", {}).get("select", {})
                category_name = category.get("name", "") if category else ""
                lines.append(f"- [{status_name}] {name} ({category_name})")
                if content_text:
                    lines.append(f"  {content_text}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error querying ideas: {e}"


NOTION_CAPTURE_TOOLS = [NotionCreateIdeaTool(), NotionQueryIdeasTool()]


# Known Notion database IDs (hardcoded so agents don't need to search)
NOTION_TASK_DB_ID = os.environ.get("NOTION_TASK_DB_ID", "249bcf1a302980739c26c61cad212477")


class NotionQueryTasksTool(BaseTool):
    """Queries the Notion task database for open, overdue, or due-today tasks."""
    name: str = "query_notion_tasks"
    description: str = (
        "Query the Notion task database for open tasks. "
        "Input: JSON with optional 'due_on_or_before' (ISO date string, e.g. '2026-04-09') "
        "to filter tasks due on or before that date. "
        "Returns a formatted list of tasks with title, status, and due date."
    )

    def _run(self, input_data: str = "{}") -> str:
        try:
            data = {}
            if input_data:
                try:
                    data = json.loads(input_data) if isinstance(input_data, str) else input_data
                except Exception:
                    pass
            from skills.notion_skill.notion_tool import query_database
            due_filter = data.get("due_on_or_before", "")
            filter_body = None
            if due_filter:
                filter_body = {
                    "and": [
                        {
                            "property": "Due Date",
                            "date": {"on_or_before": due_filter},
                        },
                        {
                            "property": "Status",
                            "select": {"does_not_equal": "Done"},
                        },
                    ]
                }
            else:
                filter_body = {
                    "property": "Status",
                    "select": {"does_not_equal": "Done"},
                }
            results = query_database(NOTION_TASK_DB_ID, filter_body=filter_body, sorts=[
                {"property": "Due Date", "direction": "ascending"}
            ])
            if not results:
                return "No open tasks found matching the criteria."
            lines = [f"Open Tasks ({len(results)} found):\n"]
            for r in results:
                props = r.get("properties", {})
                # Title
                title_prop = props.get("Task", props.get("Name", props.get("title", {})))
                title = ""
                if isinstance(title_prop, dict):
                    title_list = title_prop.get("title", [])
                    if title_list:
                        title = title_list[0].get("plain_text", "Untitled")
                # Status — DB uses select type, not status type
                status_prop = props.get("Status", {})
                status = ""
                if isinstance(status_prop, dict):
                    s = status_prop.get("select", {})
                    status = s.get("name", "") if s else ""
                # Due date — DB property is "Due Date" not "Due"
                due_prop = props.get("Due Date", {})
                due_str = ""
                if isinstance(due_prop, dict):
                    d = due_prop.get("date", {})
                    due_str = d.get("start", "") if d else ""
                lines.append(f"- [{status}] {title or 'Untitled'}" + (f" — due {due_str}" if due_str else ""))
            return "\n".join(lines)
        except Exception as e:
            return f"Error querying tasks: {e}"


NOTION_TASK_TOOLS = [NotionQueryTasksTool()]


# ── Tool sets by category ─────────────────────────────────────
# These are convenience bundles used in agents.py

voice_polisher_tool = VoicePolisherTool()
harvest_apollo_leads = ApolloLeadHarvestTool()
prospecting_tool = UtahProspectingTool()
class CRMMarkOutreachSentTool(BaseTool):
    """Marks leads as messaged after you manually send their Gmail drafts."""
    name: str = "mark_outreach_sent"
    description: str = (
        "Call this after manually sending outreach drafts from Gmail. "
        "Finds every lead that had an outreach_draft interaction logged in the last 48 hours "
        "and still has status='new' and no last_contacted_at. "
        "Sets status='messaged' and last_contacted_at=now for each. "
        "No input required. Returns how many leads were marked and their names."
    )
    def _run(self, _=None) -> str:
        result = mark_outreach_sent()
        if result.get("error"):
            return f"Error: {result['error']}"
        marked = result["marked"]
        if marked == 0:
            return "No leads pending confirmation. Either all already marked or no drafts were logged in the last 48 hours."
        names = ", ".join(r["name"] for r in result["leads"])
        return f"Marked {marked} lead(s) as messaged: {names}"


class CRMQueryTool(BaseTool):
    """Answer natural-language questions about CRM leads by querying Supabase directly."""
    name: str = "query_crm"
    description: str = (
        "Answer questions about the CRM leads database. "
        "Use this for questions like: how many leads have been contacted, "
        "total leads in the CRM, how many leads by status, how many have emails, "
        "show me leads in a specific industry, or any other CRM data question. "
        "Input: the user's question as a plain string. "
        "Returns a plain-text summary with the answer."
    )
    def _run(self, question: str = "") -> str:
        try:
            import sys
            if "/app" not in sys.path:
                sys.path.insert(0, "/app")
            from db import get_crm_connection_with_fallback
            conn, _ = get_crm_connection_with_fallback()
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'new') as new_leads,
                    COUNT(*) FILTER (WHERE status = 'messaged') as contacted,
                    COUNT(*) FILTER (WHERE status = 'replied') as replied,
                    COUNT(*) FILTER (WHERE status = 'booked') as booked,
                    COUNT(*) FILTER (WHERE status = 'closed') as closed,
                    COUNT(*) FILTER (WHERE email IS NOT NULL AND email != '') as with_email,
                    COUNT(*) FILTER (WHERE linkedin_url IS NOT NULL AND linkedin_url != '') as with_linkedin,
                    COUNT(*) FILTER (WHERE last_contacted_at IS NOT NULL) as ever_contacted
                FROM leads
            """)
            row = cur.fetchone()

            cur.execute("""
                SELECT industry, COUNT(*) as cnt
                FROM leads
                WHERE industry IS NOT NULL
                GROUP BY industry
                ORDER BY cnt DESC
                LIMIT 10
            """)
            by_industry = cur.fetchall()
            cur.close()
            conn.close()

            industry_lines = "\n".join(
                f"  - {r['industry']}: {r['cnt']}" for r in by_industry
            ) or "  (no industry data)"

            return (
                f"CRM Summary:\n"
                f"- Total leads: {row['total']}\n"
                f"- Never contacted (new): {row['new_leads']}\n"
                f"- Contacted (messaged): {row['contacted']}\n"
                f"- Replied: {row['replied']}\n"
                f"- Calls booked: {row['booked']}\n"
                f"- Closed: {row['closed']}\n"
                f"- Ever contacted (last_contacted_at set): {row['ever_contacted']}\n"
                f"- With email: {row['with_email']}\n"
                f"- With LinkedIn: {row['with_linkedin']}\n\n"
                f"By industry:\n{industry_lines}"
            )
        except Exception as e:
            return f"CRM query failed: {e}"


crm_add_tool = CRMAddLeadTool()
crm_log_tool = CRMLogInteractionTool()
crm_reveal_tool = CRMRevealEmailTool()
crm_uncontacted_tool = CRMGetUncontactedTool()
scoreboard_tool = DailyScoreboardTool()
crm_mark_sent_tool = CRMMarkOutreachSentTool()
crm_query_tool = CRMQueryTool()


class EnrichLeadsTool(BaseTool):
    """Run deep email + LinkedIn enrichment on all leads missing an email."""
    name: str = "enrich_leads"
    description: str = (
        "Run deep enrichment on all leads currently missing an email address or phone number. "
        "Uses Serper to find company websites and Firecrawl to scrape for emails. "
        "Also finds missing LinkedIn URLs. Call this after discovering and saving leads. "
        "Input: optional JSON with 'limit' (default 50). "
        "Returns a summary of emails found, LinkedIn found, and leads still missing."
    )
    def _run(self, input_data: str = "{}") -> str:
        try:
            import sys
            if "/app" not in sys.path:
                sys.path.insert(0, "/app")
            from skills.email_enrichment.enrichment_tool import enrich_missing_emails
            data = {}
            if input_data:
                try:
                    data = json.loads(input_data) if isinstance(input_data, str) else input_data
                except Exception:
                    pass
            limit = data.get("limit", 50) if isinstance(data, dict) else 50
            result = enrich_missing_emails(limit=limit)
            return (
                f"Enrichment complete: {result['emails_found']} emails found, "
                f"{result['linkedin_found']} LinkedIn found, "
                f"{result['no_website']} no website (web prospects), "
                f"{result['still_missing']} still missing email out of {result['processed']} processed."
            )
        except Exception as e:
            return f"Enrichment error: {e}"


enrich_leads_tool = EnrichLeadsTool()


_NLM_LINUX = "/usr/local/bin/nlm"
_NLM_WINDOWS = r"C:\Users\HUAWEI\AppData\Roaming\Python\Python313\Scripts\nlm.exe"
NLM_BIN = _NLM_LINUX if os.path.exists(_NLM_LINUX) else _NLM_WINDOWS
AUDIENCE_ENGINE_NOTEBOOK_ID = "e246e525-8618-47ef-afd6-e279eed17d37"


class QueryAudienceEngineTool(BaseTool):
    """Query the CW_Audience Engine NotebookLM notebook for audience-building insights."""
    name: str = "query_audience_engine"
    description: str = (
        "Query the CW_Audience Engine NotebookLM notebook — 62 sources including "
        "AOP course materials, X growth transcripts, and social media playbooks. "
        "Use this to ground content in proven audience-building tactics and frameworks. "
        "Input: a specific question about X/LinkedIn growth, content strategy, "
        "audience building, monetisation, or personal branding. "
        "Returns synthesised insights with citations from the source material."
    )

    def _run(self, question: str) -> str:
        try:
            env = {**os.environ, "PYTHONUTF8": "1"}
            result = subprocess.run(
                [NLM_BIN, "query", "notebook", AUDIENCE_ENGINE_NOTEBOOK_ID, question,
                 "--json"],
                capture_output=True, text=True, env=env, timeout=120,
                creationflags=SUBPROCESS_FLAGS,
            )
            if result.returncode != 0:
                err = result.stderr.strip()
                if "Authentication" in err or "expired" in err:
                    return (
                        "NotebookLM auth expired. Run 'nlm login' on the VPS host "
                        "to re-authenticate, then retry."
                    )
                return f"Audience Engine query failed: {err[-300:]}"
            data = json.loads(result.stdout)
            answer = data.get("value", {}).get("answer", data.get("answer", ""))
            if not answer:
                return "No answer returned from Audience Engine."
            return f"[Audience Engine]\n{answer}"
        except subprocess.TimeoutExpired:
            return "Audience Engine query timed out (120s)."
        except Exception as e:
            return f"Audience Engine error: {e}"


class KieGenerateImageTool(BaseTool):
    """
    Generate an image via Kai (kie.ai). Supports ranked-ladder and direct-model routes.
    Stores output in Google Drive 05_Asset_Library/01_Images/<quarter>/ and local cache.
    Every attempt logs to Supabase media_generations.

    Input: JSON with:
      'prompt'           (required)
      'task_type'        (default 'text_to_image') — one of:
                           'text_to_image'    rank-ladder, photoreal (Seedream rank-1)
                           'image_to_image'   rank-ladder, edit/transform (Nano Banana rank-1)
                           'gpt_image_2_text' DIRECT: GPT Image 2 text-to-image; best for typography,
                                              signs, chalkboards, menus, social cards, UI mockups
                           'gpt_image_2_edit' DIRECT: GPT Image 2 image-to-image; pass input_urls
      'aspect_ratio'     (default '16:9'; ignored for gpt_image_2 routes which use 'auto')
      'input_urls'       (list of image URLs; required for gpt_image_2_edit)
      'linked_content_id' (Notion Content Board row ID)

    Returns JSON with drive_url, drive_file_id, local_path, model_used, attempts.
    """
    name: str = "kie_generate_image"
    description: str = (
        "Generate an image via Kai (kie.ai), saved to Google Drive 05_Asset_Library/01_Images. "
        "task_type controls model routing: 'text_to_image' (ranked ladder, default), "
        "'image_to_image' (ranked ladder), 'gpt_image_2_text' (direct GPT Image 2, best for "
        "typography/signs/menus/social cards/UI mockups), 'gpt_image_2_edit' (direct GPT Image 2 "
        "edit, requires input_urls). "
        "Input: JSON with 'prompt' (required), 'task_type', 'aspect_ratio', 'input_urls', "
        "'linked_content_id'. Returns JSON with drive_url, drive_file_id, local_path, model_used."
    )

    def _run(self, input_data: str) -> str:
        if not _kie_available:
            return f"kie_media module not available: {_kie_import_error_msg}"
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            prompt = data.get("prompt")
            if not prompt:
                return "Error: 'prompt' is required."
            result = _kie_generate_image(
                prompt=prompt,
                aspect_ratio=data.get("aspect_ratio", "16:9"),
                task_type=data.get("task_type", "text_to_image"),
                linked_content_id=data.get("linked_content_id"),
                input_urls=data.get("input_urls"),
            )
            return json.dumps(result)
        except Exception as e:
            logger.error(f"KieGenerateImageTool failed: {type(e).__name__}: {e}")
            return f"kie_generate_image failed: {type(e).__name__}: {e}"


class KieGenerateVideoTool(BaseTool):
    """
    Generate a video via Kai (kie.ai) using the top-ranked text-to-video model.
    Same retry/fallback/storage/logging behavior as kie_generate_image.
    Input: JSON with 'prompt' (required), optional 'aspect_ratio' (default '16:9'),
    'task_type' (text_to_video or image_to_video), 'linked_content_id'.
    Returns JSON with drive_url, drive_file_id, local_path, model_used, attempts.
    """
    name: str = "kie_generate_video"
    description: str = (
        "Generate a video via Kai (kie.ai), saved to Google Drive 05_Asset_Library/02_Videos. "
        "Uses top-ranked model per task_type with auto-fallback on failure. "
        "Input: JSON with 'prompt' (required), optional 'aspect_ratio' (default '16:9'), "
        "'task_type' (text_to_video or image_to_video), 'linked_content_id'. "
        "Returns JSON with drive_url, drive_file_id, local_path, model_used, attempts."
    )

    def _run(self, input_data: str) -> str:
        if not _kie_available:
            return f"kie_media module not available: {_kie_import_error_msg}"
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            prompt = data.get("prompt")
            if not prompt:
                return "Error: 'prompt' is required."
            result = _kie_generate_video(
                prompt=prompt,
                aspect_ratio=data.get("aspect_ratio", "16:9"),
                task_type=data.get("task_type", "text_to_video"),
                linked_content_id=data.get("linked_content_id"),
            )
            return json.dumps(result)
        except Exception as e:
            logger.error(f"KieGenerateVideoTool failed: {type(e).__name__}: {e}")
            return f"kie_generate_video failed: {type(e).__name__}: {e}"


class KieGeneratePromoVideoTool(BaseTool):
    """
    Generate a liquid glass cinematic promo video from 2-5 reference screenshots using Seedance 2 via Kie.
    Use this specifically when you want an Apple-keynote-style promo clip from app/site screenshots.
    NOT for general video generation -- use kie_generate_video for that.
    Input: JSON with:
      - 'image_urls' (required): list of 2-5 publicly accessible image URLs
      - 'subject_descriptions' (optional): one plain-English label per image, e.g. ["a dark SaaS dashboard"]
      - 'accent_color' (optional): brand accent color for lighting, e.g. "orange"
      - 'duration_hint' (optional): target duration in seconds as string, default "10"
      - 'custom_prompt' (optional): override the auto-generated liquid glass prompt entirely
      - 'linked_content_id' (optional): Notion Content Board row ID
    Returns JSON with drive_url, drive_file_id, local_path, model_used, attempts.
    """
    name: str = "kie_generate_promo_video"
    description: str = (
        "Generate a liquid glass cinematic promo video from 2-5 reference screenshots using Seedance 2 via Kie. "
        "Use for app/site promo clips in the Apple-keynote aesthetic. NOT for general video gen. "
        "Input: JSON with 'image_urls' (required, list of 2-5 URLs), optional 'subject_descriptions', "
        "'accent_color', 'duration_hint' (default '10'), 'custom_prompt', 'linked_content_id'. "
        "Returns JSON with drive_url, drive_file_id, local_path, model_used, attempts."
    )

    def _run(self, input_data: str) -> str:
        if not _kie_available:
            return f"kie_media module not available: {_kie_import_error_msg}"
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            image_urls = data.get("image_urls")
            if not image_urls:
                return "Error: 'image_urls' is required (list of 2-5 screenshot URLs)."
            result = _kie_generate_promo_video(
                image_urls=image_urls,
                subject_descriptions=data.get("subject_descriptions"),
                accent_color=data.get("accent_color", ""),
                duration_hint=data.get("duration_hint", "10"),
                custom_prompt=data.get("custom_prompt"),
                linked_content_id=data.get("linked_content_id"),
            )
            return json.dumps(result)
        except Exception as e:
            logger.error(f"KieGeneratePromoVideoTool failed: {type(e).__name__}: {e}")
            return f"kie_generate_promo_video failed: {type(e).__name__}: {e}"


class KieSoraWatermarkRemoveTool(BaseTool):
    """
    Remove a Sora watermark from a video via Kai (kie.ai).
    Input: JSON with 'video_url' (required).
    Returns JSON with result_url and task_id.
    """
    name: str = "kie_sora_watermark_remove"
    description: str = (
        "Remove a Sora watermark from a video via Kai (kie.ai). "
        "Input: JSON with 'video_url' (required). "
        "Returns JSON with result_url and task_id."
    )

    def _run(self, input_data: str) -> str:
        if not _kie_available:
            return f"kie_media module not available: {_kie_import_error_msg}"
        try:
            import kie_media

            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            video_url = data.get("video_url")
            if not video_url:
                return "Error: 'video_url' is required."
            result = kie_media.sora_watermark_remover(video_url)
            return json.dumps(result)
        except Exception as e:
            logger.error(f"KieSoraWatermarkRemoveTool failed: {type(e).__name__}: {e}")
            return f"kie_sora_watermark_remove failed: {type(e).__name__}: {e}"


class KieAudioRemixTool(BaseTool):
    """
    Remix audio via Kai (kie.ai).
    Input: JSON with 'source_url' (required) and 'prompt' (required).
    Returns JSON with result_url and task_id.
    """
    name: str = "kie_audio_remix"
    description: str = (
        "Remix audio via Kai (kie.ai). "
        "Input: JSON with 'source_url' (required) and 'prompt' (required). "
        "Returns JSON with result_url and task_id."
    )

    def _run(self, input_data: str) -> str:
        if not _kie_available:
            return f"kie_media module not available: {_kie_import_error_msg}"
        try:
            import kie_media

            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            source_url = data.get("source_url")
            prompt = data.get("prompt")
            if not source_url:
                return "Error: 'source_url' is required."
            if not prompt:
                return "Error: 'prompt' is required."
            result = kie_media.audio_remix(source_url, prompt)
            return json.dumps(result)
        except Exception as e:
            logger.error(f"KieAudioRemixTool failed: {type(e).__name__}: {e}")
            return f"kie_audio_remix failed: {type(e).__name__}: {e}"


class KieEnqueueVideoJobTool(BaseTool):
    """
    Enqueue a unified video crew job.
    Input: JSON with 'job_type' and 'prompt', plus optional 'params',
    'linked_content_id', and 'requested_by'.
    Returns JSON with job_id.
    """
    name: str = "kie_enqueue_video_job"
    description: str = (
        "Enqueue a unified video crew job. "
        "Input: JSON with 'job_type' and 'prompt', plus optional 'params', "
        "'linked_content_id', and 'requested_by'. "
        "Returns JSON with job_id."
    )

    def _run(self, input_data: str) -> str:
        try:
            from video_crew import enqueue_video_job

            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            result = enqueue_video_job(
                job_type=data.get("job_type"),
                prompt=data.get("prompt"),
                params=data.get("params"),
                linked_content_id=data.get("linked_content_id"),
                requested_by=data.get("requested_by", "system"),
            )
            return json.dumps(result)
        except Exception as e:
            logger.error(f"KieEnqueueVideoJobTool failed: {type(e).__name__}: {e}")
            return f"kie_enqueue_video_job failed: {type(e).__name__}: {e}"


class KieListModelsTool(BaseTool):
    """
    List priority-ordered Kai model registry for image and video tasks.
    Input: JSON with optional 'task_type' (text_to_image, image_to_image, text_to_video, image_to_video).
    With no input, returns the full registry grouped by task type.
    """
    name: str = "kie_list_models"
    description: str = (
        "Return the current priority-ordered Kai model registry. "
        "Input: JSON with optional 'task_type' to filter, or empty for all."
    )

    def _run(self, input_data: str = "{}") -> str:
        if not _kie_available:
            return f"kie_media module not available: {_kie_import_error_msg}"
        try:
            data = json.loads(input_data) if isinstance(input_data, str) and input_data else {}
            return json.dumps(_kie_list_models(task_type=data.get("task_type")))
        except Exception as e:
            return f"kie_list_models failed: {e}"


class KieCheckCreditsTool(BaseTool):
    """Return remaining Kai credit balance."""
    name: str = "kie_check_credits"
    description: str = "Return remaining Kai (kie.ai) credit balance. No input required."

    def _run(self, _input_data: str = "") -> str:
        if not _kie_available:
            return f"kie_media module not available: {_kie_import_error_msg}"
        try:
            return json.dumps({"credits_remaining": _kie_check_credits()})
        except Exception as e:
            return f"kie_check_credits failed: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Atlas M7b: Blotato publisher tools (verified API contract via M7a smoke test)
# Wired here per the always-wire-tools rule; consumers can call publish/status/
# accounts via standard BaseTool interface or via the auto_publisher tick.
# ─────────────────────────────────────────────────────────────────────────────

class BlotatoListAccountsTool(BaseTool):
    """List Blotato connected social accounts. Returns id + platform per account.
    Read-only, safe to call anywhere. No input required.
    """
    name: str = "blotato_list_accounts"
    description: str = "List all Blotato connected social accounts (LinkedIn/X/etc) with their accountIds. No input required."

    def _run(self, _input_data: str = "") -> str:
        try:
            from blotato_publisher import list_accounts
            return json.dumps({"items": list_accounts()})
        except Exception as e:
            return f"blotato_list_accounts failed: {e}"


class BlotatoPublishTool(BaseTool):
    """Publish text to a Blotato connected account. Returns postSubmissionId
    for status polling. Input format JSON:
      {"text": "...", "account_id": "12345", "platform": "linkedin|twitter|..."}
    Optional: media_urls (list of public URLs).
    """
    name: str = "blotato_publish"
    description: str = (
        "Publish a post via Blotato API. Input JSON: "
        '{"text": "post body", "account_id": "12345", "platform": "linkedin"}. '
        "Returns postSubmissionId. Use blotato_get_status to poll."
    )

    def _run(self, _input_data: str = "") -> str:
        try:
            from blotato_publisher import get_publisher
            payload = json.loads(_input_data) if _input_data else {}
            text = payload.get("text")
            account_id = payload.get("account_id")
            platform = payload.get("platform")
            if not (text and account_id and platform):
                return "blotato_publish: missing required field (text, account_id, platform)"
            sub_id = get_publisher().publish(
                text=text,
                account_id=str(account_id),
                platform=platform,
                media_urls=payload.get("media_urls"),
            )
            return json.dumps({"post_submission_id": sub_id})
        except Exception as e:
            return f"blotato_publish failed: {e}"


class BlotatoGetStatusTool(BaseTool):
    """Check status of a previously-submitted Blotato post.
    Input: post_submission_id (string).
    Returns: status, publicUrl (on success), errorMessage (on failure).
    """
    name: str = "blotato_get_status"
    description: str = (
        "Check status of a Blotato submission. "
        "Input: post_submission_id string. "
        "Returns status (in-progress|published|failed), plus publicUrl or errorMessage."
    )

    def _run(self, _input_data: str = "") -> str:
        try:
            from blotato_publisher import get_publisher
            sub_id = (_input_data or "").strip().strip('"').strip("'")
            if not sub_id:
                return "blotato_get_status: missing post_submission_id"
            data = get_publisher().get_status(sub_id)
            return json.dumps(data)
        except Exception as e:
            return f"blotato_get_status failed: {e}"


class SpawnJobTool(BaseTool):
    """Spawn a background job from inside an agent turn.

    Submits task_text to the existing job queue and returns a job_id
    immediately. The job runs in a daemon thread via the standard
    worker._run_background_job path. Use this when a crew agent needs
    to fire a long-running sub-task without blocking its own turn.

    Input JSON: {"task": "...", "session_key": "optional"}
    Returns: JSON {"job_id": "...", "status": "queued"}
    """
    name: str = "spawn_job"
    description: str = (
        "Spawn a background job for a long-running task. "
        "Input JSON: {\"task\": \"<task text>\", \"session_key\": \"<optional>\"}. "
        "Returns {\"job_id\": \"...\", \"status\": \"queued\"} immediately. "
        "The job runs async via the worker pool. Use when you need fire-and-forget sub-tasks."
    )

    def _run(self, _input_data: str = "") -> str:
        import uuid
        import threading

        try:
            payload = json.loads(_input_data) if _input_data else {}
        except Exception:
            payload = {"task": str(_input_data)}

        task_text = (payload.get("task") or "").strip()
        if not task_text:
            return json.dumps({"error": "spawn_job: 'task' field is required"})

        session_key = payload.get("session_key") or "spawn_job"
        # Parse real Telegram chat_id from session_key (format: "<chat_id>:<project>").
        # Passing session_key verbatim as from_number caused worker to send Telegram
        # messages to a string instead of a numeric chat_id, failing silently.
        from_number = session_key.split(":")[0]
        job_id = f"job_{uuid.uuid4().hex[:12]}"

        # Worker owns job registration via create_job() at worker.py:96.
        # Calling it here too caused a duplicate INSERT on the same job_id.

        def _launch():
            try:
                from worker import _run_background_job
                _run_background_job(
                    task=task_text,
                    from_number=from_number,
                    session_key=session_key,
                    job_id=job_id,
                )
            except Exception as exc:
                logger.error(f"SpawnJobTool: background job {job_id} failed: {exc}")

        threading.Thread(target=_launch, daemon=True, name=f"spawn-{job_id}").start()
        logger.info(f"SpawnJobTool: queued job_id={job_id} task={task_text[:60]!r}")
        return json.dumps({"job_id": job_id, "status": "queued"})


class BeehiivCreateDraftTool(BaseTool):
    """Create a draft newsletter post in beehiiv via POST /v2/publications/{pub_id}/posts.

    Non-fatal: returns None (and logs) on any failure so the newsletter
    still saves to Drive even if beehiiv is unavailable.

    Input format JSON:
      {"title": "Subject line", "content": "<html>...", "subtitle": "optional preview"}
    Optional: subtitle.
    """
    name: str = "beehiiv_create_draft"
    description: str = (
        "Create a draft post in beehiiv. "
        'Input JSON: {"title": "Subject line", "content": "<html>...", "subtitle": "optional"}. '
        "Requires BEEHIIV_API_KEY and BEEHIIV_PUBLICATION_ID env vars. "
        "Returns the post URL or ID on success, or None if env vars are missing or the call fails."
    )

    def _run(self, _input_data: str = "") -> str:
        try:
            from beehiiv import create_draft
            payload = json.loads(_input_data) if _input_data else {}
            title = payload.get("title", "").strip()
            content = payload.get("content", "").strip()
            subtitle = payload.get("subtitle")
            if not title or not content:
                return "beehiiv_create_draft: missing required field (title, content)"
            result = create_draft(title=title, content=content, subtitle=subtitle)
            if result is None:
                return "beehiiv_create_draft: skipped (env vars missing) or failed (see logs)"
            return json.dumps({"post_url": result})
        except Exception as e:
            return f"beehiiv_create_draft failed: {e}"


RESEARCH_TOOLS = [search_tool, file_reader, QueryMemoryTool(), QueryAudienceEngineTool()]
MEMORY_TOOLS = [QueryMemoryTool(), SaveLearningTool()]
SCRAPING_TOOLS = [FirecrawlScrapeTool(), FirecrawlCrawlTool(), FirecrawlSearchTool()]
PUBLISHER_TOOLS = [BlotatoListAccountsTool(), BlotatoPublishTool(), BlotatoGetStatusTool()]


# ─────────────────────────────────────────────────────────────────────────────
# Studio M1 tools (trend scout + QA crew). Wired here per always-wire-tools rule.
# ─────────────────────────────────────────────────────────────────────────────

class StudioTrendScoutTool(BaseTool):
    """Run the studio trend scout tick on demand. Scans configured niches
    (Under the Baobab, AI Catalyst, First Generation Money), writes top
    picks to the Studio Pipeline Notion DB, sends Telegram brief.
    No input required.
    """
    name: str = "studio_trend_scout_run"
    description: str = (
        "Run the Studio trend scout tick. Scans niches for viral content patterns, "
        "writes top picks to Studio Pipeline DB, sends Telegram brief. No input."
    )

    def _run(self, _input_data: str = "") -> str:
        try:
            from studio_trend_scout import studio_trend_scout_tick
            studio_trend_scout_tick()
            return "studio_trend_scout_run: tick completed (see logs + Telegram for results)"
        except Exception as e:
            return f"studio_trend_scout_run failed: {e}"


class StudioQARunTool(BaseTool):
    """Run the 8-check Studio QA crew on a specific Pipeline DB record.
    Input: Notion page ID of the record to check.
    Returns: pass/fail summary per check, plus updates the record's
    Status to qa-passed or qa-failed.
    """
    name: str = "studio_qa_run"
    description: str = (
        "Run Studio QA crew (8 checks) on a Pipeline DB record. "
        "Input: Notion page ID. Updates record Status to qa-passed or qa-failed."
    )

    def _run(self, _input_data: str = "") -> str:
        try:
            from studio_qa_crew import run_qa_on_record
            page_id = (_input_data or "").strip().strip('"').strip("'")
            if not page_id:
                return "studio_qa_run: missing notion page id"
            report = run_qa_on_record(page_id)
            if report is None:
                return f"studio_qa_run: could not load record {page_id}"
            lines = [f"QA report for {report.title[:60]}: {'PASS' if report.passed else 'FAIL'}"]
            for c in report.checks:
                mark = "OK" if c.passed else "FAIL"
                lines.append(f"  [{mark}] {c.name}: {c.detail}")
            return "\n".join(lines)
        except Exception as e:
            return f"studio_qa_run failed: {e}"


STUDIO_TOOLS = [StudioTrendScoutTool(), StudioQARunTool()]


try:
    from niche_research import get_tools as _niche_research_tools
    NICHE_RESEARCH_TOOLS = _niche_research_tools()
except Exception as _e:
    logger.warning(f"NICHE_RESEARCH_TOOLS unavailable: {_e}")
    NICHE_RESEARCH_TOOLS = []
try:
    from video_analyze import get_tools as _video_analyze_tools
    VIDEO_ANALYZE_TOOLS = _video_analyze_tools()
except Exception as _e:
    logger.warning(f"VIDEO_ANALYZE_TOOLS unavailable: {_e}")
    VIDEO_ANALYZE_TOOLS = []
MEDIA_TOOLS = [
    KieGenerateImageTool(),
    KieGenerateVideoTool(),
    KieGeneratePromoVideoTool(),
    KieSoraWatermarkRemoveTool(),
    KieAudioRemixTool(),
    KieEnqueueVideoJobTool(),
    KieListModelsTool(),
    KieCheckCreditsTool(),
]
VALIDATION_TOOLS = [ValidateOutputTool()]
WRITING_TOOLS = [file_writer, SaveOutputTool(), voice_polisher_tool, BeehiivCreateDraftTool()]
CODE_TOOLS = [t for t in [code_interpreter, file_writer, file_reader, SaveOutputTool(), CLIHubSearchTool(), launch_vercel_tool] if t is not None]
ORCHESTRATION_TOOLS = [EscalateTool(), ProposeNewAgentTool(), QueryMemoryTool(), scoreboard_tool, CLIHubSearchTool(), GitHubRepoTool(), GitHubIssueTool(), GitHubFileTool(), NotionSearchTool(), NotionPageTool(), launch_vercel_tool, SpawnJobTool()] + VERCEL_TOOLS + NOTION_STYLING_TOOLS + FORGE_TOOLS + GWS_TOOLS
HUNTER_TOOLS = [harvest_apollo_leads, prospecting_tool, crm_add_tool, crm_log_tool, crm_reveal_tool, enrich_leads_tool, scoreboard_tool, QueryMemoryTool(), NotionPageTool(), forge_pipeline_tool, forge_log_tool]
OUTREACH_TOOLS = [crm_uncontacted_tool, crm_reveal_tool, crm_log_tool, scoreboard_tool, crm_mark_sent_tool]
HYPERFRAMES_TOOLS = [t for t in [hyperframes_tool] if t is not None]
