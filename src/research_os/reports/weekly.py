"""Weekly Industrial AI Briefing (spec section 38)."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_os.agents.briefing import BriefingAgent
from research_os.agents.trend import TrendAgent
from research_os.core.paths import resolve
from research_os.core.timeutils import utc_now
from research_os.database.models import TransferOpportunity
from research_os.knowledge.skills import LEVEL_LABELS, list_skills
from research_os.models.gateway import ModelGateway
from research_os.reports._shared import fetch_scored_documents


def generate_weekly_report(session: Session, use_llm: bool = True) -> str:
    now = utc_now()
    since = now - dt.timedelta(days=7)

    scored = fetch_scored_documents(session, since)

    trend = TrendAgent().analyze(session, window_days=7)
    transfers = session.scalars(select(TransferOpportunity).where(TransferOpportunity.created_at >= since)).all()
    skills = list_skills(session)

    gateway = ModelGateway() if use_llm else None
    briefing = BriefingAgent(gateway)
    facts = [f"{len(scored)} documents collected this week", f"top technologies: {trend['top_technologies']}"]
    summary = briefing.executive_summary(facts)

    battery_docs = [d for d, _ in scored if d.industry == "battery_manufacturing"]
    pm_docs = [d for d, _ in scored if d.problem in ("fault_diagnosis", "rul_estimation", "condition_monitoring")]

    lines = [
        f"# Weekly Industrial AI Briefing — {since.date()} to {now.date()}",
        "",
        "## 1. Executive Summary",
        summary,
        "",
        "## 2. Battery Manufacturing",
    ]
    lines += [f"- {d.title}" for d in battery_docs] or ["- No battery-specific items this week."]

    lines += ["", "## 3. Predictive Maintenance"]
    lines += [f"- {d.title}" for d in pm_docs] or ["- No predictive-maintenance items this week."]

    lines += ["", "## 4. Manufacturing AI"]
    lines += [f"- {d.title}" for d, _ in scored[:10]] or ["- No documents this week."]

    lines += ["", "## 5. AI Technology Trends"]
    lines += [f"- {tech}: {count}" for tech, count in trend["top_technologies"]] or ["- No trend data yet."]

    lines += ["", "## 6. Cross-Industry Transfer Radar"]
    lines += [
        f"- {t.source_industry} → {t.target_battery_process} (confidence {t.transfer_confidence:.0f}): {t.research_question}"
        for t in transfers
    ] or ["- No transfer opportunities identified this week."]

    lines += ["", "## 7. Important Papers"]
    lines += [f"- {d.title} ({d.url})" for d, _ in scored if d.source_type == "arxiv"][:10] or ["- None."]

    lines += ["", "## 8. Important GitHub Projects"]
    lines += [f"- {d.title} ({d.url})" for d, _ in scored if d.source_type == "github"][:10] or ["- None."]

    lines += ["", "## 9. Emerging Technologies"]
    lines += [f"- {tech}" for tech, count in trend["top_technologies"] if count == 1][:5] or ["- Not enough data yet."]

    lines += ["", "## 10. Recommended Reading"]
    lines += [f"- {d.title} ({d.url})" for d, s in scored if s and s.priority in ("Critical", "High")][:5] or ["- None flagged this week."]

    lines += ["", "## 11. Recommended Experiments"]
    lines += ["- Review the highest-confidence transfer opportunity above and scope a small feasibility check."] if transfers else ["- No experiments recommended yet — collect more data."]

    lines += ["", "## 12. Personal Skill Development"]
    lines += [f"- {s.name}: Level {s.level} ({LEVEL_LABELS.get(s.level, '?')})" for s in skills] or ["- Run `research-os init` to seed the skill graph."]

    lines += ["", "## 13. Recommended Deep Research Topics"]
    lines += [f"- {tech} applied to Battery Manufacturing" for tech, _ in trend["top_technologies"][:3]] or ["- Not enough data yet."]

    return "\n".join(lines) + "\n"


def write_weekly_report(session: Session, use_llm: bool = True) -> str:
    content = generate_weekly_report(session, use_llm=use_llm)
    today = utc_now().date().isoformat()
    out_path = resolve("data/reports") / f"{today}-weekly.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    return str(out_path)
