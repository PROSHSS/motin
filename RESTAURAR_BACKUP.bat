@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Restaurar Motion - Versao Anterior
where py >nul 2>nul
if not errorlevel 1 (
    py -3 instalar.py --restaurar
) else (
    python instalar.py --restaurar
)
echo.
pause
