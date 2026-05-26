from src.models.enums import TipoReceta
from src.models.forma_pago import FormaPago

MOVIMIENTOS = [
    {
        "tipo": "pedido",
        "data": {
            "farmacia": "06732F02",
            "cliente": "00033257",
            "prescriptor": "14571",
            "forma_pago": FormaPago.SIS,
            "tipo_receta": TipoReceta.SIN_NUMERO,
            "diagnosticos": [
                "R100",
                "R05X",
            ],
            "Medicamentos": [
                {
                    "codigo": "00091",
                    "cantidad": 1,
                },
                {
                    "codigo": "10155",
                    "cantidad": 1,
                },
            ],
            "fua": "786636652",
        },
    },
    {
        "tipo": "ingreso",
        "data": {
            "almacen_destino": "06732F01",
            "almacen_virtual_origen": "030S0101",
            "concepto": "DISTRIBUCION",
            "medicamentos": [
                {
                    "codigo": "36394",
                    "cantidad": 400,
                    "lote": "LteNvo1",
                    "tipo_ingreso": "SISMED-COMPRA NACIONAL (CN)",
                    "documento": "Contribuciones a Fondos (CON)",
                    "registro_sanitario": "SIN_REG_SAN",
                    "fecha_vencimiento": "2029/12/20",
                    "precio": "500",
                }
            ],
        },
    },
    {
        "tipo": "salida",
        "data": {
            "almacen_origen": "06732F01",
            "almacen_destino": "06732F02",
            "almacen_virtual_origen": "06732F0101",
            "concepto": "DISTRIBUCION",
            "medicamentos": [
                {
                    "codigo": "36394",
                    "cantidad": 900,
                    "lote": "DE5FDJ6D",
                    "tipo": 1,
                    "subtipo": 5,
                }
            ],
        },
    },
    {
        "tipo": "salida",
        "data": {
            "almacen_origen": "06732F01",
            "almacen_destino": "06732F02",
            "almacen_virtual_origen": "06732F0101",
            "concepto": "DISTRIBUCION",
            "medicamentos": [
                {
                    "codigo": "36394",
                    "cantidad": 950,
                    "lote": "DE5FDJ6D",
                    "tipo": 1,
                    "subtipo": 5,
                }
            ],
        },
    },
    # INTERVENCION_SANITARIA ahora es válido (se eliminó ups_codigo)
    {
        "tipo": "pedido",
        "data": {
            "farmacia": "06732F01",
            "cliente": "00033257",
            "prescriptor": "14571",
            "forma_pago": FormaPago.INTERVENCION_SANITARIA,
            "tipo_receta": TipoReceta.SIN_NUMERO,
            "diagnosticos": [
                "R05X",
            ],
            "Medicamentos": [
                {
                    "codigo": "00091",
                    "cantidad": 1,
                }
            ],
            "fua": "786636652",
        },
    },
    {
        "tipo": "ingreso",
        "data": {
            "almacen_destino": "06732F01",
            "almacen_virtual_origen": "030S0101",
            "concepto": "DISTRIBUCION",
            "medicamentos": [
                {
                    "codigo": "30588",
                    "cantidad": 400,
                    "lote": "LteNvo7",
                    "tipo_ingreso": "SISMED-COMPRA NACIONAL (CN)",
                    "documento": "Contribuciones a Fondos (CON)",
                    "registro_sanitario": "SIN_REG_SAN",
                    "fecha_vencimiento": "2029/12/20",
                    "precio": "500",
                },
            ],
        },
    },
    # SIS sin FUA → EN REVISION (antes lanzaba excepción)
    {
        "tipo": "pedido",
        "data": {
            "farmacia": "06732F01",
            "cliente": "00033257",
            "prescriptor": "14571",
            "forma_pago": FormaPago.SIS,
            "tipo_receta": TipoReceta.SIN_NUMERO,
            "diagnosticos": [
                "R05X",
            ],
            "Medicamentos": [
                {
                    "codigo": "00091",
                    "cantidad": 1,
                }
            ],
            "fua": None,
        },
    },
    # INTERVENCION_SANITARIA válido
    {
        "tipo": "pedido",
        "data": {
            "farmacia": "06732F01",
            "cliente": "00033257",
            "prescriptor": "14571",
            "forma_pago": FormaPago.INTERVENCION_SANITARIA,
            "tipo_receta": TipoReceta.SIN_NUMERO,
            "diagnosticos": [
                "R05X",
            ],
            "Medicamentos": [
                {
                    "codigo": "00091",
                    "cantidad": 1,
                }
            ],
            "fua": "786636652",
        },
    },
    # tipo_receta != SIN_NUMERO → EN REVISION
    {
        "tipo": "pedido",
        "data": {
            "farmacia": "06732F01",
            "cliente": "00033257",
            "prescriptor": "14571",
            "forma_pago": FormaPago.CONTADO,
            "tipo_receta": TipoReceta.NUMERADA,
            "diagnosticos": [
                "R05X",
            ],
            "Medicamentos": [
                {
                    "codigo": "00091",
                    "cantidad": 1,
                }
            ],
            "fua": None,
        },
    },
]
