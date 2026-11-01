@echo off
title Atualizar Estatisticas Gamers Club
echo ========================================================
echo   Sincronizando estatisticas recentes da Gamers Club...
echo ========================================================
python sync_now.py
echo.
echo [OK] Processo finalizado com sucesso!
ping -n 5 127.0.0.1 >nul
