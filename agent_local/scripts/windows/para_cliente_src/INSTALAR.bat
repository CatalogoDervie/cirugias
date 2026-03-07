@echo off
:: ================================================================
::  INSTALAR.bat — Conector Cirugías, Centro de Ojos Esteves
::
::  Doble clic para instalar. Solo se hace UNA vez.
::  No necesita Python instalado. Todo viene incluido.
:: ================================================================
setlocal EnableDelayedExpansion
title Instalando Conector Cirugias...
color 0A
cd /d "%~dp0"

echo.
echo  ================================================================
echo   INSTALADOR  ^|  Conector Centro de Ojos Esteves
echo  ================================================================
echo.
echo   Este proceso instala el conector automaticamente.
echo   Necesita internet solo para descargar el navegador (~150 MB).
echo   Por favor espera sin cerrar esta ventana.
echo.

:: ── PASO 1: Verificar que Python embebido existe ─────────────
echo   [1/5]  Verificando Python incluido...
if not exist "%~dp0python\python.exe" (
    echo.
    echo   ERROR: No se encontro python\python.exe
    echo   El paquete esta incompleto. Descargalo de nuevo.
    echo.
    pause & exit /b 1
)
echo          OK - Python listo

:: ── PASO 2: Instalar pip en Python embebido ──────────────────
echo   [2/5]  Preparando gestor de paquetes...
set "PY=%~dp0python\python.exe"
set "PIP=%~dp0python\Scripts\pip.exe"
set "MARKER_PIP=%~dp0python\.pip_ok"

if not exist "%MARKER_PIP%" (
    :: Descargar get-pip.py
    powershell -NoProfile -Command ^
        "try { Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%~dp0python\get-pip.py' -UseBasicParsing } catch { exit 1 }"
    if errorlevel 1 (
        echo.
        echo   ERROR: No se pudo descargar pip. Verifica tu conexion a internet.
        pause & exit /b 1
    )
    "%PY%" "%~dp0python\get-pip.py" --no-warn-script-location -q
    del "%~dp0python\get-pip.py" >nul 2>&1
    echo. > "%MARKER_PIP%"
)
echo          OK - pip listo

:: ── PASO 3: Instalar dependencias Python ─────────────────────
echo   [3/5]  Instalando dependencias (fastapi, uvicorn, playwright)...
set "MARKER_DEPS=%~dp0python\.deps_ok"

if not exist "%MARKER_DEPS%" (
    "%PY%" -m pip install -q --no-warn-script-location ^
        fastapi "uvicorn[standard]" pydantic playwright
    if errorlevel 1 (
        echo.
        echo   ERROR al instalar dependencias.
        echo   Verifica tu conexion a internet e intenta de nuevo.
        pause & exit /b 1
    )
    echo. > "%MARKER_DEPS%"
)
echo          OK - dependencias instaladas

:: ── PASO 4: Instalar Chrome de Playwright ────────────────────
echo   [4/5]  Instalando navegador para automatizacion...
echo          (descarga ~150 MB, puede tardar varios minutos)
set "MARKER_CHROME=%~dp0python\.chrome_ok"

if not exist "%MARKER_CHROME%" (
    :: Forzar que Playwright guarde el browser en la carpeta del paquete
    set "PLAYWRIGHT_BROWSERS_PATH=%~dp0playwright_browsers"
    "%PY%" -m playwright install chrome
    if errorlevel 1 (
        echo.
        echo   ADVERTENCIA: No se pudo descargar el navegador de Playwright.
        echo   Se intentara usar Google Chrome del sistema.
    ) else (
        echo. > "%MARKER_CHROME%"
    )
)
echo          OK - navegador listo

:: ── PASO 5: Crear acceso directo en Escritorio ───────────────
echo   [5/5]  Creando icono en el Escritorio...
set "TARGET=%~dp0Iniciar Conector.bat"
set "SHORTCUT=%USERPROFILE%\Desktop\Iniciar Conector.lnk"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $s = $ws.CreateShortcut('%SHORTCUT%'); ^
   $s.TargetPath = '%TARGET%'; ^
   $s.WorkingDirectory = '%~dp0'; ^
   $s.Description = 'Conector Centro de Ojos Esteves'; ^
   $s.Save()"

echo          OK - icono creado

:: ── LISTO ─────────────────────────────────────────────────────
echo.
echo  ================================================================
echo   INSTALACION COMPLETADA
echo.
echo   Para usar el conector todos los dias:
echo     ^> Doble clic en "Iniciar Conector" del Escritorio
echo     ^> Dejá esa ventana abierta mientras trabajas
echo.
echo   La primera vez que uses Recetas o Lentess desde la web,
echo   Chrome se abre solo para que hagas login en PAMI.
echo   Despues queda guardado y ya no pide mas.
echo  ================================================================
echo.
set /p "ABRIR=  Queres iniciarlo ahora? (S + Enter para si, Enter para no): "
if /i "!ABRIR!"=="S" (
    start "" "%~dp0Iniciar Conector.bat"
)
pause
