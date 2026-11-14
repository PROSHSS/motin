@echo off
REM Copia os arquivos gerados na pasta doc-tiktok para o projeto de video
copy /Y "..\roteiro.json" "public\roteiro.json"
copy /Y "..\tempos_cenas.json" "public\tempos_cenas.json"
copy /Y "..\palavras.json" "public\palavras.json"
copy /Y "..\narracao.wav" "public\narracao.wav"
echo Pronto.
pause
