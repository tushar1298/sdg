#!/usr/bin/env python3
"""
run.py – One-command launcher for the SDG AI Knowledgebase.
Usage:  python run.py
"""
import subprocess, sys, os

APP = os.path.join(os.path.dirname(__file__), "app.py")

cmd = [
    sys.executable, "-m", "streamlit", "run", APP,
    "--server.port", "8501",
    "--server.address", "0.0.0.0",
    "--server.headless", "true",
    "--browser.gatherUsageStats", "false",
]
print("🌍 Starting SDG AI Knowledgebase on http://localhost:8501")
print("🔌 REST API will be available at http://localhost:8765/api/docs")
print("Press Ctrl+C to stop.\n")
subprocess.run(cmd)
