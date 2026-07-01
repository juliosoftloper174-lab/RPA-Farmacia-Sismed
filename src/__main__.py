from collections import Counter

from loguru import logger

# from src.sidmed.pedido import procesar_pedidos
from PedidosSP.pedido_SP import procesar_pedidos
from src.datos.sp_adapter import obtener_movimientos
from src.models.forma_pago import FormaPago
from src.models.pedido import generar_fua_ficticio
from src.reportes.excel_schema import crear_row_incidencia_validacion
from src.reportes.excel_writer import (
    guardar_movimientos,
    obtener_siguiente_numero_procesado,
)
from src.sidmed.ingreso import procesar_ingresos
from src.sidmed.salidas import procesar_salidas

# --- FLAGS: controlar qué flujos ejecutar ---
PROCESAR_INGRESOS = True
PROCESAR_SALIDAS = True
PROCESAR_PEDIDOS = True



def _obtener_fechas() -> tuple[str, str]:
    return "2026-06-09", "2026-06-09"


@logger.catch
def main():

    logger.info("=" * 50)
    logger.info("SISMED BOT - FLUJO COMPLETO (INGRESOS + SALIDAS + PEDIDOS)")
    logger.info("=" * 50)

    fecha_ini, fecha_fin = _obtener_fechas()
    logger.info(f"Procesando movimientos desde {fecha_ini} hasta {fecha_fin}")

    pedidos, ingresos, salidas = obtener_movimientos(fecha_ini, fecha_fin)
    logger.info(
        f"SP devolvio: {len(pedidos)} pedidos, {len(ingresos)} ingresos, {len(salidas)} salidas"
    )

    # --- INYECTAR FUA FICTICIO PARA PEDIDOS SIS SIN FUA ---
    total_sis = sum(1 for p in pedidos if p.forma_pago == FormaPago.SIS)
    sis_sin_fua = 0
    for pedido in pedidos:
        if pedido.forma_pago == FormaPago.SIS and not pedido.fua:
            pedido.fua = generar_fua_ficticio()
            sis_sin_fua += 1

    logger.info(
        f"Pedidos: {len(pedidos)} total, {total_sis} SIS "
        f"({sis_sin_fua} sin FUA → ficticios generados), "
        f"{len(pedidos) - total_sis} otras formas de pago"
    )

    # --- INGRESOS ---
    if PROCESAR_INGRESOS and ingresos:
        logger.info(f"Iniciando procesamiento de {len(ingresos)} ingresos...")
        try:
            procesar_ingresos(tuple(ingresos))
            logger.success("Ingresos procesados correctamente.")
        except Exception as e:
            logger.exception(f"Error procesando ingresos: {e}")
    elif not PROCESAR_INGRESOS:
        logger.info("INGRESOS: desactivado por configuracion.")
    else:
        logger.info("No hay ingresos para procesar.")

    # --- SALIDAS ---
    if PROCESAR_SALIDAS and salidas:
        logger.info(f"Iniciando procesamiento de {len(salidas)} salidas...")
        try:
            procesar_salidas(tuple(salidas))
            logger.success("Salidas procesadas correctamente.")
        except Exception as e:
            logger.exception(f"Error procesando salidas: {e}")
    elif not PROCESAR_SALIDAS:
        logger.info("SALIDAS: desactivado por configuracion.")
    else:
        logger.info("No hay salidas para procesar.")

    # --- PEDIDOS ---
    if not PROCESAR_PEDIDOS:
        logger.info("PEDIDOS: desactivado por configuracion.")
    elif not pedidos:
        logger.warning("No se encontraron pedidos en el rango de fechas.")
    else:
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
                        data={
                            "farmacia": pedido.farmacia.codigo,
                            "cliente": pedido.cliente.codigo,
                            "Medicamentos": pedido.Medicamentos,
                        },
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
                logger.success(
                    f"Incidencias de validacion guardadas: {len(filas_excel)}"
                )
            except Exception as e:
                logger.exception(f"Error guardando incidencias de validacion: {e}")

        if not pedidos_validos:
            logger.warning(
                "Ningun pedido paso la validacion. No hay nada que procesar."
            )
        else:
            agrupado = Counter(
                (p.farmacia.codigo, p.forma_pago.value) for p in pedidos_validos
            )
            logger.info(f"Pedidos validos: {len(pedidos_validos)}")
            for (farmacia, forma), count in sorted(agrupado.items()):
                logger.info(f"  {farmacia} - {forma}: {count}")

            logger.info("Iniciando procesamiento de pedidos en SISMED...")
            try:
                procesar_pedidos(tuple(pedidos_validos))
                logger.success("Todos los pedidos fueron procesados correctamente.")
            except Exception as e:
                logger.exception(f"Error procesando pedidos: {e}")

    logger.info("=" * 50)
    logger.success("PROCESO COMPLETO FINALIZADO")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
