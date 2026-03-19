"""core/database.py – SQLite backend for SDG AI Knowledgebase."""
import sqlite3
import json
import os
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "sdg_knowledgebase.db"


def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS resources (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        year        INTEGER,
        url         TEXT,
        type        TEXT,
        tags        TEXT,
        region      TEXT,
        how         TEXT,
        description TEXT,
        sdgs        TEXT,           -- JSON list e.g. [1,3]
        impact_score REAL DEFAULT 0,
        embedding   TEXT,           -- JSON list of floats
        source      TEXT DEFAULT 'seed',
        verified    INTEGER DEFAULT 1,
        created_at  TEXT,
        updated_at  TEXT,
        UNIQUE(name, url)
    );

    CREATE TABLE IF NOT EXISTS scrape_log (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        source     TEXT,
        status     TEXT,
        count      INTEGER DEFAULT 0,
        message    TEXT,
        ran_at     TEXT
    );

    CREATE TABLE IF NOT EXISTS user_feedback (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        resource_id INTEGER,
        rating      INTEGER,
        comment     TEXT,
        created_at  TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_resources_year ON resources(year);
    CREATE INDEX IF NOT EXISTS idx_resources_type ON resources(type);
    CREATE INDEX IF NOT EXISTS idx_resources_impact ON resources(impact_score DESC);
    """)
    conn.commit()
    conn.close()


def _hash(name: str, url: str) -> str:
    return hashlib.md5(f"{name}{url}".encode()).hexdigest()


def upsert_resource(row: dict) -> bool:
    """Insert or update a resource. Returns True if new."""
    now = datetime.utcnow().isoformat()
    sdgs_json = json.dumps(row.get("sdgs", []))
    conn = get_conn()
    try:
        existing = conn.execute(
            "SELECT id FROM resources WHERE name=? AND url=?",
            (row["name"], row.get("url", ""))
        ).fetchone()
        if existing:
            conn.execute("""
                UPDATE resources SET year=?,type=?,tags=?,region=?,how=?,description=?,
                    sdgs=?,source=?,updated_at=?
                WHERE id=?
            """, (row.get("year"), row.get("type"), row.get("tags"),
                  row.get("region"), row.get("how"), row.get("description"),
                  sdgs_json, row.get("source","seed"), now, existing["id"]))
            conn.commit()
            return False
        else:
            conn.execute("""
                INSERT INTO resources
                    (name,year,url,type,tags,region,how,description,sdgs,source,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (row["name"], row.get("year"), row.get("url",""),
                  row.get("type"), row.get("tags"), row.get("region"),
                  row.get("how"), row.get("description"),
                  sdgs_json, row.get("source","seed"), now, now))
            conn.commit()
            return True
    finally:
        conn.close()


def update_embedding(resource_id: int, embedding: list):
    conn = get_conn()
    conn.execute("UPDATE resources SET embedding=? WHERE id=?",
                 (json.dumps(embedding), resource_id))
    conn.commit()
    conn.close()


def update_impact_score(resource_id: int, score: float):
    conn = get_conn()
    conn.execute("UPDATE resources SET impact_score=? WHERE id=?", (score, resource_id))
    conn.commit()
    conn.close()


def get_all_resources(verified_only=True) -> list[dict]:
    conn = get_conn()
    q = "SELECT * FROM resources"
    if verified_only:
        q += " WHERE verified=1"
    q += " ORDER BY impact_score DESC, year DESC"
    rows = [dict(r) for r in conn.execute(q).fetchall()]
    conn.close()
    for r in rows:
        try:
            r["sdgs"] = json.loads(r["sdgs"]) if r["sdgs"] else []
        except Exception:
            r["sdgs"] = []
        try:
            r["embedding"] = json.loads(r["embedding"]) if r["embedding"] else None
        except Exception:
            r["embedding"] = None
    return rows


def get_resource_by_id(rid: int) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM resources WHERE id=?", (rid,)).fetchone()
    conn.close()
    if not row:
        return None
    r = dict(row)
    r["sdgs"] = json.loads(r["sdgs"]) if r["sdgs"] else []
    r["embedding"] = json.loads(r["embedding"]) if r["embedding"] else None
    return r


def filter_resources(sdg: Optional[int] = None, rtype: Optional[str] = None,
                     year_min: Optional[int] = None, year_max: Optional[int] = None,
                     region: Optional[str] = None, min_score: float = 0) -> list[dict]:
    rows = get_all_resources()
    result = []
    for r in rows:
        if sdg and sdg not in r["sdgs"]:
            continue
        if rtype and r.get("type") != rtype:
            continue
        if year_min and r.get("year") and r["year"] < year_min:
            continue
        if year_max and r.get("year") and r["year"] > year_max:
            continue
        if region and region.lower() not in (r.get("region") or "").lower():
            continue
        if r.get("impact_score", 0) < min_score:
            continue
        result.append(r)
    return result


def get_stats() -> dict:
    conn = get_conn()
    total    = conn.execute("SELECT COUNT(*) FROM resources WHERE verified=1").fetchone()[0]
    by_type  = conn.execute("SELECT type, COUNT(*) as n FROM resources WHERE verified=1 GROUP BY type").fetchall()
    by_year  = conn.execute("SELECT year, COUNT(*) as n FROM resources WHERE verified=1 AND year IS NOT NULL GROUP BY year ORDER BY year").fetchall()
    scrapes  = conn.execute("SELECT COUNT(*) FROM scrape_log WHERE status='success'").fetchone()[0]
    last_update = conn.execute("SELECT MAX(updated_at) FROM resources").fetchone()[0]
    conn.close()
    return {
        "total": total,
        "by_type": {r["type"]: r["n"] for r in by_type},
        "by_year": {str(r["year"]): r["n"] for r in by_year},
        "scrapes_run": scrapes,
        "last_update": last_update,
    }


def log_scrape(source: str, status: str, count: int = 0, message: str = ""):
    conn = get_conn()
    conn.execute("INSERT INTO scrape_log (source,status,count,message,ran_at) VALUES (?,?,?,?,?)",
                 (source, status, count, message, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def get_scrape_log(limit=20) -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM scrape_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_feedback(resource_id: int, rating: int, comment: str = ""):
    conn = get_conn()
    conn.execute("INSERT INTO user_feedback (resource_id,rating,comment,created_at) VALUES (?,?,?,?)",
                 (resource_id, rating, comment, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
