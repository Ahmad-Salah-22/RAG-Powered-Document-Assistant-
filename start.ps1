# RAG-Powered Document Assistant PowerShell Launcher
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   Starting RAG-Powered Document Assistant" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Cyan

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Start Ollama
Write-Host "[1/3] Starting Ollama service..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ollama serve"

Start-Sleep -Seconds 2

# 2. Start FastAPI Backend
Write-Host "[2/3] Starting FastAPI backend on http://127.0.0.1:8000..." -ForegroundColor Yellow
$backendCmd = "Set-Location '$rootDir\backend'; ..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

Start-Sleep -Seconds 2

# 3. Start Vite Frontend
Write-Host "[3/3] Starting React frontend dev server on http://localhost:3000..." -ForegroundColor Yellow
$frontendCmd = "Set-Location '$rootDir\frontend'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   All services started successfully!" -ForegroundColor Green
Write-Host "   Frontend Web UI : http://localhost:3000" -ForegroundColor White
Write-Host "   Backend API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "===================================================" -ForegroundColor Cyan

Start-Sleep -Seconds 3
Start-Process "http://localhost:3000"
