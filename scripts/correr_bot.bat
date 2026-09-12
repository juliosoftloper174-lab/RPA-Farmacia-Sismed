@echo off
chcp 65001 >nul
TITLE RPA SISMED

if not "%1" == "h" (
    start /min cmd /C "%~dpnx0" h
    exit /b
)

cd ..\

:: Validar que el entorno virtual exista
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual .venv
    echo.
    echo Ejecute setup.bat primero para instalar las dependencias.
    echo.
    pause
    exit /b 1
)

.\.venv\Scripts\python.exe -m src
pause
