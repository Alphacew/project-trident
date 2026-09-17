# Project TRIDENT — Unified Demo Runner Script
# Launches both the FastAPI Backend and the Next.js SOC Console

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  PROJECT TRIDENT — SOC RISK INTELLIGENCE CONSOLE        " -ForegroundColor Cyan
Write-Host "  Trust the context. Track the trajectory. Prove the threat." -ForegroundColor DarkCyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ROOT_DIR = $PSScriptRoot

# 1. Start FastAPI Backend in background job
Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
$BackendJob = Start-Job -ScriptBlock {
    param($Dir)
    Set-Location $Dir
    if (Test-Path ".venv\Scripts\activate.ps1") {
        & .venv\Scripts\activate.ps1
    }
    uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --reload
} -ArgumentList $ROOT_DIR

Start-Sleep -Seconds 2

# 2. Start Next.js Frontend
Write-Host "[2/2] Starting Next.js SOC Dashboard on http://localhost:3000..." -ForegroundColor Green
Set-Location "$ROOT_DIR\frontend"

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
}

Write-Host "Launching Next.js development server..." -ForegroundColor Cyan
npm run dev

# Cleanup on exit
Stop-Job $BackendJob
Remove-Job $BackendJob
