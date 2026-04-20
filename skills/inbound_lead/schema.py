"""Pydantic data contracts for the inbound lead routine."""
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field


class InboundPayload(BaseModel):
    """Shape of the body n8n posts to /run-async for task_type=inbound_lead."""
    name: str
    email: EmailStr
    company: Optional[str] = None
    booking_id: str
    meeting_time: Optional[datetime] = None
    source: Literal["calendly", "formspree"]
    notion_row_id: Optional[str] = None
    raw_company_url: Optional[str] = None


class ResearchBrief(BaseModel):
    """Researcher agent output. Internal only; never shown verbatim to the prospect."""
    company_domain: Optional[str] = None
    what_they_do: str
    industry_signals: list[str] = Field(default_factory=list, max_length=5)
    likely_friction: list[str] = Field(default_factory=list, max_length=3)
    conversation_hooks: list[str] = Field(default_factory=list, max_length=3)
    lens_entry_point: str
    sources: list[str] = Field(default_factory=list)
    research_confidence: Literal["high", "medium", "low", "none"]
    notes: Optional[str] = None


class DraftedEmail(BaseModel):
    """Voice drafter agent output."""
    subject: str = Field(max_length=60)
    body_markdown: str
    tone_note: Optional[str] = None


class LogResult(BaseModel):
    """Logger output: what got written to Notion and Gmail.

    All fields optional so the logger can degrade: Gmail drafts can fail,
    Notion writes can fail, neither prevents the routine from reporting
    partial progress.
    """
    notion_page_id: Optional[str] = None
    notion_row_url: Optional[str] = None
    gmail_draft_id: Optional[str] = None
    gmail_draft_url: Optional[str] = None
    fields_written: list[str] = Field(default_factory=list)
    fields_skipped: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class InboundRoutineResult(BaseModel):
    """Final artifact produced by the routine runner."""
    status: Literal["enriched", "rebook_update", "partial", "failed"]
    payload: InboundPayload
    brief: Optional[ResearchBrief] = None
    email: Optional[DraftedEmail] = None
    log: Optional[LogResult] = None
    telegram_sent: bool = False
    error: Optional[str] = None
