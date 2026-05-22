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
    "CantidadMedicamentos",
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
            "CantidadMedicamentos": len(ingreso.medicamentos),
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
            "CantidadMedicamentos": len(getattr(pedido, "Medicamentos", [])),
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
            "CantidadMedicamentos": len(salida.medicamentos),
        }
    )

    return row


def crear_row_incidencia_validacion(
    tipo: str,
    error: str,
    data: dict = None,
    i: int = None,
):
    """
    Crea un diccionario para registrar incidencias de validación en Excel.

    Args:
        tipo: tipo de movimiento ("INGRESO", "SALIDA", "PEDIDO", etc.)
        error: mensaje de error de validación
        data: dict con los datos que causaron el error (opcional)
        i: número de procesado (opcional, se auto-incrementa)

    Returns:
        dict listo para Excel con estructura amigable
    """
    row = crear_row_base()
    now = datetime.now()

    # Contar medicamentos si están presentes en data
    cant_meds = 0
    if data:
        cant_meds = len(data.get("Medicamentos", data.get("medicamentos", [])))

    # Normalizar el tipo
    tipo_normalizado = str(tipo).upper() if tipo else "DESCONOCIDO"

    row.update(
        {
            "Nº de Procesado": i if i is not None else "",
            "Fecha": now.strftime("%Y-%m-%d"),
            "Hora": now.strftime("%H:%M:%S"),
            "TipoMovimiento": tipo_normalizado,
            "Estado": "ERROR_VALIDACION",
            "Error": str(error),
            "CantidadMedicamentos": cant_meds,
        }
    )

    # Añadir 'tipo' al dict para acceso directo
    row["tipo"] = tipo_normalizado

    return row
