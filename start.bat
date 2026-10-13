@echo off
title RAG-Powered Document Assistant Launcher
echo ===================================================
echo   Starting RAG-Powered Document Assistant
echo ===================================================

echo [1/3] Checking Ollama daemon...
start "Ollama Service" cmd /k "ollama serve"

timeout /t 2 /nobreak >nul

echo [2/3] Launching FastAPI Backend...
start "FastAPI Backend" cmd /k "cd /d %~dp0backend && ..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [3/3] Launching Vite Frontend...
start "React Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ===================================================
echo   All services launched!
echo   Frontend UI : http://localhost:3000
echo   Backend API : http://127.0.0.1:8000/docs
echo   Ollama      : http://127.0.0.1:11434
echo ===================================================
timeout /t 3 /nobreak >nul
start http://localhost:3000
