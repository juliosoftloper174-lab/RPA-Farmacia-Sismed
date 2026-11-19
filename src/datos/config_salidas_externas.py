"""
Configuración de mapeo para salidas externas (doc 05 - NOTA DE SALIDA POR OTROS EGRESOS).

Fuente: DOC_TIPMOV_CON_NOTA_DE_SALIDA_KSALUD.xlsx
Clave de búsqueda: (KS_DOCUMENTO, KS_TIPO_MOVIMIENTO, KS_CONCEPTO)

Reglas:
- Si la combinación no está en la tabla -> NO procesar.
- Si ALMACEN_DESTINO del SP no coincide con destino_ksalud -> NO procesar.
- Los códigos SISMED de destino y las coordenadas de UI se completan a medida que se confirmen.
"""

# NSEAPs definidos en el Excel:
# C1 = DEVOLUCION x SOBRE STOCK
# C2 = DEV. X R.S. CAN/SUSP/VENC/ANUL
# C3 = DISTRIBUCION

MAPA_SALIDAS_EXTERNAS: dict[tuple[str, str, str], dict] = {
    # Tipo 203 - EGRESO TRANSFERENCIA A OTRO CENTRO ASISTENCIAL -> C1
    ("05", "203", "31"): {
        "nseap": "C1",
        "concepto_sismed": "DEVOLUCION X SOBRE STOCK",
        "destino_ksalud": "1",  # Anexo Rioja
        "destino_sismed": "030S01",  # TODO: confirmar código real en SISMED
        "coordenadas": [
            (700, 280),  # abrir combo box
            (700, 361),  # bajar combo box
            (596, 307),  # seleccionar Sobre Stock (bajado 4 px)
        ],
    },
    ("05", "203", "32"): {
        "nseap": "C1",
        "concepto_sismed": "DEVOLUCION X SOBRE STOCK",
        "destino_ksalud": "1",
        "destino_sismed": "030S01",
        "coordenadas": None,
    },
    ("05", "203", "33"): {
        "nseap": "C1",
        "concepto_sismed": "DEVOLUCION X SOBRE STOCK",
        "destino_ksalud": "1",
        "destino_sismed": "030S01",
        "coordenadas": None,
    },
    ("05", "203", "35"): {
        "nseap": "C1",
        "concepto_sismed": "DEVOLUCION X SOBRE STOCK",
        "destino_ksalud": "1",
        "destino_sismed": "030S01",
        "coordenadas": None,
    },
    ("05", "203", "36"): {
        "nseap": "C1",
        "concepto_sismed": "DEVOLUCION X SOBRE STOCK",
        "destino_ksalud": "1",
        "destino_sismed": "030S01",
        "coordenadas": None,
    },
    # Tipo 208 - EXTORNO DE UN INGRESO -> C2
    ("05", "208", "20"): {
        "nseap": "C2",
        "concepto_sismed": "DEV. X R.S. CAN/SUSP/VENC/ANUL",
        "destino_ksalud": "1",
        "destino_sismed": "030S01",
        "coordenadas": [
            (700, 280),  # abrir combo box
            (598, 343),  # seleccionar Dev. x R.S.
        ],
    },
    # Tipo 213 - EGRESO POR VENCIMIENTO -> C2
    ("05", "213", "10"): {
        "nseap": "C2",
        "concepto_sismed": "DEV. X R.S. CAN/SUSP/VENC/ANUL",
        "destino_ksalud": "1",
        "destino_sismed": "030S01",
        "coordenadas": None,
    },
    # Tipo 214 - EGRESO - POR OTROS EGRESOS -> C3 (DISTRIBUCION)
    ("05", "214", "26"): {
        "nseap": "C3",
        "concepto_sismed": "DISTRIBUCION",
        "destino_ksalud": "2",  # Logistica
        "destino_sismed": "030A00",  # TODO: confirmar código real en SISMED
        "coordenadas": [
            (700, 280),  # abrir combo box
            (700, 361),  # bajar combo box
            (515, 315),  # seleccionar Distribucion
        ],
    },
}


# Conceptos pendientes de confirmar por el grupo de desarrollo:
# - Tipo 203, concepto 34 (si existe)
# - Tipo 213, REGISTRO SANITARIO (concepto desconocido)
# - Tipo 214, SUSPENSION (concepto desconocido)
# - Tipo 216, VENTA INSTITUCIONAL, concepto 24
# - Tipo 217, EGRESO POR DETERIORO, concepto 09


def obtener_config_salida_externa(doc: str, tipo: str, concepto: str) -> dict | None:
    """Devuelve la configuración para una salida externa o None si no existe."""
    return MAPA_SALIDAS_EXTERNAS.get((doc.strip(), tipo.strip(), concepto.strip()))
