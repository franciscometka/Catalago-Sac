@echo off
REM ============================================================
REM  Catalogo SAC - inicializador local (Windows)
REM  Primeira execucao: cria a venv e instala as dependencias.
REM  Proximas execucoes: apenas sobe o app.
REM ============================================================
cd /d "%~dp0"

if not exist "venv\" (
    echo Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo [ERRO] Python nao encontrado. Instale o Python e tente de novo.
        pause
        exit /b 1
    )
    echo Instalando dependencias...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

if not exist ".streamlit\secrets.toml" (
    echo.
    echo [ATENCAO] Arquivo .streamlit\secrets.toml nao encontrado.
    echo Copie .streamlit\secrets.toml.example para .streamlit\secrets.toml
    echo e preencha a connection string do Supabase antes de usar o app.
    echo.
    pause
)

echo Iniciando o Catalogo SAC...
streamlit run app.py
pause
