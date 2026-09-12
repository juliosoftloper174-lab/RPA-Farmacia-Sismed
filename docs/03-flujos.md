# Automatización de Flujos

## Login (`_login.py`)

Función `login(username, password)`:

1. Win+D (minimiza todo)
2. Busca ventana "Acceso al Sistema"
3. Si no existe, abre SISMED.exe con Popen
4. Escribe usuario y contraseña
5. Click en Aceptar
6. Cierra ventana "Productos Vencidos y por Vencer"

### Manejo de backup diario

El bot detecta ventanas de backup automático de SISMED:

- "Envío de información de Consumo Diaria"
- "Backups Automático"
- "Regeneración de índices"

Si detecta backup, se pausa y espera confirmación del operador (Enter). Envía correo de notificación.

`esperar_hora_backup_si_aplica()` se activa una vez al día a la hora configurada (`HORA_CIERRE`) para pausar el bot y permitir backup manual.

---

## Ingreso (`ingreso.py`)

### Flujo completo

```
login() → navegar_a_ingresos() → [para cada ingreso]:
    abrir_registro()
    rellenar_cabecera(ingreso)
    agregar_productos(ingreso.medicamentos)
    guardar()
    extraer_correlativo_almacen()
    ejecutar_sp_update_estado()   ← estado=00
    guardar_movimientos(row)      ← estado=OK
    cerrar_ventana_registro()
cerrar_sismed()
```

### Cabecera

- Almacén origen: **hardcodeado** "ALM. ANEXO RIOJA - SAN MARTIN"
- Almacén destino: desde datos del SP
- Almacén virtual: desde SP (mapeado: "0" → "030S0101")
- Concepto: "DISTRIBUCION" (seleccionado por combo)
- NGR: código autogenerado (YYYYMMDDHHMM)
- UPS: hardcodeado "000"

### Productos

Para cada medicamento:
1. `Ctrl+Insert` — abre modal de producto
2. Escribe código, Enter
3. Escribe lote, Enter
4. Escribe fecha vencimiento (DDMMYYYY), Enter
5. Escribe registro sanitario
6. Selecciona tipo suministro (combo)
7. Selecciona fuente financiamiento (combo)
8. Escribe cantidad
9. Enter (temperatura default)
10. Escribe precio
11. Click en "Aceptar"

### Extracción de correlativo

Busca en ventana "ALMACEN - MINSA SISMED" el mensaje:
"Se grabó correctamente la Nota de Ingreso N° XXXX"

### Actualización BD

Si `update_key` existe, llama `SP_UPDESTADOMOV_RPA` con estado `"00"` (éxito) o `"10"` (error).

---

## Salida (`salida.py`)

### Flujo completo

```
login() → navegar_a_salidas() → [para cada salida]:
    abrir_registro_salida()
    rellenar_cabecera_salidas(salida)
    [para cada producto]: agregar_producto(producto)
    guardar()
    extraer_correlativo_almacen()
    ejecutar_sp_update_estado()   ← estado=00
    guardar_movimientos(row)      ← estado=OK
    cerrar_ventana_salida_guardada()
cerrar_sismed()
```

### Cabecera

1. Almacén origen: código desde SP (Enter en campo)
2. Almacén destino: busca por código en tabla `GrdCatalogo`, click en fila correcta
3. Almacén virtual: se construye como `{almacen_origen}01`
4. Concepto: **hardcodeado** "DISTRIBUCION" mediante 6 clicks ciegos en coordenadas fijas

### Productos

- `Ctrl+Insert` abre ventana de producto
- Clicks ciegos en coordenadas para código, cantidad
- No usa helpers de UI

### Extracción de correlativo

Mismo mecanismo que ingreso ("Se grabó correctamente la Nota de Salida N° XXXX").

### Actualización BD

Estado `"00"` (éxito) o `"20"` (error).

---

## Pedido (`pedido.py`)

### Flujo completo

```
login() → [para cada pedido con reintentos]:
    navegar_a_pedidos(pedido)
    rellenar_cabecera(pedido)
      └─ seleccionar_forma_pago()
      └─ manejar_forma_pago()
      └─ selecionar_receta()
      └─ seleccionar_cliente()
      └─ rellenar_ups_pedido()
      └─ prescriptor (si existe)
      └─ diagnosticos (si existen)
    agregar_productos(medicamentos)
    guardar()
    verificar_receta()              ← corrige error de receta si aparece
    extraer_correlativo_farmacia()  ← correlativo REAL desde título ventana
    procesar_boleta_venta()
    volver_a_menuprincipal()
```

### Navegación a farmacia

1. Click en menú principal
2. Selecciona farmacia por código desde ventana "Selección de Farmacias"
3. Navega al submenú de pedidos

### Cabecera

1. **Forma de pago**: selecciona en combo `CboDato` según `FormaPago`
2. **FUA**: si es SIS, escribe FUA en `Txtfua`
3. **Tipo receta**: click ciego en coordenadas
4. **Cliente**: buscar por DNI en `TxtDNICli`. Si no se encuentra:
   - Si cliente tiene nombre: **registrarlo automáticamente** en SISMED
   - Si no tiene nombre: lanzar `ClienteNoEncontradoError`
5. **UPS**: código hardcodeado "301" o desde pedido
6. **Prescriptor**: si existe, escribir código en `TxtColPresc`
7. **Diagnósticos**: hasta 3 códigos CIE-10 en `TxtCodCIE[1-3]`

### Productos

Para cada medicamento:
1. `Ctrl+Insert` — nueva fila
2. Enter — abre ventana "Seleccionar medicamento"
3. Ordena por código (click header)
4. Busca por código en `TxtBusca`
5. Click "Seleccionar"
6. Escribe cantidad
7. `Ctrl+Insert` + `Ctrl+Delete` — confirma línea

### Guardado y Boleta/Ticket

1. Click `CmdSave`
2. `verificar_receta()`: si aparece error "Aviso" o "Microsoft Visual FoxPro", corrige tipo receta y reintenta guardar
3. Busca ventana según forma de pago:
   - **CONTADO**: `"BOLETA DE VENTA #..."` — extrae correlativo, llena `TxtValVta` → `TxtImpPag` (0.01 si es 0) → Aceptar
   - **SIS/INTERVENCION**: `"TICKET #..."` — extrae correlativo → solo Aceptar
4. Correlativo real extraído del título (ej: `"176-0000007"`)

### Reintentos automáticos

`MAX_REINTENTOS_PEDIDO = 2` (3 intentos totales):

| Situación | Acción |
|-----------|--------|
| Error normal | Cierra ventanas, reloguea, reintenta (hasta 3 veces) |
| `ClienteNoEncontradoError` | NO reintenta, marca como `CLIENTE_NO_ENCONTRADO` |
| 3 fallos | Marca como `ERROR`, continúa con siguiente pedido |

### Actualización BD

| Estado | Situación |
|--------|-----------|
| `00` | Pedido procesado OK |
| `01` | Error definitivo (3 reintentos fallidos) |
| `02` | Cliente no encontrado |

### Registro en Excel

| Estado | Significado |
|--------|-------------|
| `OK` | Primer intento exitoso |
| `OK_REPROCESADO` | Exitoso tras reintentos |
| `RETRY` | Intento fallido (se reintentará) |
| `ERROR` | Fallo definitivo |
| `CLIENTE_NO_ENCONTRADO` | Cliente no existe en SISMED |
