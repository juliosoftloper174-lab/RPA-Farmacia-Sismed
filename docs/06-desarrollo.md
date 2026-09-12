# Guía para Desarrolladores

## Convenciones del proyecto

- **Sin comentarios** en código a menos que sean estrictamente necesarios
- **Logging con loguru** — Usar `logger.info()`, `logger.debug()`, `logger.warning()`, `logger.error()`, `logger.exception()`, `logger.success()`
- **Errores**: levantar `Exception` con mensaje descriptivo
- **Nombres de clases**: PascalCase
- **Nombres de funciones/variables**: snake_case
- **Modelos**: plain classes para `Ingreso`, `Salidas`, `Medicamento`; Pydantic (`BaseModel`) para `Pedido`
- **Enums**: usar `StrEnum`

## Estructura del proyecto

```
src/
├── __main__.py          ← Orquestador (entry point: python -m src)
├── config.py            ← Variables de entorno desde .env
├── paths.py             ← Rutas del proyecto (logs, etc.)
├── logger.py            ← Configuración de loguru
├── datos/
│   └── sp_adapter.py    ← Mapeo SP → modelos de dominio
├── flujos/              ← Automatización UI de cada flujo
│   ├── _login.py
│   ├── _comun_almacen.py
│   ├── ingreso.py
│   ├── salida.py
│   └── pedido.py
├── helpers/
│   ├── comun/           ← Funciones compartidas
│   └── pedido/          ← Funciones específicas de pedidos
├── models/              ← Clases de dominio
├── reportes/            ← Excel (polars)
└── notifications/       ← Correos SMTP
database/
    └── conexion.py      ← Conexión pyodbc a SQL Server
```

## Cómo agregar un nuevo flujo

1. Crear modelo en `src/models/` (plain class)
2. Agregar mapeo en `src/datos/sp_adapter.py` (en función `obtener_movimientos`)
3. Crear flujo en `src/flujos/` con función `procesar_{flujo}(movimientos)`
4. Agregar función de procesamiento en `src/__main__.py`
5. Agregar estado BD en `database/conexion.py`
6. Agregar esquema de fila en `src/reportes/excel_schema.py`
7. Agregar flag en `src/config.py`

## Cómo funciona el SP Adapter

`obtener_movimientos(fecha_ini, fecha_fin, skip_errores)`:

1. Llama a `ejecutar_sp_movimientos()` que retorna `(headers, detalles)`
2. Filtra headers por `TIPO_MOVIMIENTO_DES` en ("PEDIDO", "INGRESO", "SALIDA")
3. Filtra por estado: salta `ESTADO == "1"` (ya procesados)
4. Si `skip_errores=True`, salta estados error (`01`, `02`, `10`, `20`)
5. Salta OTROS INGRESOS/EGRESOS (pendientes de implementación)
6. Agrupa detalles por `CORRELATIVO_KSALUD`
7. Construye objetos del dominio para cada header + sus detalles
8. Retorna `(pedidos, ingresos, salidas, saltados_otros)`

### Update Key

Se construye con 8 campos del header:
`(KS_ORIGEN_CAS, KS_CENTRO_CAS, KS_TIPO_ALMACEN, KS_ALMACEN, KS_DOCUMENTO, KS_NUMERO_MOVIMIENTO, KS_TIPO_TRANSACCION, KS_COD_TIPO_ALMACEN_VIRTUAL)`

Esta tupla se pasa a `SP_UPDESTADOMOV_RPA` para actualizar el estado del movimiento.

## Testing

### Ejecutar tests

```powershell
pytest tests/
```

### Tests existentes

| Archivo | Lo que prueba |
|---------|---------------|
| `test_pedido.py` | Modelo Pedido (Pydantic), reglas de negocio, mapeo SP adapter, Excel schema |
| `test_ingreso.py` | Flujo de ingreso |
| `test_salida.py` | Flujo de salida |
| `test_children.py` | Definiciones de UI |

### Mocking del SP

Los tests de `sp_adapter` usan `monkeypatch` para reemplazar `ejecutar_sp_movimientos` con datos falsos:

```python
def fake_ejecutar_sp(fecha_ini, fecha_fin):
    return headers_fake, detalles_fake

monkeypatch.setattr(sp_adapter, "ejecutar_sp_movimientos", fake_ejecutar_sp)
```

## Logging

Formato: `{time} | {level} | {module}:{function}:{line} | {message}`

- Consola: stdout (coloreado)
- Archivo: `.data/logs/YYYY-MM-DD.log` (rotación diaria, retención 2 meses, comprimido ZIP)

## Errores comunes

### "No se encontró la ventana X"

SISMED cambia títulos de ventanas según la configuración. Verificar con `inspect.exe` (herramienta de uiautomation) el nombre real de la ventana.

### Coordenadas de click incorrectas

Las coordenadas fijas (click ciego) son sensibles a:
- Resolución de pantalla
- Posición de la ventana SISMED
- Versión de SISMED

Si un click ciego falla, usar `inspect.exe` para identificar el control y reemplazar por acceso por nombre.

### COMError en extracción de correlativo

La función `extraer_correlativo_almacen()` tiene `@retry(tries=3, backoff=2, delay=2, exceptions=(COMError,))` para manejar errores transitorios de COM.

### Pedido falla y no reintenta

Si el error es `ClienteNoEncontradoError`, el bot NO reintenta. Si el cliente tiene datos (`nombre`, `sexo`, etc.), el bot lo registra automáticamente en SISMED. Si no tiene nombre, el pedido se marca como `CLIENTE_NO_ENCONTRADO`.

## Dependencias principales

| Librería | Versión | Propósito |
|----------|---------|-----------|
| `uiautomation` | 2.0.29 | Automatización UI Windows |
| `pydantic` | 2.13.3 | Validación de modelos |
| `polars` | 1.40.1 | Lectura/escritura Excel |
| `loguru` | 0.7.3 | Logging |
| `python-dotenv` | 1.2.2 | Variables de entorno |
| `pyodbc` | 5.3.0 | Conexión SQL Server |
| `retry` | - | Reintentos con backoff |
| `comtypes` | - | COM interop |
