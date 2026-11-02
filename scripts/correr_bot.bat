@echo off
chcp 65001 >nul
TITLE RPA SISMED - Produccion

:: Funciona desde cualquier ubicacion: sube un nivel desde scripts\
cd /d "%~dp0.."

:: Validar que el entorno virtual exista
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual .venv
    echo.
    echo Ejecute setup.bat primero para instalar las dependencias.
    echo.
    pause
    exit /b 1
)

echo ==========================================
echo  Iniciando RPA SISMED...
echo  No cierre esta ventana.
echo ==========================================

.\.venv\Scripts\python.exe -m src

echo.
echo El bot se detuvo. Presione una tecla para cerrar...
pause >nul
