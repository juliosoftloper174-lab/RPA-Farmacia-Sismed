import signal
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from time import sleep

from loguru import logger

from src.flujos.pedido import procesar_pedidos
from src import config
from src.datos.sp_adapter import obtener_movimientos
from src.models.forma_pago import FormaPago
from src.models.pedido import generar_fua_ficticio
from src.notifications.email_sender import (
    construir_cuerpo_error,
    construir_cuerpo_reinicio,
    construir_cuerpo_resumen_diario,
    enviar_correo,
    enviar_correo_con_adjunto,
)
from src.reportes.excel_schema import crear_row_incidencia_validacion
from src.reportes.excel_writer import (
    _path_del_dia,
    guardar_movimientos,
    leer_resumen_diario,
    obtener_siguiente_numero_procesado,
)
from src.flujos.ingreso import procesar_ingresos
from src.flujos.salida import procesar_salidas

RUNNING_FILE = Path(__file__).resolve().parent.parent / ".running"


def _obtener_fechas() -> tuple[str, str]:
    fecha_ini = config.FECHA_INI or datetime.now().strftime("%Y-%m-%d")
    fecha_fin = config.FECHA_FIN or datetime.now().strftime("%Y-%m-%d")
    return fecha_ini, fecha_fin


def _verificar_centinela():
    if RUNNING_FILE.exists():
        logger.warning(
            "Centinela .running detectado — ejecucion anterior se interrumpio!"
        )
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


def _signal_handler(sig, frame):
    logger.warning("Ctrl+C detectado. Limpiando .running y saliendo...")
    _limpiar_centinela()
    sys.exit(0)


def _procesar_ingreso(ingresos, fecha=None, fecha_fin=None, modo="horario"):
    if not config.procesar_ingresos or not ingresos:
        logger.info("INGRESOS: desactivado o sin datos.")
        return None
    logger.info(f"Iniciando procesamiento de {len(ingresos)} ingresos...")
    try:
        stats_ing = procesar_ingresos(tuple(ingresos), fecha=fecha, fecha_fin=fecha_fin, modo=modo)
        logger.success("Ingresos procesados correctamente.")
        return stats_ing
    except Exception as e:
        logger.exception(f"Error procesando ingresos: {e}")
        return {"total": len(ingresos), "ok": 0, "error": len(ingresos)}


def _procesar_salida(salidas, fecha=None, fecha_fin=None, modo="horario"):
    if not config.procesar_salidas or not salidas:
        logger.info("SALIDAS: desactivado o sin datos.")
        return None
    logger.info(f"Iniciando procesamiento de {len(salidas)} salidas...")
    try:
        stats_sal = procesar_salidas(tuple(salidas), fecha=fecha, fecha_fin=fecha_fin, modo=modo)
        logger.success("Salidas procesadas correctamente.")
        return stats_sal
    except Exception as e:
        logger.exception(f"Error procesando salidas: {e}")
        return {"total": len(salidas), "ok": 0, "error": len(salidas)}


def _procesar_pedido(pedidos, fecha=None, fecha_fin=None, modo="horario"):
    if not config.procesar_pedidos:
        logger.info("PEDIDOS: desactivado por configuracion.")
        return None
    if not pedidos:
        logger.warning("No se encontraron pedidos.")
        return None

    pedidos_validos = []
    filas_excel = []
    numero_procesado = obtener_siguiente_numero_procesado(fecha, fecha_fin, modo)

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
            guardar_movimientos(filas_excel, fecha=fecha, fecha_fin=fecha_fin, modo=modo)
        except Exception as e:
            logger.exception(f"Error guardando incidencias de validacion: {e}")

    if not pedidos_validos:
        logger.warning("Ningun pedido paso la validacion.")
        return None

    agrupado = Counter((p.farmacia.codigo, p.forma_pago.value) for p in pedidos_validos)
    logger.info(f"Pedidos validos: {len(pedidos_validos)}")
    for (farmacia, forma), count in sorted(agrupado.items()):
        logger.info(f"  {farmacia} - {forma}: {count}")

    logger.info("Iniciando procesamiento de pedidos en SISMED...")
    try:
        stats_ped = procesar_pedidos(tuple(pedidos_validos), fecha=fecha, fecha_fin=fecha_fin, modo=modo)
        logger.success("Todos los pedidos fueron procesados correctamente.")
        return stats_ped
    except Exception as e:
        logger.exception(f"Error procesando pedidos: {e}")
        return {
            "total": len(pedidos_validos),
            "ok": 0,
            "error": len(pedidos_validos),
            "sin_cliente": 0,
        }


def _ejecutar_ciclo_unico(fecha_hoy: str) -> dict | None:
    pedidos, ingresos, salidas, saltados_otros = obtener_movimientos(
        fecha_hoy, fecha_hoy, skip_errores=not config.procesar_errores
    )

    total = len(pedidos) + len(ingresos) + len(salidas)
    if total == 0:
        return None

    logger.info(
        f"SP devolvio: {len(pedidos)} pedidos, {len(ingresos)} ingresos, "
        f"{len(salidas)} salidas"
    )

    for pedido in pedidos:
        if pedido.forma_pago == FormaPago.SIS and not pedido.fua:
            pedido.fua = generar_fua_ficticio()

    return {
        "ingresos": _procesar_ingreso(ingresos),
        "salidas": _procesar_salida(salidas),
        "pedidos": _procesar_pedido(pedidos),
    }


def _ejecutar_batch():
    signal.signal(signal.SIGINT, _signal_handler)

    fecha_ini = config.FECHA_INI
    fecha_fin = config.FECHA_FIN
    if not fecha_ini or not fecha_fin:
        logger.error("MODO=batch requiere FECHA_INI y FECHA_FIN en .env")
        return

    logger.info("=" * 50)
    logger.info("SISMED BOT - MODO BATCH")
    logger.info(f"Procesando {fecha_ini} → {fecha_fin}")
    logger.info(
        f"Flags: ING={config.procesar_ingresos} SAL={config.procesar_salidas} "
        f"PED={config.procesar_pedidos} ERR={config.procesar_errores}"
    )
    logger.info("=" * 50)

    pedidos, ingresos, salidas, saltados_otros = obtener_movimientos(
        fecha_ini, fecha_fin, skip_errores=not config.procesar_errores
    )
    total = len(pedidos) + len(ingresos) + len(salidas)
    if total == 0:
        logger.warning("No se encontraron movimientos en el rango.")
        return

    logger.info(
        f"SP devolvio: {len(pedidos)} pedidos, {len(ingresos)} ingresos, "
        f"{len(salidas)} salidas"
    )

    for pedido in pedidos:
        if pedido.forma_pago == FormaPago.SIS and not pedido.fua:
            pedido.fua = generar_fua_ficticio()

    try:
        _procesar_ingreso(ingresos, fecha_ini, fecha_fin, modo="batch")
        _procesar_salida(salidas, fecha_ini, fecha_fin, modo="batch")
        _procesar_pedido(pedidos, fecha_ini, fecha_fin, modo="batch")
        logger.success("Batch completado.")

        if config.NOTIFICAR_CORREO:
            resumen = leer_resumen_diario(fecha_ini, fecha_fin, modo="batch")
            excel_path = _path_del_dia(fecha_ini, fecha_fin, modo="batch")
            enviar_correo_con_adjunto(
                f"📊 Bot N°{config.BOT_NUMBER} - Resumen batch {fecha_ini} → {fecha_fin}",
                construir_cuerpo_resumen_diario(resumen, fecha_ini),
                excel_path,
            )
    except Exception as e:
        logger.exception(f"ERROR EN BATCH: {e}")
        enviar_correo(
            f"❌ Bot N°{config.BOT_NUMBER} - ERROR EN BATCH",
            construir_cuerpo_error(str(e)),
        )


def main():
    _verificar_centinela()
    signal.signal(signal.SIGINT, _signal_handler)

    cierre_enviado_hoy = False
    fecha_actual = ""

    logger.info("=" * 50)
    logger.info("SISMED BOT - MODO CONTINUO 24/7")
    logger.info(f"HORA_CIERRE = {config.HORA_CIERRE}")
    logger.info(
        f"Flags: ING={config.procesar_ingresos} SAL={config.procesar_salidas} "
        f"PED={config.procesar_pedidos} ERR={config.procesar_errores}"
    )
    logger.info("=" * 50)

    while True:
        ahora = datetime.now()
        fecha_hoy = ahora.strftime("%Y-%m-%d")

        if fecha_actual and fecha_actual != fecha_hoy:
            cierre_enviado_hoy = False
            logger.info(f"=== NUEVO DIA: {fecha_hoy} ===")
        fecha_actual = fecha_hoy

        try:
            resultado = _ejecutar_ciclo_unico(fecha_hoy)
            if resultado is None:
                for i in range(60, 0, -1):
                    print(f"  Sin datos — próximo ciclo en {i:2d}s...  ", end='\r')
                    sleep(1)
                print(" " * 50, end='\r')
                continue
            logger.success("Movimientos procesados correctamente.")
        except Exception as e:
            logger.exception(f"ERROR EN CICLO: {e}")
            enviar_correo(
                f"❌ Bot N°{config.BOT_NUMBER} - ERROR EN CICLO",
                construir_cuerpo_error(str(e)),
            )

        hora_cierre = datetime.strptime(config.HORA_CIERRE, "%H:%M").time()
        if ahora.time() >= hora_cierre and not cierre_enviado_hoy:
            cierre_enviado_hoy = True
            logger.info("Hora de cierre alcanzada. Enviando resumen diario...")
            try:
                resumen = leer_resumen_diario(fecha_hoy)
                excel_path = _path_del_dia(fecha_hoy)
                enviar_correo_con_adjunto(
                    f"📅 Bot N°{config.BOT_NUMBER} - Resumen diario {fecha_hoy}",
                    construir_cuerpo_resumen_diario(resumen, fecha_hoy),
                    excel_path,
                )
                logger.success("Resumen diario enviado.")
                print("\n" + "=" * 50)
                print(f"  RESUMEN DIARIO - {fecha_hoy}")
                ok = resumen.get("ok", 0)
                error = resumen.get("error", 0)
                saltados = resumen.get("saltados", 0)
                print(f"  OK: {ok} | Error: {error} | Saltados: {saltados}")
                print("=" * 50)
            except Exception as e:
                logger.exception(f"Error al enviar resumen diario: {e}")

        sleep(60)


if __name__ == "__main__":
    if config.MODO == "batch":
        _ejecutar_batch()
    else:
        main()
