"""DRAFT for skills/score_request/schema.py.

Pre-staged 2026-04-30. Do not import from production code yet. Move to
skills/score_request/schema.py during the Friday build.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class ScoreRequestPayload(BaseModel):
    """Shape of the body n8n posts to /score-request when geolisted.co form fires."""

    name: str = Field(min_length=1, max_length=120)
    business: str = Field(min_length=1, max_length=200)
    email: EmailStr
    city: str = Field(min_length=1, max_length=120)
    niche: str = Field(min_length=1, max_length=120)
    website_url: Optional[str] = None
    source: str = "geolisted.co - Score Request"


class ScoreBreakdown(BaseModel):
    chatgpt: bool
    perplexity: bool
    robots_ok: bool
    maps_present: bool


class ScoreResult(BaseModel):
    """What the /score-request endpoint returns to n8n (and through to the browser)."""

    score: int = Field(ge=0, le=100)
    breakdown: ScoreBreakdown
    quick_wins: list[str] = Field(default_factory=list, max_length=3)
    business: str
    city: str
    niche: str
    lead_id: Optional[str] = None
    email_status: str = Field(default="pending")
