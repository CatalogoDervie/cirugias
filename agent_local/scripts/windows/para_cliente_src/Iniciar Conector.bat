@echo off
:: ================================================================
::  Iniciar Conector.bat
::  Doble clic para arrancar el conector.
::  Dejar esta ventana abierta mientras se trabaja.
:: ================================================================
setlocal EnableDelayedExpansion
title Conector Cirugias - Centro de Ojos Esteves
cd /d "%~dp0"

set "PY=%~dp0python\python.exe"

:: ── Verificar instalación ────────────────────────────────────
if not exist "%PY%" (
    echo.
    echo  ERROR: El conector no esta instalado correctamente.
    echo  Ejecuta primero INSTALAR.bat
    echo.
    pause & exit /b 1
)

:: ── Verificar que el puerto no esté ocupado ──────────────────
netstat -ano | findstr ":8765 " >nul 2>&1
if not errorlevel 1 (
    echo.
    echo  ================================================================
    echo   El conector ya esta corriendo en otro lado.
    echo   No necesitas abrir otra ventana.
    echo.
    echo   Si la web no lo detecta, espera 10 segundos y recarga.
    echo  ================================================================
    echo.
    pause & exit /b 0
)

:: ── Configurar Playwright browser path ───────────────────────
if exist "%~dp0playwright_browsers" (
    set "PLAYWRIGHT_BROWSERS_PATH=%~dp0playwright_browsers"
)

:: ── Mostrar encabezado ────────────────────────────────────────
echo.
echo  ================================================================
echo   CONECTOR ACTIVO  ^|  http://127.0.0.1:8765
echo  ================================================================
echo.
echo   NO cierres esta ventana mientras usas Recetas o Lentess.
echo.
echo   Chrome se abrira automaticamente al ejecutar una
echo   automatizacion desde la web.
echo.
echo   Para cerrar el conector: presiona Ctrl+C aqui
echo   o cierra directamente esta ventana.
echo  ----------------------------------------------------------------
echo.

:: ── Arrancar el servidor ─────────────────────────────────────
"%PY%" -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --log-level warning

echo.
echo  El conector se detuvo.
pause
