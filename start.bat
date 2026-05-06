@echo off
title Loopgate
setlocal

echo.
echo ======================================
echo          LOOPGATE
echo ======================================
echo.

:: ── 1. Build frontend ─────────────────────────────────────────────────────────
echo [1/3] Compilando frontend...
cd frontend

if not exist "node_modules" (
    echo Instalando dependencias npm...
    call npm install --silent
    if errorlevel 1 ( echo ERROR: npm install fallo. & pause & exit /b 1 )
)

call npm run build
if errorlevel 1 ( echo ERROR: npm build fallo. & pause & exit /b 1 )
cd ..

:: ── 2. Prepare backend ────────────────────────────────────────────────────────
echo [2/3] Preparando backend...
cd backend

if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -q -r requirements.txt
cd ..

:: ── 3. Start backend in separate window ───────────────────────────────────────
echo [3/3] Arrancando servidor en http://localhost:8000
start "Loopgate Backend" cmd /k "cd /d "%CD%\backend" && venv\Scripts\python.exe run.py"

timeout /t 3 /nobreak > nul

:: ── Ngrok tunnel (optional) ───────────────────────────────────────────────────
where ngrok > nul 2>&1
if %errorlevel% == 0 (
    echo.
    echo Iniciando tunel ngrok...
    start "Ngrok Tunnel" ngrok http 8000
    timeout /t 2 /nobreak > nul
    echo.
    echo  Tunel activo. Abre http://localhost:4040 para ver la URL publica.
    echo  Copia la URL https://... en tu movil y conectate directamente.
) else (
    echo.
    echo  Ngrok no encontrado. Para acceso desde movil:
    echo    1. Descarga ngrok en https://ngrok.com/download
    echo    2. Ejecuta: ngrok http 8000
    echo    3. Usa la URL https://... en tu navegador movil
    echo.
    echo  Acceso local: http://localhost:8000
)

echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause > nul
