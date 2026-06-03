from src.models.enums import TipoReceta
from src.models.forma_pago import FormaPago

MOVIMIENTOS = [
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
                    "codigo": "30588",
                    "cantidad": 1,
                }
            ],
            "fua": "786636652",
        },
    },
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
                    "codigo": "30588",
                    "cantidad": 1,
                }
            ],
            "fua": "786636652",
        },
    },
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
                    "codigo": "30588",
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
                    "cantidad": 1,
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
    {
        "tipo": "salida",
        "data": {
            "almacen_origen": "06732F01",
            "almacen_destino": "06732F02",
            "almacen_virtual_origen": "06732F0101",
            "concepto": "DISTRIBUCION",
            "medicamentos": [
                {
                    "codigo": "30588",
                    "cantidad": 1,
                    "lote": "LteNvo7",
                    "tipo": 1,
                    "subtipo": 5,
                }
            ],
        },
    },
]
