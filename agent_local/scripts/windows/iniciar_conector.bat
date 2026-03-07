@echo off
:: ================================================================
:: iniciar_conector.bat
:: Arranca el conector local de cirugías SIN necesidad de compilar.
:: Doble clic para abrir. No requiere ser administrador.
:: ================================================================
setlocal EnableDelayedExpansion
title Conector Cirugias - Centro de Ojos Esteves
color 0A

cd /d "%~dp0..\.."
set "BASE=%CD%"
set "VENV=%BASE%\.venv"
set "LOG=%BASE%\logs\conector.log"

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║      CONECTOR LOCAL — Centro de Ojos Esteves        ║
echo  ║      http://127.0.0.1:8765                          ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: ── 1. Verificar Python ────────────────────────────────────────
echo [1/5] Verificando Python...
py --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python no encontrado.
    echo.
    echo  Instala Python 3.11 o superior desde:
    echo    https://www.python.org/downloads/
    echo  (marca "Add Python to PATH" durante la instalacion)
    echo.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('py --version 2^>^&1') do set PYVER=%%v
echo  OK: %PYVER%

:: ── 2. Crear entorno virtual si no existe ──────────────────────
echo [2/5] Entorno virtual...
if not exist "%VENV%\Scripts\activate.bat" (
    echo  Creando entorno virtual (solo la primera vez)...
    py -m venv "%VENV%"
    if errorlevel 1 (
        echo  ERROR: No pude crear el entorno virtual.
        pause & exit /b 1
    )
)
call "%VENV%\Scripts\activate.bat"
echo  OK: entorno virtual listo

:: ── 3. Instalar/actualizar dependencias ────────────────────────
echo [3/5] Verificando dependencias...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo  Instalando dependencias (solo la primera vez, puede tardar 2-3 min)...
    pip install -q -r "%BASE%\requirements.txt"
    if errorlevel 1 (
        echo  ERROR: No pude instalar dependencias. Revisa tu conexion a internet.
        pause & exit /b 1
    )
)
echo  OK: dependencias instaladas

:: ── 4. Instalar Playwright / Chrome si no está ─────────────────
echo [4/5] Verificando Playwright/Chrome...
python -c "from playwright.sync_api import sync_playwright; print('OK')" >nul 2>&1
if errorlevel 1 (
    echo  Instalando playwright...
    pip install -q playwright
)
:: Verificar si ya está instalado el browser (evita reinstalar siempre)
set "PW_MARKER=%VENV%\.playwright_installed"
if not exist "%PW_MARKER%" (
    echo  Instalando navegador Chrome para Playwright (solo la primera vez)...
    python -m playwright install chrome
    if errorlevel 1 (
        echo  ERROR: No pude instalar el navegador de Playwright.
        pause & exit /b 1
    )
    echo. > "%PW_MARKER%"
)
echo  OK: Playwright listo

:: ── 5. Verificar que el puerto 8765 esté libre ────────────────
echo [5/5] Verificando puerto 8765...
netstat -ano | findstr ":8765 " >nul 2>&1
if not errorlevel 1 (
    echo.
    echo  ADVERTENCIA: El puerto 8765 ya está en uso.
    echo  Probablemente el conector ya está corriendo.
    echo.
    echo  Si querés reiniciarlo:
    echo    1. Cerrá la otra ventana del conector
    echo    2. O en Administrador de tareas buscá "python" y terminalo
    echo    3. Luego volvé a ejecutar este script
    echo.
    pause & exit /b 1
)
echo  OK: puerto disponible

:: ── Crear carpeta de logs ──────────────────────────────────────
if not exist "%BASE%\logs" mkdir "%BASE%\logs"

:: ── Arrancar el servidor ───────────────────────────────────────
echo.
echo  Iniciando conector en http://127.0.0.1:8765
echo  Logs en: %LOG%
echo.
echo  IMPORTANTE:
echo    - NO cierres esta ventana mientras uses el conector
echo    - Chrome se abrirá automaticamente al ejecutar recetas/lentess
echo    - Si ves un captcha en Chrome, completalo y el proceso continua solo
echo.
echo  Presiona Ctrl+C para detener el conector.
echo  ─────────────────────────────────────────────────────────
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --log-level info 2>&1 | tee "%LOG%"

echo.
echo  El conector se detuvo.
pause
