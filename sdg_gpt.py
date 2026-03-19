# =============================
# SDG AI INTELLIGENCE PLATFORM
# Full Auto-Updating Streamlit App
# =============================

import streamlit as st
import pandas as pd
import requests
import time
import os
from datetime import datetime
from bs4 import BeautifulSoup

# =============================
# CONFIG
# =============================

DATA_FILE = "sdg_master_database.csv"
UPDATE_LOG = "update_log.txt"

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

# =============================
# DATA SOURCES
# =============================

def fetch_openalex(query):
    data = []
    try:
        url = f"https://api.openalex.org/works?search={query}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for item in r.json()["results"]:
                data.append({
                    "Resource Name": item.get("display_name"),
                    "Link": item.get("id"),
                    "Description": item.get("title"),
                    "Year": item.get("publication_year"),
                    "Type": "Research",
                    "Source": "OpenAlex"
                })
    except:
        pass
    return data


def fetch_github(query):
    data = []
    try:
        url = f"https://api.github.com/search/repositories?q={query}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for repo in r.json()["items"]:
                data.append({
                    "Resource Name": repo["name"],
                    "Link": repo["html_url"],
                    "Description": repo["description"],
                    "Year": repo["created_at"][:4],
                    "Type": "Tool",
                    "Source": "GitHub"
                })
    except:
        pass
    return data


def fetch_google(query):
    data = []
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        url = f"https://www.google.com/search?q={query}"
        r = requests.get(url, headers=headers, timeout=10)
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

# =============================
# SDG CLASSIFIER
# =============================

def classify_sdg(text):
    text = str(text).lower()

    if "climate" in text:
        return "SDG 13"
    elif "health" in text:
        return "SDG 3"
    elif "water" in text:
        return "SDG 6"
    elif "education" in text:
        return "SDG 4"
    elif "energy" in text:
        return "SDG 7"
    elif "agriculture" in text or "food" in text:
        return "SDG 2"
    else:
        return "Multiple"

# =============================
# VALIDATION FILTER
# =============================

def is_valid(text):
    keywords = ["ai", "sustain", "climate", "health", "data", "sdg"]
    return any(k in str(text).lower() for k in keywords)

# =============================
# UPDATE ENGINE
# =============================

def update_database():
    df_master = load_data()

    queries = [
        "AI climate change",
        "AI healthcare tools",
        "AI agriculture",
        "sustainability platforms",
        "renewable energy AI"
    ]

    new_data = []

    for q in queries:
        new_data += fetch_openalex(q)
        new_data += fetch_github(q)
        new_data += fetch_google(q)
        time.sleep(2)

    df_new = pd.DataFrame(new_data)

    if df_new.empty:
        return df_master

    df_new["SDG Goal"] = df_new["Description"].apply(classify_sdg)
    df_new = df_new[df_new["Description"].apply(is_valid)]

    df_master = pd.concat([df_master, df_new])
    df_master = df_master.drop_duplicates(subset=["Resource Name", "Link"])

    save_data(df_master)
    log_update("Database updated")

    return df_master

# =============================
# STREAMLIT UI
# =============================

st.set_page_config(page_title="SDG AI Intelligence Platform", layout="wide")

st.title("🌍 SDG AI Intelligence Platform")

# Sidebar
st.sidebar.header("Controls")

if st.sidebar.button("🔄 Update Database"):
    with st.spinner("Fetching latest data..."):
        df = update_database()
    st.success(f"Updated! Total records: {len(df)}")

# Load data

df = load_data()

if df.empty:
    st.warning("No data available. Click update to fetch data.")
else:

    # Filters
    sdg_filter = st.sidebar.multiselect("Filter by SDG", df["SDG Goal"].unique())
    type_filter = st.sidebar.multiselect("Filter by Type", df["Type"].unique())

    filtered_df = df.copy()

    if sdg_filter:
        filtered_df = filtered_df[filtered_df["SDG Goal"].isin(sdg_filter)]

    if type_filter:
        filtered_df = filtered_df[filtered_df["Type"].isin(type_filter)]

    # Search
    search = st.text_input("Search resources")

    if search:
        filtered_df = filtered_df[
            filtered_df["Resource Name"].str.contains(search, case=False, na=False)
        ]

    st.write(f"Showing {len(filtered_df)} resources")

    st.dataframe(filtered_df, use_container_width=True)

    # Download
    st.download_button(
        "Download Data",
        filtered_df.to_csv(index=False),
        "sdg_data.csv",
        "text/csv"
    )

# =============================
# AUTO UPDATE STATUS
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
st.markdown("Built as an Autonomous SDG AI Discovery Engine")
