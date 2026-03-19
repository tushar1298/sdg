# 🌍 SDG AI Knowledgebase

A full-stack, auto-updating intelligence platform that maps AI tools, companies,
platforms, patents, research papers and initiatives to the UN Sustainable
Development Goals (SDGs) — with semantic search, smart recommendations, impact
scoring, rich visualizations, and a REST API.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Semantic Search** | TF-IDF + LSA (Latent Semantic Analysis) embeddings, 128-dim vector space |
| **Smart Recommender** | Query-based + SDG-based + Portfolio Gap Analysis |
| **SDG Mapping** | Multi-label tagging across all 17 SDGs, cross-SDG heatmap |
| **Impact Scoring** | 6-dimensional scoring: SDG priority, type credibility, recency, scale, regional coverage |
| **Auto-Updating** | APScheduler every 6h; scrapes ArXiv, GitHub, Semantic Scholar, ITU AI4Good, UN SDG Platform |
| **REST API** | FastAPI with Swagger/ReDoc, 7 endpoints, JSON output |
| **Visualizations** | Radar, bubble, heatmap, treemap, histogram, timeline charts |
| **Dashboard** | Real-time metrics, top resources, resource timeline |
| **Admin Panel** | Manual scraping, scheduler control, add resources, scrape logs |
| **Export** | CSV download from any search/filter view |

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch everything (Streamlit app + API server + scheduler)
python run.py

# Or directly:
streamlit run app.py
```

Open **http://localhost:8501** for the dashboard.  
Open **http://localhost:8765/api/docs** for the REST API.

---

## 🏗️ Architecture

```
sdg_app/
├── app.py                  # Streamlit UI (all pages)
├── run.py                  # One-command launcher
├── requirements.txt
├── .streamlit/
│   └── config.toml         # Dark theme config
├── core/
│   ├── database.py         # SQLite ORM (WAL mode, indexes)
│   ├── embeddings.py       # TF-IDF + LSA semantic index
│   ├── impact_scorer.py    # 6-dimension impact scoring
│   ├── recommender.py      # Query, SDG & gap-based recs
│   ├── scraper.py          # 5-source web scraper
│   └── scheduler.py        # APScheduler background jobs
├── api/
│   └── server.py           # FastAPI REST server (port 8765)
└── data/
    └── seed_data.py        # 110+ curated seed resources
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/resources` | List with filters: `sdg`, `type`, `year_min/max`, `region`, `min_score` |
| GET | `/api/v1/resources/{id}` | Single resource |
| GET | `/api/v1/search?q=...` | Semantic search |
| GET | `/api/v1/recommend?q=...` | AI recommendations |
| GET | `/api/v1/sdgs` | All 17 SDGs with counts |
| GET | `/api/v1/stats` | System stats |
| GET | `/api/v1/health` | Health check |

### Examples

```bash
# Semantic search
curl "http://localhost:8765/api/v1/search?q=AI+for+water+quality&top_k=10"

# Climate action tools (SDG 13), min score 60
curl "http://localhost:8765/api/v1/resources?sdg=13&min_score=60&limit=20"

# Smart recommendations for a project
curl "http://localhost:8765/api/v1/recommend?q=help+farmers+detect+crop+disease&sdgs=2,1"
```

---

## 📊 Impact Scoring Model

Each resource is scored 0–100 across 6 dimensions:

| Dimension | Weight | Description |
|---|---|---|
| SDG Priority | 25% | Average priority weight of mapped SDGs |
| Type Credibility | 20% | UN Initiative (100%) → Website (70%) |
| Scale Signals | 20% | Keywords: "million", "deployed", "Series A/B", etc. |
| Recency | 15% | Exponential decay: newer = higher |
| Regional Coverage | 10% | Global (100%) → Regional (70–85%) |
| Multi-SDG Breadth | 10% | +4% per additional SDG covered |

---

## 🔄 Auto-Update Sources

| Source | Type | Frequency |
|---|---|---|
| **ArXiv** | Research papers (cs.AI + SDG keywords) | Every 6h |
| **GitHub** | Open-source AI+SDG repositories | Every 6h |
| **Semantic Scholar** | High-citation academic papers | Every 6h |
| **ITU AI for Good** | UN-validated AI solutions | Every 6h |
| **UN SDG Platform** | Official UN SDG AI news | Every 6h |

---

## 🎨 Tech Stack

- **Frontend**: Streamlit + custom CSS (Space Grotesk + Unbounded fonts)
- **Charts**: Plotly (radar, bubble, heatmap, treemap, timeline)
- **Search**: scikit-learn TF-IDF + TruncatedSVD (LSA)
- **Database**: SQLite (WAL mode, indexed)
- **API**: FastAPI + Uvicorn
- **Scheduler**: APScheduler (BackgroundScheduler)
- **Scraping**: requests + BeautifulSoup + ArXiv/GitHub/S2 APIs

---

## 📄 License
MIT — Free for research, humanitarian, and commercial use.
