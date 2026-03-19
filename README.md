"""app.py – Main Streamlit entry point for SDG AI Knowledgebase."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SDG AI Knowledgebase",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ──────────────────────────────────────────────────────────────
SDG_NAMES = {
    1:"No Poverty",2:"Zero Hunger",3:"Good Health & Wellbeing",
    4:"Quality Education",5:"Gender Equality",6:"Clean Water & Sanitation",
    7:"Affordable & Clean Energy",8:"Decent Work & Economic Growth",
    9:"Industry, Innovation & Infrastructure",10:"Reduced Inequalities",
    11:"Sustainable Cities & Communities",12:"Responsible Consumption & Production",
    13:"Climate Action",14:"Life Below Water",15:"Life on Land",
    16:"Peace, Justice & Strong Institutions",17:"Partnerships for Goals",
}
SDG_COLORS = {
    1:"#E5243B",2:"#DDA63A",3:"#4C9F38",4:"#C5192D",5:"#FF3A21",
    6:"#26BDE2",7:"#FCC30B",8:"#A21942",9:"#FD6925",10:"#DD1367",
    11:"#FD9D24",12:"#BF8B2E",13:"#3F7E44",14:"#0A97D9",15:"#56C02B",
    16:"#00689D",17:"#19486A",
}
SDG_ICONS = {
    1:"🚫💰",2:"🌾",3:"💊",4:"📚",5:"⚖️",6:"💧",7:"⚡",8:"💼",9:"🏗️",
    10:"📉",11:"🏙️",12:"♻️",13:"🌡️",14:"🌊",15:"🌿",16:"⚖️",17:"🤝",
}
TYPE_COLORS = {
    "Company":"#6366f1","Tool":"#22d3ee","Platform":"#34d399",
    "Website":"#f59e0b","UN Initiative":"#3b82f6","Research":"#a855f7",
    "Framework":"#ec4899","Program":"#14b8a6",
}

# ── Global CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&family=Unbounded:wght@700;900&display=swap');

:root {
    --bg-primary: #070B14;
    --bg-card: #0D1424;
    --bg-card2: #111827;
    --accent-cyan: #00D4FF;
    --accent-green: #00FF9F;
    --accent-purple: #7C3AED;
    --accent-orange: #F97316;
    --text-primary: #F1F5F9;
    --text-muted: #64748B;
    --border: #1E293B;
    --glow: 0 0 20px rgba(0,212,255,0.15);
}

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--text-primary);
}

/* Hide default Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* Main background */
.stApp { background: var(--bg-primary); }
.block-container { padding: 1rem 2rem 2rem 2rem !important; max-width: 1600px; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0A0E1A 0%, #0D1424 100%) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--accent-cyan) !important;
}

/* Hero header */
.hero-header {
    background: linear-gradient(135deg, #070B14 0%, #0D1424 40%, #0A1628 100%);
    border: 1px solid #1E293B;
    border-radius: 20px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(0,212,255,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.hero-header::after {
    content: '';
    position: absolute;
    bottom: -30%;
    left: 20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(0,255,159,0.04) 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-family: 'Unbounded', sans-serif !important;
    font-size: 2.2rem;
    font-weight: 900;
    background: linear-gradient(135deg, #00D4FF 0%, #00FF9F 50%, #7C3AED 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.1;
}
.hero-sub {
    color: #94A3B8;
    font-size: 1rem;
    margin-top: 0.5rem;
    font-weight: 400;
}
.hero-badges {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-top: 1rem;
}
.badge {
    background: rgba(0,212,255,0.1);
    border: 1px solid rgba(0,212,255,0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.72rem;
    color: #00D4FF;
    font-weight: 500;
    font-family: 'JetBrains Mono', monospace;
}
.badge-green { background: rgba(0,255,159,0.1); border-color: rgba(0,255,159,0.3); color: #00FF9F; }
.badge-purple { background: rgba(124,58,237,0.15); border-color: rgba(124,58,237,0.4); color: #A78BFA; }

/* Metric cards */
.metric-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; margin-bottom: 1.5rem; }
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: var(--accent-cyan); }
.metric-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-green));
}
.metric-value {
    font-family: 'Unbounded', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent-cyan);
    line-height: 1;
}
.metric-label { color: var(--text-muted); font-size: 0.8rem; margin-top: 0.3rem; font-weight: 500; }
.metric-delta { color: var(--accent-green); font-size: 0.75rem; margin-top: 0.2rem; }

/* Resource cards */
.resource-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.75rem;
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
}
.resource-card:hover {
    border-color: rgba(0,212,255,0.4);
    box-shadow: 0 4px 24px rgba(0,212,255,0.08);
    transform: translateY(-1px);
}
.resource-card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
.resource-name {
    font-weight: 700;
    font-size: 1rem;
    color: var(--text-primary);
    margin: 0;
}
.resource-name a { color: var(--accent-cyan); text-decoration: none; }
.resource-name a:hover { text-decoration: underline; }
.resource-how { color: #94A3B8; font-size: 0.85rem; margin: 0.4rem 0; line-height: 1.5; }
.resource-desc { color: #64748B; font-size: 0.8rem; margin: 0.3rem 0; line-height: 1.5; }
.resource-meta { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; margin-top: 0.6rem; }
.tag-sdg {
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 600;
    border: 1px solid;
}
.tag-type {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 2px 8px;
    font-size: 0.7rem;
    color: #94A3B8;
}
.tag-year {
    font-family: 'JetBrains Mono', monospace;
    color: #64748B;
    font-size: 0.72rem;
}
.score-badge {
    background: linear-gradient(135deg, rgba(0,212,255,0.15), rgba(0,255,159,0.1));
    border: 1px solid rgba(0,212,255,0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--accent-cyan);
    white-space: nowrap;
}
.sim-badge {
    background: rgba(124,58,237,0.15);
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    font-weight: 700;
    color: #A78BFA;
    white-space: nowrap;
}

/* Section headers */
.section-header {
    font-family: 'Unbounded', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.75rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-header span { color: var(--accent-cyan); }

/* Search bar */
.stTextInput input {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.6rem 1rem !important;
}
.stTextInput input:focus {
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 0 2px rgba(0,212,255,0.15) !important;
}

/* Buttons */
.stButton button {
    background: linear-gradient(135deg, #00D4FF22, #00FF9F11) !important;
    border: 1px solid var(--accent-cyan) !important;
    color: var(--accent-cyan) !important;
    border-radius: 10px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton button:hover {
    background: linear-gradient(135deg, #00D4FF33, #00FF9F22) !important;
    box-shadow: 0 0 16px rgba(0,212,255,0.2) !important;
}

/* Selectbox, multiselect */
.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card) !important;
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: var(--text-muted) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0,212,255,0.2), rgba(0,255,159,0.1)) !important;
    color: var(--accent-cyan) !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
}

/* Dataframe */
.stDataFrame { border-radius: 12px; overflow: hidden; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-cyan); }

/* Status indicators */
.status-live {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.75rem;
    color: #22c55e;
    font-family: 'JetBrains Mono', monospace;
}
.status-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #22c55e;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%,100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* SDG grid */
.sdg-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    border: 1px solid;
    margin: 2px;
    cursor: pointer;
    transition: all 0.15s;
}
.sdg-pill:hover { transform: scale(1.05); }

/* Info box */
.info-box {
    background: rgba(0,212,255,0.05);
    border: 1px solid rgba(0,212,255,0.2);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
    font-size: 0.85rem;
    color: #94A3B8;
    line-height: 1.6;
}

/* API code block */
.api-block {
    background: #0D1117;
    border: 1px solid #21262D;
    border-radius: 10px;
    padding: 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #79C0FF;
    overflow-x: auto;
}

/* Impact score bar */
.score-bar-container { display: flex; align-items: center; gap: 0.5rem; }
.score-bar {
    flex: 1;
    height: 4px;
    background: #1E293B;
    border-radius: 2px;
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    border-radius: 2px;
    background: linear-gradient(90deg, #00D4FF, #00FF9F);
}
</style>
""", unsafe_allow_html=True)


# ── Initialisation (run once) ──────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def bootstrap():
    """One-time setup: DB, seed data, scoring, indexing, scheduler, API."""
    from core.database import init_db, upsert_resource, get_all_resources, update_impact_score
    from core.impact_scorer import score_resource
    from core import embeddings as emb
    from core.scheduler import start_scheduler
    from api.server import start_api_server
    from data.seed_data import SEED_RESOURCES

    init_db()

    # Seed database
    for row in SEED_RESOURCES:
        upsert_resource({**row, "source": "seed"})

    # Score all
    resources = get_all_resources()
    for r in resources:
        update_impact_score(r["id"], score_resource(r))

    # Build semantic index
    resources = get_all_resources()
    emb.build_index(resources)

    # Start background scheduler (every 6h) and API
    start_scheduler(interval_hours=6)
    try:
        start_api_server(port=8765)
    except Exception:
        pass

    return True


def get_resources_cached():
    """Refresh resources every 60s via cache."""
    from core.database import get_all_resources
    return get_all_resources()


# ── Helpers ────────────────────────────────────────────────────────────────
def sdg_badge(sdg: int, small=False) -> str:
    color = SDG_COLORS.get(sdg, "#555")
    name  = SDG_NAMES.get(sdg, f"SDG {sdg}")
    sz    = "0.65rem" if small else "0.72rem"
    return (f'<span class="tag-sdg" style="background:{color}22;'
            f'border-color:{color}66;color:{color};font-size:{sz}">'
            f'SDG {sdg}</span>')


def type_badge(rtype: str) -> str:
    color = TYPE_COLORS.get(rtype, "#64748B")
    return f'<span class="tag-type" style="color:{color}">{rtype}</span>'


def score_color(score: float) -> str:
    if score >= 75: return "#00FF9F"
    if score >= 55: return "#00D4FF"
    if score >= 35: return "#F97316"
    return "#EF4444"


def render_resource_card(r: dict, show_similarity: float | None = None,
                         show_rec_score: float | None = None, show_breakdown=False):
    sdg_badges = "".join(sdg_badge(s) for s in r.get("sdgs", []))
    score = r.get("impact_score", 0)
    sc = score_color(score)
    url = r.get("url", "")
    name_html = (f'<a href="{url}" target="_blank">{r["name"]}</a>'
                 if url else r["name"])

    sim_html = ""
    if show_similarity is not None:
        sim_html = f'<span class="sim-badge">🎯 {show_similarity:.0%} match</span>'
    if show_rec_score is not None:
        sim_html += f'<span class="sim-badge">⭐ {show_rec_score:.0%} rec</span>'

    year = r.get("year") or "—"
    region = r.get("region") or "Global"

    st.markdown(f"""
    <div class="resource-card">
        <div class="resource-card-header">
            <div style="flex:1">
                <div class="resource-name">{name_html}</div>
                <div class="resource-how">{r.get("how","")}</div>
                <div class="resource-desc">{r.get("description","")[:200]}{"..." if len(r.get("description",""))>200 else ""}</div>
            </div>
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;min-width:100px">
                <span class="score-badge" style="color:{sc};border-color:{sc}44;background:{sc}11">
                    ⚡ {score:.0f}/100
                </span>
                {sim_html}
            </div>
        </div>
        <div class="resource-meta">
            {sdg_badges}
            {type_badge(r.get("type","Tool"))}
            <span class="tag-year">📅 {year}</span>
            <span class="tag-year">🌍 {region}</span>
        </div>
        <div class="score-bar-container" style="margin-top:0.5rem">
            <div class="score-bar"><div class="score-bar-fill" style="width:{score}%"></div></div>
            <span style="font-size:0.65rem;color:#475569;font-family:'JetBrains Mono',monospace">{score:.0f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────
def render_sidebar(resources):
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:1rem 0 0.5rem">
            <div style="font-family:'Unbounded',sans-serif;font-size:1.1rem;font-weight:900;
                background:linear-gradient(135deg,#00D4FF,#00FF9F);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                background-clip:text">🌍 SDG AI KB</div>
            <div style="color:#475569;font-size:0.7rem;margin-top:2px">Knowledgebase v2.0</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        nav = st.radio(
            "Navigate",
            ["🏠 Dashboard", "🔍 Search & Explore", "🤖 Smart Recommender",
             "🗺️ SDG Mapping", "📊 Visualizations", "🔌 API Access", "⚙️ Admin"],
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown('<div class="status-live"><div class="status-dot"></div>Live Updates</div>',
                    unsafe_allow_html=True)

        from core.database import get_stats
        from core.scheduler import get_scheduler_status
        stats = get_stats()
        sched = get_scheduler_status()

        st.markdown(f"""
        <div style="margin-top:0.75rem;font-size:0.75rem;color:#475569;line-height:2">
            📦 <b style="color:#94A3B8">{stats['total']}</b> resources<br>
            🔄 <b style="color:#94A3B8">{stats.get('scrapes_run',0)}</b> auto-updates<br>
            🕐 <b style="color:#94A3B8">{(stats.get('last_update','—') or '—')[:10]}</b> last update<br>
            ⚙️ Scheduler: <b style="color:{'#22c55e' if sched['running'] else '#ef4444'}">
            {'Running' if sched['running'] else 'Stopped'}</b>
        </div>
        """, unsafe_allow_html=True)

        if sched["running"] and sched.get("jobs"):
            next_run = sched["jobs"][0].get("next_run","—")[:16]
            st.markdown(f'<div style="font-size:0.72rem;color:#334155;margin-top:4px">Next: {next_run}</div>',
                        unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div style="font-size:0.7rem;color:#334155;text-align:center">API: localhost:8765/api/docs</div>',
                    unsafe_allow_html=True)

    return nav.split(" ", 1)[1].strip()


# ── Page: Dashboard ────────────────────────────────────────────────────────
def page_dashboard(resources):
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">SDG AI Knowledgebase</div>
        <div class="hero-sub">Mapping AI tools, companies, platforms & research to the UN 2030 Agenda</div>
        <div class="hero-badges">
            <span class="badge">🤖 Semantic Search</span>
            <span class="badge badge-green">⚡ Auto-Updating</span>
            <span class="badge badge-purple">📡 REST API</span>
            <span class="badge">🎯 Smart Recommender</span>
            <span class="badge badge-green">🗺️ Multi-label SDG Mapping</span>
            <span class="badge badge-purple">📊 Impact Scoring</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    from core.database import get_stats
    stats = get_stats()
    total = stats["total"]
    by_type = stats.get("by_type", {})
    companies = by_type.get("Company", 0) + by_type.get("Platform", 0)
    research  = by_type.get("Research", 0)
    programs  = by_type.get("UN Initiative", 0) + by_type.get("Program", 0) + by_type.get("Framework", 0)

    from collections import Counter
    sdg_counts = Counter()
    for r in resources:
        for s in r.get("sdgs", []):
            sdg_counts[s] += 1
    multi_sdg = sum(1 for r in resources if len(r.get("sdgs",[])) > 1)
    avg_score = sum(r.get("impact_score",0) for r in resources) / max(len(resources),1)

    # Metrics row
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-value">{total}</div>
            <div class="metric-label">Total Resources</div>
            <div class="metric-delta">↑ Auto-updating via 5 sources</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{companies}</div>
            <div class="metric-label">Companies & Platforms</div>
            <div class="metric-delta">Private sector AI innovators</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{research}</div>
            <div class="metric-label">Research Papers</div>
            <div class="metric-delta">ArXiv + Semantic Scholar</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{avg_score:.0f}</div>
            <div class="metric-label">Avg Impact Score</div>
            <div class="metric-delta">Multi-dimensional scoring</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="section-header">📊 <span>Resources per SDG</span></div>', unsafe_allow_html=True)
        sdg_df = pd.DataFrame([
            {"SDG": f"SDG {i}", "Name": SDG_NAMES[i][:22], "Count": sdg_counts.get(i,0),
             "Color": SDG_COLORS[i]}
            for i in range(1, 18)
        ])
        fig = px.bar(
            sdg_df, x="SDG", y="Count",
            color="SDG",
            color_discrete_map={f"SDG {i}": SDG_COLORS[i] for i in range(1,18)},
            hover_data={"Name": True},
            template="plotly_dark",
        )
        fig.update_layout(
            plot_bgcolor="#0D1424", paper_bgcolor="#0D1424",
            showlegend=False, margin=dict(t=10,b=40,l=10,r=10),
            height=320, font_family="Space Grotesk",
            xaxis=dict(tickfont=dict(size=10), gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B"),
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">🏷️ <span>By Resource Type</span></div>', unsafe_allow_html=True)
        type_df = pd.DataFrame([
            {"Type": k, "Count": v} for k,v in by_type.items() if v > 0
        ])
        if not type_df.empty:
            fig2 = px.pie(
                type_df, values="Count", names="Type",
                color="Type",
                color_discrete_map=TYPE_COLORS,
                template="plotly_dark",
                hole=0.5,
            )
            fig2.update_layout(
                plot_bgcolor="#0D1424", paper_bgcolor="#0D1424",
                margin=dict(t=10,b=10,l=10,r=10), height=320,
                font_family="Space Grotesk",
                legend=dict(font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
                showlegend=True,
            )
            fig2.update_traces(textposition="inside", textinfo="percent",
                               marker=dict(line=dict(color="#070B14", width=2)))
            st.plotly_chart(fig2, use_container_width=True)

    # Timeline
    st.markdown('<div class="section-header">📅 <span>Resources Over Time</span></div>', unsafe_allow_html=True)
    year_data = [(r.get("year"), r.get("type","Other")) for r in resources if r.get("year")]
    if year_data:
        ydf = pd.DataFrame(year_data, columns=["year","type"])
        ydf = ydf.groupby(["year","type"]).size().reset_index(name="count")
        fig3 = px.area(
            ydf, x="year", y="count", color="type",
            color_discrete_map=TYPE_COLORS,
            template="plotly_dark",
        )
        fig3.update_layout(
            plot_bgcolor="#0D1424", paper_bgcolor="#0D1424",
            margin=dict(t=10,b=40,l=10,r=10), height=240,
            font_family="Space Grotesk",
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B", title=""),
            legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)", orientation="h"),
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Top resources
    st.markdown('<div class="section-header">🏆 <span>Top Rated Resources</span></div>', unsafe_allow_html=True)
    top = sorted(resources, key=lambda x: x.get("impact_score",0), reverse=True)[:6]
    cols = st.columns(2)
    for i, r in enumerate(top):
        with cols[i % 2]:
            render_resource_card(r)


# ── Page: Search & Explore ─────────────────────────────────────────────────
def page_search(resources):
    st.markdown('<div class="section-header" style="font-size:1.5rem">🔍 <span>Search & Explore</span></div>',
                unsafe_allow_html=True)

    from core.embeddings import semantic_search, is_index_built

    col_s, col_f = st.columns([3, 1])
    with col_s:
        query = st.text_input("", placeholder="🔍  Search: 'AI for water quality monitoring in Africa'…",
                              key="main_search", label_visibility="collapsed")
    with col_f:
        search_mode = st.selectbox("Mode", ["Semantic", "Keyword"], label_visibility="collapsed")

    # Filters row
    fc1, fc2, fc3, fc4, fc5 = st.columns(5)
    with fc1:
        sdg_f = st.selectbox("SDG", ["All"] + [f"SDG {i} – {SDG_NAMES[i][:20]}" for i in range(1,18)])
    with fc2:
        all_types = sorted(set(r.get("type","") for r in resources if r.get("type")))
        type_f = st.selectbox("Type", ["All"] + all_types)
    with fc3:
        all_regions = sorted(set(r.get("region","") for r in resources if r.get("region")))
        region_f = st.selectbox("Region", ["All"] + all_regions)
    with fc4:
        years = [r.get("year") for r in resources if r.get("year")]
        year_range = st.slider("Year range", min(years, default=2000), max(years, default=2025),
                               (min(years, default=2000), max(years, default=2025))) if years else (2000, 2025)
    with fc5:
        min_score = st.slider("Min impact score", 0, 100, 0)

    # Apply filters
    sdg_num = int(sdg_f.split(" ")[1]) if sdg_f != "All" else None
    type_sel = type_f if type_f != "All" else None
    region_sel = region_f if region_f != "All" else None

    filtered = resources
    if sdg_num:
        filtered = [r for r in filtered if sdg_num in r.get("sdgs",[])]
    if type_sel:
        filtered = [r for r in filtered if r.get("type") == type_sel]
    if region_sel:
        filtered = [r for r in filtered if region_sel.lower() in (r.get("region","")).lower()]
    filtered = [r for r in filtered
                if (not r.get("year") or year_range[0] <= r["year"] <= year_range[1])
                and r.get("impact_score",0) >= min_score]

    # Semantic search
    search_results = None
    if query.strip():
        if search_mode == "Semantic" and is_index_built():
            sdg_filter = [sdg_num] if sdg_num else None
            raw = semantic_search(query.strip(), top_k=100,
                                  sdg_filter=sdg_filter, resources=filtered)
            search_results = [(item["resource"], item["similarity"]) for item in raw if item["similarity"] > 0.01]
        else:
            q_lower = query.strip().lower()
            search_results = [
                (r, 1.0) for r in filtered
                if q_lower in (r.get("name","") + r.get("description","") + r.get("how","")
                               + r.get("tags","")).lower()
            ]

    display = search_results if search_results is not None else [(r, None) for r in filtered]
    display.sort(key=lambda x: (-(x[1] or 0), -x[0].get("impact_score",0)))

    # Sort & limit
    col_sort, col_cnt, col_export = st.columns([2,1,1])
    with col_sort:
        sort_by = st.selectbox("Sort by", ["Relevance / Impact Score", "Year (newest)", "Year (oldest)", "Name A-Z"],
                               label_visibility="collapsed")
    with col_cnt:
        st.markdown(f'<div style="color:#64748B;font-size:0.85rem;padding-top:0.6rem">📦 {len(display)} results</div>',
                    unsafe_allow_html=True)
    with col_export:
        if st.button("⬇️ Export CSV"):
            df_exp = pd.DataFrame([r for r,_ in display])
            df_exp.pop("embedding", None) if "embedding" in df_exp.columns else None
            csv = df_exp.to_csv(index=False)
            st.download_button("Download", csv, "sdg_resources.csv", "text/csv",
                               key="dl_csv", label_visibility="collapsed")

    if sort_by == "Year (newest)":
        display.sort(key=lambda x: x[0].get("year",0) or 0, reverse=True)
    elif sort_by == "Year (oldest)":
        display.sort(key=lambda x: x[0].get("year",0) or 0)
    elif sort_by == "Name A-Z":
        display.sort(key=lambda x: x[0].get("name",""))

    if not display:
        st.markdown('<div class="info-box">🔍 No results found. Try broadening your filters or search terms.</div>',
                    unsafe_allow_html=True)
    else:
        for r, sim in display[:60]:
            render_resource_card(r, show_similarity=sim if sim is not None else None)


# ── Page: Smart Recommender ────────────────────────────────────────────────
def page_recommender(resources):
    st.markdown('<div class="section-header" style="font-size:1.5rem">🤖 <span>Smart Recommender</span></div>',
                unsafe_allow_html=True)

    from core.recommender import recommend_for_query, recommend_for_sdgs, sdg_portfolio_gap

    tab1, tab2, tab3 = st.tabs(["💬 Query-based", "🗺️ SDG-based", "📈 Portfolio Gap Analysis"])

    with tab1:
        st.markdown('<div class="info-box">Describe your project, challenge, or need. The AI recommender will find the most relevant resources using semantic similarity + impact scoring.</div>',
                    unsafe_allow_html=True)
        proj_desc = st.text_area(
            "Project description",
            placeholder="e.g. 'We are building a mobile app to help smallholder farmers in West Africa detect crop diseases and access microfinance...'",
            height=120, label_visibility="collapsed",
        )
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            pref_sdgs = st.multiselect("Focus SDGs (optional)", [f"SDG {i} – {SDG_NAMES[i][:25]}" for i in range(1,18)],
                                       key="rec_sdgs")
        with rc2:
            pref_types = st.multiselect("Preferred types", list(TYPE_COLORS.keys()), key="rec_types")
        with rc3:
            top_k = st.slider("Max recommendations", 5, 30, 10)

        if st.button("🚀 Get Recommendations", key="btn_rec"):
            if proj_desc.strip():
                sdg_nums = [int(s.split()[1]) for s in pref_sdgs] if pref_sdgs else None
                with st.spinner("Analyzing and matching…"):
                    recs = recommend_for_query(proj_desc, resources,
                                              sdg_focus=sdg_nums,
                                              preferred_types=pref_types or None,
                                              top_k=top_k)
                if recs:
                    st.markdown(f'<div class="info-box">✅ Found <b>{len(recs)}</b> recommendations for your project.</div>',
                                unsafe_allow_html=True)
                    for item in recs:
                        render_resource_card(item["resource"],
                                           show_similarity=item["similarity"],
                                           show_rec_score=item["rec_score"])
                else:
                    st.warning("No recommendations found. Try a more descriptive query.")
            else:
                st.info("Please enter a project description above.")

    with tab2:
        st.markdown('<div class="info-box">Select one or more SDGs and we\'ll surface the most impactful resources that address your chosen goals.</div>',
                    unsafe_allow_html=True)
        sdg_sel = st.multiselect(
            "Select SDGs",
            options=list(range(1,18)),
            format_func=lambda x: f"SDG {x} – {SDG_NAMES[x]}",
            default=[13,15],
        )
        top_k2 = st.slider("Max results", 5, 30, 12, key="sdg_topk")
        if sdg_sel:
            recs2 = recommend_for_sdgs(sdg_sel, resources, top_k=top_k2)
            for item in recs2:
                render_resource_card(item["resource"], show_rec_score=item["rec_score"])

    with tab3:
        st.markdown('<div class="info-box">Identify which SDGs in your portfolio have the fewest high-quality AI resources, and where to focus next.</div>',
                    unsafe_allow_html=True)
        portfolio = st.multiselect(
            "Your SDG portfolio",
            options=list(range(1,18)),
            format_func=lambda x: f"SDG {x} – {SDG_NAMES[x]}",
            default=list(range(1,18)),
            key="portfolio",
        )
        if portfolio:
            gap_data = sdg_portfolio_gap(portfolio, resources)
            gaps = gap_data["gaps"]
            gdf = pd.DataFrame(gaps)
            fig = px.bar(
                gdf, x="name", y="resource_count",
                color="gap_priority",
                color_continuous_scale=["#22c55e","#f59e0b","#ef4444"],
                hover_data={"avg_impact": True, "gap_priority": True},
                template="plotly_dark",
                labels={"resource_count":"Resources","name":"SDG","gap_priority":"Gap Priority"},
            )
            fig.update_layout(
                plot_bgcolor="#0D1424", paper_bgcolor="#0D1424",
                margin=dict(t=10,b=100,l=10,r=10), height=350,
                xaxis=dict(tickangle=-35, gridcolor="#1E293B"),
                yaxis=dict(gridcolor="#1E293B"),
                font_family="Space Grotesk",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(
                gdf.rename(columns={"sdg":"SDG#","name":"Goal","resource_count":"# Resources",
                                     "avg_impact":"Avg Impact","gap_priority":"Gap Priority %"}),
                hide_index=True, use_container_width=True,
            )


# ── Page: SDG Mapping ──────────────────────────────────────────────────────
def page_sdg_mapping(resources):
    st.markdown('<div class="section-header" style="font-size:1.5rem">🗺️ <span>SDG Mapping</span></div>',
                unsafe_allow_html=True)

    from collections import Counter

    tab1, tab2, tab3 = st.tabs(["🌐 SDG Overview Grid", "🔗 Cross-SDG Network", "📋 Multi-label Explorer"])

    with tab1:
        st.markdown('<div class="info-box">Each card shows total resources, average impact score, and top resource for that SDG.</div>',
                    unsafe_allow_html=True)
        sdg_data = {}
        for i in range(1,18):
            sdg_res = [r for r in resources if i in r.get("sdgs",[])]
            sdg_data[i] = {
                "count": len(sdg_res),
                "avg_score": sum(r.get("impact_score",0) for r in sdg_res) / max(len(sdg_res),1),
                "top": sorted(sdg_res, key=lambda x: x.get("impact_score",0), reverse=True)[:1],
            }
        cols = st.columns(4)
        for i in range(1,18):
            d = sdg_data[i]
            color = SDG_COLORS[i]
            icon = SDG_ICONS.get(i,"🎯")
            top_name = d["top"][0]["name"] if d["top"] else "—"
            with cols[(i-1) % 4]:
                st.markdown(f"""
                <div style="background:{color}11;border:1px solid {color}44;border-radius:14px;
                    padding:1rem;margin-bottom:0.75rem;position:relative;overflow:hidden">
                    <div style="position:absolute;top:-10px;right:-10px;font-size:3rem;opacity:0.08">{icon}</div>
                    <div style="font-family:'Unbounded',sans-serif;font-size:0.65rem;
                        color:{color};font-weight:700;letter-spacing:0.05em">SDG {i}</div>
                    <div style="font-size:0.78rem;font-weight:600;color:#F1F5F9;
                        margin:0.2rem 0;line-height:1.3">{SDG_NAMES[i]}</div>
                    <div style="display:flex;justify-content:space-between;margin-top:0.5rem">
                        <span style="font-size:0.72rem;color:#94A3B8">📦 {d['count']} resources</span>
                        <span style="font-size:0.72rem;color:{color}">⚡ {d['avg_score']:.0f}</span>
                    </div>
                    <div style="font-size:0.68rem;color:#475569;margin-top:0.3rem;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
                        🏆 {top_name[:35]}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="info-box">Resources mapped to multiple SDGs create connections between goals. This network shows cross-SDG AI coverage.</div>',
                    unsafe_allow_html=True)

        # Build cross-SDG matrix
        matrix = [[0]*17 for _ in range(17)]
        for r in resources:
            sdgs = r.get("sdgs",[])
            for i, a in enumerate(sdgs):
                for b in sdgs[i+1:]:
                    if 1 <= a <= 17 and 1 <= b <= 17:
                        matrix[a-1][b-1] += 1
                        matrix[b-1][a-1] += 1

        labels = [f"SDG {i}" for i in range(1,18)]
        fig = go.Figure(go.Heatmap(
            z=matrix, x=labels, y=labels,
            colorscale="Viridis",
            hoverongaps=False,
            hovertemplate="<b>%{x} ↔ %{y}</b><br>Shared resources: %{z}<extra></extra>",
        ))
        fig.update_layout(
            plot_bgcolor="#0D1424", paper_bgcolor="#0D1424",
            margin=dict(t=10,b=80,l=80,r=10), height=550,
            font=dict(family="Space Grotesk", color="#94A3B8"),
            xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
            yaxis=dict(tickfont=dict(size=9)),
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown('<div class="info-box">Browse resources by their multi-SDG label combinations.</div>',
                    unsafe_allow_html=True)
        multi = [r for r in resources if len(r.get("sdgs",[])) > 1]
        st.markdown(f'<div style="color:#64748B;font-size:0.85rem;margin-bottom:1rem">Showing {len(multi)} multi-SDG resources (mapped to 2+ goals)</div>',
                    unsafe_allow_html=True)
        multi.sort(key=lambda x: len(x.get("sdgs",[])), reverse=True)
        for r in multi[:40]:
            render_resource_card(r)


# ── Page: Visualizations ───────────────────────────────────────────────────
def page_visualizations(resources):
    st.markdown('<div class="section-header" style="font-size:1.5rem">📊 <span>Visualizations</span></div>',
                unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🌍 SDG Coverage", "📈 Impact Analysis", "🗺️ Regional", "🔬 Deep Dive"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            sdg_counts = {}
            for i in range(1,18):
                sdg_counts[f"SDG {i}"] = sum(1 for r in resources if i in r.get("sdgs",[]))
            fig = go.Figure(go.Scatterpolar(
                r=list(sdg_counts.values()),
                theta=list(sdg_counts.keys()),
                fill="toself",
                fillcolor="rgba(0,212,255,0.1)",
                line=dict(color="#00D4FF", width=2),
                marker=dict(color="#00D4FF", size=6),
            ))
            fig.update_layout(
                polar=dict(
                    bgcolor="#0D1424",
                    radialaxis=dict(gridcolor="#1E293B", linecolor="#1E293B",
                                   tickfont=dict(color="#475569",size=8)),
                    angularaxis=dict(gridcolor="#1E293B", linecolor="#1E293B",
                                    tickfont=dict(color="#94A3B8",size=9)),
                ),
                paper_bgcolor="#0D1424", plot_bgcolor="#0D1424",
                margin=dict(t=30,b=30,l=30,r=30), height=400,
                showlegend=False, title=dict(text="SDG Coverage Radar",
                    font=dict(color="#F1F5F9",size=14,family="Unbounded")),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Impact score distribution
            scores = [r.get("impact_score",0) for r in resources]
            fig2 = go.Figure(go.Histogram(
                x=scores, nbinsx=20,
                marker_color="#7C3AED",
                marker_line=dict(width=1, color="#0D1424"),
            ))
            fig2.update_layout(
                plot_bgcolor="#0D1424", paper_bgcolor="#0D1424",
                margin=dict(t=30,b=40,l=40,r=10), height=400,
                xaxis=dict(title="Impact Score", gridcolor="#1E293B", color="#94A3B8"),
                yaxis=dict(title="Count", gridcolor="#1E293B", color="#94A3B8"),
                title=dict(text="Impact Score Distribution",
                    font=dict(color="#F1F5F9",size=14,family="Unbounded")),
                font_family="Space Grotesk",
            )
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        # Bubble chart: SDG vs avg score vs count
        sdg_bubble = []
        for i in range(1,18):
            sdg_res = [r for r in resources if i in r.get("sdgs",[])]
            if sdg_res:
                avg = sum(r.get("impact_score",0) for r in sdg_res) / len(sdg_res)
                sdg_bubble.append({
                    "SDG": i, "Name": SDG_NAMES[i][:28], "Count": len(sdg_res),
                    "Avg Impact": avg, "Color": SDG_COLORS[i],
                })
        bdf = pd.DataFrame(sdg_bubble)
        fig3 = px.scatter(
            bdf, x="SDG", y="Avg Impact", size="Count",
            color="SDG", color_discrete_map={i: SDG_COLORS[i] for i in range(1,18)},
            hover_data={"Name":True,"Count":True,"Avg Impact":":.1f"},
            template="plotly_dark",
            size_max=60,
        )
        fig3.update_layout(
            plot_bgcolor="#0D1424", paper_bgcolor="#0D1424",
            margin=dict(t=30,b=40,l=40,r=10), height=450,
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B"),
            title=dict(text="SDG: Resource Count vs. Average Impact Score",
                font=dict(color="#F1F5F9",size=14,family="Unbounded")),
            showlegend=False, font_family="Space Grotesk",
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Box plot by type
        type_scores = [(r.get("type","Other"), r.get("impact_score",0)) for r in resources]
        tdf = pd.DataFrame(type_scores, columns=["Type","Score"])
        fig4 = px.box(
            tdf, x="Type", y="Score", color="Type",
            color_discrete_map=TYPE_COLORS, template="plotly_dark",
        )
        fig4.update_layout(
            plot_bgcolor="#0D1424", paper_bgcolor="#0D1424",
            margin=dict(t=30,b=80,l=40,r=10), height=380,
            xaxis=dict(gridcolor="#1E293B", tickangle=-30),
            yaxis=dict(gridcolor="#1E293B"),
            title=dict(text="Impact Score by Resource Type",
                font=dict(color="#F1F5F9",size=14,family="Unbounded")),
            showlegend=False, font_family="Space Grotesk",
        )
        st.plotly_chart(fig4, use_container_width=True)

    with tab3:
        from collections import Counter
        region_counts = Counter(r.get("region","Unknown") for r in resources)
        rdf = pd.DataFrame(list(region_counts.items()), columns=["Region","Count"])
        rdf = rdf.sort_values("Count", ascending=False).head(15)
        fig5 = px.bar(
            rdf, x="Count", y="Region", orientation="h",
            color="Count", color_continuous_scale=["#19486A","#00D4FF"],
            template="plotly_dark",
        )
        fig5.update_layout(
            plot_bgcolor="#0D1424", paper_bgcolor="#0D1424",
            margin=dict(t=30,b=40,l=10,r=10), height=450,
            yaxis=dict(gridcolor="#1E293B"),
            xaxis=dict(gridcolor="#1E293B"),
            title=dict(text="Resources by Region",
                font=dict(color="#F1F5F9",size=14,family="Unbounded")),
            font_family="Space Grotesk", showlegend=False,
        )
        st.plotly_chart(fig5, use_container_width=True)

    with tab4:
        # Treemap
        rows = []
        for r in resources:
            for s in r.get("sdgs",[]):
                rows.append({
                    "SDG": f"SDG {s} – {SDG_NAMES.get(s,'?')[:20]}",
                    "Type": r.get("type","Other"),
                    "Name": r.get("name","")[:40],
                    "Score": r.get("impact_score",0),
                })
        if rows:
            treedf = pd.DataFrame(rows)
            type_counts = treedf.groupby(["SDG","Type"]).size().reset_index(name="count")
            fig6 = px.treemap(
                type_counts, path=["SDG","Type"], values="count",
                color="count", color_continuous_scale="Viridis",
                template="plotly_dark",
            )
            fig6.update_layout(
                paper_bgcolor="#0D1424", margin=dict(t=30,b=10,l=10,r=10), height=500,
                title=dict(text="Resources: SDG → Type Treemap",
                    font=dict(color="#F1F5F9",size=14,family="Unbounded")),
            )
            fig6.update_traces(textfont=dict(family="Space Grotesk"))
            st.plotly_chart(fig6, use_container_width=True)


# ── Page: API Access ───────────────────────────────────────────────────────
def page_api(resources):
    st.markdown('<div class="section-header" style="font-size:1.5rem">🔌 <span>API Access</span></div>',
                unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        The SDG AI Knowledgebase exposes a full <b>REST API</b> at <code>http://localhost:8765</code>.
        Interactive Swagger docs are available at <a href="http://localhost:8765/api/docs" target="_blank" style="color:#00D4FF">localhost:8765/api/docs</a>.
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📚 Endpoints", "🧪 Try It Live", "💻 Code Samples"])

    with tab1:
        endpoints = [
            ("GET", "/api/v1/resources",      "List all resources with optional filters (sdg, type, year, region, score)"),
            ("GET", "/api/v1/resources/{id}",  "Get a single resource by its database ID"),
            ("GET", "/api/v1/search",          "Semantic search: ?q=your+query&sdg=13&top_k=20"),
            ("GET", "/api/v1/recommend",       "AI recommendations: ?q=description&sdgs=1,3&types=Company"),
            ("GET", "/api/v1/sdgs",            "List all 17 SDGs with resource counts"),
            ("GET", "/api/v1/stats",           "Database statistics, index status, scheduler info"),
            ("GET", "/api/v1/health",          "Service health check & timestamp"),
        ]
        for method, path, desc in endpoints:
            col_m, col_p, col_d = st.columns([1,3,5])
            with col_m:
                st.markdown(f'<span style="background:#22d3ee22;border:1px solid #22d3ee44;color:#22d3ee;border-radius:6px;padding:2px 8px;font-size:0.75rem;font-family:\'JetBrains Mono\',monospace">{method}</span>',
                            unsafe_allow_html=True)
            with col_p:
                st.markdown(f'<code style="color:#7C3AED;font-size:0.82rem">{path}</code>', unsafe_allow_html=True)
            with col_d:
                st.markdown(f'<span style="color:#64748B;font-size:0.82rem">{desc}</span>', unsafe_allow_html=True)
            st.divider()

    with tab2:
        st.markdown("**Live API Tester** – queries run against local FastAPI server")
        api_ep = st.selectbox("Endpoint", [
            "/api/v1/stats", "/api/v1/sdgs", "/api/v1/health",
            "/api/v1/resources?limit=5",
            "/api/v1/search?q=climate+AI&top_k=5",
        ])
        if st.button("▶️ Execute"):
            import requests as req
            try:
                r = req.get(f"http://127.0.0.1:8765{api_ep}", timeout=5)
                st.json(r.json())
            except Exception as e:
                st.error(f"API call failed: {e}\n\nThe API server may need a moment to start.")

    with tab3:
        st.markdown("**Python**")
        st.code("""import requests

BASE = "http://localhost:8765"

# Semantic search
results = requests.get(f"{BASE}/api/v1/search",
    params={"q": "AI for drought prediction Africa", "top_k": 10}).json()

# Get recommendations
recs = requests.get(f"{BASE}/api/v1/recommend",
    params={"q": "renewable energy rural communities",
            "sdgs": "7,1", "types": "Company,Tool"}).json()

# Filter by SDG 13 (Climate Action)
climate = requests.get(f"{BASE}/api/v1/resources",
    params={"sdg": 13, "min_score": 60, "limit": 20}).json()
""", language="python")

        st.markdown("**cURL**")
        st.code("""# Semantic search
curl "http://localhost:8765/api/v1/search?q=food+security+AI&top_k=10"

# Get all SDGs
curl "http://localhost:8765/api/v1/sdgs"

# Filter by type and year
curl "http://localhost:8765/api/v1/resources?type=Company&year_min=2020&min_score=60"
""", language="bash")

        st.markdown("**JavaScript (fetch)**")
        st.code("""const BASE = 'http://localhost:8765';

// Semantic search
const results = await fetch(`${BASE}/api/v1/search?q=water+quality+AI`)
    .then(r => r.json());

// Smart recommendations  
const recs = await fetch(
    `${BASE}/api/v1/recommend?q=ocean+plastic+cleanup&sdgs=14&types=Company`
).then(r => r.json());
""", language="javascript")


# ── Page: Admin ────────────────────────────────────────────────────────────
def page_admin(resources):
    st.markdown('<div class="section-header" style="font-size:1.5rem">⚙️ <span>Admin & System</span></div>',
                unsafe_allow_html=True)

    from core.database import get_stats, get_scrape_log
    from core.scheduler import get_scheduler_status, trigger_manual_update, start_scheduler, stop_scheduler
    from core import embeddings as emb

    tab1, tab2, tab3, tab4 = st.tabs(["📊 System Status", "🔄 Scraper Control", "📋 Scrape Log", "➕ Add Resource"])

    with tab1:
        stats = get_stats()
        sched = get_scheduler_status()
        idx_ready = emb.is_index_built()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Resources", stats["total"])
            st.metric("Scrapes Run", stats.get("scrapes_run",0))
        with col2:
            st.metric("Semantic Index", "✅ Ready" if idx_ready else "⏳ Building")
            st.metric("Scheduler", "🟢 Running" if sched["running"] else "🔴 Stopped")
        with col3:
            st.metric("Last Update", (stats.get("last_update","—") or "—")[:16])
            if sched.get("jobs"):
                st.metric("Next Update", sched["jobs"][0].get("next_run","—")[:16])
        st.json(stats)

    with tab2:
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("▶️ Start Scheduler"):
                start_scheduler(6)
                st.success("Scheduler started (every 6h)")
        with col_b:
            if st.button("⏹️ Stop Scheduler"):
                stop_scheduler()
                st.warning("Scheduler stopped")
        with col_c:
            if st.button("🔄 Run Scraper Now"):
                with st.spinner("Scraping all sources..."):
                    trigger_manual_update()
                st.success("Update triggered in background! Check log in ~30s.")

        st.markdown("---")
        st.markdown("**Scraper Sources**")
        for src, desc in [
            ("ArXiv API", "Recent AI+SDG research papers"),
            ("GitHub API", "Open-source AI+SDG repositories"),
            ("Semantic Scholar", "High-citation academic papers"),
            ("ITU AI for Good", "UN-validated AI solutions"),
            ("UN SDG Platform", "Official UN SDG AI initiatives"),
        ]:
            col_n, col_d = st.columns([2,5])
            with col_n:
                st.markdown(f'<span style="color:#00D4FF;font-weight:600">{src}</span>', unsafe_allow_html=True)
            with col_d:
                st.markdown(f'<span style="color:#64748B;font-size:0.85rem">{desc}</span>', unsafe_allow_html=True)

    with tab3:
        log = get_scrape_log(30)
        if log:
            ldf = pd.DataFrame(log)[["ran_at","source","status","count","message"]]
            ldf["ran_at"] = ldf["ran_at"].str[:16]
            st.dataframe(ldf, hide_index=True, use_container_width=True)
        else:
            st.info("No scrape runs recorded yet. Run the scraper to see logs here.")

    with tab4:
        st.markdown('<div class="info-box">Add a custom AI resource to the knowledgebase manually.</div>',
                    unsafe_allow_html=True)
        with st.form("add_resource"):
            f1, f2 = st.columns(2)
            with f1:
                a_name = st.text_input("Resource Name *")
                a_url  = st.text_input("URL")
                a_type = st.selectbox("Type", list(TYPE_COLORS.keys()))
                a_year = st.number_input("Year", 1990, 2026, 2024)
            with f2:
                a_region = st.text_input("Region", "Global")
                a_tags = st.text_input("Tags (comma-separated)")
                a_sdgs = st.multiselect("SDGs", list(range(1,18)),
                                        format_func=lambda x: f"SDG {x}")
            a_how  = st.text_area("How it helps *", height=80)
            a_desc = st.text_area("Full description *", height=100)
            submitted = st.form_submit_button("➕ Add Resource")
            if submitted:
                if a_name and a_how and a_desc and a_sdgs:
                    from core.database import upsert_resource, update_impact_score
                    from core.impact_scorer import score_resource
                    row = {"name":a_name,"url":a_url,"type":a_type,"year":int(a_year),
                           "region":a_region,"tags":a_tags,"sdgs":a_sdgs,
                           "how":a_how,"description":a_desc,"source":"manual"}
                    is_new = upsert_resource(row)
                    score = score_resource(row)
                    from core.database import get_all_resources
                    all_res = get_all_resources()
                    for r in all_res:
                        if r["name"] == a_name:
                            update_impact_score(r["id"], score)
                    emb.build_index(all_res)
                    st.success(f"{'Added' if is_new else 'Updated'}: {a_name} (score: {score:.1f})")
                else:
                    st.error("Please fill in: Name, SDGs, How it helps, Description")


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    bootstrap()

    from core.database import get_all_resources
    resources = get_all_resources()

    nav = render_sidebar(resources)

    if nav == "Dashboard":
        page_dashboard(resources)
    elif nav == "Search & Explore":
        page_search(resources)
    elif nav == "Smart Recommender":
        page_recommender(resources)
    elif nav == "SDG Mapping":
        page_sdg_mapping(resources)
    elif nav == "Visualizations":
        page_visualizations(resources)
    elif nav == "API Access":
        page_api(resources)
    elif nav == "Admin":
        page_admin(resources)


if __name__ == "__main__":
    main()
