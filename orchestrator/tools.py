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
    from skills.local_crm.crm_tool import add_lead, log_interaction, update_lead_status, get_daily_scoreboard, update_lead_email, get_lead_by_name
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
    """Adds a newly discovered lead to the local CRM."""
    name: str = "add_lead"
    description: str = (
        "Add a discovered lead to the local PostgreSQL CRM. "
        "Input: JSON dict with name, company, title, location, linkedin_url, industry."
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

def get_mcp_tools(server_url: str) -> list:
    """
    Connect to an MCP server and return its tools as CrewAI tools.
    Usage: tools = get_mcp_tools("http://mcp-server-url/sse")
    """
    try:
        from crewai_tools import MCPServerAdapter
        adapter = MCPServerAdapter({"url": server_url})
        tools = adapter.tools
        logger.info(f"Loaded {len(tools)} tools from MCP server: {server_url}")
        return tools
    except Exception as e:
        logger.warning(f"MCP server unavailable ({server_url}): {e}")
        return []


# ── Tool sets by category ─────────────────────────────────────
# These are convenience bundles used in agents.py

voice_polisher_tool = VoicePolisherTool()
prospecting_tool = UtahProspectingTool()
crm_add_tool = CRMAddLeadTool()
crm_log_tool = CRMLogInteractionTool()
crm_reveal_tool = CRMRevealEmailTool()
scoreboard_tool = DailyScoreboardTool()

RESEARCH_TOOLS = [search_tool, file_reader, QueryMemoryTool()]
SCRAPING_TOOLS = [FirecrawlScrapeTool(), FirecrawlCrawlTool(), FirecrawlSearchTool()]
WRITING_TOOLS = [file_writer, SaveOutputTool(), voice_polisher_tool]
CODE_TOOLS = [code_interpreter, file_writer, file_reader, SaveOutputTool(), CLIHubSearchTool()]
ORCHESTRATION_TOOLS = [EscalateTool(), ProposeNewAgentTool(), QueryMemoryTool(), scoreboard_tool, CLIHubSearchTool()]
HUNTER_TOOLS = [prospecting_tool, crm_add_tool, crm_log_tool, crm_reveal_tool, scoreboard_tool, QueryMemoryTool()]
