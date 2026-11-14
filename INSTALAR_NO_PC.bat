@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Atualizacao Motion Pro - Instalacao local
where py >nul 2>nul
if not errorlevel 1 (
    py -3 instalar.py
) else (
    python instalar.py
)
if errorlevel 1 (
    echo.
    echo [ERRO] Nada foi alterado se a verificacao inicial falhou.
    echo Confirme se voce escolheu a pasta que contem painel.py e motion_editor.py.
) else (
    echo.
    echo [OK] Instalacao concluida. Abra seu painel.bat normalmente.
)
echo.
pause
