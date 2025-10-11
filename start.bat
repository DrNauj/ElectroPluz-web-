@echo off
echo Cambiando al directorio raiz del proyecto...
cd /d %~dp0
powershell -ExecutionPolicy Bypass -File start_services.ps1