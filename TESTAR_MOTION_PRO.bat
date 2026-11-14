@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Testar Motion Pro
where py >nul 2>nul
if not errorlevel 1 (
    py -3 verificar.py
) else (
    python verificar.py
)
echo.
pause
