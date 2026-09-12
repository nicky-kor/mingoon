"""Canonical Research Item schema (spec section 19).

Collectors emit raw dicts; `normalize.py` turns them into a validated
`ResearchItem`. Fields are grouped exactly as in the build spec.
"""
from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field

from research_os.core.timeutils import utc_now

PrivacyLevel = Literal["public", "personal", "restricted"]
EvidenceKind = Literal["FACT", "INFERENCE", "HYPOTHESIS"]


class EvidenceStatement(BaseModel):
    """A single analytical statement, explicit about its epistemic status
    (spec section 21 — never store inference as fact)."""

    kind: EvidenceKind
    text: str


class ResearchItem(BaseModel):
    # --- Required ---
    id: str
    title: str
    url: str | None = None
    source: str
    source_type: str
    published_at: dt.datetime | None = None
    collected_at: dt.datetime = Field(default_factory=utc_now)
    authors: list[str] = Field(default_factory=list)
    abstract: str | None = None
    content: str | None = None
    industry: str | None = None
    technology: str | None = None
    problem: str | None = None
    keywords: list[str] = Field(default_factory=list)
    summary: str | None = None

    # --- Battery ---
    battery_relevance: float | None = None
    target_process: str | None = None
    target_equipment: str | None = None

    # --- Analysis ---
    key_findings: list[str] = Field(default_factory=list)
    limitations: str | None = None
    evidence_score: float | None = None
    practical_score: float | None = None
    novelty_score: float | None = None

    # --- Transfer ---
    transferability: float | None = None
    candidate_process: str | None = None
    candidate_equipment: str | None = None
    expected_benefit: str | None = None
    implementation_difficulty: str | None = None
    risk: str | None = None

    # --- Research ---
    research_questions: list[str] = Field(default_factory=list)
    knowledge_gaps: str | None = None
    related_items: list[str] = Field(default_factory=list)

    # --- Operational ---
    privacy_level: PrivacyLevel = "public"
    status: str = "collected"
    model_used: str | None = None
    processing_time: float | None = None
    processing_status: str | None = None

    # --- Dedup helpers ---
    doi: str | None = None
    arxiv_id: str | None = None
    github_url: str | None = None
    normalized_title: str | None = None
    content_hash: str | None = None
