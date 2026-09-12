"""The 6 benchmark prompt templates (spec section 8).

Every candidate model gets the exact same prompt text for a given task so
that prompt-wording differences don't confound the model comparison (spec
section 8: "프롬프트 차이 때문에 모델 성능 비교가 왜곡되지 않도록 한다").
"""
from __future__ import annotations

from research_os.evaluation.dataset import BenchmarkCase

TASK1_CLASSIFICATION = """Classify this paper abstract. Return ONLY a JSON object with keys:
industry, technology, problem.

Title: {title}
Abstract: {abstract}
"""

TASK2_KOREAN_SUMMARY = """다음 기술 초록을 분석하여 한국어로 JSON 형식으로만 출력하라.
키: problem, method, result, limitation (모두 한국어 문장).

제목: {title}
초록: {abstract}
"""

TASK3_KEYWORD_EXTRACTION = """Extract 5 to 10 technical keywords from this abstract.
Return ONLY a JSON array of strings.

Title: {title}
Abstract: {abstract}
"""

TASK4_BATTERY_RELEVANCE = """Assess this document's relevance to Battery Manufacturing.
Return ONLY a JSON object with keys: score (0-5 integer), reason, candidate_process,
candidate_equipment. Be conservative — if it's not about batteries, score should be low.

Title: {title}
Abstract: {abstract}
"""

TASK5_TRANSFERABILITY = """Assess whether the technology in this document (from another industry)
could transfer to Battery Manufacturing. Return ONLY a JSON object with keys:
source_industry, technology, target_battery_process, target_equipment,
transfer_score (0-100 integer), reason. Do not invent facts not in the text.

Title: {title}
Abstract: {abstract}
"""

TASK6_REASONING = (
    "질문: 다른 산업의 예지보전(predictive maintenance) 기술을 배터리 제조설비에 "
    "적용할 때 가장 큰 기술적 장애요인은 무엇인가? 근거를 들어 설명하라."
)


def build_prompt(task_key: str, case: BenchmarkCase) -> str:
    templates = {
        "classification": TASK1_CLASSIFICATION,
        "korean_summary": TASK2_KOREAN_SUMMARY,
        "keyword_extraction": TASK3_KEYWORD_EXTRACTION,
        "battery_relevance": TASK4_BATTERY_RELEVANCE,
        "transferability": TASK5_TRANSFERABILITY,
        "reasoning": TASK6_REASONING,
    }
    template = templates[task_key]
    if task_key == "reasoning":
        return template
    return template.format(title=case.title, abstract=case.abstract)


TASK_KEYS = ["classification", "korean_summary", "keyword_extraction", "battery_relevance", "transferability", "reasoning"]
