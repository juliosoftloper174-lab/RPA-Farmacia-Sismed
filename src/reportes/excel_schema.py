from datetime import datetime

EXCEL_COLUMNS = [
    "Nº de Procesado",
    "Nº correlativo Ksalud",
    "Nº correlativo Sismed",
    "Fecha",
    "Hora",
    "Usuario",
    "TipoMovimiento",
    "Estado",
    "Error",
    # INGRESOS / SALIDAS
    "almOrigen",
    "almDestino",
    "almVirtual",
    "Concepto",
    "UPS",
    # PEDIDOS
    "farmacia",
    "cliente",
    "prescriptor",
    "forma_pago",
    "tipo_receta",
    "FUA",
    # DIAGNOSTICOS
    "Diag Nº1",
    "Diag Nº2",
    "Diag Nº3",
    # GENERAL
    "CantidadProductos",
]


def crear_row_base() -> dict:
    return {column: "" for column in EXCEL_COLUMNS}


def crear_row_ingreso(
    i: int,
    username: str,
    correlativo_ksalud: str,
    correlativo_sismed: str,
    ingreso,
    estado: str,
    error: str = "",
):
    row = crear_row_base()

    now = datetime.now()

    row.update(
        {
            "Nº de Procesado": i,
            "Nº correlativo Ksalud": correlativo_ksalud,
            "Nº correlativo Sismed": correlativo_sismed,
            "Fecha": now.strftime("%Y-%m-%d"),
            "Hora": now.strftime("%H:%M:%S"),
            "Usuario": username,
            "TipoMovimiento": "INGRESO",
            "Estado": estado,
            "Error": error,
            # INGRESOS
            "almOrigen": ingreso.almacen_origen,
            "almDestino": ingreso.almacen_destino,
            "almVirtual": ingreso.almacen_virtual_origen,
            "Concepto": ingreso.concepto,
            "UPS": ingreso.ups_codigo,
            # GENERAL
            "CantidadProductos": len(ingreso.medicamentos),
        }
    )

    return row


def crear_row_pedido(
    i: int,
    username: str,
    correlativo_ksalud: str,
    correlativo_sismed: str,
    pedido,
    estado: str,
    error: str = "",
):
    row = crear_row_base()

    now = datetime.now()

    diagnosticos = [
        getattr(d, "codigo", str(d)) for d in getattr(pedido, "diagnosticos", [])
    ]

    row.update(
        {
            "Nº de Procesado": i,
            "Nº correlativo Ksalud": correlativo_ksalud,
            "Nº correlativo Sismed": correlativo_sismed,
            "Fecha": now.strftime("%Y-%m-%d"),
            "Hora": now.strftime("%H:%M:%S"),
            "Usuario": username,
            "TipoMovimiento": "PEDIDO",
            "Estado": estado,
            "Error": error,
            # PEDIDOS
            "farmacia": getattr(
                pedido.farmacia,
                "codigo",
                str(pedido.farmacia),
            ),
            "cliente": getattr(
                pedido.cliente,
                "codigo",
                str(pedido.cliente),
            ),
            "prescriptor": getattr(
                pedido.prescriptor,
                "codigo",
                str(pedido.prescriptor),
            ),
            "forma_pago": getattr(
                pedido.forma_pago,
                "value",
                str(pedido.forma_pago),
            ),
            "tipo_receta": getattr(
                pedido.tipo_receta,
                "value",
                str(pedido.tipo_receta),
            ),
            "FUA": pedido.fua or "",
            # DIAGNOSTICOS
            "Diag Nº1": diagnosticos[0] if len(diagnosticos) > 0 else "",
            "Diag Nº2": diagnosticos[1] if len(diagnosticos) > 1 else "",
            "Diag Nº3": diagnosticos[2] if len(diagnosticos) > 2 else "",
            # GENERAL
            "CantidadProductos": len(getattr(pedido, "medicamentos", [])),
        }
    )

    return row


def crear_row_salida(
    i: int,
    username: str,
    correlativo_ksalud: str,
    correlativo_sismed: str,
    salida,
    estado: str,
    error: str = "",
):
    row = crear_row_base()

    now = datetime.now()

    row.update(
        {
            "Nº de Procesado": i,
            "Nº correlativo Ksalud": correlativo_ksalud,
            "Nº correlativo Sismed": correlativo_sismed,
            "Fecha": now.strftime("%Y-%m-%d"),
            "Hora": now.strftime("%H:%M:%S"),
            "Usuario": username,
            "TipoMovimiento": "SALIDA",
            "Estado": estado,
            "Error": error,
            # SALIDAS
            "almOrigen": salida.almacen_origen,
            "almDestino": salida.almacen_destino,
            "almVirtual": salida.almacen_virtual_origen,
            "Concepto": salida.concepto,
            # GENERAL
            "CantidadProductos": len(salida.medicamentos),
        }
    )

    return row
