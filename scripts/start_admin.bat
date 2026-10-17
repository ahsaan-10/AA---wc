@echo off
set SITE_ID=%~1
if "%SITE_ID%"=="" set SITE_ID=2

cd /d "%~dp0.."
start "Backend API" cmd /k ""%~dp0start_backend.bat""
timeout /t 3 >nul
start "" "http://127.0.0.1:5001/admin/site/%SITE_ID%/login"
