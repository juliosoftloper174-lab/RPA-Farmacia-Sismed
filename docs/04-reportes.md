# Reportes Excel

## Archivos generados

| Archivo | Contenido |
|---------|-----------|
| `movimientos_YYYY-MM-DD.xlsx` | Registro de todos los movimientos procesados en el día |
| `incidencias.xlsx` | Incidencias de validación (separado) |

## Columnas del Excel (`movimientos_*.xlsx`)

| Columna | Descripción |
|---------|-------------|
| `Nº de Procesado` | Número correlativo único |
| `Nº correlativo Ksalud` | ID del movimiento en KSalud |
| `Nº correlativo Sismed` | Número de documento generado en SISMED |
| `Fecha` | Fecha de procesamiento |
| `Hora` | Hora de procesamiento |
| `Usuario` | Usuario de SISMED |
| `TipoMovimiento` | INGRESO / SALIDA / PEDIDO |
| `Estado` | OK / ERROR / RETRY / CLIENTE_NO_ENCONTRADO / VALIDACION / SALTADO |
| `Error` | Mensaje de error (si aplica) |
| `almOrigen` | Almacén origen (solo SALIDA) |
| `almDestino` | Almacén destino (INGRESO/SALIDA) |
| `almVirtual` | Almacén virtual (INGRESO/SALIDA) |
| `Concepto` | Concepto del movimiento |
| `farmacia` | Código de farmacia (solo PEDIDO) |
| `cliente` | Código de cliente (solo PEDIDO) |
| `prescriptor` | Código de prescriptor (solo PEDIDO) |
| `forma_pago` | Forma de pago (solo PEDIDO) |
| `tipo_receta` | Tipo de receta (solo PEDIDO) |
| `FUA` | Número FUA (solo PEDIDO) |
| `Diag Nº1` | Diagnóstico CIE-10 (solo PEDIDO) |
| `Diag Nº2` | Diagnóstico CIE-10 (solo PEDIDO) |
| `Diag Nº3` | Diagnóstico CIE-10 (solo PEDIDO) |
| `CantidadMedicamentos` | Número de medicamentos en el movimiento |

## Estados posibles

| Estado | Significado |
|--------|-------------|
| `OK` | Procesado correctamente al primer intento |
| `OK_REPROCESADO` | Procesado correctamente tras reintentos (solo pedidos) |
| `ERROR` | Falló definitivamente |
| `RETRY` | Falló en un intento pero se reintentará (solo pedidos) |
| `CLIENTE_NO_ENCONTRADO` | Cliente no existe en SISMED (solo pedidos) |
| `VALIDACION` | No pasó validación de datos |
| `SALTADO` | Movimiento omitido (OTROS INGRESOS/EGRESOS) |

## Escritura (polars)

La librería `excel_writer.py` usa **polars** para leer/escribir Excel:

- **Append**: Si el archivo ya existe, lee el actual, concatena filas nuevas y sobrescribe
- **Normalización**: Asegura que las columnas existentes coincidan con el esquema esperado
- **Nº de Procesado**: Lee el último número del archivo existente y suma 1

## Resumen diario

`leer_resumen_diario()` calcula desde el Excel del día:

```python
{
    "ingresos": N,      # Total de ingresos
    "salidas": N,       # Total de salidas
    "pedidos": N,       # Total de pedidos
    "ok": N,            # Total OK + OK_REPROCESADO
    "error": N,         # Total ERROR
    "saltados": N,      # Total SALTADO
}
```

Este resumen se envía por correo al final del día.
