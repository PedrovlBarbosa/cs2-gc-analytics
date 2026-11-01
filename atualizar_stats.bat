@echo off
title Atualizar Estatisticas Gamers Club
echo ========================================================
echo   Sincronizando estatisticas recentes da Gamers Club...
echo ========================================================
python sync_now.py
echo.
echo [OK] Banco de dados atualizado com sucesso!
timeout /t 5
