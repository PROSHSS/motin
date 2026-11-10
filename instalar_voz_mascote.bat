@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Instalando voz por REFERENCIA, no seu computador.
echo Recomendado: Windows 64 bits, 16 GB de RAM e 7 GB livres.
echo O download inicial dos modelos e de cerca de 2,6 GB, alem das dependencias.
echo.
if exist ".venv-voz\Scripts\python.exe" goto dependencias
py -3.12 -c "import sys;print(sys.version)" >nul 2>nul
if errorlevel 1 goto python_padrao
py -3.12 -m venv .venv-voz
if errorlevel 1 goto erro
goto dependencias
:python_padrao
python -c "import sys;assert (3,10) <= sys.version_info[:2] <= (3,12) and sys.maxsize > 2**32" >nul 2>nul
if errorlevel 1 goto python_falta
python -m venv .venv-voz
if errorlevel 1 goto erro
:dependencias
".venv-voz\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto erro
".venv-voz\Scripts\python.exe" -m pip install "torch==2.6.0" "torchaudio==2.6.0" --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto erro
".venv-voz\Scripts\python.exe" -m pip install "qwen-tts==0.1.1" "faster-whisper==1.2.1" soundfile
if errorlevel 1 goto erro
".venv-voz\Scripts\python.exe" preparar_voz_referencia.py
if errorlevel 1 goto erro
echo.
echo Pronto. Abra painel.bat e use Ouvir voz.
echo O audio e a transcricao da referencia ja estao incluidos na pasta vozes.
echo A geracao usa o processador e pode demorar alguns minutos.
pause
exit /b 0
:python_falta
echo Instale o Python 3.12 de 64 bits em python.org e execute este arquivo novamente.
pause
exit /b 1
:erro
echo.
echo A instalacao nao foi concluida. Confira as mensagens acima e tente novamente.
echo O instalador reaproveita os arquivos de modelo ja baixados.
pause
exit /b 1
