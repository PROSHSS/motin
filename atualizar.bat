@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
where git >nul 2>nul
if errorlevel 1 (
  echo Instale o Git ou use o GitHub Desktop para atualizar este projeto.
  pause
  exit /b 1
)
git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
  echo Esta pasta veio de um ZIP. Clone o repositorio para usar a atualizacao por Git.
  pause
  exit /b 1
)
git diff --quiet
if errorlevel 1 goto alteracoes
git diff --cached --quiet
if errorlevel 1 goto alteracoes
echo Feche o painel e aguarde os trabalhos terminarem antes de continuar.
pause
git pull --ff-only
if errorlevel 1 (
  echo Nao foi possivel atualizar. Confira a mensagem acima. Nenhuma atualizacao foi forcada.
  pause
  exit /b 1
)
echo Atualizacao concluida. Abra painel.bat para usar o editor.
pause
exit /b 0
:alteracoes
echo Ha alteracoes locais nos arquivos do programa. Salve ou revise essas alteracoes antes de atualizar.
echo A atualizacao foi interrompida para preservar o seu trabalho.
pause
exit /b 1
