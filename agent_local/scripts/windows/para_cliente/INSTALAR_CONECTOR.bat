@echo off
:: ================================================================
::  INSTALAR CONECTOR — Centro de Ojos Esteves
::
::  ¿Qué hace este archivo?
::    - Instala el conector automáticamente en tu PC
::    - Crea un ícono en el Escritorio para iniciarlo
::    - Solo se corre UNA vez
::
::  Requisito: conexión a internet la primera vez
:: ================================================================
title Instalando Conector Centro de Ojos...
color 0A
setlocal EnableDelayedExpansion

set "INSTALL_DIR=%USERPROFILE%\ConectorCirugias"
set "EXE_SRC=%~dp0cirugias_connector.exe"

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║     Instalador — Conector Centro de Ojos Esteves       ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: ── Verificar que el exe esté en la misma carpeta ────────────
if not exist "%EXE_SRC%" (
    echo.
    echo  ERROR: No se encontró cirugias_connector.exe en esta carpeta.
    echo  Asegurate de que este archivo y cirugias_connector.exe
    echo  estén en la misma carpeta.
    echo.
    pause & exit /b 1
)

:: ── Crear carpeta de instalación ─────────────────────────────
echo  [1/4] Instalando en: %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy /Y "%EXE_SRC%" "%INSTALL_DIR%\cirugias_connector.exe" >nul
echo  OK

:: ── Instalar Chrome para Playwright (solo la primera vez) ────
echo  [2/4] Preparando navegador automatizado...
echo        (solo la primera vez, descarga unos archivos — puede tardar 2 min)
set "PW_MARKER=%INSTALL_DIR%\.pw_ready"
if not exist "%PW_MARKER%" (
    :: Correr el exe en modo instalación para que descargue el browser
    "%INSTALL_DIR%\cirugias_connector.exe" --install-browser
    :: Si falla (el exe no soporta ese flag), intentar con Python si existe
    py -c "from playwright.sync_api import sync_playwright" >nul 2>&1
    if not errorlevel 1 (
        py -m playwright install chrome >nul 2>&1
    )
    echo. > "%PW_MARKER%"
)
echo  OK

:: ── Crear acceso directo en escritorio ───────────────────────
echo  [3/4] Creando ícono en el Escritorio...
set "SHORTCUT=%USERPROFILE%\Desktop\Iniciar Conector.lnk"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%');^
     $s.TargetPath='%INSTALL_DIR%\cirugias_connector.exe';^
     $s.WorkingDirectory='%INSTALL_DIR%';^
     $s.Description='Conector Centro de Ojos Esteves';^
     $s.Save()" >nul 2>&1
echo  OK

:: ── Crear acceso directo en menú inicio ──────────────────────
echo  [4/4] Agregando al Menú Inicio...
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "SHORTCUT2=%STARTMENU%\Conector Cirugias.lnk"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT2%');^
     $s.TargetPath='%INSTALL_DIR%\cirugias_connector.exe';^
     $s.WorkingDirectory='%INSTALL_DIR%';^
     $s.Save()" >nul 2>&1
echo  OK

:: ── Listo ─────────────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║   ✅  INSTALACIÓN LISTA                                 ║
echo  ║                                                         ║
echo  ║   Cómo usar el conector:                                ║
echo  ║                                                         ║
echo  ║   1. Doble clic en "Iniciar Conector" del Escritorio    ║
echo  ║   2. Aparece una pequeña ventana verde — dejala abierta ║
echo  ║   3. Usá la web normalmente para Recetas y Lentess      ║
echo  ║                                                         ║
echo  ║   IMPORTANTE:                                           ║
echo  ║   La PRIMERA vez Chrome se abre solo para login en PAMI ║
echo  ║   Hacé el login vos — después queda guardado.           ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
set /p "INI=  ¿Iniciarlo ahora? (S para Sí, Enter para no): "
if /i "!INI!"=="S" (
    start "" "%INSTALL_DIR%\cirugias_connector.exe"
)
echo.
pause
