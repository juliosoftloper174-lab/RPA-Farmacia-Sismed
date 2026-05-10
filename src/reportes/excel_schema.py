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
    "Referencia",
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


from datetime import datetime


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
            "almOrigen": ingreso.almacen_origen,
            "almDestino": ingreso.almacen_destino,
            "almVirtual": ingreso.almacen_virtual_origen,
            "Concepto": ingreso.concepto,
            "Referencia": ingreso.referencia,
            "UPS": ingreso.ups_codigo,
            "CantidadProductos": len(ingreso.productos),
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
            "Referencia": salida.referencia,
            # GENERAL
            "CantidadProductos": len(salida.productos),
        }
    )

    return row
