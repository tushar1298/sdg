"""core/recommender.py – Smart recommender for SDG resources."""
import logging
from collections import defaultdict
from core.embeddings import semantic_search, get_similar

logger = logging.getLogger(__name__)

SDG_NAMES = {
    1:"No Poverty",2:"Zero Hunger",3:"Good Health & Wellbeing",
    4:"Quality Education",5:"Gender Equality",6:"Clean Water & Sanitation",
    7:"Affordable & Clean Energy",8:"Decent Work & Economic Growth",
    9:"Industry, Innovation & Infrastructure",10:"Reduced Inequalities",
    11:"Sustainable Cities & Communities",12:"Responsible Consumption",
    13:"Climate Action",14:"Life Below Water",15:"Life on Land",
    16:"Peace, Justice & Strong Institutions",17:"Partnerships for Goals",
}


def recommend_for_query(query: str, resources: list[dict],
                        sdg_focus: list[int] | None = None,
                        preferred_types: list[str] | None = None,
                        top_k: int = 10) -> list[dict]:
    """
    Content-based recommendations from a free-text query.
    Applies SDG and type boosts on top of semantic similarity.
    """
    results = semantic_search(query, top_k=50, resources=resources,
                              sdg_filter=sdg_focus if sdg_focus else None)
    boosted = []
    for item in results:
        r = item["resource"]
        score = item["similarity"]

        # Type preference boost (+10%)
        if preferred_types and r.get("type") in preferred_types:
            score *= 1.10

        # Impact score boost (normalized 0-1 range, weight 20%)
        impact = r.get("impact_score", 50) / 100
        final = score * 0.80 + impact * 0.20
        boosted.append({"resource": r, "similarity": round(score, 4),
                        "rec_score": round(final, 4)})

    boosted.sort(key=lambda x: x["rec_score"], reverse=True)
    return boosted[:top_k]


def recommend_for_sdgs(sdg_list: list[int], resources: list[dict],
                       top_k: int = 12) -> list[dict]:
    """
    Returns top resources covering the given SDGs, sorted by coverage breadth
    then impact score.
    """
    relevant = [r for r in resources if any(s in r.get("sdgs", []) for s in sdg_list)]
    scored = []
    for r in relevant:
        overlap = len(set(r.get("sdgs", [])) & set(sdg_list))
        coverage = overlap / max(len(sdg_list), 1)
        impact = r.get("impact_score", 50) / 100
        rec_score = coverage * 0.60 + impact * 0.40
        scored.append({"resource": r, "sdg_coverage": round(coverage, 2),
                       "rec_score": round(rec_score, 4)})
    scored.sort(key=lambda x: x["rec_score"], reverse=True)
    return scored[:top_k]


def similar_resources(resource_id: int, resources: list[dict], top_k: int = 6) -> list[dict]:
    """Find semantically similar resources to a given one."""
    return get_similar(resource_id, resources, top_k=top_k)


def sdg_portfolio_gap(sdg_list: list[int], resources: list[dict]) -> dict:
    """
    Given a portfolio of SDGs the user cares about, identify which SDGs
    have the fewest high-quality resources and surface recommendations.
    """
    sdg_counts: dict[int, int] = defaultdict(int)
    sdg_scores: dict[int, list[float]] = defaultdict(list)
    for r in resources:
        for s in r.get("sdgs", []):
            sdg_counts[s] += 1
            sdg_scores[s].append(r.get("impact_score", 50))

    gaps = []
    for sdg in sdg_list:
        count = sdg_counts.get(sdg, 0)
        avg_score = sum(sdg_scores.get(sdg, [0])) / max(count, 1)
        gaps.append({
            "sdg": sdg,
            "name": SDG_NAMES.get(sdg, f"SDG {sdg}"),
            "resource_count": count,
            "avg_impact": round(avg_score, 1),
            "gap_priority": round((1 - count/max(max(sdg_counts.values(),default=1),1)) * 100, 1),
        })
    gaps.sort(key=lambda x: x["gap_priority"], reverse=True)
    return {"gaps": gaps}
