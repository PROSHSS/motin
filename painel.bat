@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Abrindo o painel no navegador... (deixe esta janela aberta)
python painel.py
pause
