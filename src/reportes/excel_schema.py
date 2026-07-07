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
            "almDestino": ingreso.almacen_destino,
            "almVirtual": ingreso.almacen_virtual_origen,
            "Concepto": ingreso.concepto,
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
                str(pedido.prescriptor) if pedido.prescriptor is not None else "",
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


def crear_row_saltado(
    i: int,
    tipo_mov: str,
    data,
    motivo: str = "Pendiente de implementacion",
) -> dict:
    row = crear_row_base()
    now = datetime.now()
    cant_meds = len(getattr(data, "medicamentos", getattr(data, "Medicamentos", [])))
    row.update(
        {
            "Nº de Procesado": i,
            "Fecha": now.strftime("%Y-%m-%d"),
            "Hora": now.strftime("%H:%M:%S"),
            "TipoMovimiento": tipo_mov,
            "Estado": "SALTADO",
            "Error": motivo,
            "CantidadMedicamentos": cant_meds,
        }
    )
    return row


def crear_row_incidencia_validacion(
    tipo: str,
    error: str,
    data: dict = None,
    i: int = None,
    estado: str = "VALIDACION",
):
    """
    Crea un diccionario para registrar incidencias de validación en el Excel general.

    Args:
        tipo: tipo de movimiento ("INGRESO", "SALIDA", "PEDIDO", etc.)
        error: mensaje de error de validación o procesamiento
        data: dict con los datos que causaron el error (opcional)
        i: número de procesado (opcional)
        estado: estado del registro (por ejemplo, "VALIDACION" o "PROCESAMIENTO")

    Returns:
        dict listo para Excel con estructura compatible con guardar_movimientos
    """
    row = crear_row_base()
    now = datetime.now()

    cant_meds = 0
    if data:
        cant_meds = len(data.get("Medicamentos", data.get("medicamentos", [])))

    tipo_normalizado = str(tipo).upper() if tipo else "DESCONOCIDO"

    row.update(
        {
            "Nº de Procesado": i if i is not None else "",
            "Fecha": now.strftime("%Y-%m-%d"),
            "Hora": now.strftime("%H:%M:%S"),
            "TipoMovimiento": tipo_normalizado,
            "Estado": estado.upper(),
            "Error": str(error),
            "CantidadMedicamentos": cant_meds,
            "almOrigen": (
                data.get("almacen_origen", "") if isinstance(data, dict) else ""
            ),
            "almDestino": (
                data.get("almacen_destino", "") if isinstance(data, dict) else ""
            ),
            "almVirtual": (
                data.get("almacen_virtual_origen", "") if isinstance(data, dict) else ""
            ),
            "Concepto": data.get("concepto", "") if isinstance(data, dict) else "",
            "farmacia": data.get("farmacia", "") if isinstance(data, dict) else "",
            "cliente": data.get("cliente", "") if isinstance(data, dict) else "",
            "prescriptor": (
                data.get("prescriptor", "") if isinstance(data, dict) else ""
            ),
            "forma_pago": (
                getattr(data.get("forma_pago"), "value", str(data.get("forma_pago")))
                if isinstance(data, dict)
                else ""
            ),
            "tipo_receta": (
                getattr(data.get("tipo_receta"), "value", str(data.get("tipo_receta")))
                if isinstance(data, dict)
                else ""
            ),
            "FUA": data.get("fua", "") if isinstance(data, dict) else "",
            "Diag Nº1": (
                (
                    data.get("diagnosticos", [])[0]
                    if isinstance(data.get("diagnosticos", []), list)
                    and len(data.get("diagnosticos", [])) > 0
                    else ""
                )
                if isinstance(data, dict)
                else ""
            ),
            "Diag Nº2": (
                (
                    data.get("diagnosticos", [])[1]
                    if isinstance(data.get("diagnosticos", []), list)
                    and len(data.get("diagnosticos", [])) > 1
                    else ""
                )
                if isinstance(data, dict)
                else ""
            ),
            "Diag Nº3": (
                (
                    data.get("diagnosticos", [])[2]
                    if isinstance(data.get("diagnosticos", []), list)
                    and len(data.get("diagnosticos", [])) > 2
                    else ""
                )
                if isinstance(data, dict)
                else ""
            ),
        }
    )

    row["tipo"] = tipo_normalizado

    return row
