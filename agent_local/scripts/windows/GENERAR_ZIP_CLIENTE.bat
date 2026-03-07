@echo off
:: ================================================================
::  GENERAR_ZIP_CLIENTE.bat
::
::  Este script lo corre EL DESARROLLADOR (vos) en tu PC.
::  Genera el zip completo para entregar al cliente.
::
::  Incluye Python embebido — el cliente NO necesita instalar nada.
::
::  Requisitos: Python 3.11+ instalado en TU PC, internet.
::  Tiempo estimado: 3-5 minutos.
:: ================================================================
setlocal EnableDelayedExpansion
title Generando paquete cliente...
color 0A
cd /d "%~dp0..\.."

echo.
echo  ================================================================
echo   GENERADOR DE PAQUETE CLIENTE — Conector Cirugias
echo  ================================================================
echo.

:: ── Python en el sistema ─────────────────────────────────────
echo   [1/6]  Verificando Python...
py --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python no encontrado en esta PC de desarrollo.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('py --version 2^>^&1') do echo          OK: %%v

:: ── Carpeta de salida ─────────────────────────────────────────
set "OUT=%~dp0para_cliente"
echo   [2/6]  Preparando carpeta de salida: %OUT%
if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%"
mkdir "%OUT%\app\runners"
mkdir "%OUT%\python"
mkdir "%OUT%\logs"
mkdir "%OUT%\chrome_profiles"
echo          OK

:: ── Copiar código del conector ───────────────────────────────
echo   [3/6]  Copiando codigo del conector...
xcopy /E /Y /Q "%~dp0..\..\app" "%OUT%\app\" >nul
copy /Y "%~dp0..\..\service_main.py" "%OUT%\" >nul
copy /Y "%~dp0..\..\requirements.txt" "%OUT%\" >nul
copy /Y "%~dp0para_cliente_src\INSTALAR.bat" "%OUT%\" >nul 2>&1
copy /Y "%~dp0para_cliente_src\Iniciar Conector.bat" "%OUT%\" >nul 2>&1
copy /Y "%~dp0para_cliente_src\LEEME.txt" "%OUT%\" >nul 2>&1
echo          OK

:: ── Descargar Python embebido ────────────────────────────────
echo   [4/6]  Descargando Python embebido (portable, ~15 MB)...
set "PY_VER=3.12.9"
set "PY_ZIP=%TEMP%\python-embed.zip"
set "PY_URL=https://www.python.org/ftp/python/%PY_VER%/python-%PY_VER%-embed-amd64.zip"

if not exist "%PY_ZIP%" (
    powershell -NoProfile -Command ^
        "Invoke-WebRequest -Uri '%PY_URL%' -OutFile '%PY_ZIP%' -UseBasicParsing"
    if errorlevel 1 (
        echo   ERROR: No se pudo descargar Python embebido.
        echo   URL: %PY_URL%
        echo   Verifica tu conexion a internet.
        pause & exit /b 1
    )
)
powershell -NoProfile -Command ^
    "Expand-Archive '%PY_ZIP%' -DestinationPath '%OUT%\python' -Force"
echo          OK: Python %PY_VER% embebido

:: ── Configurar Python embebido para poder instalar paquetes ──
echo   [5/6]  Configurando Python embebido...
::
:: Python embebido tiene un archivo pythonXX._pth que por defecto
:: deshabilita site-packages. Hay que modificarlo y agregar Scripts\.
::
set "PTH_FILE="
for %%f in ("%OUT%\python\python3*._pth") do set "PTH_FILE=%%f"
if not defined PTH_FILE (
    for %%f in ("%OUT%\python\python*._pth") do set "PTH_FILE=%%f"
)
if defined PTH_FILE (
    :: Habilitar import site (descomentar la línea)
    powershell -NoProfile -Command ^
        "(Get-Content '%PTH_FILE%') -replace '#import site','import site' | Set-Content '%PTH_FILE%'"
    :: Agregar Scripts y Lib\site-packages al path
    echo Lib\site-packages>> "%PTH_FILE%"
    echo Scripts>> "%PTH_FILE%"
    echo .>> "%PTH_FILE%"
)
echo          OK

:: ── Crear archivo de lanzador batch ──────────────────────────
:: (ya copiado en paso 3, solo verificar)
if not exist "%OUT%\INSTALAR.bat" (
    echo   ADVERTENCIA: INSTALAR.bat no encontrado en para_cliente_src\
    echo   Asegurate de que los archivos fuente esten en:
    echo   %~dp0para_cliente_src\
)
echo          OK

:: ── Comprimir en zip ─────────────────────────────────────────
echo   [6/6]  Comprimiendo paquete final...
set "ZIPFILE=%~dp0ConectorCirugias_CLIENTE.zip"
if exist "%ZIPFILE%" del /f /q "%ZIPFILE%"
powershell -NoProfile -Command ^
    "Compress-Archive -Path '%OUT%\*' -DestinationPath '%ZIPFILE%' -Force"
if errorlevel 1 (
    echo   ERROR al comprimir. El zip se puede crear manualmente.
) else (
    echo          OK: %ZIPFILE%
)

:: ── Resultado ─────────────────────────────────────────────────
echo.
echo  ================================================================
echo   PAQUETE GENERADO
echo.
echo   Archivo a entregar al cliente:
echo   %ZIPFILE%
echo.
echo   Instrucciones para el cliente:
echo     1. Descomprimir el zip en una carpeta (ej: C:\Conector\)
echo     2. Doble clic en INSTALAR.bat
echo     3. Esperar ~5 minutos (necesita internet)
echo     4. Usar el icono del Escritorio todos los dias
echo  ================================================================
echo.
explorer "%~dp0"
pause
