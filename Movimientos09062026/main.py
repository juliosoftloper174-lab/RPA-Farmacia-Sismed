from loguru import logger

from src.sidmed.ingreso import procesar_ingresos
from src.sidmed.salidas import procesar_salidas
from src.reportes.excel_schema import crear_row_incidencia_validacion
from src.reportes.excel_writer import guardar_movimientos

from ingresos import generar_ingresos
from salidas import generar_salidas


@logger.catch
def main():

    logger.info("==========================================")
    logger.info("SISMED BOT - MOVIMIENTOS 09/06/2026")
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
    # PASO 2: DISTRIBUIR DESDE F01 A LAS DEMAS
    # =========================================

    logger.info("Paso 2/2: Distribuyendo desde 06732F01 a las demas farmacias...")

    try:
        salidas = generar_salidas()
        logger.info(f"Generadas {len(salidas)} salidas")
        procesar_salidas(salidas)
        logger.success("Salidas procesadas correctamente.")
    except Exception as e:
        filas_excel.append(
            crear_row_incidencia_validacion(
                tipo="SALIDA", error=str(e), data={}, i=None,
                estado="PROCESAMIENTO",
            )
        )
        logger.exception(f"Error en salidas: {e}")

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
