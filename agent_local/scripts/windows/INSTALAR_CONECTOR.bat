@echo off
:: ============================================================
::  INSTALAR CONECTOR — Centro de Ojos Esteves
::  Doble clic para instalar. Solo se hace UNA vez.
::  Requiere conexión a internet la primera vez.
:: ============================================================
title Instalando Conector Centro de Ojos...
color 0A
setlocal EnableDelayedExpansion

set "INSTALL_DIR=%USERPROFILE%\ConectorCirugias"
set "SHORTCUT_DESKTOP=%USERPROFILE%\Desktop\Iniciar Conector.lnk"
set "SHORTCUT_START=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Conector Cirugias.lnk"

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║        INSTALADOR — Conector Centro de Ojos            ║
echo  ║        Versión 1.0                                     ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
echo  Este proceso instala el conector automáticamente.
echo  No necesita hacer nada más que esperar.
echo.

:: ─── PASO 1: Verificar Python ────────────────────────────────
echo  [1/5] Verificando Python...
py --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  Python no está instalado. Descargando instalador...
    echo  (Esto puede tardar unos minutos según tu conexión)
    echo.
    :: Descargar Python 3.12 con winget si está disponible
    winget install Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements >nul 2>&1
    :: Actualizar PATH para esta sesión
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
    :: Si winget no funcionó, abrir el instalador manual
    py --version >nul 2>&1
    if errorlevel 1 (
        echo.
        echo  ┌─────────────────────────────────────────────────────┐
        echo  │  ACCIÓN REQUERIDA                                   │
        echo  │                                                     │
        echo  │  1. Se va a abrir la página de descarga de Python   │
        echo  │  2. Descargá el instalador y ejecutalo              │
        echo  │  3. IMPORTANTE: marcá "Add Python to PATH"          │
        echo  │  4. Cuando termine, volvé a ejecutar este archivo   │
        echo  └─────────────────────────────────────────────────────┘
        echo.
        start https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%v in ('py --version 2^>^&1') do echo  OK: %%v

:: ─── PASO 2: Crear carpeta de instalación ────────────────────
echo  [2/5] Preparando carpeta de instalación...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
:: Copiar todos los archivos del conector
xcopy /E /Y /Q "%~dp0..\.." "%INSTALL_DIR%\" >nul 2>&1
echo  OK: instalado en %INSTALL_DIR%

:: ─── PASO 3: Crear entorno virtual e instalar dependencias ───
echo  [3/5] Instalando dependencias Python...
echo        (solo la primera vez, tarda 2-3 minutos)
if not exist "%INSTALL_DIR%\.venv\Scripts\activate.bat" (
    py -m venv "%INSTALL_DIR%\.venv"
)
call "%INSTALL_DIR%\.venv\Scripts\activate.bat"
pip install -q --upgrade pip
pip install -q fastapi "uvicorn[standard]" pydantic playwright
if errorlevel 1 (
    echo.
    echo  ERROR al instalar dependencias.
    echo  Verificá tu conexión a internet e intentá de nuevo.
    pause & exit /b 1
)
echo  OK: dependencias instaladas

:: ─── PASO 4: Instalar Chrome para Playwright ─────────────────
echo  [4/5] Instalando navegador para automatización...
echo        (solo la primera vez, descarga ~150 MB)
set "PW_MARKER=%INSTALL_DIR%\.pw_installed"
if not exist "%PW_MARKER%" (
    python -m playwright install chrome
    if errorlevel 1 (
        echo.
        echo  ADVERTENCIA: No se pudo instalar el navegador de Playwright.
        echo  Se usará Google Chrome instalado en el sistema.
    ) else (
        echo. > "%PW_MARKER%"
    )
)
echo  OK: navegador listo

:: ─── PASO 5: Crear accesos directos ──────────────────────────
echo  [5/5] Creando accesos directos...

:: Crear el launcher principal
set "LAUNCHER=%INSTALL_DIR%\INICIAR CONECTOR.bat"
(
    echo @echo off
    echo title Conector Cirugias - Centro de Ojos Esteves
    echo cd /d "%INSTALL_DIR%"
    echo call "%INSTALL_DIR%\.venv\Scripts\activate.bat"
    echo.
    echo :: Verificar puerto libre
    echo netstat -ano ^| findstr ":8765 " ^>nul 2^>^&1
    echo if not errorlevel 1 ^(
    echo     echo.
    echo     echo  El conector ya está corriendo.
    echo     echo  Podés cerrar esta ventana.
    echo     pause ^& exit /b 0
    echo ^)
    echo.
    echo echo.
    echo echo  ╔══════════════════════════════════════════╗
    echo echo  ║  CONECTOR ACTIVO — No cerrar esta ventana║
    echo echo  ║  http://127.0.0.1:8765                  ║
    echo echo  ╚══════════════════════════════════════════╝
    echo echo.
    echo python -m uvicorn app.main:app --host 127.0.0.1 --port 8765
    echo pause
) > "%LAUNCHER%"

:: Acceso directo en escritorio via PowerShell
powershell -NoProfile -Command ^
    "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT_DESKTOP%');^
     $s.TargetPath='%LAUNCHER%';^
     $s.WorkingDirectory='%INSTALL_DIR%';^
     $s.IconLocation='%SystemRoot%\System32\imageres.dll,21';^
     $s.Description='Conector Centro de Ojos';^
     $s.Save()" >nul 2>&1

:: Acceso directo en menú inicio
powershell -NoProfile -Command ^
    "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT_START%');^
     $s.TargetPath='%LAUNCHER%';^
     $s.WorkingDirectory='%INSTALL_DIR%';^
     $s.IconLocation='%SystemRoot%\System32\imageres.dll,21';^
     $s.Save()" >nul 2>&1

echo  OK: accesos directos creados

:: ─── LISTO ────────────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║   ✅  INSTALACIÓN COMPLETADA                            ║
echo  ║                                                         ║
echo  ║   Para usar el conector:                                ║
echo  ║     → Doble clic en "Iniciar Conector" en el Escritorio ║
echo  ║     → Dejá esa ventana abierta mientras trabajás        ║
echo  ║                                                         ║
echo  ║   La primera vez que uses Recetas o Lentess,            ║
echo  ║   Chrome se abre para que hagas login en PAMI.          ║
echo  ║   Después queda guardado automáticamente.               ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: Preguntar si quiere iniciar ahora
set /p "INICIAR=  ¿Iniciar el conector ahora? (S/N): "
if /i "!INICIAR!"=="S" (
    start "" "%LAUNCHER%"
)

pause
