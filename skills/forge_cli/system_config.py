import json
from datetime import date
from pathlib import Path
from typing import Optional

from skills.forge_cli.notion_client import NotionClient
from skills.forge_cli import config


def load_forge_config() -> dict:
    """Load forge_config.json from the skill directory."""
    config_path = Path(__file__).parent / "forge_config.json"
    with open(config_path) as f:
        return json.load(f)


class SystemConfig:
    """Read/write the single-row System Config database."""

    PHASE_LABELS = {
        0: "Phase 0: Installing the Animal",
        1: "Phase 1: Building the Machine",
        2: "Phase 2: Becoming the Operator",
        3: "Phase 3: The $10K/Day Version",
    }

    UNLOCK_CRITERIA = {
        0: [
            ("P0>1: 30-Day Streak", "p0_1_streak", "30-day execution streak"),
            ("P0>1: First Revenue", "p0_1_revenue", "First revenue logged"),
        ],
        1: [
            ("P1>2: First Retainer", "p1_2_retainer", "First retainer signed"),
            ("P1>2: Agent Task Live", "p1_2_agent", "Agent task live end-to-end"),
        ],
    }

    def __init__(self, client: Optional[NotionClient] = None):
        self.client = client or NotionClient(secret=config.NOTION_SECRET)
        self.forge_config = load_forge_config()
        self.db_id = self.forge_config["system_config_db_id"]

    def _get_config_row(self) -> dict:
        pages = self.client.query_database(
            self.db_id,
            filter_obj={
                "property": "Config Name",
                "title": {"equals": "Catalyst OS Config"},
            },
        )
        if not pages:
            raise RuntimeError("System Config row not found. Check Notion setup.")
        return pages[0]

    def get(self) -> dict:
        row = self._get_config_row()
        props = row["properties"]
        return {
            "page_id": row["id"],
            "phase": props.get("Current Phase", {}).get("number", 0) or 0,
            "phase_label": (props.get("Phase Label", {}).get("select") or {}).get("name", "Phase 0: Installing the Animal"),
            "phase_start": (props.get("Phase Start Date", {}).get("date") or {}).get("start", date.today().isoformat()),
            "streak_start": (props.get("Streak Start Date", {}).get("date") or {}).get("start", date.today().isoformat()),
            "streak": props.get("Current Streak", {}).get("number", 0) or 0,
            "longest_streak": props.get("Longest Streak", {}).get("number", 0) or 0,
            "p0_1_streak": props.get("P0>1: 30-Day Streak", {}).get("checkbox", False),
            "p0_1_revenue": props.get("P0>1: First Revenue", {}).get("checkbox", False),
            "p1_2_retainer": props.get("P1>2: First Retainer", {}).get("checkbox", False),
            "p1_2_agent": props.get("P1>2: Agent Task Live", {}).get("checkbox", False),
        }

    def update(self, **kwargs) -> dict:
        row = self._get_config_row()
        props = {}
        if "phase" in kwargs:
            props["Current Phase"] = {"number": kwargs["phase"]}
        if "phase_label" in kwargs:
            props["Phase Label"] = {"select": {"name": kwargs["phase_label"]}}
        if "phase_start" in kwargs:
            props["Phase Start Date"] = {"date": {"start": kwargs["phase_start"]}}
        if "streak_start" in kwargs:
            props["Streak Start Date"] = {"date": {"start": kwargs["streak_start"]}}
        if "streak" in kwargs:
            props["Current Streak"] = {"number": kwargs["streak"]}
        if "longest_streak" in kwargs:
            props["Longest Streak"] = {"number": kwargs["longest_streak"]}
        if "p0_1_streak" in kwargs:
            props["P0>1: 30-Day Streak"] = {"checkbox": kwargs["p0_1_streak"]}
        if "p0_1_revenue" in kwargs:
            props["P0>1: First Revenue"] = {"checkbox": kwargs["p0_1_revenue"]}
        if "p1_2_retainer" in kwargs:
            props["P1>2: First Retainer"] = {"checkbox": kwargs["p1_2_retainer"]}
        if "p1_2_agent" in kwargs:
            props["P1>2: Agent Task Live"] = {"checkbox": kwargs["p1_2_agent"]}
        return self.client.update_page(row["id"], properties=props)
