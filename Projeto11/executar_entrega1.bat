@echo off
title TennisSync - Executar Entrega 1 (OpenCV Standalone)
color 0E
cls
echo ==============================================================================
echo                         TENNISSYNC - ENTREGA 1
echo ==============================================================================
echo.
set "ROOT_DIR=%~dp0"
set "PYTHON_EXE=%ROOT_DIR%.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

cd /d "%ROOT_DIR%src\Entrega 1\Backend"
"%PYTHON_EXE%" pose_estimation.py
pause
