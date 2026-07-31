# SISMED RPA Bot

Bot RPA que automatiza el registro de **ingresos**, **salidas**, **pedidos** (recetas) y **extornos** (anulaciones) en el sistema desktop **SISMED** (MINSA), extrayendo datos desde una base de datos SQL Server mediante stored procedures.

## Requisitos

- Windows 10/11
- SISMED v2 instalado (sistema desktop)
- Python 3.12+
- ODBC Driver 17 for SQL Server
- Entorno virtual (`.venv`)

## Instalación

### Instalación automática (recomendada)

```powershell
setup.bat
```

El script:
1. Verifica que Python 3.12+ esté instalado
2. Crea el entorno virtual `.venv` (si no existe)
3. Instala las dependencias desde `requirements.txt`
4. Crea `.env` desde `.env.example` (si no existe)
5. Verifica que ODBC Driver 17 esté instalado

### Instalación manual

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

Copiar `.env.example` a `.env` y completar:

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
PROCESAR_EXTORNOS = true

# false: salta movimientos con estado de error (01,02,10,20)
PROCESAR_ERRORES = false

# Notificaciones por correo (opcional)
NOTIFICAR_CORREO = false
SMTP_EMAIL = tu_correo@gmail.com
SMTP_PASSWORD = tu_password
SMTP_DESTINO = destino@correo.com
```

## Ejecución

### Modo continuo (24/7)

El bot consulta la BD periódicamente y procesa movimientos del día actual:

```powershell
scripts\correr_bot.bat
```

o manualmente:

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
| **Extorno** | Anulación de pedidos (devolución de medicamentos) |

### Detalle de flujos

**Ingreso** (`src/flujos/ingreso.py`)
- Entrada de medicamentos desde el almacén origen al almacén destino (F01)
- Llena cabecera, NGR autogenerado, y productos (código, lote, fecha, registro sanitario, tipo suministro, fuente financiamiento)

**Salida** (`src/flujos/salida.py`)
- Transferencia de stock entre almacenes (F01 → F02/F04/F05)
- Selección de almacén destino por código desde grilla

**Pedido** (`src/flujos/pedido.py`)
- Dispensación de recetas a pacientes (venta/entrega)
- Navega a farmacia por código, forma de pago, tipo de receta, cliente, prescriptor y diagnósticos
- Genera Boleta (CONTADO) o Ticket (SIS/INTERVENCIÓN)
- **Reintentos automáticos**: hasta 3 intentos por pedido, relogueando en cada fallo
- **Cliente no encontrado**: lo detecta y lo registra sin reintentar

**Extorno** (`src/flujos/extorno.py`)
- Anulación de pedidos mediante devolución
- Filtra por fecha del pedido original (`KS_PEDIDO_FECHA`) + DNI del cliente
- Selecciona la primera fila encontrada y ejecuta la anulación (CmdDel → Anular → Sí)
- Vuelve al menú principal después de cada anulación

## Arquitectura

```
SP_MOVIMIENTOS_SISMED_RPA (fecha_ini, fecha_fin)
  → database/conexion.py (pyodbc → SQL Server)
    → src/datos/sp_adapter.py (mapea headers+detalles → modelos)
      → src/__main__.py (valida con Pydantic, orquesta procesamiento)
        → src/flujos/ingreso.py, salida.py, pedido.py, extorno.py (automatización UI)
          → src/reportes/excel_writer.py (guarda cada movimiento en movimientos.xlsx)
```

Cada flujo ejecuta `SP_UPDESTADOMOV_RPA` para actualizar el estado del movimiento en BD tras procesarlo exitosamente.

## Tipos de movimiento soportados

| KS_TIPO_MOV | Descripción | Flujo | Estado |
|---|---|---|---|
| 211 / 207 | PEDIDO (venta a terceros / paciente) | Pedido | ✅ |
| 205 | SALIDA (transferencia entre farmacias) | Salida | ✅ |
| 101 / 112 | INGRESO (compra institucional / transferencia) | Ingreso | ✅ |
| 108 | EXTORNO (anulación de pedido) | Extorno | ✅ |

## Notificaciones por correo

El bot envía correos automáticos cuando:
- Se detecta el **backup diario** (pausa y reanudación)
- El bot se **reinicia tras una caída**
- Ocurre un **error crítico** en el ciclo
- Llega la **hora de cierre** (resumen diario con el Excel adjunto)

Los resúmenes incluyen el conteo de los 4 flujos (ingresos, salidas, pedidos, extornos).

## Estructura del proyecto

```
sismed_wrapper/
├── setup.bat                ← Instalación automática
├── README.md
├── .env                     ← Configuración (no se commitea)
├── .env.example             ← Plantilla de configuración
├── requirements.txt         ← Dependencias
├── pyproject.toml
├── movimientos.xlsx         ← Excel de resultados (autogenerado)
├── src/
│   ├── __main__.py          ← Orquestador principal
│   ├── config.py            ← Variables de entorno
│   ├── flujos/              ← Automatización UI (ingreso, salida, pedido, extorno)
│   ├── helpers/             ← Helpers de interacción con SISMED
│   ├── models/              ← Modelos de datos
│   ├── reportes/            ← Generación de reportes Excel
│   ├── notifications/       ← Notificaciones por correo
│   └── datos/               ← Adaptador SP → modelos
├── database/                ← Conexión SQL Server
├── scripts/
│   └── correr_bot.bat       ← Ejecución del bot (modo continuo)
├── docs/                    ← Documentación
└── tests/                   ← Pruebas unitarias
```

## Documentación

Ver la carpeta `docs/` para documentación detallada:

- `01-arquitectura.md` — Visión general del sistema
- `02-modelos.md` — Modelos de datos
- `03-flujos.md` — Automatización de flujos
- `04-reportes.md` — Reportes Excel
- `05-despliegue.md` — Guía de despliegue en producción
- `06-desarrollo.md` — Guía para desarrolladores
