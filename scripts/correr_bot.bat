REM Hide the command prompt window
@echo off

TITLE RPA SISMED

if not "%1" == "h" (
    start /min cmd /C "%~dpnx0" h
    exit /b
)

cd ..\

.\.venv\Scripts\python.exe -m src
pause