@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ===== CRIADOR DE VIDEOS =====
echo  (roteiro + narracao + legenda + musica + efeitos + edicao Showcase)
echo.
echo  1 = criar um video (voce digita o tema)
echo  2 = criar varios videos (le o arquivo temas.txt, um tema por linha)
echo  3 = verificar se esta tudo instalado certo
echo.
set /p MODO=Escolha 1, 2 ou 3: 
if "%MODO%"=="3" (
  python criar.py --verificar
  pause
  exit /b
)
set ARGS=
if exist fatos.txt (
  echo Encontrei fatos.txt: vou usar esses fatos no roteiro.
  set ARGS=--fatos fatos.txt
)
if "%MODO%"=="2" (
  if not exist temas.txt (
    echo Crie o arquivo temas.txt nesta pasta, com um tema por linha.
    pause
    exit /b
  )
  python criar.py --lote temas.txt %ARGS%
  pause
  exit /b
)
set /p TEMA=Digite o tema do video: 
if "%TEMA%"=="" (
  echo Nenhum tema digitado.
  pause
  exit /b
)
python criar.py "%TEMA%" %ARGS%
echo.
pause
