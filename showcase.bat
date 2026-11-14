@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ===== SHOWCASE: VIDEO DE ANIMACAO =====
echo.
echo  1 = um tema
echo  2 = varios temas (arquivo temas.txt, um por linha)
echo.
set /p MODO=Escolha 1 ou 2: 
if "%MODO%"=="2" (
  if not exist temas.txt (
    echo Crie o arquivo temas.txt nesta pasta, com um tema por linha.
    pause
    exit /b
  )
  python criar_showcase.py --lote temas.txt
  pause
  exit /b
)
set /p TEMA=Digite o tema do video: 
if "%TEMA%"=="" (
  echo Nenhum tema digitado.
  pause
  exit /b
)
set ARGS=
if exist fatos.txt (
  echo Encontrei fatos.txt: vou usar esses fatos.
  set ARGS=--fatos fatos.txt
)
python criar_showcase.py "%TEMA%" %ARGS%
echo.
pause
