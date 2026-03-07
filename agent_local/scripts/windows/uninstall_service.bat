@echo off
:: ============================================================
:: uninstall_service.bat  —  Desinstala el conector de Windows
:: DEBE ejecutarse como ADMINISTRADOR
:: ============================================================
setlocal
cd /d "%~dp0"

set SERVICE_NAME=CirugiasConector
set NSSM=%~dp0nssm.exe

if not exist "%NSSM%" (
    echo ERROR: nssm.exe no encontrado. El servicio puede que no este instalado.
    pause & exit /b 1
)

echo Deteniendo servicio...
"%NSSM%" stop "%SERVICE_NAME%" >nul 2>&1

echo Desinstalando servicio...
"%NSSM%" remove "%SERVICE_NAME%" confirm

echo.
echo Servicio desinstalado correctamente.
pause
