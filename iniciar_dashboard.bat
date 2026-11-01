@echo off
chcp 65001 >nul
title Dashboard CS2 - Gamers Club ^& Steam
cls

echo ========================================================
echo   Iniciando Dashboard CS2 (Gamers Club ^& Steam)...
echo ========================================================
echo.

:: Verifica se o Python esta no PATH
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Python nao foi encontrado no PATH do sistema.
    echo Instale o Python ou adicione-o as variaveis de ambiente.
    pause
    exit /b 1
)

echo [1/2] Otimizando inicializacao (sem telemetria)...
echo [2/2] Abrindo navegador em http://localhost:8501 ...
echo.

python -m streamlit run app.py --browser.gatherUsageStats false

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERRO] O servidor foi encerrado com codigo de erro %ERRORLEVEL%.
    pause
)
