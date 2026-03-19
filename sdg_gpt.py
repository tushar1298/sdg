# ==========================================================
# SDG AI INTELLIGENCE PLATFORM - ADVANCED (LLM + GRAPH + NLP)
# ==========================================================

import streamlit as st
import pandas as pd
import requests
import os
import time
import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from neo4j import GraphDatabase

# =============================
# CONFIG
# =============================
DATA_FILE = "sdg_master.csv"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"

embed_model = SentenceTransformer('all-MiniLM-L6-v2')
llm_classifier = pipeline("text-classification", model="facebook/bart-large-mnli")

# =============================
# LOAD/SAVE
# =============================

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame()


def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# =============================
# LLM SDG CLASSIFIER
# =============================

SDG_LABELS = [
    "No Poverty","Zero Hunger","Good Health","Quality Education",
    "Gender Equality","Clean Water","Affordable Energy",
    "Economic Growth","Industry Innovation","Reduced Inequality",
    "Sustainable Cities","Responsible Consumption","Climate Action",
    "Life Below Water","Life on Land","Peace Justice","Partnerships"
]


def classify_sdg_llm(text):
    try:
        result = llm_classifier(text, SDG_LABELS)
        return result[0]['label']
    except:
        return "Unknown"

# =============================
# MULTI-LANGUAGE SUPPORT
# =============================

translator = pipeline("translation", model="Helsinki-NLP/opus-mt-mul-en")


def translate_to_english(text):
    try:
        return translator(text)[0]['translation_text']
    except:
        return text

# =============================
# EMBEDDINGS + SEARCH
# =============================

def compute_embeddings(df):
    return embed_model.encode(df["Description"].fillna("").tolist())


def semantic_search(query, df, embeddings):
    q_emb = embed_model.encode([query])[0]
    scores = np.dot(embeddings, q_emb)
    idx = np.argsort(scores)[-10:][::-1]
    return df.iloc[idx]

# =============================
# GPT-STYLE EXPLANATION
# =============================


def generate_explanation(query, row):
    return f"This resource '{row['Resource Name']}' is relevant to '{query}' because it focuses on {row['Description']} and contributes to {row['SDG']} goals."

# =============================
# DATA FETCH
# =============================

def fetch_openalex(query):
    url = f"https://api.openalex.org/works?search={query}"
    r = requests.get(url)
    data = []
    if r.status_code == 200:
        for item in r.json()["results"]:
            desc = item.get("title")
            desc_en = translate_to_english(desc)
            data.append({
                "Resource Name": item.get("display_name"),
                "Description": desc_en,
                "Link": item.get("id"),
                "Type": "Research",
                "SDG": classify_sdg_llm(desc_en),
                "Organization": "Research",
                "Country": "Global"
            })
    return data

# =============================
# NEO4J GRAPH
# =============================

class Neo4jGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def insert_data(self, df):
        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.run("""
                MERGE (t:Tool {name:$tool})
                MERGE (s:SDG {name:$sdg})
                MERGE (o:Org {name:$org})
                MERGE (c:Country {name:$country})
                MERGE (t)-[:ALIGNS_WITH]->(s)
                MERGE (t)-[:BUILT_BY]->(o)
                MERGE (o)-[:LOCATED_IN]->(c)
                """, tool=row['Resource Name'], sdg=row['SDG'],
                     org=row['Organization'], country=row['Country'])

# =============================
# UPDATE
# =============================

def update_database():
    df = load_data()
    queries = ["AI climate", "AI health", "AI agriculture"]

    new_data = []
    for q in queries:
        new_data += fetch_openalex(q)
        time.sleep(1)

    df_new = pd.DataFrame(new_data)

    df = pd.concat([df, df_new])
    df = df.drop_duplicates(subset=["Resource Name", "Link"])

    save_data(df)
    return df

# =============================
# STREAMLIT UI
# =============================

st.set_page_config(layout="wide")
st.title("🌍 SDG AI Intelligence Platform (ULTIMATE)")

if st.button("Update Database"):
    df = update_database()
    st.success(f"Updated {len(df)} records")


df = load_data()

if not df.empty:

    embeddings = compute_embeddings(df)

    query = st.text_input("🔍 Ask (semantic search)")

    if query:
        results = semantic_search(query, df, embeddings)

        for _, row in results.iterrows():
            st.subheader(row["Resource Name"])
            st.write("SDG:", row["SDG"])
            st.write(generate_explanation(query, row))
            st.markdown(row["Link"])

    st.dataframe(df)

# =============================
# GRAPH EXPORT
# =============================

if st.button("Push to Neo4j"):
    graph = Neo4jGraph(NEO4J_URI, NEO4J_USER, NEO4J_PASS)
    graph.insert_data(df)
    graph.close()
    st.success("Graph updated in Neo4j")

st.markdown("---")
st.markdown("Next-gen SDG AI Knowledge Engine")
