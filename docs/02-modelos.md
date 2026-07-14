# Modelos de Datos

## Pedido (Pydantic)

Modelo principal con validación automática. Usa Pydantic `BaseModel`.

```python
class Pedido(BaseModel):
    farmacia: Farmacia                  # Obligatorio
    cliente: Cliente                    # Obligatorio
    prescriptor: Prescriptor | None     # Opcional
    forma_pago: FormaPago               # Obligatorio
    tipo_receta: TipoReceta             # Obligatorio
    diagnosticos: list[Diagnostico]     # Default []
    Medicamentos: list[Medicamento]     # Obligatorio (min 1)
    fua: str | None                     # Opcional
    ups_codigo: str = "301"
    correlativo_ksalud: str = ""
    update_key: tuple[str, ...] | None
```

### Validaciones (`obtener_revisiones()`)

| Regla | Condición |
|-------|-----------|
| FUA obligatorio | Si `forma_pago == SIS` y `fua` es None |
| Tipo receta debe ser SIN_NUMERO | Si `tipo_receta != "Receta Sin Numero"` |

### FUA ficticio

`generar_fua_ficticio()` genera un FUA correlativo (`00000001`, `00000002`, ...) para pedidos SIS que no tienen FUA.

## Ingreso (plain class)

```python
class Ingreso:
    almacen_destino: str
    almacen_virtual_origen: str
    concepto: str                       # Siempre "DISTRIBUCION"
    medicamentos: list[Medicamento]
    correlativo_ksalud: str = ""
    update_key: tuple[str, ...] | None
```

## Salidas (plain class)

```python
class Salidas:
    almacen_origen: str
    almacen_destino: str
    almacen_virtual_origen: str         # Se construye como "{almacen_origen}01"
    concepto: str                       # Siempre "DISTRIBUCION"
    medicamentos: list[Medicamento]
    correlativo_ksalud: str = ""
    update_key: tuple[str, ...] | None
```

## Medicamento (plain class)

```python
class Medicamento:
    codigo: str
    cantidad: int
    lote: str | None
    tipo_sum: str | None                # Ej: "SISMED-COMPRA NACIONAL (CN)"
    fuente_fin: str | None              # Ej: "Donaciones y Transferencias (DYT)"
    registro_sanitario: str | None
    fecha_vencimiento: str | None       # Formato: "2029/12/20"
    precio_compra: float | None
```

**Alias:** `ProductoIngreso = Medicamento` (compatibilidad).

## Clases auxiliares

```python
class Cliente:
    codigo: str             # DNI/RUC
    nombre: str | None
    sexo: str | None        # "FEMENINO" | "MASCULINO"
    fecha_nacimiento: str | None
    tipo_documento: str | None

class Farmacia:
    codigo: str             # Ej: "06732F01"

class Prescriptor:
    codigo: str             # Ej: "87705"

class Diagnostico:
    codigo: str             # Código CIE-10, Ej: "R100"
```

## Enums

```python
class FormaPago(StrEnum):
    CONTADO = "CONTADO"
    INTERVENCION_SANITARIA = "INTERVENCION SANITAR"
    SIS = "SIS"

class TipoReceta(StrEnum):
    SIN_NUMERO = "Receta Sin Numero"
    NUMERADA = "Receta Numerada"
    ESTANDAR = "Receta Estandar"
```

## Mapeo SP → Modelos

### Forma de pago

| Valor SP | FormaPago |
|----------|-----------|
| NULL / "" | CONTADO |
| "0" | INTERVENCION_SANITARIA |
| "1" | SIS |

### Almacén virtual origen

| Valor SP | Mapeo |
|----------|-------|
| "0" | "030S0101" |
| "1" | "030S0102" |
| otro | "030S0101" (default) |

### Tipo suministro

| Código SP | Texto en SISMED |
|-----------|-----------------|
| CN | SISMED-COMPRA NACIONAL (CN) |
| CI | SISMED-COMPRA UNIDAD EJECUTORA (CI) |
| SC | SISMED-CENTRALIZADO (SC) |

### Fuente financiamiento

| Código SP | Texto en SISMED |
|-----------|-----------------|
| DYT | Donaciones y Transferencias (DYT) |
| RDR | Recursos Directamente Recaudados (RDR) |
| ROR | Recursos Ordinarios (ROR) |

### Hardcodeados

- `CLIENTE = "00025759"` (fallback si no hay datos)
- `PRESCRIPTOR = "87705"` (siempre que exista un prescriptor en el SP)
- UPS en ingresos: `"000"` (significa "sin UPS")
