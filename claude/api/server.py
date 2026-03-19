"""api/server.py – FastAPI REST API for the SDG AI Knowledgebase."""
import json
import threading
import logging
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SDG AI Knowledgebase API",
    description=(
        "REST API providing access to AI tools, companies, platforms, patents, "
        "and research resources mapped to the UN Sustainable Development Goals. "
        "Includes semantic search, filtering, and impact scoring."
    ),
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_resources(sdg=None, rtype=None, year_min=None, year_max=None,
                   region=None, min_score=0):
    from core.database import filter_resources
    return filter_resources(sdg=sdg, rtype=rtype, year_min=year_min,
                            year_max=year_max, region=region, min_score=min_score)


@app.get("/api/v1/resources", summary="List resources with optional filters")
def list_resources(
    sdg: Optional[int] = Query(None, ge=1, le=17, description="Filter by SDG number (1-17)"),
    type: Optional[str] = Query(None, description="Resource type (Company, Tool, Platform, etc.)"),
    year_min: Optional[int] = Query(None, description="Minimum year"),
    year_max: Optional[int] = Query(None, description="Maximum year"),
    region: Optional[str] = Query(None, description="Region keyword filter"),
    min_score: float = Query(0, ge=0, le=100, description="Minimum impact score"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    resources = _get_resources(sdg=sdg, rtype=type, year_min=year_min,
                               year_max=year_max, region=region, min_score=min_score)
    total = len(resources)
    page = resources[offset:offset+limit]
    # Remove embedding from response
    for r in page:
        r.pop("embedding", None)
    return {"total": total, "limit": limit, "offset": offset, "data": page}


@app.get("/api/v1/resources/{resource_id}", summary="Get single resource by ID")
def get_resource(resource_id: int):
    from core.database import get_resource_by_id
    r = get_resource_by_id(resource_id)
    if not r:
        raise HTTPException(status_code=404, detail="Resource not found")
    r.pop("embedding", None)
    return r


@app.get("/api/v1/search", summary="Semantic search across all resources")
def search(
    q: str = Query(..., min_length=2, description="Search query"),
    sdg: Optional[int] = Query(None, ge=1, le=17),
    top_k: int = Query(20, ge=1, le=100),
):
    from core.database import get_all_resources
    from core.embeddings import semantic_search, is_index_built
    if not is_index_built():
        raise HTTPException(status_code=503, detail="Semantic index not yet ready. Retry in 30s.")
    resources = get_all_resources()
    sdg_filter = [sdg] if sdg else None
    results = semantic_search(q, top_k=top_k, sdg_filter=sdg_filter, resources=resources)
    out = []
    for item in results:
        r = dict(item["resource"])
        r.pop("embedding", None)
        out.append({"resource": r, "similarity": item["similarity"]})
    return {"query": q, "count": len(out), "results": out}


@app.get("/api/v1/recommend", summary="Get AI-powered recommendations")
def recommend(
    q: str = Query(..., description="Describe your project or need"),
    sdgs: Optional[str] = Query(None, description="Comma-separated SDG numbers e.g. '1,3,13'"),
    types: Optional[str] = Query(None, description="Comma-separated types e.g. 'Tool,Company'"),
    top_k: int = Query(10, ge=1, le=50),
):
    from core.database import get_all_resources
    from core.recommender import recommend_for_query
    resources = get_all_resources()
    sdg_filter = [int(s) for s in sdgs.split(",") if s.strip().isdigit()] if sdgs else None
    type_pref = [t.strip() for t in types.split(",")] if types else None
    recs = recommend_for_query(q, resources, sdg_focus=sdg_filter,
                               preferred_types=type_pref, top_k=top_k)
    out = []
    for item in recs:
        r = dict(item["resource"])
        r.pop("embedding", None)
        out.append({**r, "rec_score": item["rec_score"],
                    "similarity": item["similarity"]})
    return {"query": q, "count": len(out), "recommendations": out}


@app.get("/api/v1/sdgs", summary="List all 17 SDGs with resource counts")
def list_sdgs():
    from core.database import get_all_resources
    from collections import Counter
    resources = get_all_resources()
    SDG_NAMES = {
        1:"No Poverty",2:"Zero Hunger",3:"Good Health & Wellbeing",
        4:"Quality Education",5:"Gender Equality",6:"Clean Water & Sanitation",
        7:"Affordable & Clean Energy",8:"Decent Work & Economic Growth",
        9:"Industry, Innovation & Infrastructure",10:"Reduced Inequalities",
        11:"Sustainable Cities & Communities",12:"Responsible Consumption",
        13:"Climate Action",14:"Life Below Water",15:"Life on Land",
        16:"Peace, Justice & Strong Institutions",17:"Partnerships for Goals",
    }
    counts = Counter()
    for r in resources:
        for s in r.get("sdgs", []):
            counts[s] += 1
    return [{"sdg": i, "name": SDG_NAMES[i], "resource_count": counts.get(i, 0)}
            for i in range(1, 18)]


@app.get("/api/v1/stats", summary="Database and system statistics")
def stats():
    from core.database import get_stats
    from core.embeddings import is_index_built
    from core.scheduler import get_scheduler_status
    s = get_stats()
    s["semantic_index_ready"] = is_index_built()
    s["scheduler"] = get_scheduler_status()
    return s


@app.get("/api/v1/health", summary="Health check")
def health():
    return {"status": "ok", "timestamp": __import__("datetime").datetime.utcnow().isoformat()}


# ── Background server launcher ──────────────────────────────────────────────
_server_thread: threading.Thread | None = None

def start_api_server(host: str = "127.0.0.1", port: int = 8765):
    global _server_thread
    if _server_thread and _server_thread.is_alive():
        return
    def run():
        uvicorn.run(app, host=host, port=port, log_level="warning")
    _server_thread = threading.Thread(target=run, daemon=True, name="api-server")
    _server_thread.start()
    logger.info(f"API server started on http://{host}:{port}/api/docs")
