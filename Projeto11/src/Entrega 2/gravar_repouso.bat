@echo off
title TenniSync - Gravador Autonomo com MediaPipe Pose 3D
cd /d "%~dp0"
cls
echo ======================================================================
echo  TENNISSYNC: GRAVADOR AUTONOMO DE REPOUSO (50 VIDEOS)
echo ======================================================================
echo  Pressione [ESPACO] para iniciar a gravacao do video exibido na tela.
echo  Pressione [P] para pausar o fluxo.
echo  Pressione [Q] para encerrar e salvar o progresso.
echo ======================================================================
echo.
set "PYTHON_EXE=..\..\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"
"%PYTHON_EXE%" Backend\record_batch_repouso.py
echo.
echo Sessao finalizada.
pause
