"""core/scraper.py – Multi-source web scraper for SDG AI resources."""
import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; SDGKnowledgebase/1.0; "
        "+https://github.com/sdg-ai-kb) research bot"
    ),
    "Accept": "application/json, text/html, */*",
}
TIMEOUT = 15

SDG_KEYWORDS = {
    1: ["poverty", "cash transfer", "microfinance", "financial inclusion"],
    2: ["food security", "hunger", "malnutrition", "agriculture AI", "crop disease"],
    3: ["health AI", "medical AI", "clinical AI", "disease diagnosis", "drug discovery"],
    4: ["education AI", "adaptive learning", "edtech", "e-learning AI"],
    5: ["gender equality AI", "women empowerment AI", "gender bias detection"],
    6: ["water quality AI", "clean water AI", "sanitation AI", "water management AI"],
    7: ["renewable energy AI", "solar AI", "energy efficiency AI", "clean energy AI"],
    8: ["decent work AI", "employment AI", "labor market AI", "job matching AI"],
    9: ["infrastructure AI", "smart manufacturing", "industry 4.0", "innovation AI"],
    10: ["inequality AI", "social inclusion AI", "digital divide"],
    11: ["smart city AI", "urban AI", "sustainable city", "city planning AI"],
    12: ["circular economy AI", "waste AI", "sustainable consumption AI", "ESG AI"],
    13: ["climate AI", "carbon emissions AI", "climate change AI", "net zero AI"],
    14: ["ocean AI", "marine AI", "illegal fishing AI", "ocean plastic AI"],
    15: ["deforestation AI", "wildlife AI", "biodiversity AI", "forest monitoring AI"],
    16: ["peace AI", "justice AI", "corruption AI", "governance AI"],
    17: ["SDG partnership AI", "development finance AI", "global goals AI"],
}


def _safe_get(url: str, params=None, accept_json=False) -> Optional[requests.Response]:
    try:
        hdrs = HEADERS.copy()
        if accept_json:
            hdrs["Accept"] = "application/json"
        r = requests.get(url, params=params, headers=hdrs, timeout=TIMEOUT)
        r.raise_for_status()
        return r
    except Exception as e:
        logger.warning(f"GET {url} failed: {e}")
        return None


def _detect_sdg(text: str) -> list[int]:
    """Simple keyword heuristic to detect which SDGs a resource relates to."""
    text_lower = text.lower()
    sdgs = []
    for sdg, keywords in SDG_KEYWORDS.items():
        if any(kw.lower() in text_lower for kw in keywords):
            sdgs.append(sdg)
    # Also detect explicit SDG mentions
    for m in re.finditer(r'\bsdg[\s-]?(\d{1,2})\b', text_lower):
        n = int(m.group(1))
        if 1 <= n <= 17 and n not in sdgs:
            sdgs.append(n)
    return sdgs or [13]  # default to Climate if nothing detected


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 1: ArXiv API  (cs.AI + SDG keywords)
# ─────────────────────────────────────────────────────────────────────────────
def scrape_arxiv(max_results: int = 40) -> list[dict]:
    """Fetch recent AI+SDG papers from ArXiv."""
    results = []
    query = (
        'all:(("sustainable development goals" OR "SDG" OR "climate AI" OR '
        '"food security AI" OR "health AI developing") AND '
        '("artificial intelligence" OR "machine learning" OR "deep learning"))'
    )
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    resp = _safe_get(url, params=params)
    if resp is None:
        return []
    try:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(resp.text)
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            link_el = entry.find("atom:id", ns)
            published = entry.find("atom:published", ns)

            title_text = title.text.strip().replace("\n", " ") if title is not None else ""
            summary_text = summary.text.strip().replace("\n", " ") if summary is not None else ""
            link_text = link_el.text.strip() if link_el is not None else ""
            year = int(published.text[:4]) if published is not None else 2024

            if not title_text:
                continue
            sdgs = _detect_sdg(title_text + " " + summary_text)
            results.append({
                "name": f"[ArXiv Paper] {title_text[:100]}",
                "year": year,
                "url": link_text,
                "type": "Research",
                "tags": "arxiv,paper,AI,SDG",
                "region": "Global",
                "how": f"Academic research advancing AI methods for SDG {sdgs[0] if sdgs else 13}",
                "description": summary_text[:500] + ("..." if len(summary_text) > 500 else ""),
                "sdgs": sdgs[:3],
                "source": "arxiv",
            })
    except Exception as e:
        logger.error(f"ArXiv parse error: {e}")
    logger.info(f"ArXiv: {len(results)} papers")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 2: GitHub Search API  (AI + SDG repos)
# ─────────────────────────────────────────────────────────────────────────────
def scrape_github(max_results: int = 30) -> list[dict]:
    """Search GitHub for open-source AI + SDG projects."""
    results = []
    queries = [
        "sustainable development goals AI machine learning",
        "climate change artificial intelligence open source",
        "food security machine learning open",
    ]
    seen = set()
    for q in queries:
        resp = _safe_get(
            "https://api.github.com/search/repositories",
            params={"q": q, "sort": "stars", "per_page": 15},
            accept_json=True,
        )
        if resp is None:
            continue
        try:
            data = resp.json()
            for repo in data.get("items", []):
                name = repo.get("full_name", "")
                if name in seen:
                    continue
                seen.add(name)
                desc = repo.get("description") or ""
                topics = " ".join(repo.get("topics", []))
                stars = repo.get("stargazers_count", 0)
                if stars < 10:
                    continue
                combined = f"{name} {desc} {topics}"
                sdgs = _detect_sdg(combined)
                year = int(repo.get("created_at", "2020")[:4])
                results.append({
                    "name": f"[GitHub] {repo.get('name', name)}",
                    "year": year,
                    "url": repo.get("html_url", ""),
                    "type": "Tool",
                    "tags": f"open source,github,{topics[:80]}",
                    "region": "Global",
                    "how": f"Open-source AI tool for SDG {sdgs[0] if sdgs else 13} with {stars}★ on GitHub",
                    "description": desc[:500] if desc else f"Open-source AI project: {name}",
                    "sdgs": sdgs[:3],
                    "source": "github",
                })
        except Exception as e:
            logger.warning(f"GitHub parse error: {e}")
        time.sleep(1)
    logger.info(f"GitHub: {len(results)} repos")
    return results[:max_results]


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 3: Semantic Scholar API
# ─────────────────────────────────────────────────────────────────────────────
def scrape_semantic_scholar(max_results: int = 20) -> list[dict]:
    """Fetch high-citation AI+SDG papers from Semantic Scholar."""
    results = []
    queries = [
        "artificial intelligence sustainable development goals",
        "machine learning climate change adaptation",
    ]
    for q in queries:
        resp = _safe_get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={"query": q, "limit": 15,
                    "fields": "title,abstract,year,externalIds,citationCount,openAccessPdf"},
            accept_json=True,
        )
        if resp is None:
            continue
        try:
            for paper in resp.json().get("data", []):
                title = paper.get("title", "")
                abstract = paper.get("abstract") or ""
                year = paper.get("year") or 2023
                citations = paper.get("citationCount", 0)
                if citations < 5:
                    continue
                doi = paper.get("externalIds", {}).get("DOI", "")
                url = f"https://doi.org/{doi}" if doi else ""
                pdf = paper.get("openAccessPdf", {})
                if pdf:
                    url = pdf.get("url", url)
                sdgs = _detect_sdg(title + " " + abstract)
                results.append({
                    "name": f"[S2] {title[:100]}",
                    "year": year,
                    "url": url,
                    "type": "Research",
                    "tags": f"paper,citations:{citations},semantic scholar",
                    "region": "Global",
                    "how": f"Peer-reviewed AI research for SDG {sdgs[0] if sdgs else 13} ({citations} citations)",
                    "description": abstract[:500] + ("..." if len(abstract)>500 else ""),
                    "sdgs": sdgs[:3],
                    "source": "semantic_scholar",
                })
        except Exception as e:
            logger.warning(f"Semantic Scholar parse: {e}")
        time.sleep(1)
    logger.info(f"Semantic Scholar: {len(results)} papers")
    return results[:max_results]


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 4: ITU AI for Good  
# ─────────────────────────────────────────────────────────────────────────────
def scrape_itu_ai_for_good(max_results: int = 20) -> list[dict]:
    """Scrape ITU AI for Good solutions catalogue."""
    results = []
    resp = _safe_get("https://aiforgood.itu.int/about-ai-for-good/about/")
    if resp is None:
        return []
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        # Look for any article/card elements
        cards = soup.find_all(["article", "div"], class_=re.compile(r"card|post|solution", re.I))
        for card in cards[:max_results]:
            title_el = card.find(["h2","h3","h4","a"])
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if len(title) < 10:
                continue
            link_el = card.find("a", href=True)
            url = link_el["href"] if link_el else "https://aiforgood.itu.int"
            if url.startswith("/"):
                url = "https://aiforgood.itu.int" + url
            desc_el = card.find("p")
            desc = desc_el.get_text(strip=True) if desc_el else ""
            sdgs = _detect_sdg(title + " " + desc)
            results.append({
                "name": f"[ITU AI4Good] {title[:100]}",
                "year": 2024,
                "url": url,
                "type": "Tool",
                "tags": "ITU,AI for Good,UN,SDG tool",
                "region": "Global",
                "how": f"ITU-validated AI solution for SDG {sdgs[0] if sdgs else 17}",
                "description": desc[:500] if desc else f"AI solution from ITU AI for Good: {title}",
                "sdgs": sdgs[:4],
                "source": "itu",
            })
    except Exception as e:
        logger.warning(f"ITU parse error: {e}")
    logger.info(f"ITU AI for Good: {len(results)} items")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 5: UN SDG Knowledge Platform (news/reports)
# ─────────────────────────────────────────────────────────────────────────────
def scrape_un_sdg_platform() -> list[dict]:
    """Scrape UN SDG Knowledge Platform for AI-related news."""
    results = []
    resp = _safe_get("https://sdgs.un.org/news")
    if resp is None:
        return []
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.find_all(["article","div"], class_=re.compile(r"view|news|item", re.I))
        for item in items[:15]:
            a = item.find("a", href=True)
            if not a:
                continue
            title = a.get_text(strip=True)
            if "ai" not in title.lower() and "artificial" not in title.lower() and "digital" not in title.lower():
                continue
            url = a["href"]
            if url.startswith("/"):
                url = "https://sdgs.un.org" + url
            sdgs = _detect_sdg(title)
            results.append({
                "name": f"[UN SDG] {title[:100]}",
                "year": 2024,
                "url": url,
                "type": "UN Initiative",
                "tags": "UN,SDG,official,digital,AI",
                "region": "Global",
                "how": f"UN official initiative applying AI/digital tools for sustainable development",
                "description": f"UN SDG Knowledge Platform resource: {title}",
                "sdgs": sdgs[:4] if sdgs else [17],
                "source": "un_sdg",
            })
    except Exception as e:
        logger.warning(f"UN SDG parse error: {e}")
    logger.info(f"UN SDG Platform: {len(results)} items")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# MASTER SCRAPER
# ─────────────────────────────────────────────────────────────────────────────
def run_all_scrapers() -> list[dict]:
    """Run all scrapers and return merged, deduplicated list."""
    all_results = []
    sources = [
        ("ArXiv", scrape_arxiv),
        ("GitHub", scrape_github),
        ("Semantic Scholar", scrape_semantic_scholar),
        ("ITU AI for Good", scrape_itu_ai_for_good),
        ("UN SDG Platform", scrape_un_sdg_platform),
    ]
    for name, fn in sources:
        try:
            items = fn()
            all_results.extend(items)
            logger.info(f"{name}: +{len(items)} resources")
        except Exception as e:
            logger.error(f"{name} scraper exception: {e}")

    # Deduplicate by URL
    seen_urls: set[str] = set()
    unique = []
    for item in all_results:
        url = item.get("url","").strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(item)
        elif not url:
            unique.append(item)
    return unique
