@echo off
title Project TRIDENT SOC Console
echo ==========================================================
echo   PROJECT TRIDENT -- SOC RISK INTELLIGENCE CONSOLE
echo   Trust the context. Track the trajectory. Prove the threat.
echo ==========================================================

cd /d "%~dp0"

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000...
start "TRIDENT Backend" cmd /k "if exist .venv\Scripts\activate.bat (call .venv\Scripts\activate.bat) && uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Next.js SOC Dashboard on http://localhost:3000...
cd frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
)

call npm run dev
