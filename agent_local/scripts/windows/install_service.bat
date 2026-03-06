@echo off
:: ============================================================
:: install_service.bat  —  Instala el conector como Servicio de Windows
:: DEBE ejecutarse como ADMINISTRADOR (clic derecho → Ejecutar como admin)
:: ============================================================
setlocal
cd /d "%~dp0"

set SERVICE_NAME=CirugiasConector
set DISPLAY_NAME=Cirugias Conector (Centro de Ojos)
set EXE_PATH=%~dp0cirugias_connector.exe
set NSSM=%~dp0nssm.exe

:: --- Verificar que el exe existe ---
if not exist "%EXE_PATH%" (
    echo ERROR: No se encontro cirugias_connector.exe en esta carpeta.
    echo Ejecuta primero build.bat para generarlo.
    pause & exit /b 1
)

:: --- Descargar NSSM si no está ---
if not exist "%NSSM%" (
    echo Descargando NSSM...
    powershell -Command ^
      "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile nssm.zip; ^
       Expand-Archive nssm.zip -DestinationPath nssm_tmp -Force; ^
       Copy-Item nssm_tmp\nssm-2.24\win64\nssm.exe '%NSSM%'; ^
       Remove-Item nssm.zip,nssm_tmp -Recurse -Force"
    if not exist "%NSSM%" (
        echo ERROR: No se pudo descargar NSSM. Descargalo manualmente desde https://nssm.cc
        pause & exit /b 1
    )
)

:: --- Desinstalar servicio previo si existe ---
"%NSSM%" status "%SERVICE_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo Desinstalando version anterior del servicio...
    "%NSSM%" stop "%SERVICE_NAME%" >nul 2>&1
    "%NSSM%" remove "%SERVICE_NAME%" confirm >nul 2>&1
)

:: --- Instalar servicio ---
echo Instalando servicio "%SERVICE_NAME%"...
"%NSSM%" install "%SERVICE_NAME%" "%EXE_PATH%"
"%NSSM%" set "%SERVICE_NAME%" DisplayName "%DISPLAY_NAME%"
"%NSSM%" set "%SERVICE_NAME%" Description "Conector local para automatizaciones PAMI/Lentess del Control de Cirugiás"
"%NSSM%" set "%SERVICE_NAME%" Start SERVICE_AUTO_START
"%NSSM%" set "%SERVICE_NAME%" AppDirectory "%~dp0"

:: Sin ventana visible nunca
"%NSSM%" set "%SERVICE_NAME%" AppNoConsole 1

:: Log del servicio (no del job — esos van a logs/)
"%NSSM%" set "%SERVICE_NAME%" AppStdout "%~dp0logs\service_stdout.log"
"%NSSM%" set "%SERVICE_NAME%" AppStderr "%~dp0logs\service_stderr.log"
"%NSSM%" set "%SERVICE_NAME%" AppRotateFiles 1
"%NSSM%" set "%SERVICE_NAME%" AppRotateBytes 5000000

:: --- Iniciar servicio ---
echo Iniciando servicio...
"%NSSM%" start "%SERVICE_NAME%"

:: --- Verificar ---
timeout /t 3 /nobreak >nul
"%NSSM%" status "%SERVICE_NAME%"

echo.
echo ====================================================
echo  Servicio instalado y corriendo.
echo  Se inicia automaticamente con Windows.
echo  URL: http://127.0.0.1:8765/health
echo ====================================================
echo.
echo Podes verificar en:  Servicios de Windows (services.msc)
pause
