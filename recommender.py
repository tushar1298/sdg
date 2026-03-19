"""core/embeddings.py – TF-IDF + LSA semantic search engine."""
import json
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ── SDG term expansions to improve semantic coverage ──────────────────────
SDG_SYNONYMS = {
    "poverty": ["poor", "low-income", "microfinance", "destitute", "cash transfer"],
    "hunger": ["food security", "malnutrition", "famine", "crop", "agriculture"],
    "health": ["medical", "clinical", "disease", "diagnostic", "hospital", "drug"],
    "education": ["learning", "school", "student", "curriculum", "literacy", "training"],
    "gender": ["women", "girls", "equality", "feminist", "diversity", "inclusion"],
    "water": ["sanitation", "freshwater", "aquifer", "irrigation", "hygiene", "sewage"],
    "energy": ["renewable", "solar", "wind", "electricity", "power", "grid", "battery"],
    "work": ["employment", "jobs", "labor", "economic", "growth", "GDP", "skills"],
    "industry": ["manufacturing", "infrastructure", "innovation", "tech", "startup"],
    "inequality": ["disparity", "equity", "marginalized", "excluded", "underserved"],
    "cities": ["urban", "municipal", "housing", "transport", "smart city", "planning"],
    "consumption": ["waste", "circular economy", "sustainable production", "recycling"],
    "climate": ["carbon", "emissions", "greenhouse", "global warming", "CO2", "net zero"],
    "ocean": ["marine", "fish", "sea", "coral", "plastic pollution", "IUU fishing"],
    "land": ["forest", "biodiversity", "wildlife", "deforestation", "ecosystem"],
    "peace": ["justice", "governance", "corruption", "conflict", "institution", "law"],
    "partnership": ["collaboration", "data sharing", "SDG", "financing", "cooperation"],
}

_vectorizer: TfidfVectorizer | None = None
_svd: TruncatedSVD | None = None
_matrix: np.ndarray | None = None
_resource_ids: list[int] = []


def _build_doc(r: dict) -> str:
    """Build rich text document for a resource."""
    sdg_terms = []
    for sdg in r.get("sdgs", []):
        # Inject SDG-specific vocabulary
        for kw, syns in SDG_SYNONYMS.items():
            if any(kw in (r.get("description","") + r.get("how","")).lower() for _ in [1]):
                sdg_terms.extend(syns)

    parts = [
        r.get("name", "") * 3,  # name weighted 3x
        r.get("how", "") * 2,
        r.get("description", ""),
        r.get("tags", "").replace(",", " "),
        r.get("type", ""),
        r.get("region", ""),
        " ".join(sdg_terms),
    ]
    return " ".join(filter(None, parts))


def build_index(resources: list[dict]) -> bool:
    """Build TF-IDF + LSA index from resource list. Returns True on success."""
    global _vectorizer, _svd, _matrix, _resource_ids
    if not resources:
        return False
    try:
        docs = [_build_doc(r) for r in resources]
        _resource_ids = [r["id"] for r in resources]

        _vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,
            strip_accents="unicode",
        )
        tfidf = _vectorizer.fit_transform(docs)

        # LSA: reduce to 128 dims (or less if corpus is tiny)
        n_components = min(128, tfidf.shape[0] - 1, tfidf.shape[1] - 1)
        n_components = max(n_components, 1)
        _svd = TruncatedSVD(n_components=n_components, random_state=42)
        reduced = _svd.fit_transform(tfidf)
        _matrix = normalize(reduced)
        logger.info(f"Semantic index built: {len(resources)} docs, {n_components} dims")
        return True
    except Exception as e:
        logger.error(f"Index build failed: {e}")
        return False


def semantic_search(query: str, top_k: int = 20, sdg_filter: list[int] | None = None,
                    resources: list[dict] | None = None) -> list[dict]:
    """
    Semantic search: returns list of (resource_dict, similarity_score) tuples,
    filtered and sorted by relevance.
    """
    global _vectorizer, _svd, _matrix, _resource_ids

    if _vectorizer is None or _matrix is None or not resources:
        return []

    try:
        q_tfidf = _vectorizer.transform([query])
        q_reduced = _svd.transform(q_tfidf)
        q_norm = normalize(q_reduced)

        sims = cosine_similarity(q_norm, _matrix)[0]

        # Build id→resource map
        id_map = {r["id"]: r for r in resources}

        results = []
        for idx, sim in enumerate(sims):
            if idx >= len(_resource_ids):
                break
            rid = _resource_ids[idx]
            r = id_map.get(rid)
            if r is None:
                continue
            if sdg_filter and not any(s in r.get("sdgs", []) for s in sdg_filter):
                continue
            results.append({"resource": r, "similarity": round(float(sim), 4)})

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        return []


def get_similar(resource_id: int, resources: list[dict], top_k: int = 6) -> list[dict]:
    """Return top_k most similar resources to a given resource_id."""
    global _matrix, _resource_ids
    if _matrix is None:
        return []
    try:
        if resource_id not in _resource_ids:
            return []
        idx = _resource_ids.index(resource_id)
        vec = _matrix[idx:idx+1]
        sims = cosine_similarity(vec, _matrix)[0]
        id_map = {r["id"]: r for r in resources}
        results = []
        for i, sim in enumerate(sims):
            rid = _resource_ids[i]
            if rid == resource_id:
                continue
            r = id_map.get(rid)
            if r:
                results.append({"resource": r, "similarity": round(float(sim), 4)})
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    except Exception as e:
        logger.error(f"Similarity error: {e}")
        return []


def is_index_built() -> bool:
    return _matrix is not None
