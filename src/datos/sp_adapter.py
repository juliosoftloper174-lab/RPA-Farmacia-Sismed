from src.models.cliente import Cliente
from src.models.diagnostico import Diagnostico
from src.models.farmacia import Farmacia
from src.models.forma_pago import FormaPago
from src.models.ingreso import Ingreso
from src.models.Medicamento import Medicamento
from src.models.pedido import Pedido
from src.models.prescriptor import Prescriptor
from src.models.Salidas import Salidas
from src.models.enums import TipoReceta
from src.logger import logger
from database.conexion import ejecutar_sp_movimientos

CLIENTE_HARDCODEADO = "00025759"
PRESCRIPTOR_HARDCODEADO = "87705"

COLUMNAS_HEADER = [
    "CORRELATIVO_KSALUD", "TIPO_MOVIMIENTO", "TIPO_MOVIMIENTO_DES",
    "FECHA_MOVIMIENTO", "ALMACEN_ORIGEN", "ALMACEN_VIRTUAL_ORIGEN",
    "ALMACEN_DESTINO", "ALMACEN_VIRTUAL_DESTINO", "FARMACIA",
    "PRESCRIPTOR", "FORMA_PAGO", "DIAGNOSTICO", "FUA",
    "KS_ORIGEN_CAS", "KS_CENTRO_CAS", "KS_TIPO_ALMACEN", "KS_ALMACEN",
    "KS_ALMACEN_DES", "KS_DOCUMENTO", "KS_DOCUMENTO_DES",
    "KS_NUMERO_MOVIMIENTO", "KS_TIPO_TRANSACCION", "KS_TIPO_TRANSACCION_DES",
    "KS_TIPO_MOVIMIENTO", "KS_TIPO_MOVIMIENTO_DES",
    "KS_CONCEPTO", "KS_CONCEPTO_DES", "KS_PEDIDO_NUMERO",
    "KS_PEDIDO_FECHA", "KS_PEDIDO_SEGURO", "KS_PEDIDO_SEGURO_DES",
    "KS_PEDIDO_FORMA_PAGO",
]


def _mapear_forma_pago(valor) -> FormaPago:
    if valor is None or str(valor).strip() in ("", "NULL"):
        return FormaPago.CONTADO
    v = str(valor).strip()
    if v == "0":
        return FormaPago.INTERVENCION_SANITARIA
    if v == "1":
        return FormaPago.SIS
    return FormaPago.CONTADO


def _parsear_fecha_vencimiento(fecha: str) -> str:
    if not fecha or fecha in ("NULL", ""):
        return ""
    fecha = fecha.replace("-", "/")
    partes = fecha.split("/")
    if len(partes) == 3 and partes[2] == "31":
        partes[2] = "30"
        fecha = "/".join(partes)
    return fecha


def _extraer_precio(valor) -> float | None:
    if valor is None:
        return None
    v = str(valor).strip()
    if not v or v == "NULL":
        return None
    try:
        return float(v.split()[0])
    except (ValueError, IndexError):
        return None


def _construir_medicamentos(detalles: list[dict]) -> list[Medicamento]:
    medicamentos = []
    for det in detalles:
        medicamentos.append(Medicamento(
            codigo=str(det.get("MATERIAL_CODIGO", "")).strip(),
            cantidad=int(float(str(det.get("CANTIDAD", 0)).strip())),
            lote=str(det.get("LOTE", "")).strip() or None,
            tipo_sum=_mapear_tipo_suministro(str(det.get("TIPO_SUMINISTRO", "")).strip()) or None,
            fuente_fin=_mapear_fuente_financiamiento(str(det.get("FUENTE_FINANCIAMIENTO", "")).strip()) or None,
            registro_sanitario=str(det.get("REGISTRO_SANITARIO", "")).strip() or None,
            fecha_vencimiento=_parsear_fecha_vencimiento(str(det.get("FECHA_VENCIMIENTO", "")).strip()),
            precio_compra=_extraer_precio(det.get("PRECIO_COMPRA")),
        ))
    return medicamentos


MAPA_ALMACEN_VIRTUAL_ORIGEN = {"0": "030S0101", "1": "030S0102"}

MAPA_TIPO_SUMINISTRO = {
    "CN": "SISMED-COMPRA NACIONAL (CN)",
    "CI": "SISMED-COMPRA UNIDAD EJECUTORA (CI)",
    "SC": "SISMED-CENTRALIZADO (SC)",
}

MAPA_FUENTE_FINANCIAMIENTO = {
    "DYT": "Donaciones y Transferencias (DYT)",
    "RDR": "Recursos Directamente Recaudados (RDR)",
    "ROR": "Recursos Ordinarios (ROR)",
}


def _mapear_almacen_virtual(valor_sp: str) -> str:
    return MAPA_ALMACEN_VIRTUAL_ORIGEN.get(valor_sp.strip(), "030S0101")


def _mapear_tipo_suministro(valor_sp: str) -> str:
    return MAPA_TIPO_SUMINISTRO.get(valor_sp.strip(), valor_sp.strip())


def _mapear_fuente_financiamiento(valor_sp: str) -> str:
    return MAPA_FUENTE_FINANCIAMIENTO.get(valor_sp.strip(), valor_sp.strip())


def _obtener_safe(row: dict, key: str, default=None):
    return row.get(key, row.get(key.upper(), default))


def obtener_movimientos(fecha_ini: str, fecha_fin: str) -> tuple[list[Pedido], list[Ingreso], list[Salidas]]:
    headers_raw, detalles_raw = ejecutar_sp_movimientos(fecha_ini, fecha_fin)

    if not headers_raw:
        logger.warning("No se encontraron movimientos en el rango de fechas.")
        return [], [], []

    tipos_validos = {"PEDIDO", "INGRESO", "SALIDA"}
    headers_raw = [r for r in headers_raw if str(r.get("TIPO_MOVIMIENTO_DES", "")).strip().upper() in tipos_validos]
    logger.info(f"Headers filtrados por tipo válido: {len(headers_raw)}")

    columns_detail = list(detalles_raw[0].keys()) if detalles_raw else []
    logger.info(f"Columnas del detalle: {columns_detail}")

    detalles_por_ks: dict[str, list[dict]] = {}
    for det in detalles_raw:
        ks = str(det.get("CORRELATIVO_KSALUD", "")).strip()
        detalles_por_ks.setdefault(ks, []).append(det)

    pedidos: list[Pedido] = []
    ingresos: list[Ingreso] = []
    salidas: list[Salidas] = []

    for row in headers_raw:
        tipo = str(row.get("TIPO_MOVIMIENTO_DES", "")).strip().upper()
        ks = str(row.get("CORRELATIVO_KSALUD", "")).strip()
        detalles = detalles_por_ks.get(ks, [])
        medicamentos = _construir_medicamentos(detalles)

        if tipo == "PEDIDO":
            prescriptor = None
            prescriptor_raw = _obtener_safe(row, "PRESCRIPTOR", "NULL")
            if prescriptor_raw not in (None, "NULL", ""):
                prescriptor = Prescriptor(PRESCRIPTOR_HARDCODEADO)

            diagnosticos = []
            diag_raw = _obtener_safe(row, "DIAGNOSTICO", "NULL")
            if diag_raw not in (None, "NULL", ""):
                diagnosticos = [Diagnostico(str(diag_raw).strip())]

            fua = _obtener_safe(row, "FUA", "NULL")
            fua = str(fua).strip() if fua not in (None, "NULL", "") else None

            forma_pago = _mapear_forma_pago(_obtener_safe(row, "FORMA_PAGO"))
            farmacia_cod = _obtener_safe(row, "FARMACIA", "")
            if not farmacia_cod or str(farmacia_cod).strip() in ("NULL", ""):
                farmacia_cod = _obtener_safe(row, "ALMACEN_DESTINO", "")

            pedido = Pedido(
                farmacia=Farmacia(str(farmacia_cod).strip()),
                cliente=Cliente(CLIENTE_HARDCODEADO),
                prescriptor=prescriptor,
                forma_pago=forma_pago,
                tipo_receta=TipoReceta.SIN_NUMERO,
                diagnosticos=diagnosticos,
                Medicamentos=medicamentos,
                fua=fua,
            )
            pedidos.append(pedido)

        elif tipo == "INGRESO":
            almacen_destino = str(_obtener_safe(row, "ALMACEN_DESTINO", "")).strip()
            avo = str(_obtener_safe(row, "ALMACEN_VIRTUAL_ORIGEN", "0")).strip()

            ingreso = Ingreso(
                almacen_destino=almacen_destino,
                almacen_virtual_origen=_mapear_almacen_virtual(avo),
                concepto="DISTRIBUCION",
                medicamentos=medicamentos,
            )
            ingresos.append(ingreso)

        elif tipo == "SALIDA":
            almacen_origen = str(_obtener_safe(row, "ALMACEN_ORIGEN", "")).strip()
            almacen_destino = str(_obtener_safe(row, "ALMACEN_DESTINO", "")).strip()
            almacen_virtual_origen = f"{almacen_origen}01" if almacen_origen else ""

            salida = Salidas(
                almacen_origen=almacen_origen if almacen_origen != "NULL" else "",
                almacen_destino=almacen_destino,
                almacen_virtual_origen=almacen_virtual_origen,
                concepto="DISTRIBUCION",
                medicamentos=medicamentos,
            )
            salidas.append(salida)

    logger.info(f"SP adapter: {len(pedidos)} pedidos, {len(ingresos)} ingresos, {len(salidas)} salidas")
    return pedidos, ingresos, salidas
