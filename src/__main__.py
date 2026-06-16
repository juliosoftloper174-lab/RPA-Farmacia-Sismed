from datetime import datetime, timedelta

from loguru import logger
from pydantic import ValidationError

from src.datos.sp_adapter import obtener_movimientos

from src.models.pedido import Pedido

from src.sidmed.ingreso import procesar_ingresos
from src.sidmed.pedido import procesar_pedidos
from src.sidmed.salidas import procesar_salidas

from src.reportes.excel_schema import (
    crear_row_ingreso,
    crear_row_pedido,
    crear_row_salida,
    crear_row_incidencia_validacion,
)
from src.reportes.excel_writer import guardar_movimientos


def _obtener_fechas() -> tuple[str, str]:
    return "2026-06-09", "2026-06-10"


@logger.catch
def main():

    logger.info("==========================================")
    logger.info("SISMED BOT - INICIO DE EJECUCIÓN")
    logger.info("==========================================")

    fecha_ini, fecha_fin = _obtener_fechas()
    logger.info(f"Consultando movimientos desde {fecha_ini} hasta {fecha_fin}")

    logger.info("Obteniendo datos desde SP_MOVIMIENTOS_SISMED_RPA...")

    pedidos_raw, ingresos_raw, salidas_raw = obtener_movimientos(fecha_ini, fecha_fin)

    pedidos: list[Pedido] = []
    ingresos = []
    salidas = []

    incidencias = []
    filas_excel = []

    # =========================================
    # VALIDAR PEDIDOS
    # =========================================

    for indice, pedido in enumerate(pedidos_raw, start=1):

        try:
            Pedido.model_validate(pedido)
        except ValidationError as e:
            incidencia_row = crear_row_incidencia_validacion(
                tipo="PEDIDO",
                error=str(e),
                data=pedido.model_dump() if hasattr(pedido, "model_dump") else {},
                i=indice,
                estado="VALIDACION",
            )
            incidencias.append(incidencia_row)
            filas_excel.append(incidencia_row)
            logger.error(f"[PEDIDO #{indice}] Error de validación estructural.")
            continue
        except Exception as e:
            incidencia_row = crear_row_incidencia_validacion(
                tipo="PEDIDO",
                error=str(e),
                i=indice,
                estado="VALIDACION",
            )
            incidencias.append(incidencia_row)
            filas_excel.append(incidencia_row)
            logger.exception(f"[PEDIDO #{indice}] Error inesperado.")
            continue

        revisiones = pedido.obtener_revisiones()
        if revisiones:
            mensaje = "; ".join(revisiones)
            incidencia_row = crear_row_incidencia_validacion(
                tipo="PEDIDO",
                error=mensaje,
                data={},
                i=indice,
                estado="REVISION",
            )
            incidencias.append(incidencia_row)
            filas_excel.append(incidencia_row)
            logger.warning(f"[PEDIDO #{indice}] En revisión: {mensaje}")
        else:
            pedidos.append(pedido)
            logger.success(f"[PEDIDO #{indice}] Validado correctamente.")

    # =========================================
    # VALIDAR INGRESOS
    # =========================================

    for indice, ingreso in enumerate(ingresos_raw, start=1):
        ingresos.append(ingreso)
        logger.success(f"[INGRESO #{indice}] Validado correctamente.")

    # =========================================
    # VALIDAR SALIDAS
    # =========================================

    for indice, salida in enumerate(salidas_raw, start=1):
        salidas.append(salida)
        logger.success(f"[SALIDA #{indice}] Validado correctamente.")

    # =========================================
    # RESUMEN
    # =========================================

    logger.info("==========================================")
    logger.info("RESUMEN DE ANÁLISIS")
    logger.info("==========================================")

    logger.info(f"Ingresos válidos encontrados: {len(ingresos)}")

    logger.info(f"Salidas válidas encontradas: {len(salidas)}")

    logger.info(f"Pedidos válidos encontrados: {len(pedidos)}")

    logger.warning(f"Incidencias encontradas: {len(incidencias)}")

    # =========================================
    # MOSTRAR INCIDENCIAS
    # =========================================

    if incidencias:

        logger.warning("==========================================")
        logger.warning("DETALLE DE INCIDENCIAS")
        logger.warning("==========================================")

        for incidencia in incidencias:
            tipo_label = incidencia.get("tipo") or incidencia.get(
                "TipoMovimiento", "DESCONOCIDO"
            )
            logger.error(f"[{tipo_label.upper()}] {incidencia.get('Error', '')}")

    # =========================================
    # COMENZAR PROCESAMIENTO
    # =========================================

    logger.info("==========================================")
    logger.info("COMENZANDO PROCESAMIENTO")
    logger.info("==========================================")

    # =========================================
    # INGRESOS
    # =========================================

    if ingresos:

        logger.info(f"Procesando {len(ingresos)} ingresos...")

        try:

            procesar_ingresos(tuple(ingresos))

            logger.success("Ingresos procesados correctamente.")

        except Exception as e:

            filas_excel.append(
                crear_row_incidencia_validacion(
                    tipo="INGRESO",
                    error=str(e),
                    data={"almacen_origen": "", "almacen_destino": ""},
                    i=None,
                    estado="PROCESAMIENTO",
                )
            )
            logger.exception(f"Error procesando ingresos: {e}")

    if salidas:

        logger.info(f"Procesando {len(salidas)} salidas...")

        try:

            procesar_salidas(tuple(salidas))

            logger.success("Salidas procesadas correctamente.")

        except Exception as e:

            filas_excel.append(
                crear_row_incidencia_validacion(
                    tipo="SALIDA",
                    error=str(e),
                    data={"almacen_origen": "", "almacen_destino": ""},
                    i=None,
                    estado="PROCESAMIENTO",
                )
            )
            logger.exception(f"Error procesando salidas: {e}")

    # =========================================
    # PEDIDOS
    # =========================================

    if pedidos:

        logger.info(f"Procesando {len(pedidos)} pedidos...")

        try:

            procesar_pedidos(tuple(pedidos))

            logger.success("Pedidos procesados correctamente.")

        except Exception as e:

            filas_excel.append(
                crear_row_incidencia_validacion(
                    tipo="PEDIDO",
                    error=str(e),
                    data={"farmacia": "", "cliente": ""},
                    i=None,
                    estado="PROCESAMIENTO",
                )
            )
            logger.exception(f"Error procesando pedidos: {e}")

    if filas_excel:

        try:

            guardar_movimientos(filas_excel)

            logger.success("Reporte Excel unificado guardado correctamente.")

        except Exception as e:

            logger.exception(f"Error guardando reporte Excel: {e}")

    else:

        logger.warning("No hubo filas de incidencia para guardar en el reporte Excel.")

    logger.info("==========================================")
    logger.success("PROCESO FINALIZADO")
    logger.info("==========================================")


if __name__ == "__main__":
    main()
