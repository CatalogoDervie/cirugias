@echo off
:: ================================================================
::  build.bat  —  Genera cirugias_connector.exe
::  Ejecutar desde la carpeta agent_local\
::  El resultado en dist\cirugias_connector.exe es lo que se
::  entrega al cliente junto con INSTALAR_CONECTOR.bat
:: ================================================================
setlocal
title Compilando Conector Cirugias...
color 0A
cd /d "%~dp0..\.."

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║   COMPILADOR — Conector Cirugias v1.0               ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: ── Python ───────────────────────────────────────────────────
echo [1/5] Verificando Python...
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado.
    echo Instala Python 3.11+ desde https://www.python.org
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('py --version 2^>^&1') do echo OK: %%v

:: ── Entorno virtual ──────────────────────────────────────────
echo [2/5] Entorno virtual...
if not exist .venv ( py -m venv .venv )
call .venv\Scripts\activate.bat
echo OK

:: ── Dependencias ─────────────────────────────────────────────
echo [3/5] Instalando dependencias...
pip install -q --upgrade pip
pip install -q -r requirements.txt pyinstaller
echo OK

:: ── Limpiar builds anteriores ────────────────────────────────
echo [4/5] Limpiando build anterior...
if exist dist\cirugias_connector.exe del /f /q dist\cirugias_connector.exe
if exist cirugias_connector.spec del /f /q cirugias_connector.spec
echo OK

:: ── Compilar ─────────────────────────────────────────────────
echo [5/5] Compilando exe (puede tardar 3-5 min)...
echo.

pyinstaller ^
  --onefile ^
  --windowed ^
  --name cirugias_connector ^
  --hidden-import uvicorn.logging ^
  --hidden-import uvicorn.loops ^
  --hidden-import uvicorn.loops.auto ^
  --hidden-import uvicorn.protocols ^
  --hidden-import uvicorn.protocols.http ^
  --hidden-import uvicorn.protocols.http.auto ^
  --hidden-import uvicorn.protocols.websockets ^
  --hidden-import uvicorn.protocols.websockets.auto ^
  --hidden-import uvicorn.lifespan ^
  --hidden-import uvicorn.lifespan.on ^
  --hidden-import fastapi ^
  --hidden-import pydantic ^
  --hidden-import pydantic_core ^
  --hidden-import anyio ^
  --hidden-import anyio._backends._asyncio ^
  --hidden-import starlette ^
  --hidden-import app.main ^
  --hidden-import app.job_manager ^
  --hidden-import app.models ^
  --hidden-import app.logging_utils ^
  --hidden-import app.runners.recetas_runner ^
  --hidden-import app.runners.lentess_runner ^
  --collect-submodules playwright ^
  --collect-data playwright ^
  service_main.py

echo.
if exist dist\cirugias_connector.exe (
    echo  ╔══════════════════════════════════════════════════════╗
    echo  ║   ✅  COMPILACIÓN EXITOSA                           ║
    echo  ║                                                     ║
    echo  ║   Archivo generado:                                 ║
    echo  ║     dist\cirugias_connector.exe                     ║
    echo  ║                                                     ║
    echo  ║   Para distribuir al cliente:                       ║
    echo  ║     1. Copiar dist\cirugias_connector.exe           ║
    echo  ║        en scripts\windows\para_cliente\             ║
    echo  ║     2. Entregar la carpeta para_cliente\ completa   ║
    echo  ║     3. El cliente ejecuta INSTALAR_CONECTOR.bat     ║
    echo  ╚══════════════════════════════════════════════════════╝
) else (
    echo  ERROR: No se generó el exe. Revisá los mensajes de arriba.
)
echo.
pause
