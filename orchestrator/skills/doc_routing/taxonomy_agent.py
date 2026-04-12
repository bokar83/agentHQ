"""
taxonomy_agent.py — TaxonomyRoutingAgent definition.

This agent classifies incoming documents against the Routing Matrix
and produces a structured JSON routing decision.

Input (from crew task context):
  record_id, filename, extracted_text, mime_type, source, project_hint

Output (in TaskResponse.result as JSON string):
  See REQUIRED_OUTPUT_SCHEMA below for full field list.
"""

import os
import json
import logging
import time
from typing import Optional
from crewai import Agent, Task

logger = logging.getLogger(__name__)

# ── Controlled vocabularies ──────────────────────────────
VALID_DOMAINS = {"CLIENT", "CATALYST", "RESEARCH", "CONTENT", "LEARNING", "OPS"}
VALID_DOC_TYPES = {"transcript", "report", "notes", "draft", "proposal", "deliverable", "template", "reference", "sop"}
VALID_NOTEBOOKS = {"Client Notebook", "Catalyst Notebook", "Research Notebook", "Content Notebook", "Learning Notebook", "Unassigned"}
VALID_CONFIDENCE = {"high", "medium", "low"}

REGISTRY_SHEET_ID = os.environ.get("NOTEBOOKLM_REGISTRY_SHEET_ID", "")

ROUTING_MATRIX_SEED = [
    {"priority": 1,  "signal_keywords": ["agentsHQ", "CrewAI", "n8n", "VPS", "Docker", "orchestrator", "litellm", "workflow node"],
     "domain": "CATALYST", "target_folder_path": "02_Catalyst_Works/03_agentsHQ/", "doc_type_hint": "sop or reference", "notebook_assignment": "Catalyst Notebook"},
    {"priority": 2,  "signal_keywords": ["SOP", "checklist", "protocol", "template", "process doc", "system design"],
     "domain": "CATALYST", "target_folder_path": "02_Catalyst_Works/04_Systems_and_SOPs/", "doc_type_hint": "sop or template", "notebook_assignment": "Catalyst Notebook"},
    {"priority": 3,  "signal_keywords": ["proposal", "SOW", "contract", "invoice", "engagement", "client brief", "discovery call"],
     "domain": "CLIENT", "target_folder_path": "01_Clients/[Client Name]/", "doc_type_hint": "match to doc type", "notebook_assignment": "Client Notebook"},
    {"priority": 4,  "signal_keywords": ["constraint", "throughput", "bottleneck", "TOC", "five whys", "drum-buffer-rope", "Goldratt"],
     "domain": "RESEARCH", "target_folder_path": "03_Research/01_TOC_and_Constraints/", "doc_type_hint": "report or reference", "notebook_assignment": "Research Notebook"},
    {"priority": 5,  "signal_keywords": ["AI strategy", "LLM", "language model", "prompt", "agent", "automation", "AI tool"],
     "domain": "RESEARCH", "target_folder_path": "03_Research/02_AI_Strategy/", "doc_type_hint": "report or reference", "notebook_assignment": "Research Notebook"},
    {"priority": 6,  "signal_keywords": ["SMB", "owner-operator", "professional services", "small business", "business owner"],
     "domain": "RESEARCH", "target_folder_path": "03_Research/03_SMB_and_Operators/", "doc_type_hint": "report or reference", "notebook_assignment": "Research Notebook"},
    {"priority": 7,  "signal_keywords": ["behavioral science", "psychology", "decision making", "bias", "motivation"],
     "domain": "RESEARCH", "target_folder_path": "03_Research/04_Behavioral_Science/", "doc_type_hint": "report or reference", "notebook_assignment": "Research Notebook"},
    {"priority": 8,  "signal_keywords": ["LinkedIn", "post", "hook", "caption", "carousel", "social media"],
     "domain": "CONTENT", "target_folder_path": "04_Content/01_LinkedIn/", "doc_type_hint": "draft or reference", "notebook_assignment": "Content Notebook"},
    {"priority": 9,  "signal_keywords": ["framework", "IP", "methodology", "flywheel", "offer design", "positioning"],
     "domain": "CONTENT", "target_folder_path": "04_Content/04_Frameworks_and_IP/", "doc_type_hint": "reference or template", "notebook_assignment": "Content Notebook"},
    {"priority": 10, "signal_keywords": ["book summary", "course notes", "transcript", "learning", "chapter notes"],
     "domain": "LEARNING", "target_folder_path": "05_Learning/", "doc_type_hint": "match to doc type", "notebook_assignment": "Learning Notebook"},
    {"priority": 11, "signal_keywords": ["idea", "hypothesis", "rough thought", "brainstorm", "shower thought", "what if", "early concept", "voice memo"],
     "domain": "OPS", "target_folder_path": "06_Ideas/", "doc_type_hint": "notes or reference", "notebook_assignment": "Unassigned"},
    {"priority": 12, "signal_keywords": ["AMPLIFY", "Human AI Workflow Matrix", "proprietary framework", "IP", "methodology", "framework doc"],
     "domain": "CATALYST", "target_folder_path": "02_Catalyst_Works/06_Frameworks_and_IP/", "doc_type_hint": "reference or template", "notebook_assignment": "Catalyst Notebook"},
]


def parse_routing_matrix(raw_values: list[list]) -> list[dict]:
    """
    Parse raw Sheets values (list of rows) into routing matrix dicts.
    Skips the header row. Sorts by priority ascending.
    raw_values[0] is expected to be the header row.
    """
    if not raw_values or len(raw_values) < 2:
        return []
    rows = []
    for row in raw_values[1:]:  # skip header
        if len(row) < 6:
            continue
        try:
            rows.append({
                "priority": int(row[0]),
                "signal_keywords": [k.strip() for k in row[1].split(",") if k.strip()],
                "domain": row[2].strip(),
                "target_folder_path": row[3].strip(),
                "doc_type_hint": row[4].strip(),
                "notebook_assignment": row[5].strip(),
            })
        except (ValueError, IndexError):
            continue
    return sorted(rows, key=lambda r: r["priority"])


AGENT_SYSTEM_PROMPT = """You are the TaxonomyRoutingAgent for Catalyst Works Consulting.

Your ONLY job is to classify a document and produce a JSON routing decision.
You must output ONLY valid JSON -- no preamble, no explanation, no markdown.

ROUTING MATRIX (priority order -- first match wins):
{routing_matrix_text}

FILE NAMING CONVENTION:
[DOMAIN]_[TopicOrClient]_[doctype]_[YYYY-MM-DD]_[short-descriptor]

Domain values (exact): CLIENT | CATALYST | RESEARCH | CONTENT | LEARNING | OPS
Doc type values (exact): transcript | report | notes | draft | proposal | deliverable | template | reference | sop
Short descriptor: 3 to 5 words, kebab-case

CONFIDENCE AND AUTO-FILE RULES:
- confidence_score >= 0.92: set auto_file=true, review_required=false
- confidence_score >= 0.85 and < 0.92: set auto_file=false, review_required=false
- confidence_score < 0.85: set auto_file=false, review_required=true, target_folder_path="00_Review_Queue/"

NOTEBOOK ASSIGNMENT (use ONLY these values):
Client Notebook | Catalyst Notebook | Research Notebook | Content Notebook | Learning Notebook | Unassigned

If you cannot determine routing with confidence >= 0.85, set target_folder_path to "00_Review_Queue/" and notebook_assignment to "Unassigned".

OUTPUT SCHEMA (JSON only, no other text):
{{
  "record_id": "<same UUID from input>",
  "domain": "<CLIENT|CATALYST|RESEARCH|CONTENT|LEARNING|OPS>",
  "topic_or_client": "<string>",
  "doc_type": "<transcript|report|notes|draft|proposal|deliverable|template|reference|sop>",
  "target_folder_path": "<exact path from taxonomy or 00_Review_Queue/>",
  "standardized_filename": "<full filename following naming convention, no extension>",
  "project_id": "<existing project ID or NEW>",
  "new_project_name": "<only if project_id is NEW, else null>",
  "notebook_assignment": "<one of the five controlled values or Unassigned>",
  "confidence": "<high|medium|low>",
  "confidence_score": <0.0 to 1.0>,
  "review_required": <true|false>,
  "auto_file": <true|false>,
  "routing_notes": "<one sentence explanation>"
}}"""


def get_project_registry() -> list[dict]:
    """
    Fetch all rows from the Projects tab in the Registry Sheet.
    Returns a list of dicts with keys: project_id, project_name, client_or_topic,
    folder_path, drive_folder_id, notebook_assignment, status.
    Falls back to empty list if sheet not configured or fetch fails.
    """
    from skills.doc_routing.gws_cli_tools import GWSSheetsReadRangeTool
    if not REGISTRY_SHEET_ID:
        return []
    try:
        tool = GWSSheetsReadRangeTool()
        raw = tool._run(json.dumps({"spreadsheet_id": REGISTRY_SHEET_ID, "range": "Projects!A:H"}))
        data = json.loads(raw)
        if "error" in data:
            return []
        rows = data.get("values", [])
        if len(rows) < 2:
            return []
        return [
            {
                "project_id": row[0] if len(row) > 0 else "",
                "project_name": row[1] if len(row) > 1 else "",
                "client_or_topic": row[2] if len(row) > 2 else "",
                "folder_path": row[3] if len(row) > 3 else "",
                "drive_folder_id": row[4] if len(row) > 4 else "",
                "notebook_assignment": row[5] if len(row) > 5 else "",
                "status": row[6] if len(row) > 6 else "",
            }
            for row in rows[1:]  # skip header
        ]
    except Exception as e:
        logger.error(f"get_project_registry failed: {e}")
        return []


def propose_matrix_row(signal_keywords: str, suggested_domain: str, suggested_folder: str, suggested_notebook: str) -> str:
    """
    Send a Telegram proposal for a new Routing Matrix row and log it to PostgreSQL.
    Does NOT write to the sheet directly -- operator must reply + to approve.
    Returns: "proposed" on success, "error: <message>" on failure.
    """
    import psycopg2

    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    telegram_token = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN", "")

    msg = (
        f"Routing Matrix proposal:\n"
        f"New row suggested based on unmatched document pattern.\n"
        f"Signal keywords: {signal_keywords}\n"
        f"Suggested domain: {suggested_domain}\n"
        f"Suggested folder: {suggested_folder}\n"
        f"Suggested notebook: {suggested_notebook}\n\n"
        f"Reply + to add, x to reject."
    )

    # Send Telegram notification
    try:
        import requests
        requests.post(
            f"https://api.telegram.org/bot{telegram_token}/sendMessage",
            json={"chat_id": telegram_chat_id, "text": msg},
            timeout=10,
        )
    except Exception as e:
        logger.error(f"propose_matrix_row Telegram send failed: {e}")

    # Log proposal to PostgreSQL
    try:
        with psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "orc-postgres"),
            database=os.environ.get("POSTGRES_DB", "postgres"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            port=int(os.environ.get("POSTGRES_PORT", 5432)),
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO routing_matrix_proposals
                       (signal_keywords, suggested_domain, suggested_folder, suggested_notebook)
                       VALUES (%s, %s, %s, %s)""",
                    (signal_keywords, suggested_domain, suggested_folder, suggested_notebook),
                )
    except Exception as e:
        logger.error(f"propose_matrix_row DB insert failed: {e}")
        return f"error: {e}"

    return "proposed"


def build_taxonomy_routing_agent(routing_matrix: list[dict]) -> Agent:
    """Build the TaxonomyRoutingAgent with current routing matrix baked into its backstory."""
    from agents import select_llm

    matrix_lines = []
    for row in routing_matrix:
        keywords = ", ".join(row["signal_keywords"][:5])
        matrix_lines.append(
            f"P{row['priority']}: [{keywords}] -> {row['domain']} | {row['target_folder_path']} | {row['notebook_assignment']}"
        )
    routing_matrix_text = "\n".join(matrix_lines) if matrix_lines else "(using seed defaults)"

    return Agent(
        role="Document Taxonomy and Routing Specialist",
        goal=(
            "Classify every incoming document accurately using the routing matrix and naming convention. "
            "Prevent folder sprawl. Protect information architecture integrity. "
            "Optimize for correct notebook assignment above all other routing decisions."
        ),
        backstory=AGENT_SYSTEM_PROMPT.format(routing_matrix_text=routing_matrix_text),
        llm=select_llm("orchestrator", "moderate"),
        verbose=False,
        memory=False,
    )
