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

:: ── 3. Start backend ──────────────────────────────────────────────────────────
echo [3/3] Arrancando servidor...
start "Loopgate Backend" cmd /k "cd /d "%CD%\backend" && venv\Scripts\python.exe run.py"
timeout /t 3 /nobreak > nul

:: ── Mostrar URL de acceso ─────────────────────────────────────────────────────
echo.

:: Tailscale (prioritario — IP fija, sin tunel publico)
set TS_IP=
where tailscale > nul 2>&1
if %errorlevel% == 0 (
    for /f "delims=" %%i in ('tailscale ip -4 2^>nul') do set TS_IP=%%i
)

if defined TS_IP (
    echo  ╔══════════════════════════════════════╗
    echo  ║  Loopgate listo via Tailscale        ║
    echo  ║                                      ║
    echo  ║  http://%TS_IP%:8000
    echo  ║                                      ║
    echo  ║  Abre esa URL en tu movil.           ║
    echo  ║  La app se conecta automaticamente.  ║
    echo  ╚══════════════════════════════════════╝
    goto :end
)

:: Tailscale instalado pero sin IP (no conectado)
where tailscale > nul 2>&1
if %errorlevel% == 0 (
    echo  Tailscale instalado pero sin conexion activa.
    echo  Abre Tailscale en el PC y en el movil y vuelve a intentarlo.
    echo.
    echo  Acceso local: http://localhost:8000
    goto :end
)

:: ngrok como alternativa
where ngrok > nul 2>&1
if %errorlevel% == 0 (
    echo  Iniciando tunel ngrok...
    start "Ngrok" ngrok http 8000
    timeout /t 2 /nobreak > nul
    echo  Tunel activo. Abre http://localhost:4040 para ver la URL publica.
    goto :end
)

:: Ninguno disponible — instrucciones
echo  Para acceso desde el movil instala Tailscale (recomendado):
echo.
echo    winget install tailscale.tailscale
echo.
echo  Instala Tailscale tambien en el movil (iOS/Android).
echo  Ambos deben estar en la misma cuenta de Tailscale.
echo  Luego vuelve a ejecutar start.bat.
echo.
echo  Acceso local: http://localhost:8000

:end
echo.
pause
