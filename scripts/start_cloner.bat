@echo off
REM Starts the Streamlit operator console on http://127.0.0.1:8501
cd /d "%~dp0.."
python -m streamlit run app.py
