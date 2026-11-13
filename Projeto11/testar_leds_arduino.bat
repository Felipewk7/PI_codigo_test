@echo off
chcp 65001 >nul
title TenniSync - Teste dos 12 LEDs do Arduino

echo ========================================================
echo    TenniSync - Teste de Hardware dos 12 LEDs (Arduino)
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERRO] Ambiente virtual .venv nao encontrado em %PYTHON_EXE%
    pause
    exit /b 1
)

cd /d "%SCRIPT_DIR%src\Entrega 2\Backend"
"%PYTHON_EXE%" testar_leds_arduino.py

echo.
pause
