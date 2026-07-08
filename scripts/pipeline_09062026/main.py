from loguru import logger

from src.flujos.ingreso import procesar_ingresos
from src.flujos.salida import procesar_salidas
from src.reportes.excel_schema import crear_row_incidencia_validacion
from src.reportes.excel_writer import guardar_movimientos

from .ingresos import generar_ingresos
from .salidas import generar_pre_distribuciones


@logger.catch
def main():

    logger.info("==========================================")
    logger.info("SISMED BOT - PRE-STOCK 09/06/2026 (x20)")
    logger.info("==========================================")
    logger.info("Propósito: stockear todas las farmacias para")
    logger.info("que las salidas del SP puedan ejecutarse 20 veces.")
    logger.info("==========================================")

    filas_excel = []

    # =========================================
    # PASO 1: INGRESO DE TODOS LOS PRODUCTOS A F01
    # =========================================

    logger.info("Paso 1/2: Ingresando todos los productos a 06732F01...")

    try:
        ingresos = generar_ingresos()
        logger.info(f"Generados {len(ingresos)} ingresos")
        procesar_ingresos(ingresos)
        logger.success("Ingresos procesados correctamente.")
    except Exception as e:
        filas_excel.append(
            crear_row_incidencia_validacion(
                tipo="INGRESO", error=str(e), data={}, i=None,
                estado="PROCESAMIENTO",
            )
        )
        logger.exception(f"Error en ingresos: {e}")
        return

    # =========================================
    # PASO 2: PRE-DISTRIBUIR STOCK A F02, F03, F04, F05
    # =========================================

    logger.info("Paso 2/2: Pre-distribuyendo stock a F02, F03, F04, F05...")

    try:
        salidas = generar_pre_distribuciones()
        logger.info(f"Generadas {len(salidas)} pre-distribuciones")
        procesar_salidas(salidas)
        logger.success("Pre-distribuciones procesadas correctamente.")
    except Exception as e:
        filas_excel.append(
            crear_row_incidencia_validacion(
                tipo="SALIDA", error=str(e), data={}, i=None,
                estado="PROCESAMIENTO",
            )
        )
        logger.exception(f"Error en pre-distribuciones: {e}")

    if filas_excel:
        try:
            guardar_movimientos(filas_excel)
            logger.success("Reporte incidencias guardado.")
        except Exception as e:
            logger.exception(f"Error guardando incidencias: {e}")

    logger.info("==========================================")
    logger.success("PROCESO FINALIZADO")
    logger.info("==========================================")


if __name__ == "__main__":
    main()
