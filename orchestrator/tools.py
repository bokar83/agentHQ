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
import httpx
from datetime import datetime
from typing import Any, Optional
from crewai_tools import (
    SerperDevTool,
    FileWriterTool,
    FileReadTool,
    CodeInterpreterTool,
)
from crewai.tools import BaseTool
from pydantic import Field

from firecrawl_tools import FirecrawlScrapeTool, FirecrawlCrawlTool, FirecrawlSearchTool

# Import Phase 2 Skills
# Core hunter + CRM imports — must not fail silently
try:
    from skills.local_crm.crm_tool import add_lead, log_interaction, update_lead_status, get_daily_scoreboard, update_lead_email, get_lead_by_name, get_uncontacted_leads
except ImportError as e:
    logger_pre = __import__("logging").getLogger(__name__)
    logger_pre.warning(f"crm_tool import failed: {e}")
    def add_lead(*args, **kwargs): return "crm_not_ready"
    def log_interaction(*args, **kwargs): return False
    def update_lead_status(*args, **kwargs): return False
    def get_daily_scoreboard(*args, **kwargs): return {}
    def update_lead_email(*args, **kwargs): return False
    def get_lead_by_name(*args, **kwargs): return {}

try:
    from skills.serper_skill.hunter_tool import discover_leads, reveal_email_for_lead
except ImportError as e:
    logger_pre = __import__("logging").getLogger(__name__)
    logger_pre.warning(f"hunter_tool import failed: {e}")
    def discover_leads(*args, **kwargs): return []
    def reveal_email_for_lead(*args, **kwargs): return None

try:
    from skills.cli_hub.cli_hub_tool import execute_cli_hub_action
except ImportError:
    def execute_cli_hub_action(*args, **kwargs): return "cli_hub_not_ready"

# GitHub & Notion Skill Imports
try:
    from skills.github_skill.github_tool import create_repo, create_issue, create_file
except ImportError:
    def create_repo(*args, **kwargs): return "github_not_ready"
    def create_issue(*args, **kwargs): return "github_not_ready"
    def create_file(*args, **kwargs): return "github_not_ready"

try:
    from skills.notion_cli.notion_cli import NotionCLI
    from skills.notion_stylist.notion_stylist import NotionStylist
    from skills.HunterAgent.utils.supabase_client import SupabaseClient
    from skills.notion_skill.notion_tool import search_databases, create_page, append_block
except ImportError:
    def search_databases(*args, **kwargs): return []
    def create_page(*args, **kwargs): return "notion_not_ready"
    def append_block(*args, **kwargs): return False

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# SEARCH & RESEARCH TOOLS
# ══════════════════════════════════════════════════════════════

# Web search via Serper (2500 free searches/month)
search_tool = SerperDevTool()

# File operations
file_writer = FileWriterTool()
file_reader = FileReadTool()

# Code execution (sandboxed)
code_interpreter = CodeInterpreterTool()


# ── Notion Styling & Branding Tools ──────────────────────────
class SetNotionStyleTool(BaseTool):
    """Sets the cover and icon for a Notion page."""
    name: str = "set_notion_style"
    description: str = (
        "Set the premium cover image and icon for a Notion page. "
        "Inputs: 'page_id' (string), 'cover' (string URL), 'icon' (emoji or URL)."
    )
    def _run(self, page_id: str, cover: str = None, icon: str = None) -> str:
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
        import json
        stylist = NotionStylist()
        try:
            items = json.loads(items_json) if isinstance(items_json, str) else items_json
            return stylist.create_navigation_grid(page_id, items)
        except Exception as e:
            return f"Error: {e}"

set_notion_style_tool = SetNotionStyleTool()
add_notion_nav_tool = AddNotionNavTool()

NOTION_STYLING_TOOLS = [set_notion_style_tool, add_notion_nav_tool]


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


# ══════════════════════════════════════════════════════════════
# GOOGLE WORKSPACE TOOLS (Calendar + Gmail)
# Supports multiple accounts via separate credentials files:
#   bokar83@gmail.com       → GOOGLE_OAUTH_CREDENTIALS_JSON (default)
#   catalystworks.ai@gmail.com → GOOGLE_OAUTH_CREDENTIALS_JSON_CW
# ══════════════════════════════════════════════════════════════

_GWS_CREDS_MAP = {
    "bokar83@gmail.com": os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON", "/app/secrets/gws-oauth-credentials.json"),
    "catalystworks.ai@gmail.com": os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON_CW", "/app/secrets/gws-oauth-credentials-cw.json"),
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
        "use 'catalystworks.ai@gmail.com' for Catalyst Works outreach)."
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
        "Search Gmail messages. "
        "Input: JSON with 'query' (Gmail search syntax, e.g. 'from:someone subject:hello'). "
        "Optional: 'max_results' (default 5), 'account' (email address to search — defaults to bokar83@gmail.com)."
    )
    def _run(self, input_data: str) -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            account = data.get("account")
            result = _gws_request(
                "get",
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                account=account,
                params={"q": data["query"], "maxResults": data.get("max_results", 5)},
            )
            messages = result.get("messages", [])
            if not messages:
                return "No messages found."
            return f"Found {len(messages)} message(s). IDs: {', '.join(m['id'] for m in messages)}"
        except Exception as e:
            return f"gmail_search failed: {e}"


gws_calendar_list_tool = GWSCalendarListTool()
gws_calendar_create_tool = GWSCalendarCreateTool()
gws_calendar_delete_tool = GWSCalendarDeleteTool()
gws_gmail_draft_tool = GWSGmailCreateDraftTool()
gws_gmail_search_tool = GWSGmailSearchTool()

GWS_TOOLS = [
    gws_calendar_list_tool,
    gws_calendar_create_tool,
    gws_calendar_delete_tool,
    gws_gmail_draft_tool,
    gws_gmail_search_tool,
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
            return f"Error querying Qdrant: {e}"

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
    """Adds a newly discovered lead to Supabase and syncs to Notion."""
    name: str = "add_lead"
    description: str = (
        "Add a discovered lead to the Supabase CRM and auto-sync to Notion CRM Leads. "
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


# ── Tool sets by category ─────────────────────────────────────
# These are convenience bundles used in agents.py

voice_polisher_tool = VoicePolisherTool()
prospecting_tool = UtahProspectingTool()
crm_add_tool = CRMAddLeadTool()
crm_log_tool = CRMLogInteractionTool()
crm_reveal_tool = CRMRevealEmailTool()
crm_uncontacted_tool = CRMGetUncontactedTool()
scoreboard_tool = DailyScoreboardTool()

RESEARCH_TOOLS = [search_tool, file_reader, QueryMemoryTool()]
SCRAPING_TOOLS = [FirecrawlScrapeTool(), FirecrawlCrawlTool(), FirecrawlSearchTool()]
WRITING_TOOLS = [file_writer, SaveOutputTool(), voice_polisher_tool]
CODE_TOOLS = [code_interpreter, file_writer, file_reader, SaveOutputTool(), CLIHubSearchTool()]
ORCHESTRATION_TOOLS = [EscalateTool(), ProposeNewAgentTool(), QueryMemoryTool(), scoreboard_tool, CLIHubSearchTool(), GitHubRepoTool(), GitHubIssueTool(), GitHubFileTool(), NotionSearchTool(), NotionPageTool()] + VERCEL_TOOLS + NOTION_STYLING_TOOLS + FORGE_TOOLS + GWS_TOOLS
HUNTER_TOOLS = [prospecting_tool, crm_add_tool, crm_log_tool, crm_reveal_tool, scoreboard_tool, QueryMemoryTool(), NotionPageTool(), forge_pipeline_tool, forge_log_tool]
OUTREACH_TOOLS = [crm_uncontacted_tool, crm_reveal_tool, crm_log_tool, scoreboard_tool]
