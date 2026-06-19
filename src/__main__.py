from loguru import logger

from src.datos.sp_adapter import obtener_movimientos
from src.sidmed.pedido import procesar_pedidos
from src.reportes.excel_schema import crear_row_incidencia_validacion
from src.reportes.excel_writer import guardar_movimientos, obtener_siguiente_numero_procesado


def _obtener_fechas() -> tuple[str, str]:
    return "2026-06-09", "2026-06-10"


@logger.catch
def main():

    logger.info("==========================================")
    logger.info("SISMED BOT - PEDIDOS DESDE SP")
    logger.info("==========================================")

    fecha_ini, fecha_fin = _obtener_fechas()
    logger.info(f"Procesando movimientos desde {fecha_ini} hasta {fecha_fin}")

    pedidos, ingresos, salidas = obtener_movimientos(fecha_ini, fecha_fin)
    logger.info(f"SP devolvio: {len(pedidos)} pedidos, {len(ingresos)} ingresos, {len(salidas)} salidas")

    if not pedidos:
        logger.warning("No se encontraron pedidos en el rango de fechas.")
        return

    pedidos_validos = []
    filas_excel = []
    numero_procesado = obtener_siguiente_numero_procesado()

    for i, pedido in enumerate(pedidos, start=1):
        motivos = pedido.obtener_revisiones()
        if motivos:
            logger.warning(f"Pedido #{i} no pasa validacion: {motivos}")
            filas_excel.append(
                crear_row_incidencia_validacion(
                    tipo="PEDIDO",
                    error="; ".join(motivos),
                    data={"farmacia": pedido.farmacia.codigo, "cliente": pedido.cliente.codigo, "Medicamentos": pedido.Medicamentos},
                    i=numero_procesado,
                    estado="VALIDACION",
                )
            )
            numero_procesado += 1
        else:
            pedidos_validos.append(pedido)

    if filas_excel:
        try:
            guardar_movimientos(filas_excel)
            logger.success(f"Incidencias de validacion guardadas: {len(filas_excel)}")
        except Exception as e:
            logger.exception(f"Error guardando incidencias de validacion: {e}")

    if not pedidos_validos:
        logger.warning("Ningun pedido paso la validacion. No hay nada que procesar.")
        return

    logger.info(f"Pedidos validos: {len(pedidos_validos)}")
    for i, p in enumerate(pedidos_validos, start=1):
        logger.info(f"  #{i}: farmacia={p.farmacia.codigo}, forma_pago={p.forma_pago.value}, {len(p.Medicamentos)} medicamentos")

    logger.info("Iniciando procesamiento de pedidos en SISMED...")
    procesar_pedidos(tuple(pedidos_validos))
    logger.success("Todos los pedidos fueron procesados correctamente.")

    logger.info("==========================================")
    logger.success("PROCESO FINALIZADO")
    logger.info("==========================================")


if __name__ == "__main__":
    main()
