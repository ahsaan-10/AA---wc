@echo off
set SITE_ID=%~1
if "%SITE_ID%"=="" set SITE_ID=2

cd /d "%~dp0.."

start "Cloner" cmd /k ""%~dp0start_cloner.bat""

echo.
echo Cloner URL:
echo http://127.0.0.1:8501
echo.
echo Site-specific admin URL:
echo http://127.0.0.1:5001/admin/site/%SITE_ID%/login
echo.
echo.
echo.
pause
