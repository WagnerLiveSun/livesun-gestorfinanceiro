@echo off
REM Script de inicialização do LiveSun Financeiro em Windows

echo.
echo ========================================
echo  LiveSun Financeiro - Inicializador
echo ========================================
echo.

REM Prefer python3.11 para criar ambiente virtual
if exist ".venv" (
    call .venv\Scripts\activate.bat
) else if exist "venv" (
    call venv\Scripts\activate.bat
) else (
    echo Criando ambiente virtual...
    where python3.11 >nul 2>nul
    if %errorlevel%==0 (
        python3.11 -m venv .venv
    ) else (
        echo AVISO: python3.11 nao encontrado. Usando python padrao...
        python -m venv .venv
    )
    call .venv\Scripts\activate.bat
)

REM Verifica versao do Python
for /f "tokens=* delims=" %%i in ('python --version') do set PYVERSION=%%i
set PYVERSION=%PYVERSION:Python =%
set PYMAJOR=%PYVERSION:~0,4%
if "%PYMAJOR%"=="3.13" (
    echo ERRO: Python 3.13 nao e compativel com SQLAlchemy. Use Python 3.11 ou 3.10.
    pause
    exit /b
)

echo Instalando/atualizando dependencias...
pip install -r requirements.txt

echo.
echo Iniciando aplicação...
echo.
python run.py

pause
