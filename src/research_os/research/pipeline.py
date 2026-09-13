"""The Phase 1 research pipeline (spec section 23):

COLLECT -> NORMALIZE -> DEDUPLICATE -> CLASSIFY -> EXTRACT -> SUMMARIZE ->
SCORE -> BATTERY RELEVANCE -> TRANSFER ANALYSIS -> STORE -> REPORT

Each stage is independently callable (`run_classify`, `run_summarize`,
`run_analyze`, `run_transfer`) so `research-os classify` etc. can be run on
their own; `run_full_pipeline` chains everything for `research-os run`. A
failure on one document never stops the batch (spec section 44).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_os.agents.analyst import AnalystAgent
from research_os.agents.classifier import ClassifierAgent
from research_os.agents.discovery import DiscoveryAgent
from research_os.agents.qa import QAAgent
from research_os.agents.summarizer import SummarizerAgent
from research_os.agents.transfer import TransferAgent
from research_os.core.logging_setup import get_logger
from research_os.core.schema import ResearchItem
from research_os.database.db import session_scope
from research_os.database.models import Document, Score, TransferOpportunity
from research_os.models.gateway import ModelGateway
from research_os.processing.deduplicate import find_existing
from research_os.processing.normalize import normalize_item
from research_os.scoring.scorer import ScoreInput, compute_score

logger = get_logger("pipeline")


@dataclass
class PipelineStats:
    discovered: int = 0
    duplicates: int = 0
    new_documents: int = 0
    processed: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- COLLECT --

def collect_and_store(source: str | None = None) -> PipelineStats:
    """COLLECT -> NORMALIZE -> DEDUPLICATE -> STORE (status=collected)."""
    stats = PipelineStats()
    discovery = DiscoveryAgent()
    raw_items = discovery.discover(source=source)
    stats.discovered = len(raw_items)

    with session_scope() as session:
        for raw in raw_items:
            try:
                item = normalize_item(raw)
            except Exception as exc:  # noqa: BLE001
                stats.failed += 1
                stats.errors.append(f"normalize failed: {exc}")
                continue

            if find_existing(session, item) is not None:
                stats.duplicates += 1
                continue

            session.add(_item_to_document(item))
            stats.new_documents += 1

    logger.info(
        "collect: discovered=%d new=%d duplicates=%d failed=%d",
        stats.discovered, stats.new_documents, stats.duplicates, stats.failed,
    )
    return stats


def _item_to_document(item: ResearchItem) -> Document:
    return Document(
        external_id=item.id,
        title=item.title,
        url=item.url,
        source=item.source,
        source_type=item.source_type,
        published_at=item.published_at,
        collected_at=item.collected_at,
        authors=json.dumps(item.authors),
        abstract=item.abstract,
        content=item.content,
        keywords=json.dumps(item.keywords),
        privacy_level=item.privacy_level,
        status="collected",
        doi=item.doi,
        arxiv_id=item.arxiv_id,
        github_url=item.github_url,
        normalized_title=item.normalized_title,
        content_hash=item.content_hash,
    )


def _document_to_item(doc: Document) -> ResearchItem:
    # Round-trips every field a later stage might need to read back, not
    # just the ones the earliest (classify) stage needed — TransferAgent
    # reads target_process from ClassifierAgent's output, and QAAgent reads
    # summary/scores/key_findings from Summarizer/Analyst; leaving any of
    # those out here would silently make the later stage see None for
    # already-computed data instead of an actual DB round-trip.
    return ResearchItem(
        id=doc.external_id,
        title=doc.title,
        url=doc.url,
        source=doc.source,
        source_type=doc.source_type,
        published_at=doc.published_at,
        collected_at=doc.collected_at,
        authors=json.loads(doc.authors) if doc.authors else [],
        abstract=doc.abstract,
        content=doc.content,
        industry=doc.industry,
        technology=doc.technology,
        problem=doc.problem,
        keywords=json.loads(doc.keywords) if doc.keywords else [],
        summary=doc.summary,
        battery_relevance=doc.battery_relevance,
        target_process=doc.target_process,
        target_equipment=doc.target_equipment,
        key_findings=json.loads(doc.key_findings) if doc.key_findings else [],
        limitations=doc.limitations,
        evidence_score=doc.evidence_score,
        practical_score=doc.practical_score,
        novelty_score=doc.novelty_score,
        transferability=doc.transferability,
        candidate_process=doc.candidate_process,
        candidate_equipment=doc.candidate_equipment,
        expected_benefit=doc.expected_benefit,
        implementation_difficulty=doc.implementation_difficulty,
        risk=doc.risk,
        research_questions=json.loads(doc.research_questions) if doc.research_questions else [],
        knowledge_gaps=doc.knowledge_gaps,
        related_items=json.loads(doc.related_items) if doc.related_items else [],
        qa_status=doc.qa_status,
        qa_flags=json.loads(doc.qa_flags) if doc.qa_flags else [],
        privacy_level=doc.privacy_level,
        status=doc.status,
        model_used=doc.model_used,
        processing_status=doc.processing_status,
        doi=doc.doi,
        arxiv_id=doc.arxiv_id,
        github_url=doc.github_url,
        normalized_title=doc.normalized_title,
        content_hash=doc.content_hash,
    )


def _iterate(
    session: Session, predicate, limit: int | None, handler: Callable[[Document], None], stats: PipelineStats,
) -> list[Document]:
    """Runs `handler` on every Document matching `predicate`, tracking
    stats, and returns the documents it actually succeeded on — so a
    caller that needs to do more work on just this batch (e.g. rescoring)
    doesn't have to re-scan/re-filter the whole table again."""
    touched: list[Document] = []
    stmt = select(Document)
    if limit:
        stmt = stmt.limit(limit)
    for doc in session.scalars(stmt).all():
        if not predicate(doc):
            continue
        try:
            handler(doc)
            stats.processed += 1
            touched.append(doc)
        except Exception as exc:  # noqa: BLE001 - one bad doc must not stop the batch
            doc.processing_status = "error"
            stats.failed += 1
            stats.errors.append(f"doc={doc.external_id} error={exc}")
            logger.error("stage failed for %s: %s", doc.external_id, exc)
    return touched


# --------------------------------------------------------------- CLASSIFY --

def run_classify(use_llm: bool = True, limit: int | None = None) -> PipelineStats:
    stats = PipelineStats()
    gateway = ModelGateway() if use_llm else None
    classifier = ClassifierAgent(gateway)

    def handler(doc: Document) -> None:
        item = _document_to_item(doc)
        classification = classifier.classify(item)
        doc.industry = classification.get("industry")
        doc.technology = classification.get("technology")
        doc.problem = classification.get("problem")
        doc.keywords = json.dumps(classification.get("keywords") or [])
        doc.target_process = classification.get("target_process")
        doc.model_used = classification.get("model_used")

    with session_scope() as session:
        _iterate(session, lambda d: d.industry is None, limit, handler, stats)
    logger.info("classify: processed=%d failed=%d", stats.processed, stats.failed)
    return stats


# -------------------------------------------------------- SUMMARIZE/EXTRACT --

def run_summarize(use_llm: bool = True, limit: int | None = None) -> PipelineStats:
    stats = PipelineStats()
    gateway = ModelGateway() if use_llm else None
    summarizer = SummarizerAgent(gateway)

    def handler(doc: Document) -> None:
        item = _document_to_item(doc)
        summary = summarizer.summarize(item)
        doc.summary = summary.get("summary")
        doc.limitations = summary.get("limitation") or summary.get("limitations")

    with session_scope() as session:
        _iterate(session, lambda d: d.summary is None, limit, handler, stats)
    logger.info("summarize: processed=%d failed=%d", stats.processed, stats.failed)
    return stats


# ------------------------------------------------------------------ ANALYZE --

def _recompute_scores(session: Session, docs: list[Document]) -> None:
    """Recompute and upsert the Score row for each of `docs` that has been
    analyzed (evidence_score set) — batching the "does a Score row already
    exist" lookup into one query instead of one per document."""
    relevant = [d for d in docs if d.evidence_score is not None]
    if not relevant:
        return

    existing_by_doc_id = {
        s.document_id: s
        for s in session.scalars(select(Score).where(Score.document_id.in_(d.id for d in relevant))).all()
    }

    for doc in relevant:
        score_result = compute_score(
            ScoreInput(
                battery_relevance=doc.battery_relevance or 0.0,
                transferability=doc.transferability or 0.0,
                evidence_quality=doc.evidence_score or 0.0,
                practical_applicability=doc.practical_score or 0.0,
                novelty=doc.novelty_score or 0.0,
            )
        )
        existing = existing_by_doc_id.get(doc.id)
        if existing is None:
            existing = Score(document_id=doc.id)
            session.add(existing)
        existing.battery_relevance = doc.battery_relevance or 0.0
        existing.transferability = doc.transferability or 0.0
        existing.evidence_quality = doc.evidence_score or 0.0
        existing.practical_applicability = doc.practical_score or 0.0
        existing.novelty = doc.novelty_score or 0.0
        existing.overall_score = score_result.overall_score
        existing.priority = score_result.priority


def run_analyze(use_llm: bool = True, limit: int | None = None) -> PipelineStats:
    """AnalystAgent + BATTERY RELEVANCE + SCORE (spec sections 20/32)."""
    stats = PipelineStats()
    gateway = ModelGateway() if use_llm else None
    analyst = AnalystAgent(gateway)

    def handler(doc: Document) -> None:
        item = _document_to_item(doc)
        analysis = analyst.analyze(item)
        doc.evidence_score = analysis.get("evidence_score")
        doc.practical_score = analysis.get("practical_score")
        doc.novelty_score = analysis.get("novelty_score")
        doc.battery_relevance = analysis.get("battery_relevance")
        doc.key_findings = json.dumps(analysis.get("key_findings") or [])
        doc.model_used = analysis.get("model_used") or doc.model_used

    with session_scope() as session:
        touched = _iterate(session, lambda d: d.evidence_score is None, limit, handler, stats)
        _recompute_scores(session, touched)
    logger.info("analyze: processed=%d failed=%d", stats.processed, stats.failed)
    return stats


# ----------------------------------------------------------------- TRANSFER --

def run_transfer(use_llm: bool = True, limit: int | None = None) -> PipelineStats:
    stats = PipelineStats()
    gateway = ModelGateway() if use_llm else None
    transfer_agent = TransferAgent(gateway)

    def handler(doc: Document) -> None:
        item = _document_to_item(doc)
        transfer = transfer_agent.analyze_transfer(item)
        if transfer is None:
            doc.transferability = doc.transferability or 0.0
            return
        confidence = float(transfer.get("transfer_confidence") or 0.0)
        doc.transferability = confidence
        doc.candidate_process = transfer.get("target_battery_process")
        doc.candidate_equipment = transfer.get("target_equipment")
        doc.expected_benefit = transfer.get("expected_benefit")
        doc.implementation_difficulty = transfer.get("implementation_difficulty")
        doc.risk = transfer.get("risk")
        session.add(
            TransferOpportunity(
                document_id=doc.id,
                source_industry=doc.industry,
                source_technology=doc.technology,
                target_battery_process=transfer.get("target_battery_process"),
                target_equipment=transfer.get("target_equipment"),
                expected_benefit=transfer.get("expected_benefit"),
                implementation_difficulty=transfer.get("implementation_difficulty"),
                risk=transfer.get("risk"),
                transfer_confidence=confidence,
                research_question=transfer.get("research_question"),
            )
        )

    with session_scope() as session:
        touched = _iterate(session, lambda d: d.transferability is None and d.industry is not None, limit, handler, stats)
        _recompute_scores(session, touched)
    logger.info("transfer: processed=%d failed=%d", stats.processed, stats.failed)
    return stats


# ----------------------------------------------------------------------- QA --

def run_qa_check(limit: int | None = None) -> PipelineStats:
    """QA_CHECK (spec section 21/44 — grounding check, flags don't block):
    runs after summarize/analyze/transfer, before STORE, so a flagged
    document still reaches `mark_analyzed` like any other."""
    stats = PipelineStats()
    qa_agent = QAAgent()

    def handler(doc: Document) -> None:
        item = _document_to_item(doc)
        result = qa_agent.check(item)
        doc.qa_status = result["qa_status"]
        doc.qa_flags = json.dumps(result["qa_flags"])

    with session_scope() as session:
        _iterate(
            session,
            lambda d: d.qa_status is None and d.summary is not None and d.evidence_score is not None,
            limit, handler, stats,
        )
    logger.info("qa_check: processed=%d failed=%d", stats.processed, stats.failed)
    return stats


def mark_analyzed(session: Session | None = None) -> int:
    """Mark documents that have completed classify+summarize+analyze as
    status=analyzed (STORE stage, spec section 23), and fold them into the
    knowledge graph (spec section 26)."""
    from research_os.knowledge.graph import ingest_document

    count = 0

    def _mark(sess: Session) -> None:
        nonlocal count
        for doc in sess.scalars(select(Document)).all():
            if doc.industry and doc.summary and doc.evidence_score is not None and doc.status != "analyzed":
                doc.status = "analyzed"
                doc.processing_status = doc.processing_status or "ok"
                ingest_document(sess, doc)
                count += 1

    if session is not None:
        _mark(session)
    else:
        with session_scope() as sess:
            _mark(sess)
    return count


def run_full_pipeline(source: str | None = None, use_llm: bool = True) -> dict[str, Any]:
    collect_stats = collect_and_store(source=source)
    classify_stats = run_classify(use_llm=use_llm)
    summarize_stats = run_summarize(use_llm=use_llm)
    analyze_stats = run_analyze(use_llm=use_llm)
    transfer_stats = run_transfer(use_llm=use_llm)
    qa_stats = run_qa_check()
    stored = mark_analyzed()
    return {
        "collect": collect_stats,
        "classify": classify_stats,
        "summarize": summarize_stats,
        "analyze": analyze_stats,
        "transfer": transfer_stats,
        "qa": qa_stats,
        "stored": stored,
    }
