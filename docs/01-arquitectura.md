# Arquitectura del Sistema

## Visión general

SISMED RPA Bot es un bot de automatización de procesos robóticos (RPA) que interactúa con el sistema desktop **SISMED** (MINSA) para registrar movimientos de medicamentos. Obtiene los datos desde una base de datos SQL Server mediante un stored procedure y luego automatiza la interfaz gráfica de SISMED usando `uiautomation`.

## Diagrama de flujo de datos

```
SQL Server (SP_MOVIMIENTOS_SISMED_RPA)
    │
    ▼
database/conexion.py (pyodbc)
    │
    ▼
src/datos/sp_adapter.py (mapea headers+detalles → modelos)
    │
    ▼
src/__main__.py (valida pedidos con Pydantic, orquesta)
    │
    ├── src/flujos/ingreso.py   → SISMED (UI) → Excel
    ├── src/flujos/salida.py    → SISMED (UI) → Excel
    └── src/flujos/pedido.py    → SISMED (UI) → BD update → Excel
```

## Modos de operación

### Continuo 24/7 (default)

El orquestador (`__main__.py`) ejecuta un bucle infinito:

1. Consulta la BD por movimientos del día actual
2. Procesa ingresos → salidas → pedidos
3. Espera 5 minutos y repite
4. A la hora de cierre (configurable), envía resumen diario por correo

### Batch

Procesa todos los movimientos en un rango de fechas y termina.

## Componentes principales

### 1. Base de datos (`database/conexion.py`)

Conexión a SQL Server via pyodbc. Ejecuta dos stored procedures:

- **`SP_MOVIMIENTOS_SISMED_RPA`** — Obtiene movimientos (headers + detalles) en dos resultsets
- **`SP_UPDESTADOMOV_RPA`** — Actualiza el estado de un movimiento después de procesarlo

Detección de resultsets por columnas: `COLUMNAS_HEADER` vs `COLUMNAS_DETALLE`.

### 2. Adaptador SP (`src/datos/sp_adapter.py`)

Toma los datos crudos del SP y los convierte en objetos del dominio:

- Mapea códigos a textos legibles (tipo suministro, fuente financiamiento, etc.)
- Aplica reglas de negocio (almacén virtual, forma de pago)
- Filtra movimientos ya procesados (ESTADO = "1") y estados de error
- Construye `update_key` para actualizar estado en BD
- Omite OTROS INGRESOS/EGRESOS (pendientes de implementación)

### 3. Orquestador (`src/__main__.py`)

- Obtiene fechas (de `.env` o automáticas)
- Llama al SP adapter
- Valida pedidos con Pydantic (`obtener_revisiones()`)
- Procesa en orden: ingresos → salidas → pedidos
- Genera FUA ficticio para pedidos SIS sin FUA
- Sistema centinela (archivo `.running`) para detectar reinicios tras caída
- Manejo de señales (Ctrl+C)

### 4. Flujos de automatización (`src/flujos/`)

Cada flujo contiene la lógica de interacción con la UI de SISMED:

- `_login.py` — Login con manejo de backup diario
- `_comun_almacen.py` — Funciones compartidas (guardar, extraer correlativo, cerrar ventanas)
- `ingreso.py` — Registro de notas de ingreso
- `salida.py` — Registro de notas de salida
- `pedido.py` — Registro de pedidos/recetas con Boleta/Ticket

### 5. Helpers (`src/helpers/`)

Funciones de interacción con la UI de SISMED:

| Módulo | Propósito |
|--------|-----------|
| `comun/windows.py` | Accesores a ventanas SISMED |
| `comun/input.py` | Escribir texto en inputs con retry |
| `comun/selecionar.py` | Seleccionar items en ComboBox |
| `comun/combo.py` | Selección por click ciego |
| `comun/manejo_errores.py` | Manejo de ventanas de error |
| `comun/ui_helper.py` | Utilidades UI (normalizar texto) |
| `comun/ventana.py` | Esperar ventana con timeout |
| `pedido/cliente.py` | Buscar cliente por DNI |
| `pedido/farmacia.py` | Buscar farmacia en grilla |
| `pedido/producto.py` | Agregar productos a pedido |
| `pedido/diagnosticos.py` | Rellenar diagnósticos CIE |
| `pedido/registro_cliente.py` | Registrar nuevo cliente en SISMED |

### 6. Modelos (`src/models/`)

- `Pedido` (Pydantic) — Validación con reglas de negocio
- `Ingreso`, `Salidas`, `Medicamento` — Clases planas
- `Cliente`, `Farmacia`, `Prescriptor`, `Diagnostico` — Clases planas auxiliares
- `FormaPago`, `TipoReceta` — StrEnums

### 7. Reportes (`src/reportes/`)

- `excel_schema.py` — Define estructura de columnas y funciones creadoras de filas
- `excel_writer.py` — Escritura/append a Excel con polars

### 8. Notificaciones (`src/notifications/email_sender.py`)

Envío de correos SMTP (Gmail) para:
- Inicio/fin de backup diario
- Resumen diario (con adjunto Excel)
- Errores críticos
- Notificación de reinicio tras caída (centinela)

## Manejo de estados en BD

Cada movimiento tiene un estado que se actualiza vía `SP_UPDESTADOMOV_RPA`:

| Estado | Significado | Flujo |
|--------|-------------|-------|
| `00` | Procesado OK | Todos |
| `01` | Error en pedido | Pedido |
| `02` | Cliente no encontrado | Pedido |
| `10` | Error en ingreso | Ingreso |
| `20` | Error en salida | Salida |

## Pipeline de pre-stock (`scripts/pipeline_09062026/`)

Pipeline para un día específico:
1. Ingresa todos los productos ×20 a almacén F01
2. Pre-distribuye desde F01 a F02, F03, F04, F05

Ejecución:
```powershell
.\.venv\Scripts\python.exe scripts\pipeline_09062026\main.py
```
