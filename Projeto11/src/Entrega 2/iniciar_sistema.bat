@echo off
title TennisSync - Inicializador do Sistema Completo (Entrega 2)
color 0A
cls
echo ==============================================================================
echo                          TENNISSYNC (ENTREGA 2)
echo       Sistema de Analise Biomecanica em Tempo Real para Tenistas
echo ==============================================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=%SCRIPT_DIR%..\..\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

:: Garante Node.js no PATH se necessario
where node >nul 2>&1
if errorlevel 1 (
    if exist "%USERPROFILE%\Downloads\node-v24.17.0-win-x64\node-v24.17.0-win-x64\node.exe" (
        set "PATH=%USERPROFILE%\Downloads\node-v24.17.0-win-x64\node-v24.17.0-win-x64;%PATH%"
    )
)

echo [1/2] Iniciando Servidor Backend (FastAPI + WebSocket na porta 8000)...
start "TenniSync - Backend Server" cmd /k "cd /d "%SCRIPT_DIR%Backend" && "%PYTHON_EXE%" server.py"

echo [2/2] Iniciando Interface Web Frontend (Vite + React na porta 3000)...
start "TenniSync - Frontend Web" cmd /k "cd /d "%SCRIPT_DIR%Frontend" && npm run dev"

echo.
echo Aguardando inicializacao dos servicos...
timeout /t 3 >nul

echo Abrindo o navegador em http://localhost:3000 ...
start http://localhost:3000

echo.
echo ==============================================================================
echo  TenniSync esta em execucao!
echo  - Backend API: http://localhost:8000/docs
echo  - Interface Web: http://localhost:3000
echo.
echo  Para encerrar o sistema, basta fechar as janelas abertas.
echo ==============================================================================
echo.
pause
