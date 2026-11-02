@echo off
chcp 65001 >nul
title Atualizar Estatisticas - Gamers Club ^& Steam
cls

echo ========================================================
echo   Sincronizando Estatísticas (Gamers Club ^& Steam)...
echo ========================================================
echo.

python sync_now.py

echo.
echo ========================================================
echo   [OK] Sincronização concluída com sucesso!
echo ========================================================
echo Esta janela fechará em 5 segundos...
ping -n 5 127.0.0.1 >nul
