@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo  ANALISAR VIDEOS DE REFERENCIA
echo  Arraste um ou mais videos para cima deste arquivo (ou uma pasta).
echo  Vai gerar perfis em "estilos\ref_*.json" (ritmo, cores, cenas preferidas).
echo ============================================================
if "%~1"=="" (
  echo Nenhum video informado. Arraste os videos sobre este arquivo.
  pause
  exit /b 1
)
:loop
if "%~1"=="" goto fim
python referencias.py "%~1"
shift
goto loop
:fim
echo.
echo Pronto. Para usar um perfil:  python criar.py --estilo ref_NOME
echo (os perfis tambem entram no sorteio automatico de estilos)
pause
