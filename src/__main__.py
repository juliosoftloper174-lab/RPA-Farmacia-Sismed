from loguru import logger

from src.datos.sp_adapter import obtener_movimientos
from src.sidmed.salidas import procesar_salidas

from src.reportes.excel_schema import crear_row_incidencia_validacion
from src.reportes.excel_writer import guardar_movimientos

# =========================================================
# ORQUESTADOR PRINCIPAL - SALIDAS DESDE BD
# =========================================================
# Obtiene los 8 movimientos de SALIDA desde el SP y los
# procesa uno por uno en SISMED.
#
# REQUISITO: antes de ejecutar este script, asegurarse de
# que las farmacias tengan stock ejecutando:
#   1. simulacion_ingreso_test.py  (inyectar stock en F01)
#   2. simulacion_salida_test.py   (distribuir a F02-F05)
# =========================================================


def _obtener_fechas() -> tuple[str, str]:
    return "2026-06-09", "2026-06-10"


@logger.catch
def main():

    logger.info("==========================================")
    logger.info("SISMED BOT - SALIDAS DESDE SP")
    logger.info("==========================================")

    fecha_ini, fecha_fin = _obtener_fechas()
    logger.info(f"Consultando movimientos desde {fecha_ini} hasta {fecha_fin}")

    logger.info("Obteniendo datos desde SP_MOVIMIENTOS_SISMED_RPA...")

    _, _, salidas = obtener_movimientos(fecha_ini, fecha_fin)

    filas_excel = []

    if not salidas:
        logger.warning("No hay salidas para procesar.")
        return

    logger.info(f"Salidas encontradas: {len(salidas)}")
    for i, s in enumerate(salidas, start=1):
        total_qty = sum(m.cantidad for m in s.medicamentos)
        logger.info(f"  #{i}: {s.almacen_origen} -> {s.almacen_destino} ({len(s.medicamentos)} productos, {total_qty} unds)")

    # =========================================
    # PROCESAR SALIDAS
    # =========================================

    logger.info(f"Procesando {len(salidas)} salidas...")

    try:
        procesar_salidas(tuple(salidas))
        logger.success("Salidas procesadas correctamente.")
    except Exception as e:
        filas_excel.append(
            crear_row_incidencia_validacion(
                tipo="SALIDA",
                error=str(e),
                data={},
                i=None,
                estado="PROCESAMIENTO",
            )
        )
        logger.exception(f"Error procesando salidas: {e}")

    # =========================================
    # GUARDAR INCIDENCIAS
    # =========================================

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
