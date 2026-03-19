"""core/impact_scorer.py – Multi-dimensional impact scoring for SDG resources."""
import math
from datetime import datetime


SDG_WEIGHT = {1:0.9, 2:0.9, 3:0.95, 4:0.85, 5:0.8, 6:0.88, 7:0.92, 8:0.82,
              9:0.78, 10:0.85, 11:0.8, 12:0.82, 13:0.95, 14:0.88, 15:0.88,
              16:0.85, 17:0.75}

TYPE_CREDIBILITY = {
    "UN Initiative": 1.0, "Framework": 0.95, "Research": 0.9,
    "Platform": 0.85, "Company": 0.80, "Program": 0.85,
    "Tool": 0.75, "Website": 0.70,
}

REGION_COVERAGE = {
    "Global": 1.0, "Africa, Asia": 0.85, "Sub-Saharan Africa": 0.8,
    "South Asia": 0.8, "Europe": 0.75, "North America": 0.7,
    "Europe, Global": 0.95, "Middle East, South Asia": 0.78,
    "Asia": 0.75, "Africa": 0.8, "West Africa": 0.72,
    "Asia, Africa": 0.82, "Middle East": 0.72, "LatAm": 0.72,
    "Africa, Asia, LatAm": 0.85,
}

# keywords that signal strong deployment/scale
SCALE_KEYWORDS = [
    "million", "billion", "M+", "B+", "countries", "global", "national",
    "government", "UN", "deployed", "used by", "serving", "users",
    "hospitals", "facilities", "raised", "Series", "awarded",
]
RECENCY_KEYWORDS = ["2024", "2025", "2026", "COP30", "latest", "new"]


def score_resource(r: dict) -> float:
    """
    Returns an impact score 0–100 based on:
    1. SDG coverage breadth & priority weights
    2. Resource type credibility
    3. Recency (more recent = higher)
    4. Scale signals from text
    5. Regional coverage
    6. Multi-SDG bonus
    """
    sdgs = r.get("sdgs", [])
    if not sdgs:
        return 0.0

    # 1. SDG contribution score (avg priority weight of mapped SDGs, 0-1)
    sdg_score = sum(SDG_WEIGHT.get(s, 0.7) for s in sdgs) / max(len(sdgs), 1)

    # 2. Multi-SDG breadth bonus (up to +20%)
    breadth_bonus = min(len(sdgs) - 1, 5) * 0.04  # 4% per additional SDG

    # 3. Credibility from resource type
    credibility = TYPE_CREDIBILITY.get(r.get("type", ""), 0.70)

    # 4. Recency score (newer = higher, decay over 15 years)
    current_year = datetime.utcnow().year
    year = r.get("year") or 2015
    age = max(current_year - year, 0)
    recency = math.exp(-age / 15)  # e^(-age/15) → newer resources score higher

    # 5. Scale signals from description + how text
    combined_text = f"{r.get('description','')} {r.get('how','')} {r.get('tags','')}".lower()
    scale_hits = sum(1 for kw in SCALE_KEYWORDS if kw.lower() in combined_text)
    scale_score = min(scale_hits / 6.0, 1.0)

    # 6. Recency keywords boost
    recency_boost = 0.05 if any(kw in combined_text for kw in RECENCY_KEYWORDS) else 0

    # 7. Regional coverage
    region_score = REGION_COVERAGE.get(r.get("region", "Global"), 0.7)

    # Weighted composite
    raw = (
        sdg_score         * 0.25 +
        breadth_bonus     * 0.10 +
        credibility       * 0.20 +
        recency           * 0.15 +
        scale_score       * 0.20 +
        region_score      * 0.10 +
        recency_boost
    )

    # Normalize to 0-100, round to 1 decimal
    return round(min(raw * 100, 100), 1)


def score_all(resources: list[dict]) -> list[dict]:
    """Add impact_score field to each resource dict in place."""
    for r in resources:
        r["impact_score"] = score_resource(r)
    return resources


def get_score_breakdown(r: dict) -> dict:
    """Return scoring breakdown for transparency."""
    sdgs = r.get("sdgs", [])
    current_year = datetime.utcnow().year
    year = r.get("year") or 2015
    age = max(current_year - year, 0)
    combined = f"{r.get('description','')} {r.get('how','')} {r.get('tags','')}".lower()
    scale_hits = sum(1 for kw in SCALE_KEYWORDS if kw.lower() in combined)

    return {
        "sdg_priority_avg": round(sum(SDG_WEIGHT.get(s, 0.7) for s in sdgs) / max(len(sdgs),1), 2),
        "multi_sdg_bonus": min(len(sdgs) - 1, 5) * 4,
        "type_credibility": round(TYPE_CREDIBILITY.get(r.get("type",""), 0.70) * 100),
        "recency_score": round(math.exp(-age/15) * 100),
        "scale_signals": scale_hits,
        "regional_coverage": round(REGION_COVERAGE.get(r.get("region","Global"), 0.7) * 100),
        "final_score": score_resource(r),
    }
