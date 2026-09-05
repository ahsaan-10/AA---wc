@echo off
REM Starts the cloner console and prints the key local URLs.
REM Usage: start_all.bat [SITE_ID]
set SITE_ID=%~1
if "%SITE_ID%"=="" set SITE_ID=2

cd /d "%~dp0"

start "Cloner" cmd /k ""%~dp0start_cloner.bat""

echo.
echo Streamlit operator console:
echo http://127.0.0.1:8501
echo.
echo Site-scoped admin URL:
echo http://127.0.0.1:5001/admin/site/%SITE_ID%/login
echo.
echo Example: start_all.bat 35
echo.
pause
