# SISMED RPA Bot

Bot RPA que automatiza el registro de **ingresos**, **salidas** y **pedidos** (recetas) en el sistema desktop **SISMED** (MINSA), extrayendo datos desde una base de datos SQL Server mediante stored procedures.

## Requisitos

- Windows 10/11
- SISMED v2 instalado (sistema desktop)
- Python 3.12+
- ODBC Driver 17 for SQL Server
- Entorno virtual (`.venv`)

## Instalación

```powershell
# Clonar repositorio
git clone <repo-url>
cd sismed_wrapper

# Activar entorno virtual
.\.venv\Scripts\activate

# Instalar dependencias
pip install -e .
```

## Configuración

Copiar `example.env` a `.env` y completar:

```env
# SISMED
SISMED_EXE = C:\ruta\a\SISMED.exe
SISMED_USERNAME = tu_usuario
SISMED_PASSWORD = tu_clave

# Base de datos SQL Server
DB_SERVER = 192.168.x.x
DB_NAME = ksalud_qa
DB_USER = rpa
DB_PASS = rpaKsalud

# Modo de operacion: "continuo" (24/7) o "batch" (rango de fechas)
MODO = continuo

# Activar/desactivar flujos
PROCESAR_INGRESOS = true
PROCESAR_SALIDAS = true
PROCESAR_PEDIDOS = true

# Notificaciones por correo (opcional)
NOTIFICAR_CORREO = false
SMTP_EMAIL = tu_correo@gmail.com
SMTP_PASSWORD = tu_password
SMTP_DESTINO = destino@correo.com
```

## Ejecución

### Modo continuo (24/7)

El bot consulta la BD cada 5 minutos y procesa movimientos del día actual:

```powershell
python -m src
```

### Modo batch (rango de fechas)

Procesa todos los movimientos de un rango específico:

```powershell
# En .env: MODO=batch, FECHA_INI=2026-06-09, FECHA_FIN=2026-06-10
python -m src
```

## Flujos automatizados

| Flujo | Descripción |
|-------|-------------|
| **Ingreso** | Registro de entrada de medicamentos a almacén |
| **Salida** | Transferencia de medicamentos entre almacenes |
| **Pedido** | Dispensación de recetas a pacientes (con Boleta/Ticket) |

## Estructura del proyecto

```
src/
├── __main__.py          ← Orquestador principal
├── config.py            ← Variables de entorno
├── flujos/              ← Automatización UI de cada flujo
├── helpers/             ← Helpers de interacción con SISMED
├── models/              ← Modelos de datos
├── reportes/            ← Generación de reportes Excel
├── notifications/       ← Notificaciones por correo
└── datos/               ← Adaptador SP → modelos
database/                ← Conexión SQL Server
docs/                    ← Documentación
tests/                   ← Pruebas unitarias
```

## Documentación

Ver la carpeta `docs/` para documentación detallada:

- `01-arquitectura.md` — Visión general del sistema
- `02-modelos.md` — Modelos de datos
- `03-flujos.md` — Automatización de flujos
- `04-reportes.md` — Reportes Excel
- `05-despliegue.md` — Guía de despliegue en producción
- `06-desarrollo.md` — Guía para desarrolladores
