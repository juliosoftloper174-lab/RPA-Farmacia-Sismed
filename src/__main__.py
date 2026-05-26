from loguru import logger
from pydantic import ValidationError

from src.datos.test_data import MOVIMIENTOS

from src.models.cliente import Cliente
from src.models.diagnostico import Diagnostico
from src.models.farmacia import Farmacia
from src.models.prescriptor import Prescriptor

from src.models.Medicamento import Medicamento
from src.models.pedido import Pedido
from src.models.ingreso import Ingreso
from src.models.Salidas import Salidas

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


@logger.catch
def main():

    logger.info("==========================================")
    logger.info("SISMED BOT - INICIO DE EJECUCIÓN")
    logger.info("==========================================")

    logger.info("Analizando y organizando data...")

    pedidos = []
    ingresos = []
    salidas = []

    incidencias = []
    filas_excel = []

    # =========================================
    # ANALIZAR DATA
    # =========================================

    for indice, movimiento in enumerate(MOVIMIENTOS, start=1):

        tipo = movimiento["tipo"]
        data = movimiento["data"]

        # =========================================
        # PEDIDOS
        # =========================================

        if tipo == "pedido":

            try:
                pedido = Pedido(
                    farmacia=Farmacia(data["farmacia"]),
                    cliente=Cliente(data["cliente"]),
                    prescriptor=Prescriptor(data["prescriptor"]),
                    forma_pago=data["forma_pago"],
                    tipo_receta=data["tipo_receta"],
                    diagnosticos=[Diagnostico(d) for d in data["diagnosticos"]],
                    Medicamentos=[
                        Medicamento(m["codigo"], m["cantidad"])
                        for m in data["Medicamentos"]
                    ],
                    fua=data.get("fua"),
                )

            except ValidationError as e:
                incidencia_row = crear_row_incidencia_validacion(
                    tipo=tipo,
                    error=str(e),
                    data=data,
                    i=indice,
                    estado="VALIDACION",
                )
                incidencias.append(incidencia_row)
                filas_excel.append(incidencia_row)
                logger.error(f"[PEDIDO #{indice}] Error de validación estructural.")
                continue

            except Exception as e:
                incidencia_row = crear_row_incidencia_validacion(
                    tipo=tipo,
                    error=str(e),
                    data=data,
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
                    tipo=tipo,
                    error=mensaje,
                    data=data,
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
        # INGRESOS
        # =========================================

        elif tipo == "ingreso":

            try:
                ingreso = Ingreso(
                    almacen_destino=data["almacen_destino"],
                    almacen_virtual_origen=data["almacen_virtual_origen"],
                    concepto=data["concepto"],
                    medicamentos=[
                        Medicamento(
                            m["codigo"],
                            m["cantidad"],
                            m["lote"],
                            m["tipo_ingreso"],
                            m["documento"],
                            m["registro_sanitario"],
                            m["fecha_vencimiento"],
                            m["precio"],
                        )
                        for m in data["medicamentos"]
                    ],
                )

                ingresos.append(ingreso)
                logger.success(f"[INGRESO #{indice}] Validado correctamente.")

            except Exception as e:
                incidencia_row = crear_row_incidencia_validacion(
                    tipo=tipo,
                    error=str(e),
                    data=data,
                    i=indice,
                    estado="VALIDACION",
                )
                incidencias.append(incidencia_row)
                filas_excel.append(incidencia_row)
                logger.exception(f"[INGRESO #{indice}] Error inesperado.")

        # =========================================
        # SALIDAS
        # =========================================

        elif tipo == "salida":

            try:
                salida = Salidas(
                    almacen_origen=data["almacen_origen"],
                    almacen_destino=data["almacen_destino"],
                    almacen_virtual_origen=data["almacen_virtual_origen"],
                    concepto=data["concepto"],
                    medicamentos=[
                        Medicamento(
                            m["codigo"],
                            m["cantidad"],
                            m["lote"],
                            m["tipo"],
                            m["subtipo"],
                        )
                        for m in data["medicamentos"]
                    ],
                )

                salidas.append(salida)
                logger.success(f"[SALIDA #{indice}] Validado correctamente.")

            except Exception as e:
                incidencia_row = crear_row_incidencia_validacion(
                    tipo=tipo,
                    error=str(e),
                    data=data,
                    i=indice,
                    estado="VALIDACION",
                )
                incidencias.append(incidencia_row)
                filas_excel.append(incidencia_row)
                logger.exception(f"[SALIDA #{indice}] Error inesperado.")

        else:

            mensaje = f"Tipo de movimiento desconocido: {tipo}"

            incidencias.append(
                crear_row_incidencia_validacion(
                    tipo=tipo,
                    error=mensaje,
                    data=data,
                )
            )

            logger.error(f"[MOVIMIENTO #{indice}] {mensaje}")

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
