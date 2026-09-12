@echo off
chcp 65001 >nul
TITLE RPA SISMED - Setup

echo ==========================================
echo  RPA SISMED - Instalacion automatica
echo ==========================================
echo.

:: Nota: copie .env.example a .env y complete sus valores reales.
:: Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado.
    echo Descargue Python 3.12 desde: https://www.python.org/downloads/release/python-31210/
    echo Asegurese de marcar "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

for /f "tokens=2 delims=." %%v in ('python -c "import sys; print(sys.version)"') do set PY_MINOR=%%v
python -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Se requiere Python 3.12 o superior.
    echo Version actual detectada:
    python --version
    pause
    exit /b 1
)

echo [OK] Python detectado.
python --version

:: Crear entorno virtual
if exist ".venv\Scripts\python.exe" (
    echo [OK] Entorno virtual .venv ya existe.
) else (
    echo [INFO] Creando entorno virtual .venv...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual creado.
)

:: Instalar dependencias
echo [INFO] Instalando dependencias...
.\.venv\Scripts\pip.exe install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas.

:: Crear .env si no existe
if not exist ".env" (
    echo [INFO] Creando archivo .env desde .env.example...
    copy ".env.example" ".env" >nul
    echo [OK] Archivo .env creado.
    echo [IMPORTANTE] Edite el archivo .env con sus credenciales y rutas reales.
) else (
    echo [OK] Archivo .env ya existe.
)

:: Verificar ODBC Driver 17
reg query "HKLM\SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers" /v "ODBC Driver 17 for SQL Server" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ADVERTENCIA] ODBC Driver 17 for SQL Server NO esta instalado.
    echo El bot no podra conectarse a la base de datos.
    echo.
    echo Para instalarlo ejecute como administrador:
    echo   winget install Microsoft.SQLServer.ODBCDriver
    echo.
    echo O descarguelo manualmente desde:
    echo   https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
) else (
    echo [OK] ODBC Driver 17 for SQL Server detectado.
)

echo.
echo ==========================================
echo  Instalacion completada.
echo ==========================================
echo.
echo Recuerde:
echo  1. Editar el archivo .env con sus credenciales.
echo  2. Verificar que SISMED este instalado en la ruta indicada.
echo  3. Ejecutar: scripts\correr_bot.bat
