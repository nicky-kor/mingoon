"""Rule-based classifier (spec section 15-18, 30).

This is the deterministic fallback used when no LLM is available (no
Ollama, no cloud API key) so the pipeline always produces a classification.
`agents/classifier.py` wraps this and additionally tries an LLM first when
one is configured.
"""
from __future__ import annotations

from research_os.core.config import battery_config, problems_config, technologies_config

# Minimal keyword hints for non-battery industries. Kept small and easy to
# extend; battery keywords live in config/battery.yaml since that taxonomy
# is much richer (spec section 16).
_INDUSTRY_KEYWORDS = {
    "semiconductor": ["semiconductor", "wafer", "lithography", "fab ", "etching"],
    "automotive": ["automotive", "vehicle", "engine", "powertrain", "adas"],
    "steel": ["steel mill", "blast furnace", "rolling mill", "steelmaking"],
    "chemical": ["chemical plant", "chemical process", "distillation"],
    "petrochemical": ["petrochemical", "refinery", "cracking unit"],
    "energy": ["power grid", "renewable energy", "solar farm", "wind turbine"],
    "power_generation": ["power plant", "turbine generator", "power generation"],
    "shipbuilding": ["shipyard", "shipbuilding", "hull welding"],
    "machinery": ["cnc machine", "machine tool"],
    "aerospace": ["aerospace", "aircraft", "jet engine"],
    "food": ["food processing", "food safety"],
    "pharmaceutical": ["pharmaceutical", "drug manufacturing", "gmp"],
    "logistics": ["warehouse", "supply chain", "logistics"],
    "mining": ["mining", "ore extraction"],
}

# Strong, battery-*specific* identity terms (materials/cell terminology).
# Deliberately does NOT reuse config/battery.yaml's process keywords
# (coating, rolling mill, welding, ...): those name equipment/processes that
# are shared with other industries (e.g. steel rolling mills), and are used
# by classify_battery_process()/TransferAgent to find a *transfer target*,
# not to decide the source document's own industry (spec section 4: a
# steel rolling-mill paper must stay industry=steel so it can be evaluated
# as a transfer candidate, not be mislabeled as battery_manufacturing).
_BATTERY_IDENTITY_TERMS = [
    "battery", "lithium-ion", "li-ion", "lithium ion", "cathode", "anode",
    "electrolyte", "gigafactory", "battery cell", "battery pack", "battery manufacturing",
    "cell manufacturing", "nmc", "lfp cell", "separator film",
]


def _text_of(title: str, abstract: str | None) -> str:
    return f"{title} {abstract or ''}".lower()


def classify_industry(title: str, abstract: str | None) -> str:
    text = _text_of(title, abstract)
    if any(term.lower() in text for term in _BATTERY_IDENTITY_TERMS):
        return "battery_manufacturing"
    for industry_key, terms in _INDUSTRY_KEYWORDS.items():
        if any(term.lower() in text for term in terms):
            return industry_key
    return "general_manufacturing"


def _best_keyword_match(text: str, candidates: list[tuple[str, list[str]]]) -> str | None:
    """Returns the candidate key with the most keyword hits in `text`
    (ties keep whichever candidate was seen first), or None if nothing
    matched at all. Shared by classify_technology/problem/battery_process
    below — they differ only in where their (key, keywords) pairs come
    from."""
    best_key, best_hits = None, 0
    for key, keywords in candidates:
        hits = sum(1 for kw in keywords if kw.lower() in text)
        if hits > best_hits:
            best_key, best_hits = key, hits
    return best_key


def classify_technology(title: str, abstract: str | None) -> str | None:
    text = _text_of(title, abstract)
    candidates = [(t["id"], t.get("keywords", [])) for t in technologies_config().get("technologies", [])]
    return _best_keyword_match(text, candidates)


def classify_problem(title: str, abstract: str | None) -> str | None:
    text = _text_of(title, abstract)
    candidates = [(p["id"], p.get("keywords", [])) for p in problems_config().get("problems", [])]
    return _best_keyword_match(text, candidates)


def classify_battery_process(title: str, abstract: str | None) -> str | None:
    text = _text_of(title, abstract)
    return _best_keyword_match(text, list(battery_config().get("keywords", {}).items()))


def extract_keywords(title: str, abstract: str | None, top_n: int = 8) -> list[str]:
    """Very small keyword extractor: frequent non-stopword tokens."""
    import re
    from collections import Counter

    stopwords = {
        "the", "a", "an", "of", "and", "or", "in", "on", "for", "to", "with",
        "is", "are", "this", "that", "we", "our", "by", "as", "using", "based",
        "from", "at", "be", "can", "which", "such", "into", "its", "it",
    }
    text = _text_of(title, abstract)
    tokens = re.findall(r"[a-z][a-z0-9\-]{2,}", text)
    tokens = [t for t in tokens if t not in stopwords]
    counts = Counter(tokens)
    return [word for word, _ in counts.most_common(top_n)]
