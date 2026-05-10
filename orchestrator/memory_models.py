"""
memory_models.py - Write contract for the agentsHQ memory table.

Every write path imports one of these models and calls to_db_row()
to get the dict for the Postgres INSERT. Invalid data raises
ValidationError before hitting the DB.

8 categories, each with its own required fields and defaults:
  agent_lesson   — what the system learned (boost 1.5)
  project_state  — roadmap codename state (boost 1.0)
  lead_record    — SW T1-T5 prospect (boost 1.0)
  client_record  — CW engagement (boost 1.0)
  idea           — captured idea (boost 0.9)
  hard_rule      — agent-critical constraint (boost 2.0, always loaded)
  asset          — findable file/link (boost 0.8)
  session_log    — what happened in a session (boost 1.2)
"""
from __future__ import annotations

import re
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


def _slugify(text: str) -> str:
    """Lowercase, replace spaces/special chars with hyphens."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


class _MemoryBase(BaseModel):
    """Shared fields injected by every model's to_db_row()."""
    source: str = "claude-code"
    agent_id: Optional[str] = None
    external_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

    category: str = ""
    relevance_boost: float = 1.0
    pipeline: str = "general"
    entity_ref: Optional[str] = None

    def to_db_row(self) -> dict:
        """Return dict ready for Postgres INSERT into memory table."""
        return {
            "source": self.source,
            "category": self.category,
            "title": getattr(self, "title", None),
            "content": self._build_content(),
            "tags": self.tags,
            "entity_ref": self.entity_ref,
            "external_id": self.external_id,
            "agent_id": self.agent_id,
            "pipeline": self.pipeline,
            "relevance_boost": self.relevance_boost,
            "expires_at": getattr(self, "expires_at", None),
        }

    def _build_content(self) -> str:
        raise NotImplementedError


class AgentLesson(_MemoryBase):
    category: str = "agent_lesson"
    relevance_boost: float = 1.5

    what_happened: str
    outcome: Literal["FAILED", "SUCCEEDED", "PARTIAL"]
    rule: str
    pipeline: str = "general"
    cost_estimate: str = ""

    def _build_content(self) -> str:
        parts = [
            f"What happened: {self.what_happened}",
            f"Outcome: {self.outcome}",
            f"Rule: {self.rule}",
        ]
        if self.cost_estimate:
            parts.append(f"Cost: {self.cost_estimate}")
        return "\n".join(parts)


class ProjectState(_MemoryBase):
    category: str = "project_state"
    relevance_boost: float = 1.0

    codename: Literal["atlas", "harvest", "studio", "compass", "echo", "general"]
    milestone: str = ""
    status: Literal["on-track", "blocked", "shipped", "paused"]
    last_action: str
    next_action: str
    blockers: str = ""

    @model_validator(mode="after")
    def set_pipeline_and_entity(self) -> "ProjectState":
        self.pipeline = self.codename
        self.entity_ref = f"project:{self.codename}"
        return self

    def _build_content(self) -> str:
        parts = [
            f"Codename: {self.codename}",
            f"Status: {self.status}",
            f"Last action: {self.last_action}",
            f"Next action: {self.next_action}",
        ]
        if self.milestone:
            parts.insert(1, f"Milestone: {self.milestone}")
        if self.blockers:
            parts.append(f"Blockers: {self.blockers}")
        return "\n".join(parts)


class LeadRecord(_MemoryBase):
    category: str = "lead_record"
    relevance_boost: float = 1.0
    pipeline: str = "sw"

    company: str
    contact: str
    gmb_score: int = Field(ge=0, le=4)
    sequence: Literal["T1", "T2", "T3", "T4", "T5"]
    last_touch: str
    response: str = ""
    audit_url: str = ""

    @model_validator(mode="after")
    def set_entity_ref(self) -> "LeadRecord":
        self.entity_ref = f"sw:{_slugify(self.company)}"
        return self

    def _build_content(self) -> str:
        parts = [
            f"Company: {self.company}",
            f"Contact: {self.contact}",
            f"GMB Score: {self.gmb_score}/4",
            f"Sequence: {self.sequence}",
            f"Last touch: {self.last_touch}",
        ]
        if self.response:
            parts.append(f"Response: {self.response}")
        if self.audit_url:
            parts.append(f"Audit URL: {self.audit_url}")
        return "\n".join(parts)


class ClientRecord(_MemoryBase):
    category: str = "client_record"
    relevance_boost: float = 1.0
    pipeline: str = "cw"

    company: str
    contact: str
    offer: Literal["Signal Session", "SaaS Audit", "custom"]
    stage: Literal["prospect", "signal-session", "discovery", "active", "closed"]
    last_touch: str
    mrr: str = ""
    notes: str = ""

    @model_validator(mode="after")
    def set_entity_ref(self) -> "ClientRecord":
        self.entity_ref = f"cw:{_slugify(self.company)}"
        return self

    def _build_content(self) -> str:
        parts = [
            f"Company: {self.company}",
            f"Contact: {self.contact}",
            f"Offer: {self.offer}",
            f"Stage: {self.stage}",
            f"Last touch: {self.last_touch}",
        ]
        if self.mrr:
            parts.append(f"MRR: {self.mrr}")
        if self.notes:
            parts.append(f"Notes: {self.notes}")
        return "\n".join(parts)


class Idea(_MemoryBase):
    category: str = "idea"
    relevance_boost: float = 0.9

    title: str
    context: str
    pipeline: str = "general"
    priority: Literal["now", "soon", "someday"]

    def _build_content(self) -> str:
        return (
            f"Idea: {self.title}\n"
            f"Context: {self.context}\n"
            f"Priority: {self.priority}"
        )


class HardRule(_MemoryBase):
    category: str = "hard_rule"
    relevance_boost: float = 2.0
    pipeline: str = "general"

    rule: str
    reason: str
    applies_to: Literal["all", "content", "outreach", "code", "deploy"]

    def _build_content(self) -> str:
        return (
            f"Rule: {self.rule}\n"
            f"Reason: {self.reason}\n"
            f"Applies to: {self.applies_to}"
        )


class Asset(_MemoryBase):
    category: str = "asset"
    relevance_boost: float = 0.8

    title: str
    asset_type: Literal["drive_doc", "notion_page", "video", "report", "site"]
    url: str
    pipeline: str = "general"
    notes: str = ""

    def _build_content(self) -> str:
        parts = [
            f"Title: {self.title}",
            f"Type: {self.asset_type}",
            f"URL: {self.url}",
        ]
        if self.notes:
            parts.append(f"Notes: {self.notes}")
        return "\n".join(parts)


class SessionLog(_MemoryBase):
    category: str = "session_log"
    relevance_boost: float = 1.2

    codename: str
    summary: str
    date: str

    @model_validator(mode="after")
    def set_pipeline(self) -> "SessionLog":
        self.pipeline = self.codename
        self.entity_ref = f"project:{self.codename}"
        return self

    def _build_content(self) -> str:
        return f"[{self.date}] {self.codename}: {self.summary}"
