@echo off
title TennisSync - Inicializador do Sistema Completo
color 0A
cls
echo ==============================================================================
echo                          TENNISSYNC (ENTREGA 2)
echo       Sistema de Analise Biomecanica em Tempo Real para Tenistas
echo ==============================================================================
echo.
echo  Configurando caminhos e ambiente...

set "ROOT_DIR=%~dp0"
set "PYTHON_EXE=%ROOT_DIR%.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERRO] Ambiente virtual .venv nao encontrado em %PYTHON_EXE%!
    pause
    exit /b 1
)

:: Garante Node.js no PATH se necessario
where node >nul 2>&1
if errorlevel 1 (
    if exist "%USERPROFILE%\Downloads\node-v24.17.0-win-x64\node-v24.17.0-win-x64\node.exe" (
        set "PATH=%USERPROFILE%\Downloads\node-v24.17.0-win-x64\node-v24.17.0-win-x64;%PATH%"
    )
)

echo.
echo [1/2] Iniciando Servidor Backend (FastAPI + WebSocket na porta 8000)...
start "TenniSync - Backend Server" cmd /k "cd /d "%ROOT_DIR%src\Entrega 2\Backend" && "%PYTHON_EXE%" server.py"

echo [2/2] Iniciando Interface Web Frontend (Vite + React na porta 3000)...
start "TenniSync - Frontend Web" cmd /k "cd /d "%ROOT_DIR%src\Entrega 2\Frontend" && npm run dev"

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
