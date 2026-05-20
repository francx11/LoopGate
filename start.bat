@echo off
title Loopgate
setlocal

echo.
echo ======================================
echo          LOOPGATE  [dev]
echo ======================================
echo.

:: ── 1. Frontend deps ───────────────────────────────────────────────────────────
echo [1/3] Verificando dependencias frontend...
cd frontend
if not exist "node_modules" (
    echo Instalando dependencias npm...
    call npm install --silent
    if errorlevel 1 ( echo ERROR: npm install fallo. & pause & exit /b 1 )
)
cd ..

:: ── 2. Backend deps ────────────────────────────────────────────────────────────
echo [2/3] Preparando backend...
cd backend
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -q -r requirements.txt
cd ..

:: ── 3. Lanzar backend + frontend en paralelo ───────────────────────────────────
echo [3/3] Arrancando servidores...
start "Loopgate Backend" cmd /k "cd /d "%CD%\backend" && set "DEBUG=true" && venv\Scripts\python.exe run.py"
start "Loopgate Frontend" cmd /k "cd /d "%CD%\frontend" && npm run dev"
timeout /t 4 /nobreak > nul

:: ── Mostrar URL de acceso ──────────────────────────────────────────────────────
echo.

set TS_IP=
set TS_BIN=
where tailscale > nul 2>&1
if %errorlevel% == 0 ( set TS_BIN=tailscale )
if not defined TS_BIN (
    if exist "C:\Program Files\Tailscale\tailscale.exe" (
        set "TS_BIN=C:\Program Files\Tailscale\tailscale.exe"
    )
)
if defined TS_BIN (
    for /f "delims=" %%i in ('"%TS_BIN%" ip -4 2^>nul') do set TS_IP=%%i
)

if defined TS_IP (
    echo  ╔══════════════════════════════════════╗
    echo  ║  Loopgate listo via Tailscale        ║
    echo  ║                                      ║
    echo  ║  http://%TS_IP%:5173
    echo  ║                                      ║
    echo  ║  Cambios en .tsx/.css se aplican     ║
    echo  ║  automaticamente sin recargar.       ║
    echo  ║  Cambios en .py recargan backend.    ║
    echo  ╚══════════════════════════════════════╝
    goto :end
)

if defined TS_BIN (
    echo  Tailscale instalado pero sin sesion activa.
    echo  Ejecuta: "%TS_BIN%" login
    echo.
    echo  Acceso local: http://localhost:5173
    goto :end
)

where ngrok > nul 2>&1
if %errorlevel% == 0 (
    echo  Iniciando tunel ngrok en puerto 5173...
    start "Ngrok" ngrok http 5173
    timeout /t 2 /nobreak > nul
    echo  Tunel activo. Abre http://localhost:4040 para ver la URL publica.
    goto :end
)

echo  Para acceso desde el movil instala Tailscale (recomendado):
echo.
echo    winget install tailscale.tailscale
echo.
echo  Acceso local: http://localhost:5173

:end
echo.
pause
