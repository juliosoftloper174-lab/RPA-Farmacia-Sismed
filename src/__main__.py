from collections import Counter
from datetime import datetime
from pathlib import Path

from loguru import logger

# from src.sidmed.pedido import procesar_pedidos
from PedidosSP.pedido_SP import procesar_pedidos
from src import config
from src.datos.sp_adapter import obtener_movimientos
from src.models.forma_pago import FormaPago
from src.models.pedido import generar_fua_ficticio
from src.notifications.email_sender import (
    construir_cuerpo_error,
    construir_cuerpo_inicio,
    construir_cuerpo_reinicio,
    construir_cuerpo_resumen,
    enviar_correo,
)
from src.reportes.excel_schema import crear_row_incidencia_validacion
from src.reportes.excel_writer import (
    guardar_movimientos,
    obtener_siguiente_numero_procesado,
)
from src.sidmed.ingreso import procesar_ingresos
from src.sidmed.salidas import procesar_salidas

RUNNING_FILE = Path(__file__).resolve().parent.parent / ".running"


def _obtener_fechas() -> tuple[str, str]:
    fecha_ini = config.FECHA_INI or "2026-06-09"
    fecha_fin = config.FECHA_FIN or "2026-06-09"
    return fecha_ini, fecha_fin


def _verificar_centinela():
    if RUNNING_FILE.exists():
        logger.warning("Centinela .running detectado — ejecucion anterior se interrumpio!")
        enviar_correo(
            f"🔄 Bot N°{config.BOT_NUMBER} - REINICIADO TRAS CAIDA",
            construir_cuerpo_reinicio(),
        )

    RUNNING_FILE.write_text(datetime.now().isoformat(), encoding="utf-8")
    logger.info(f"Centinela .running creado en {RUNNING_FILE}")


def _limpiar_centinela():
    try:
        if RUNNING_FILE.exists():
            RUNNING_FILE.unlink()
            logger.info("Centinela .running eliminado.")
    except Exception as e:
        logger.warning(f"No se pudo eliminar .running: {e}")


@logger.catch
def main():

    hora_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    _verificar_centinela()

    logger.info("=" * 50)
    logger.info("SISMED BOT - FLUJO COMPLETO (INGRESOS + SALIDAS + PEDIDOS)")
    logger.info("=" * 50)
    logger.info(f"Flags: ING={config.procesar_ingresos} SAL={config.procesar_salidas} PED={config.procesar_pedidos} ERR={config.procesar_errores}")

    fecha_ini, fecha_fin = _obtener_fechas()
    logger.info(f"Procesando movimientos desde {fecha_ini} hasta {fecha_fin}")

    pedidos, ingresos, salidas, saltados_otros = obtener_movimientos(
        fecha_ini, fecha_fin, skip_errores=not config.procesar_errores
    )
    logger.info(
        f"SP devolvio: {len(pedidos)} pedidos, {len(ingresos)} ingresos, {len(salidas)} salidas"
    )

    datos_sp = {"ingresos": len(ingresos), "salidas": len(salidas), "pedidos": len(pedidos)}
    enviar_correo(
        f"🟢 Bot N°{config.BOT_NUMBER} - INICIADO",
        construir_cuerpo_inicio(datos_sp, fecha_ini, fecha_fin, saltados_otros),
    )

    stats = {
        "hora_inicio": hora_inicio,
        "hora_fin": "",
        "ingresos": None,
        "salidas": None,
        "pedidos": None,
        "pendientes_otros": saltados_otros,
    }

    try:

        # --- INYECTAR FUA FICTICIO PARA PEDIDOS SIS SIN FUA ---
        total_sis = sum(1 for p in pedidos if p.forma_pago == FormaPago.SIS)
        sis_sin_fua = 0
        for pedido in pedidos:
            if pedido.forma_pago == FormaPago.SIS and not pedido.fua:
                pedido.fua = generar_fua_ficticio()
                sis_sin_fua += 1

        logger.info(
            f"Pedidos: {len(pedidos)} total, {total_sis} SIS "
            f"({sis_sin_fua} sin FUA -> ficticios generados), "
            f"{len(pedidos) - total_sis} otras formas de pago"
        )

        # --- INGRESOS ---
        if config.procesar_ingresos and ingresos:
            logger.info(f"Iniciando procesamiento de {len(ingresos)} ingresos...")
            try:
                stats_ing = procesar_ingresos(tuple(ingresos))
                stats["ingresos"] = stats_ing
                logger.success("Ingresos procesados correctamente.")
            except Exception as e:
                logger.exception(f"Error procesando ingresos: {e}")
                stats["ingresos"] = {"total": len(ingresos), "ok": 0, "error": len(ingresos)}
        elif not config.procesar_ingresos:
            logger.info("INGRESOS: desactivado por configuracion.")
        else:
            logger.info("No hay ingresos para procesar.")

        # --- SALIDAS ---
        if config.procesar_salidas and salidas:
            logger.info(f"Iniciando procesamiento de {len(salidas)} salidas...")
            try:
                stats_sal = procesar_salidas(tuple(salidas))
                stats["salidas"] = stats_sal
                logger.success("Salidas procesadas correctamente.")
            except Exception as e:
                logger.exception(f"Error procesando salidas: {e}")
                stats["salidas"] = {"total": len(salidas), "ok": 0, "error": len(salidas)}
        elif not config.procesar_salidas:
            logger.info("SALIDAS: desactivado por configuracion.")
        else:
            logger.info("No hay salidas para procesar.")

        # --- PEDIDOS ---
        if not config.procesar_pedidos:
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
                    stats_ped = procesar_pedidos(tuple(pedidos_validos))
                    stats["pedidos"] = stats_ped
                    logger.success("Todos los pedidos fueron procesados correctamente.")
                except Exception as e:
                    logger.exception(f"Error procesando pedidos: {e}")
                    stats["pedidos"] = {
                        "total": len(pedidos_validos),
                        "ok": 0,
                        "error": len(pedidos_validos),
                        "sin_cliente": 0,
                    }

        logger.info("=" * 50)
        logger.success("PROCESO COMPLETO FINALIZADO")
        logger.info("=" * 50)

    except Exception as global_err:
        logger.exception(f"ERROR CRITICO GLOBAL: {global_err}")
        enviar_correo(
            f"❌ Bot N°{config.BOT_NUMBER} - ERROR CRITICO",
            construir_cuerpo_error(str(global_err)),
        )
        _limpiar_centinela()
        return

    stats["hora_fin"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    enviar_correo(
        f"✅ Bot N°{config.BOT_NUMBER} - PROCESO FINALIZADO",
        construir_cuerpo_resumen(stats, fecha_ini, fecha_fin),
    )
    _limpiar_centinela()


if __name__ == "__main__":
    main()
