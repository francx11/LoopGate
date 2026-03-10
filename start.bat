@echo off
title Loopgate Server

echo.
echo ======================================
echo          LOOPGATE SERVER
echo ======================================
echo.

cd backend

if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Instalando dependencias...
pip install -q -r requirements.txt

echo.
echo   API:       http://localhost:8000
echo   Docs:      http://localhost:8000/docs
echo.
echo   Presiona Ctrl+C para detener
echo.

python run.py
pause
