@echo off
REM Starts the Flask runtime / API / admin host on http://127.0.0.1:5001
cd /d "%~dp0.."
python dragdrop_flask.py
