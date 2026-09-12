# Guía de Despliegue

## Requisitos del sistema

- **Windows** 10/11 (64 bits)
- **SISMED v2** instalado y funcionando en el equipo
- **Python 3.12+** instalado
- **ODBC Driver 17 for SQL Server** instalado
- Acceso de red al servidor SQL Server (192.168.170.37)
- Usuario BD con permisos de ejecución de stored procedures

## Instalación

### 1. Crear entorno virtual

```powershell
# En la raíz del proyecto
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias

```powershell
pip install -e .
```

Esto instala las dependencias listadas en `pyproject.toml`:
- `uiautomation==2.0.29` — Automatización UI de Windows
- `pydantic==2.13.3` — Validación de modelos
- `polars==1.40.1` — Manejo de Excel
- `loguru==0.7.3` — Logging
- `python-dotenv==1.2.2` — Variables de entorno
- `pyodbc==5.3.0` — Conexión SQL Server

### 3. Configurar `.env`

Basarse en `example.env`:

```env
SISMED_EXE = C:\SISMED\SISMED.exe
SISMED_USERNAME = rpa
SISMED_PASSWORD = rpaKsalud
DB_SERVER = 192.168.170.37
DB_NAME = ksalud_qa
DB_USER = rpa
DB_PASS = rpaKsalud
```

### 4. Probar conexión

```powershell
python -c "from database.conexion import ejecutar_sp_movimientos; h, d = ejecutar_sp_movimientos('2026-06-09', '2026-06-10'); print(f'Headers: {len(h)}, Detalles: {len(d)}')"
```

## Configuración para producción

### Modo continuo 24/7 (recomendado)

En `.env`:
```env
MODO = continuo
PROCESAR_INGRESOS = true
PROCESAR_SALIDAS = true
PROCESAR_PEDIDOS = true
HORA_CIERRE = 23:45
```

### Modo batch

```env
MODO = batch
FECHA_INI = 2026-06-09
FECHA_FIN = 2026-06-10
```

### Activar notificaciones por correo

```env
NOTIFICAR_CORREO = true
SMTP_EMAIL = tu_correo@gmail.com
SMTP_PASSWORD = tu_contraseña_app
SMTP_DESTINO = destino@hospital.com
BOT_NUMBER = 1
DESCRIPCION = SISMED BOT - Hospital Rioja
```

> **Nota**: Para Gmail, usar una contraseña de aplicación.

## Programar en Task Scheduler

Para que el bot arranque automáticamente al iniciar Windows:

1. Abrir **Task Scheduler**
2. Crear tarea básica:
   - **Nombre**: SISMED RPA Bot
   - **Disparador**: "Al iniciar sesión"
   - **Acción**: Iniciar programa
   - **Programa**: `powershell.exe`
   - **Argumentos**: `-WindowStyle Hidden -Command "cd C:\ruta\sismed_wrapper; .\.venv\Scripts\Activate.ps1; python -m src"`
   - **Ejecutar como**: Usuario con SISMED instalado

## Monitoreo

### Logs

Los logs se guardan en `.data/logs/YYYY-MM-DD.log` con rotación diaria y retención de 2 meses (comprimidos en ZIP).

### Centinela (.running)

El bot crea un archivo `.running` al iniciar y lo elimina al finalizar limpiamente. Si el archivo persiste al reiniciar, se envía un correo de alerta.

### Archivos generados

- `movimientos_YYYY-MM-DD.xlsx` — Resultados del día
- `incidencias.xlsx` — Incidencias de validación

## Backup diario de SISMED

El bot se pausa automáticamente cuando detecta:
1. Ventana de backup automático de SISMED
2. Hora programada de backup (`HORA_CIERRE`)

**Procedimiento**:
1. El bot muestra mensaje en consola y espera
2. Realizar el backup manual de SISMED
3. Cerrar TODAS las ventanas de SISMED
4. Volver a la terminal y presionar Enter
5. El bot reanuda automáticamente

## Solución de problemas comunes

| Problema | Posible causa | Solución |
|----------|---------------|----------|
| Error ODBC | Driver no instalado | Instalar "ODBC Driver 17 for SQL Server" |
| SISMED no abre | Ruta incorrecta en `.env` | Verificar `SISMED_EXE` |
| Login falla repetidamente | SISMED bloqueado por ventana modal | Cerrar ventanas manuales, presionar Enter |
| Excel no se guarda | Archivo abierto en otro programa | Cerrar Excel |
| Backup detiene el bot | Ventana de backup automático | Realizar backup y presionar Enter |
