@echo off
:: ============================================================
:: build.bat  —  Genera cirugias_connector.exe con PyInstaller
:: Ejecutar desde la carpeta agent_local\
:: ============================================================
setlocal
cd /d "%~dp0"

echo.
echo [1/4] Verificando Python...
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado. Instala Python 3.11+ desde python.org
    pause & exit /b 1
)

echo [2/4] Creando entorno virtual...
if not exist .venv ( py -m venv .venv )
call .venv\Scripts\activate.bat

echo [3/4] Instalando dependencias...
pip install -q -r requirements.txt
pip install -q pyinstaller

echo [4/4] Compilando exe...
pyinstaller ^
  --onefile ^
  --noconsole ^
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
  --hidden-import app.main ^
  --hidden-import app.job_manager ^
  --hidden-import app.models ^
  --hidden-import app.logging_utils ^
  --hidden-import app.runners.recetas_runner ^
  --hidden-import app.runners.lentess_runner ^
  --collect-all playwright ^
  service_main.py

echo.
if exist dist\cirugias_connector.exe (
    echo ====================================================
    echo  OK: dist\cirugias_connector.exe generado con exito
    echo ====================================================
) else (
    echo ERROR: No se generó el exe. Revisa los mensajes de arriba.
)
pause
