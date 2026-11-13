@echo off
title TennisSync - Modo Jogo Arcade (OpenCV HUD)
color 0B
cls
echo ==============================================================================
echo                     TENNISSYNC - MODO ARCADE (OPENCV)
echo ==============================================================================
echo.
set "ROOT_DIR=%~dp0"
set "PYTHON_EXE=%ROOT_DIR%.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

cd /d "%ROOT_DIR%src\Entrega 2\Backend"
"%PYTHON_EXE%" pose_estimation.py --source 0 --lateralidade destro
pause
