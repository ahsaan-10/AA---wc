#!/usr/bin/env bash
# Starts the Streamlit operator console on http://127.0.0.1:8501
set -euo pipefail
cd "$(dirname "$0")/.."
python -m streamlit run app.py
