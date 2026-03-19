# =============================
# SDG AI INTELLIGENCE PLATFORM (ENHANCED SCRAPING + MULTI-SDG)
# =============================

import streamlit as st
import pandas as pd
import requests
import time
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup

# =============================
# CONFIG
# =============================

DATA_FILE = "sdg_master_database.csv"
UPDATE_LOG = "update_log.txt"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# =============================
# UTILITY FUNCTIONS
# =============================

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame()


def save_data(df):
    df.to_csv(DATA_FILE, index=False)


def log_update(msg):
    with open(UPDATE_LOG, "a") as f:
        f.write(f"{datetime.now()} - {msg}\n")


def clean_html(text):
    return re.sub('<.*?>', '', str(text))

# =============================
# SDG MULTI-CLASSIFIER (RETURNS NUMBERS)
# =============================

def classify_sdg_multi(text):
    text = str(text).lower()
    sdgs = []

    if any(k in text for k in ["poverty", "income"]): sdgs.append("SDG 1")
    if any(k in text for k in ["agriculture", "food", "crop"]): sdgs.append("SDG 2")
    if any(k in text for k in ["health", "disease", "medical"]): sdgs.append("SDG 3")
    if "education" in text: sdgs.append("SDG 4")
    if "gender" in text: sdgs.append("SDG 5")
    if "water" in text: sdgs.append("SDG 6")
    if "energy" in text: sdgs.append("SDG 7")
    if "economic" in text: sdgs.append("SDG 8")
    if any(k in text for k in ["industry", "innovation", "infrastructure"]): sdgs.append("SDG 9")
    if "inequality" in text: sdgs.append("SDG 10")
    if "city" in text: sdgs.append("SDG 11")
    if "consumption" in text or "waste" in text: sdgs.append("SDG 12")
    if "climate" in text: sdgs.append("SDG 13")
    if "ocean" in text or "marine" in text: sdgs.append("SDG 14")
    if "forest" in text or "biodiversity" in text: sdgs.append("SDG 15")
    if "justice" in text or "governance" in text: sdgs.append("SDG 16")
    if "partnership" in text: sdgs.append("SDG 17")

    return ", ".join(sorted(set(sdgs))) if sdgs else "Multiple"

# =============================
# VALIDATION FILTER
# =============================

def is_valid(text):
    keywords = ["ai", "sustain", "climate", "health", "data", "energy", "water"]
    return any(k in str(text).lower() for k in keywords)

# =============================
# DATA SOURCES (EXPANDED)
# =============================

# -------- OpenAlex (Research)

def fetch_openalex(query):
    data = []
    try:
        url = f"https://api.openalex.org/works?search={query}&per_page=25"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for item in r.json().get("results", []):
                desc = item.get("title")
                data.append({
                    "Resource Name": item.get("display_name"),
                    "Link": item.get("id"),
                    "Description": desc,
                    "Year": item.get("publication_year"),
                    "Type": "Research",
                    "Source": "OpenAlex"
                })
    except:
        pass
    return data

# -------- GitHub (Tools)

def fetch_github(query):
    data = []
    try:
        url = f"https://api.github.com/search/repositories?q={query}&per_page=30"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for repo in r.json().get("items", []):
                data.append({
                    "Resource Name": repo.get("name"),
                    "Link": repo.get("html_url"),
                    "Description": repo.get("description"),
                    "Year": repo.get("created_at", "")[:4],
                    "Type": "Tool",
                    "Source": "GitHub"
                })
    except:
        pass
    return data

# -------- Google (Web)

def fetch_google(query):
    data = []
    try:
        url = f"https://www.google.com/search?q={query}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        for g in soup.find_all('div', class_='tF2Cxc'):
            try:
                title = g.find('h3').text
                link = g.find('a')['href']
                desc = g.find('span').text if g.find('span') else ""

                data.append({
                    "Resource Name": title,
                    "Link": link,
                    "Description": desc,
                    "Year": "",
                    "Type": "Web",
                    "Source": "Google"
                })
            except:
                continue
    except:
        pass
    return data

# -------- arXiv (Research)

def fetch_arxiv(query):
    data = []
    try:
        url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=20"
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "xml")

        for entry in soup.find_all("entry"):
            data.append({
                "Resource Name": entry.title.text,
                "Link": entry.id.text,
                "Description": entry.summary.text,
                "Year": entry.published.text[:4],
                "Type": "Research",
                "Source": "arXiv"
            })
    except:
        pass
    return data

# -------- Patents (PatentsView API)

def fetch_patents(query):
    data = []
    try:
        url = f"https://api.patentsview.org/patents/query?q={{\"_text_any\":{{\"patent_title\":\"{query}\"}}}}&f=[\"patent_title\",\"patent_date\"]"
        r = requests.get(url)
        if r.status_code == 200:
            for p in r.json().get("patents", []):
                data.append({
                    "Resource Name": p.get("patent_title"),
                    "Link": "",
                    "Description": p.get("patent_title"),
                    "Year": p.get("patent_date", "")[:4],
                    "Type": "Patent",
                    "Source": "PatentsView"
                })
    except:
        pass
    return data

# -------- World Bank Indicators

def fetch_worldbank():
    data = []
    try:
        url = "https://api.worldbank.org/v2/indicator?format=json&per_page=50"
        r = requests.get(url)
        if r.status_code == 200:
            for item in r.json()[1]:
                data.append({
                    "Resource Name": item.get("name"),
                    "Link": "",
                    "Description": item.get("sourceNote"),
                    "Year": "",
                    "Type": "Dataset",
                    "Source": "WorldBank"
                })
    except:
        pass
    return data

# =============================
# UPDATE ENGINE (ALL SOURCES)
# =============================

def update_database():
    df_master = load_data()

    queries = [
        "AI climate change",
        "AI healthcare",
        "AI agriculture",
        "sustainable energy",
        "water sustainability"
    ]

    new_data = []

    for q in queries:
        new_data += fetch_openalex(q)
        new_data += fetch_github(q)
        new_data += fetch_google(q)
        new_data += fetch_arxiv(q)
        new_data += fetch_patents(q)
        time.sleep(2)

    new_data += fetch_worldbank()

    df_new = pd.DataFrame(new_data)

    if df_new.empty:
        return df_master

    df_new["Description"] = df_new["Description"].apply(clean_html)
    df_new = df_new[df_new["Description"].apply(is_valid)]

    df_new["SDG Goal"] = df_new["Description"].apply(classify_sdg_multi)

    df_master = pd.concat([df_master, df_new])
    df_master = df_master.drop_duplicates(subset=["Resource Name", "Link"])

    save_data(df_master)
    log_update("Database updated with multi-source scraping")

    return df_master

# =============================
# STREAMLIT UI
# =============================

st.set_page_config(page_title="SDG-AI Intelligence Platform", layout="wide")
st.title("SDG-AI: An Intelligent Platform for webscrapping SDG data (for YG and TG only) ")

st.sidebar.header("Controls")

if st.sidebar.button("🔄 Update Database"):
    with st.spinner("Collecting global SDG resources..."):
        df = update_database()
    st.success(f"Updated! Total records: {len(df)}")


df = load_data()

if df.empty:
    st.warning("No data available. Click update to fetch data.")
else:

    sdg_filter = st.sidebar.multiselect("Filter by SDG", df["SDG Goal"].dropna().unique())
    type_filter = st.sidebar.multiselect("Filter by Type", df["Type"].dropna().unique())

    filtered_df = df.copy()

    if sdg_filter:
        filtered_df = filtered_df[filtered_df["SDG Goal"].isin(sdg_filter)]

    if type_filter:
        filtered_df = filtered_df[filtered_df["Type"].isin(type_filter)]

    search = st.text_input("Search resources")

    if search:
        filtered_df = filtered_df[
            filtered_df["Resource Name"].str.contains(search, case=False, na=False)
        ]

    st.write(f"Showing {len(filtered_df)} resources")
    st.dataframe(filtered_df, use_container_width=True)

    st.download_button("Download Data", filtered_df.to_csv(index=False), "sdg_data.csv")

# =============================
# UPDATE LOG
# =============================

if os.path.exists(UPDATE_LOG):
    with open(UPDATE_LOG, "r") as f:
        logs = f.readlines()[-5:]

    st.sidebar.subheader("Recent Updates")
    for log in logs:
        st.sidebar.text(log.strip())

# =============================
# FOOTER
# =============================

st.markdown("---")
st.markdown("Autonomous Multi-Source SDG AI Discovery Engine")
st.markdown("Designed by Tushar Gupta")
