#!/usr/bin/env bash
# Starts the Flask runtime / API / admin host on http://127.0.0.1:5001
set -euo pipefail
cd "$(dirname "$0")/.."
python dragdrop_flask.py
