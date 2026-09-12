"""SQLAlchemy ORM models.

Table set follows the design in docs/architecture.md / build spec section 25.
Phase 1 actively populates: documents, scores, llm_runs.
Later phases populate: transfer_opportunities, knowledge_nodes/edges,
skills, skill_evidence, model_benchmarks, reports. Tables are created now
so the schema doesn't need migration churn as phases land.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _now() -> dt.datetime:
    return dt.datetime.utcnow()


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    source_type: Mapped[str] = mapped_column(String(50))  # arxiv/rss/github/manual
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class Industry(Base):
    __tablename__ = "industries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    priority: Mapped[int] = mapped_column(Integer, default=1)


class Technology(Base):
    __tablename__ = "technologies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # --- Required (spec section 19) ---
    external_id: Mapped[str] = mapped_column(String(300), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50))
    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    collected_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    authors: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded list
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    technology: Mapped[str | None] = mapped_column(String(100), nullable=True)
    problem: Mapped[str | None] = mapped_column(String(100), nullable=True)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Battery ---
    battery_relevance: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_process: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_equipment: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # --- Analysis ---
    key_findings: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    practical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    novelty_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- Transfer ---
    transferability: Mapped[float | None] = mapped_column(Float, nullable=True)
    candidate_process: Mapped[str | None] = mapped_column(String(100), nullable=True)
    candidate_equipment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expected_benefit: Mapped[str | None] = mapped_column(Text, nullable=True)
    implementation_difficulty: Mapped[str | None] = mapped_column(String(50), nullable=True)
    risk: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Research ---
    research_questions: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    knowledge_gaps: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_items: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list

    # --- Operational ---
    privacy_level: Mapped[str] = mapped_column(String(20), default="public")
    status: Mapped[str] = mapped_column(String(30), default="collected")
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    processing_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    processing_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # --- Deduplication helpers ---
    doi: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    arxiv_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    github_url: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    normalized_title: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    scores: Mapped[list["Score"]] = relationship(back_populates="document")


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    battery_relevance: Mapped[float] = mapped_column(Float, default=0.0)
    transferability: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_quality: Mapped[float] = mapped_column(Float, default=0.0)
    practical_applicability: Mapped[float] = mapped_column(Float, default=0.0)
    novelty: Mapped[float] = mapped_column(Float, default=0.0)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    priority: Mapped[str] = mapped_column(String(20), default="archive")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    document: Mapped["Document"] = relationship(back_populates="scores")


class DocumentTag(Base):
    __tablename__ = "document_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    tag_type: Mapped[str] = mapped_column(String(20))  # industry/technology/problem
    tag_key: Mapped[str] = mapped_column(String(100))


class TransferOpportunity(Base):
    __tablename__ = "transfer_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    source_industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_technology: Mapped[str | None] = mapped_column(String(100), nullable=True)
    original_problem: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_application: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_battery_process: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_equipment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    required_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_sensors: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_benefit: Mapped[str | None] = mapped_column(Text, nullable=True)
    implementation_difficulty: Mapped[str | None] = mapped_column(String(50), nullable=True)
    risk: Mapped[str | None] = mapped_column(Text, nullable=True)
    transfer_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    research_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_type: Mapped[str] = mapped_column(String(50))  # industry/process/equipment/sensor/...
    key: Mapped[str] = mapped_column(String(200))
    label: Mapped[str] = mapped_column(String(300))

    __table_args__ = (UniqueConstraint("node_type", "key", name="uq_node_type_key"),)


class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_node_id: Mapped[int] = mapped_column(ForeignKey("knowledge_nodes.id"))
    target_node_id: Mapped[int] = mapped_column(ForeignKey("knowledge_nodes.id"))
    relation: Mapped[str] = mapped_column(String(100), default="related_to")
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(150), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    parent_key: Mapped[str | None] = mapped_column(String(150), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=0)  # 0-5, see spec section 27
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class SkillEvidence(Base):
    __tablename__ = "skill_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_key: Mapped[str] = mapped_column(String(150))
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


class LLMRun(Base):
    """Observability record for every LLM call (spec section 43)."""

    __tablename__ = "llm_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    agent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    task: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tier: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(150), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="ok")  # ok/fallback/error/cache_hit
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    ram_usage_mb: Mapped[float | None] = mapped_column(Float, nullable=True)
    vram_usage_mb: Mapped[float | None] = mapped_column(Float, nullable=True)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)


class LLMCache(Base):
    """Response cache keyed on (provider, model, prompt, system, max_tokens,
    temperature) — spec section 15: never repeat an identical call."""

    __tablename__ = "llm_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cache_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(150))
    response_text: Mapped[str] = mapped_column(Text)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


class ModelBenchmark(Base):
    __tablename__ = "model_benchmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    task: Mapped[str] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)  # benchmark dataset category
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(150))
    role_hint: Mapped[str | None] = mapped_column(String(30), nullable=True)  # local_fast/standard/reasoning candidate
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    korean_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    technical_accuracy_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    resource_efficiency_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    stability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    composite_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fast_task_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasoning_task_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    token_usage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    ram_usage_mb: Mapped[float | None] = mapped_column(Float, nullable=True)
    vram_usage_mb: Mapped[float | None] = mapped_column(Float, nullable=True)
    disk_size_mb: Mapped[float | None] = mapped_column(Float, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    failure_rate: Mapped[float | None] = mapped_column(Float, nullable=True)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_type: Mapped[str] = mapped_column(String(20))  # daily/weekly/research
    title: Mapped[str] = mapped_column(String(300))
    path: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
