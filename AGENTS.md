# SISMED RPA - Contexto del Proyecto

## 📌 Descripción General

Proyecto **sismed_wrapper** v0.1.7 — Bot RPA que automatiza 3 flujos en el sistema desktop **SISMED**:

1. **Ingresos** (entradas de medicamentos a almacén) — ✅ Funcional con datos reales
2. **Salidas** (transferencias entre almacenes) — ✅ Funcional con datos reales
3. **Pedidos** (recetas / dispensación a pacientes) — ✅ Funcional con reintentos automáticos, actualización de estado en BD, y detección de clientes no encontrados

---

## 🏗️ Arquitectura

### Flujo de Datos (Actual - Con BD real)

```
SP_MOVIMIENTOS_SISMED_RPA (fecha_ini, fecha_fin)
  → database/conexion.py (pyodbc → SQL Server)
    → src/datos/sp_adapter.py (mapea headers+detalles → modelos)
      → src/__main__.py (valida con Pydantic, orquesta procesamiento)
        → src/sidmed/ingreso.py, salidas.py, pedido.py (automatización UI)
          → src/reportes/excel_writer.py (guarda cada movimiento individualmente en movimientos.xlsx)
```

### Ubicación BD (desde .env)
- **Server**: 192.168.170.37
- **DB**: ksalud_qa
- **User**: rpa / rpaKsalud
- Driver ODBC 17 for SQL Server

---

## 🧩 Módulos Principales

### `src/__main__.py` — Orquestador principal
- Obtiene fechas (harcodeado: 2026-06-09 a 2026-06-10)
- Llama a `obtener_movimientos()` del SP adapter
- Valida pedidos con Pydantic + reglas de negocio (`obtener_revisiones()`)
- Procesa en orden: ingresos → salidas → pedidos
- Guarda incidencias de validación y resultados en Excel
- Cada flujo se ejecuta con try/except independiente para no bloquear los demás

### `database/conexion.py` — Conexión a BD
- `ejecutar_sp_movimientos(fecha_ini, fecha_fin)` → `(headers: list[dict], detalles: list[dict])`
- `ejecutar_sp_update_estado(update_key: tuple[str,...])` → Ejecuta `SP_UPDESTADOMOV_RPA` y hace `conn.commit()`. Sin SELECT final ni lectura de resultsets.
- Detecta resultsets por columnas: `COLUMNAS_HEADER` vs `COLUMNAS_DETALLE`

### `src/datos/sp_adapter.py` — Adaptador SP → Modelos
- `obtener_movimientos()` → `tuple[list[Pedido], list[Ingreso], list[Salidas]]`
- Mapeos clave:
  - `FormaPago`: NULL/"" → CONTADO, "0" → INTERVENCION_SANITARIA, "1" → SIS
  - `AlmacenVirtualOrigen`: "0" → "030S0101", "1" → "030S0102"
  - `TipoSuministro`: "CN" → "SISMED-COMPRA NACIONAL (CN)", etc.
  - `FuenteFinanciamiento`: "DYT" → "Donaciones y Transferencias (DYT)", etc.
- **Hardcodeados**: CLIENTE = "00025759", PRESCRIPTOR = "87705"
- Fecha vencimiento: convierte `-` a `/`, corrige día 31 → 30
- Log de "Columnas del detalle" en DEBUG (no INFO)
- `update_key`: construye tupla de 8 campos para `SP_UPDESTADOMOV_RPA`
- Filtro `ESTADO == "1"` → salta movimientos ya procesados

### `src/datos/test_data.py` — Datos de prueba (simulados, reemplazados por SP)
- Contiene MOVIMIENTOS con pedidos, ingresos, salidas harcodeados
- Ya no es importado por ningún módulo

### `src/models/pedido.py` — Modelo Pydantic con validación
```python
class Pedido(BaseModel):
    farmacia: Farmacia
    cliente: Cliente
    prescriptor: Prescriptor | None = None
    forma_pago: FormaPago
    tipo_receta: TipoReceta
    diagnosticos: list[Diagnostico] = []
    Medicamentos: list[Medicamento]
    fua: str | None = None
```
- `obtener_revisiones()`: FUA obligatorio si SIS; tipo_receta debe ser SIN_NUMERO

### `src/models/ingreso.py` — Plain class
```python
class Ingreso:
    almacen_destino: str
    almacen_virtual_origen: str
    concepto: str
    medicamentos: list[Medicamento]
```

### `src/models/Salidas.py` — Plain class
```python
class Salidas:
    almacen_origen: str
    almacen_destino: str
    almacen_virtual_origen: str
    concepto: str
    medicamentos: list[Medicamento]
```

### `src/models/Medicamento.py` — Plain class (usado por los 3 flujos)
```python
class Medicamento:
    codigo, cantidad, lote, tipo_sum, fuente_fin,
    registro_sanitario, fecha_vencimiento, precio_compra
```
- `ProductoIngreso = Medicamento` (alias para compatibilidad)

### `src/sidmed/_comun_almacen.py` — Funciones compartidas ALMACEN ✅
- `guardar()`: Click en botón CmdSave
- `extraer_correlativo_almacen()`: Extrae correlativo del mensaje "Se grabó correctamente la Nota de Ingreso/Salida N° XXXX" — con retry COM, cierra ventanas de error y Report Designer
- `cerrar_sismed()`: Cierra ventanas ALMACEN y MINSA SISMED por WindowPattern
- `close_doc_windows()`: Cierra ventanas de error y Report Designer con @retry

### `src/sidmed/ingreso.py` — Automatización Ingresos ✅
- `procesar_ingresos(tuple[Ingreso])`: Itera, llama `procesar_ingreso()`, guarda cada movimiento a Excel individualmente
- `procesar_ingreso(ingreso)`: login → navegar → abrir registro → cabecera → productos → guardar → extraer correlativo → cerrar
- Cabecera: almacén origen harcodeado "ALM. ANEXO RIOJA - SAN MARTIN", combo concepto, NGR autogenerado
- Productos: modal Ctrl+Insert, escribe código, lote, fecha (DDMMYYYY), registro sanitario, tipo suministro, fuente fin, cantidad, temperatura, precio
- Logging con formato `[INGRESO N/M]`
- No importa `from ..helpers.windows import *` (usa `_comun_almacen`)

### `src/sidmed/salidas.py` — Automatización Salidas ✅
- `procesar_salidas(tuple[Salidas])`: Itera, llama `procesar_salida()`, guarda cada movimiento a Excel individualmente
- `procesar_salida(salida)`: login → Navegar_Salidas → cabecera → productos → guardar → extraer correlativo → cerrar
- Selección de almacén destino por código desde tabla GrdCatalogo
- Concepto harcodeado: click en coordenadas fijas (700,280 → 704,340 → 507,307)
- Productos: Ctrl+Insert, clicks ciegos en coordenadas
- Logging con formato `[SALIDA N/M]`
- Importa desde `_comun_almacen` (no desde `ingreso.py`)

### `src/sidmed/pedido.py` — Automatización Pedidos ✅ (con reintentos)
- `procesar_pedidos(tuple[Pedido])`: login una vez, itera pedidos con reintentos
- `procesar_pedido(pedido)`: navegar → cabecera → productos → guardar → extraer correlativo (placeholder randint) → volver a menú
- Navega a farmacia por código, forma_pago, tipo_receta, cliente, prescriptor, diagnósticos, productos
- **Reintentos automáticos**: `MAX_REINTENTOS_PEDIDO = 3`. En cada fallo: cierra ventanas huérfanas (`cerrar_ventanas_sismed()` click 1585,15 ×2), reloguea, reintenta
- **Registro en Excel**: intentos fallidos → `estado="RETRY"`, éxito → `estado="OK"` (con mensaje "tras N reintento(s)"), fallo definitivo → `estado="ERROR"` + raise
- Mismo `Nº de Procesado` en todos los intentos del mismo pedido
- Logging con formato `[LOTE] Pedido N/M`

### `src/sidmed/_login.py` — Login SISMED
- `login(username, password)`: Win+D → si no existe ventana login, abre .exe con Popen → escribe credenciales → cierra ventana productos vencidos
- Manejo automático de backup diario: `_verificar_backup_diario()`, `_ignorar_program_error()` (cada 10s), `_esperar_backup_automatico()` con 2 fases (Backups Automátic[o] + Regeneración de índices)
- Retry loop infinito con `input()` si el login falla

### `PedidosSP/pedido_SP.py` — Automatización Pedidos (VERSIÓN ACTIVA) ✅
- Módulo principal de pedidos con correlativo real (Boleta/Ticket) y actualización de estado en BD
- `procesar_pedidos(tuple[Pedido])`: login una vez, itera pedidos con reintentos
- `procesar_pedido(pedido)`: navegar → cabecera → productos → guardar → extraer correlativo real desde título ventana → procesar Boleta/Ticket → volver a menú
- **Extracción real de correlativo**: CONTADO → ventana "BOLETA DE VENTA #176-0000007", SIS → "TICKET #003-0000008"
- **Actualización BD**: llama `ejecutar_sp_update_estado(pedido.update_key)` tras cada pedido exitoso
- **Detección de cliente no encontrado**: `seleccionar_cliente()` retorna `False` → llama `volver_a_menuprincipal()` → levanta `ClienteNoEncontradoError` → log `CLIENTE_NO_ENCONTRADO` en Excel sin reintentar
- **Reintentos automáticos**: `MAX_REINTENTOS_PEDIDO = 3`. En cada fallo: cierra ventanas, reloguea, reintenta. Excepción: `ClienteNoEncontradoError` no reintenta
- **Registro en Excel**: estado="OK", "OK_REPROCESADO", "RETRY", "ERROR", "CLIENTE_NO_ENCONTRADO"
- Mismo `Nº de Procesado` en todos los intentos del mismo pedido
- Boleta CONTADO: llena TxtValVta → TxtImpPag (0 → 0.01) → Aceptar. SIS/INTERVENCION: solo Aceptar

### `src/helpers/` — Helpers UI
- `windows.py`: Accesores para ventanas SISMED (Farmacia, RegistroPedido, MenuPrincipal, etc.)
- `selecionar.py`: `seleccionar_combo_por_texto()` y `seleccionar_combo_por_texto_con_autoenter()` — logging en DEBUG
- `cliente.py`: `seleccionar_cliente(dni) -> bool` — Busca cliente por DNI; retorna `True` si TxtCliente cambió (encontrado), `False` si no
- `farmacia.py`: Busca farmacia por código en grilla
- `producto.py`: `agregar_producto()` y `agregar_productos()` para pedidos
- `diagnosticos.py`: Rellena hasta 3 diagnósticos CIE
- `input.py`: `escribir_input()` con retry COM
- `manejo_errores.py`: Manejo de ventanas de error SISMED

### `src/reportes/` — Reportes Excel
- `excel_schema.py`: Define columnas y funciones `crear_row_ingreso/pedido/salida/incidencia_validacion`
- `excel_writer.py`: Guarda/append a `movimientos.xlsx` con `polars`. `guardar_movimientos()` acepta dict o list[dict], convierte todos los valores a string, usa `schema_overrides` para evitar dtype warnings. `obtener_siguiente_numero_procesado()` lee el último Nº de Procesado y suma 1. `guardar_incidencias()` separado para `incidencias.xlsx`

---

## 📁 Estructura de Archivos

```
sismed_wrapper/
├── AGENTS.md                          ← Este archivo de contexto
├── .env                               ← Config BD y SISMED
├── pyproject.toml                     ← Dependencias
├── reporte_rpa.csv                    ← Reporte del SP (datos de movimientos)
├── movimientos.xlsx                   ← Excel de resultados (autogenerado)
│
├── Movimientos09062026/               ← Pipeline dia especifico 09/06/2026
│   ├── ingresos.py                    ← Ingreso de todos los productos x5 a 06732F01
│   ├── salidas.py                     ← 3 salidas: F01→F02, F01→F04, F01→F05
│   └── main.py                        ← main propio: ingreso → salidas
│
├── PedidosSP/                         ← Módulo activo de pedidos (correlativo real + BD)
│   └── pedido_SP.py                   ← Flujo Pedidos con Boleta/Ticket, update_key, ClienteNoEncontradoError
│
├── database/
│   └── conexion.py                    ← Conexión pyodbc + ejecutar_sp
│
├── src/
│   ├── __main__.py                    ← Orquestador (ahora solo salidas simuladas)
│   ├── config.py                      ← Variables de entorno
│   ├── paths.py                       ← Rutas del proyecto
│   ├── logger.py                      ← Loguru config
│   ├── data_simulator.py              ← Simulador antiguo (reemplazado)
│   ├── simulacion_ingreso_test.py     ← Genera ingresos *5 stock para test de salidas
│   ├── simulacion_salida_test.py      ← Distribuye stock desde 06732F01 a otras farmacias
│   │
│   ├── datos/
│   │   ├── sp_adapter.py              ← Mapeo SP → Modelos (NUEVO)
│   │   └── test_data.py               ← Datos simulados (ANTIGUO, no usado)
│   │
│   ├── models/
│   │   ├── pedido.py                  ← Pydantic (con validaciones)
│   │   ├── ingreso.py                 ← Plain class
│   │   ├── Salidas.py                 ← Plain class
│   │   ├── Medicamento.py             ← Plain class ( + ProductoIngreso alias)
│   │   ├── enums.py                   ← TipoReceta
│   │   ├── forma_pago.py              ← FormaPago (StrEnum)
│   │   ├── cliente.py, farmacia.py    ← Plain classes
│   │   ├── diagnostico.py, prescriptor.py
│   │   ├── producto.py               ← Dataclass (no usado)
│   │   └── validation_utils.py       ← Util Pydantic errors
│   │
│   ├── sidmed/
│   │   ├── _login.py                  ← Login SISMED
│   │   ├── _comun_almacen.py          ← Funciones compartidas ALMACEN ✅
│   │   ├── ingreso.py                 ← Flujo Ingreso ✅
│   │   ├── salidas.py                 ← Flujo Salida 🔄
│   │   ├── pedido.py                  ← Flujo Pedido 🔄
│   │   └── wrapper.py                 ← Stub (no usado)
│   │
│   ├── helpers/
│   │   ├── windows.py                 ← Accesores ventanas SISMED
│   │   ├── selecionar.py              ← ComboBox helpers
│   │   ├── cliente.py, farmacia.py    ← Selección UI
│   │   ├── producto.py, diagnosticos.py
│   │   ├── input.py, combo.py
│   │   ├── manejo_errores.py, ventana.py
│   │   ├── ui_helper.py
│   │   └── Ingreso/                   ← Helpers ingreso antiguos
│   │
│   ├── reportes/
│   │   ├── excel_schema.py            ← Schema filas Excel
│   │   └── excel_writer.py            ← Escritura Excel (polars)
│   │
│   └── controller/                    ← Vacío
│
└── tests/
    ├── test_ingreso.py                ← Test ingreso (llamada real)
    ├── test_salida.py                 ← Test salida (llamada real)
    ├── test_pedido.py                 ← Tests modelo, mapeo, SP adapter, schema
    ├── test_children.py               ← Definiciones UI
    └── __init__.py
```

---

## ✅ Estado Actual (lo que ya funciona)

- **Conexión BD**: `pyodbc` → SQL Server funciona correctamente
- **SP_MOVIMIENTOS_SISMED_RPA**: Ejecuta y devuelve headers + detalles
- **`sp_adapter.py`**: Mapea correctamente headers+detalles a objetos del dominio
- **Ingresos**: Flujo completo funcional — obtiene datos del SP, llena en SISMED, guarda correlativo
- **Salidas**: Flujo completo funcional — `almacen_virtual_origen` corregido (f"{cod_almacen}01")
- **Validación Pedidos**: Pydantic + reglas de negocio funcionando
- **Reporte Excel**: Guardado con polars, append a movimientos.xlsx
- **`src/__main__.py`**: Ejecuta SOLO salidas simuladas (sin SP, sin ingresos previos) — para pruebas rápidas de salidas
- **`Movimientos09062026/main.py`**: Pipeline completo del día 09/06/2026 — ingreso de todos los productos a F01, luego distribución a F02/F04/F05
- **`simulacion_ingreso_test.py`**: Helper que genera ingresos *5 stock para cada producto de SALIDA (para pruebas de stock)
- **`test_data.py` y `data_simulator.py`**: Ya no son importados por ningún módulo
- **`SP_UPDESTADOMOV_RPA`**: Actualización de estado en BD tras cada ingreso/salida/pedido exitoso (vía `ejecutar_sp_update_estado`)
- **`_login.py`**: Manejo automático de backup diario (detecta ventanas y espera regeneración de índices)
- **Detección cliente no encontrado**: `seleccionar_cliente()` retorna `False` si TxtCliente no cambia → `ClienteNoEncontradoError` → log en Excel sin reintentar

### 📊 Análisis de Tipos de Movimiento (SP_Junio.csv)
Datos del SP para junio 2026: **7,152 movimientos totales**.

| KS_TIPO_MOV | KS_TIPO_MOVIMIENTO_DES | TIPO_MOV_DES | Cantidad | % | Unidades | % Unid. | Estado |
|---|---|---|---|---|---|---|---|
| 211 | ENTREGA A TERCERO POR VENTA | PEDIDO | 6,725 | 94.0% | 1,198,446 | 59.3% | ✅ Procesado como PEDIDO |
| 207 | ENTREGA A PACIENTE | PEDIDO | 113 | 1.6% | 2,349 | 0.1% | ✅ Procesado como PEDIDO |
| 205 | EGRESO TRANSFERENCIA A FARMACIA | SALIDA | 144 | 2.0% | 326,805 | 16.2% | ✅ Implementado |
| 101 | COMPRA INSTITUCIONAL | INGRESO | 58 | 0.8% | ~370,000 | 18.4% | ✅ Implementado |
| 112 | TRANSFERENCIAS ESTRATEGICAS | INGRESO | 10 | 0.1% | ~5,000 | 0.2% | ✅ Implementado |
| 108 | EXTORNO DE UN EGRESO | EXTORNO | 80 | 1.1% | 109,615 | 5.4% | ⚠️ No implementado |
| 206 | ENTREGA A SERVICIO | SALIDA | 21 | 0.3% | 7,082 | 0.3% | ⚠️ No implementado |
| 202 | EGRESO NO INFORMA AL SAP | SALIDA | 1 | <0.1% | — | — | ⚠️ No implementado |

#### Detalle: PEDIDO 211 vs 207
Ambos caen en TIPO_MOVIMIENTO_DES="PEDIDO" y el SP adapter los procesa igual.
La diferencia clave es TIPO_PACIENTE:

| Campo | 211 (Venta/Tercero) | 207 (Paciente Internado) |
|---|---|---|
| TIPO_PACIENTE | E (Externo) | I (Internado) |
| DIAGNOSTICO | Siempre NULL | Siempre lleno (CIE) |
| PRESCRIPTOR | Siempre NULL | Siempre lleno |
| FARMACIA/DESTINO | F02/F03/F04/F05 | Solo F02 |
| Seguros | SIS-MINSA, SALUDPOL, PARTICULAR | Solo SIS-MINSA |

El bot actual procesa ambos como PEDIDO y funciona. Para 211 (externo) es innecesario llenar diagnóstico/prescriptor.

#### Detalle: SALIDA 205 vs 206
| Campo | 205 (Transferencia) | 206 (Servicio/UPSS) |
|---|---|---|
| ALMACEN_DESTINO | Siempre lleno | Siempre NULL |
| FARMACIA | Siempre lleno | Siempre NULL |
| ALMACEN_ORIGEN | 06732F01 o F05 | Solo 06732F06 (UPSS) |
| KS_CONCEPTO | 22 (TRANSFERENCIA) | 02 (CONSUMO) |
| Movimientos | 144 | 21 |

#### Flujo EXTORNO (KS_TIPO_MOV=108)
- **Volumen**: 80 movimientos/mes, 504 líneas, 109,615 unidades (5.4% del total)
- **KS_CONCEPTO**: 20 (NOTA DE ENTRADA POR OTROS INGRESOS)
- **ALMACEN_ORIGEN**: Siempre NULL
- **ALMACEN_DESTINO**: Código de farmacia (ej. 06732F01)
- **KS_PEDIDO_NUMERO**: Referencia al pedido original
- **Campos vacíos**: FORMA_PAGO, DIAGNOSTICO, PRESCRIPTOR, UPS_VIRTUAL_ORIGEN
- **Flujo UI esperado**: Similar a INGRESO pero con concepto "OTROS INGRESOS" y referencia al pedido

### 🔍 Investigación Extorno — datos reales 19/07/2026

Archivo analizado: `19-07-26_SP_extorno.csv`

- **6 extornos** y **138 pedidos** en el día.
- Todos los extornos tienen `KS_PEDIDO_FECHA = 2026-07-19` → **corresponden a pedidos del mismo día**.
- **Los extornos NO extornan todo el pedido**. Son **devoluciones parciales** de medicamentos específicos.
- Cada extorno trae su propia lista de medicamentos en el detalle.

| Extorno | Pedido Ref | Farmacia | DNI | Medicamentos en extorno |
|---|---|---|---|---|
| 1 | 57 | 06732F02 | 62450106 | 6 medicamentos |
| 2 | 132 | 06732F03 | 90976850 | 1 medicamento (39992 x 1) |
| 3 | 134 | 06732F03 | 71213890 | 1 medicamento (08140 x 360) |
| 4 | 23 | 06732F03 | 71213890 | 1 medicamento (39992 x 1) |
| 5 | 135 | 06732F03 | 71213890 | 1 medicamento (08140 x 360) |
| 6 | 22 | 06732F03 | 43901684 | 5 medicamentos |

**Conclusión clave**: `KS_PEDIDO_NUMERO` es una referencia al pedido original, pero el extorno procesa su propio detalle. No asumir relación 1:1 entre pedido y extorno.

### 🛠️ Plan de implementación del flujo Extorno

1. **Modelo**: `src/models/extorno.py` (clase simple: farmacia, almacen_destino, concepto, medicamentos, correlativo_ksalud, update_key)
2. **SP Adapter**: agregar `"EXTORNO"` a `tipos_validos` y construir objetos `Extorno`
3. **Navegación**: reutilizar selección de farmacia de `navegar_a_pedidos`, pero después del `{TAB}` enviar `{RIGHT}{Enter}` para llegar a "registro de consumo"
4. **Flujo**: crear `src/flujos/extorno.py` con `procesar_extornos()`
5. **Excel**: agregar `crear_row_extorno()` en `excel_schema.py`
6. **Orquestador**: en `src/__main__.py` ejecutar extornos **después de pedidos**
7. **Prueba simulada**: crear `src/datos/test_extorno.py` con datos ficticios (cliente 002964401, medicamento 30588, cantidad 1, farmacia 02). Primero ejecutar el pedido, luego el extorno.
8. **Conexión real**: una vez validada la prueba simulada, conectar al SP real.

## 🚧 Lo que falta hacer

### Flujos nuevos (por KS_TIPO_MOV)
- **Extorno** (KS_TIPO_MOV=108): Datos confirmados (ver investigación 19/07/2026). Plan definido. Pendiente implementación.
- **Consumo/Venta** (KS_TIPO_MOV=206): Salidas sin almacén destino — 21 movimientos/mes, 0.3%. Pendiente implementación.
- **Filtrar pedidos**: Distinguir KS_TIPO_MOV=201 (dispensación) de 211 (venta) en el SP adapter

### Pedidos con datos reales
- El SP adapter ya construye objetos Pedido correctamente (testeado)
- El flujo pedidos con correlativo real funciona, probando con lotes más grandes

### Mejoras pendientes
- `_obtener_fechas()` en `__main__.py` está harcodeado → parametrizar
- Manejo de cliente y prescriptor real desde SP (no harcodeado)
- `Concepto` en salidas harcodeado por click ciego → mejorar
- Validación de Ingresos y Salidas es un passthrough (no hay validación real)
- Duplicación de productos (mismo código en un movimiento, sumar cantidades) — gap conocido no presente en datos actuales
- **BOLETA_NO_ENCONTRADA**: ~2.3% de pedidos fallan porque la UI cierra la boleta sin mostrar popup "Volver a Menu" — investigar timeout o estrategia alternativa

---

## 📐 Convenciones del Proyecto

### Código
- No añadir comentarios a menos que sea necesario (el proyecto tiene muchos comentarios existentes)
- Clases planas para Ingreso/Salida/Medicamento, Pydantic para Pedido
- Enums con StrEnum (FormaPago, TipoReceta)
- Logger con loguru
- Errores: levantar Exception con mensaje descriptivo

### UI Automation
- uiautomation para interactuar con SISMED
- Coordenadas de click (ciegas) cuando no se puede acceder por Name/ControlType
- Sleeps generosos entre acciones (0.5s - 3s) por lentitud del sistema
- Retry con COMError

### Tests
- pytest con monkeypatch para mockear `ejecutar_sp_movimientos`
- Tests de: modelos, mapeo de datos, SP adapter, Excel schema

---

## 📝 Notas Importantes

- **reporte_rpa.csv**: Contiene la salida del SP, usado para entender estructura de datos
- **prueba.py**: Script de prueba manual (usa datos simulados)
- **_debug_sp.py**: Script para debuggear el SP manualmente
- **Ingresos hardcodean** almacén origen "ALM. ANEXO RIOJA - SAN MARTIN" y UPS "000"
- **Salidas hardcodean** concepto "DISTRIBUCION" con clicks ciegos
- **Flujo real**: Ingreso solo desde 030S01 → 06732F01. Salida desde 06732F01 → cualquier otro almacén.
- **`simulacion_ingreso_test.py`**: Para inyectar stock antes de probar salidas, ejecutar:
  ```python
  python -c "from src.simulacion_ingreso_test import generar_ingresos_para_prueba; from src.sidmed.ingreso import procesar_ingresos; procesar_ingresos(generar_ingresos_para_prueba())"
  ```
  Crea 1 ingreso a `06732F01` (único destino alcanzable desde el almacén origen harcodeado "ALM. ANEXO RIOJA - SAN MARTIN") con cantidad ×5 de todos los productos de SALIDA agregados.
- **`simulacion_salida_test.py`**: Distribuye stock desde `06732F01` a las farmacias que fallan por falta de stock. Ejecutar ANTES del main:
  ```python
  python -c "from src.simulacion_salida_test import generar_salidas_para_prueba; from src.sidmed.salidas import procesar_salidas; procesar_salidas(generar_salidas_para_prueba())"
  ```
  Crea 4 salidas: 06732F01 → 06732F02 (06471), → F03 (01537), → F04 (18157), → F05 (01537+04901).
- **`src/__main__.py`**: Ejecuta SOLO salidas simuladas (sin SP, sin ingresos). Para pruebas rápidas.
- **`Movimientos09062026/main.py`**: Pipeline completo del día 09/06/2026:
  1. Ingresa todos los productos (×5) a 06732F01
  2. Distribuye desde F01 a F02 (33 prods), F04 (04901), F05 (06471,18157,04922,12804,12805)
- **Para ejecutar el pipeline del día**:
  ```powershell
  .\.venv\Scripts\python.exe Movimientos09062026\main.py
  ```
- **Datos reales del SP (09/06/2026)**: 5 ingresos → F01, 8 salidas (3 desde F01 a F02/F05, 5 entre otras farmacias). Los archivos de `Movimientos09062026/` usan estos datos adaptados al flujo "ingreso central → distribución".
