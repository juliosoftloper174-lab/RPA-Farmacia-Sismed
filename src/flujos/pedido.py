"""
Flujo de pedidos en SISMED con manejo de Boleta/Ticket de Venta.

DIFERENCIAS con pedido.py (src/sidmed/):
1. Usa credenciales RPA/RPA (no admin/admin) — en producción usar estas.
2. Después de guardar, procesa la ventana que aparece:
   - CONTADO: 'BOLETA DE VENTA #...' → extrae TxtValVta → TxtImpPag → Aceptar
   - SIS / INTERVENCION_SANITARIA: 'TICKET #...' → solo Aceptar
3. Extrae el correlativo real del título de la ventana (ej. "176-0000007")
4. volver_a_menuprincipal() unificado (mismos 2 clicks para todos los casos)
5. Guarda el correlativo real en Excel (no randint)

MODO DE EJECUCIÓN:
   1. Abre terminal (VS Code: Ctrl + N, o PowerShell)
   2. Asegurate de estar en la raiz del proyecto:
      cd C:/Users/DELL/Documents/RPA-Sismed/sismed_wrapper
   3. Activa el entorno virtual (si no lo esta):
      .\\.venv\\Scripts\\activate
   4. Ejecuta:
      python -m src.flujos.pedido
   5. Espera a que SISMED se abra y procese los 3 pedidos demo.
   6. Los resultados se guardan en movimientos.xlsx.

  Para detener la ejecucion: Ctrl + C

CONFIGURACION DESDE __main__.py:
  from src.flujos.pedido import procesar_pedidos
  procesar_pedidos(tuple(pedidos))

  main(pedidos_override=tuple(pedidos))  # para usar el entry point con datos externos
"""

import re
from time import sleep

from uiautomation import (
    ButtonControl,
    Click,
    ComboBoxControl,
    ControlType,
    EditControl,
    SendKeys,
    WindowControl,
)

from database.conexion import ejecutar_sp_update_estado
from src.flujos._login import (
    esperar_hora_backup_si_aplica,
    login,
    verificar_backup_si_aplica,
)
from src.helpers.comun.input import escribir_input
from src.helpers.comun.windows import get_barrar_group, get_system_info_panel
from src.helpers.pedido.cliente import seleccionar_cliente
from src.helpers.pedido.diagnosticos import rellenar_diagnosticos
from src.helpers.pedido.farmacia import seleccionar_farmacia_por_codigo
from src.helpers.pedido.producto import agregar_productos
from src.helpers.pedido.registro_cliente import registrar_cliente_en_sismed
from src.logger import logger
from src.models import pedido
from src.models.forma_pago import FormaPago
from src.models.pedido import Pedido
from src.reportes.excel_schema import EXCEL_COLUMNS, crear_row_pedido
from src.reportes.excel_writer import (
    guardar_movimientos,
    obtener_siguiente_numero_procesado,
)

# --- USAR EN PRODUCCIÓN ---
SISMED_USERNAME = "admin"
SISMED_PASSWORD = "admin"


class ClienteNoEncontradoError(Exception):
    pass


def navegar_a_pedidos(pedido: Pedido) -> None:

    logger.debug(
        f"[NAVEGAR] Iniciando navegación para farmacia={pedido.farmacia.codigo}"
    )

    Click(355, 115)

    pane = get_system_info_panel()

    # selecte
    pane.SendKeys("{RIGHT}")

    # enter
    ventana: WindowControl = WindowControl(Name="Selección de Farmacias")
    for attempt in range(3):
        pane.SendKeys("{Enter}")
        if ventana.Exists():
            break

    if not ventana.Exists():
        raise RuntimeError(
            "No se encontró la ventana de selección de farmacias después de 3 intentos"
        )

    seleccionar_farmacia_por_codigo(pedido.farmacia.codigo)

    sleep(0.5)

    for _ in range(2):
        SendKeys("{DOWN}")

    SendKeys("{TAB}")

    SendKeys("{Enter}")

    sleep(0.5)

    logger.debug("[NAVEGAR] Navegación completada")


def rellenar_fua(pedido: Pedido) -> None:

    input_fua: EditControl = WindowControl(Name="Registro de Pedido").EditControl(
        Name="Txtfua",
    )

    escribir_input(
        input_fua,
        pedido.fua,
    )


def rellenar_ups_pedido(pedido: Pedido) -> None:

    logger.debug(f"[UPS] Rellenando UPS: {pedido.ups_codigo}")
    sleep(0.5)
    Click(735, 385)
    sleep(0.5)
    Click(1090, 345)
    sleep(0.5)
    SendKeys(pedido.ups_codigo)
    sleep(0.5)
    aceptar: ButtonControl = ButtonControl(Name="Aceptar")
    aceptar.Click()
    sleep(0.5)


def manejar_forma_pago(pedido: Pedido) -> None:

    tipo = pedido.forma_pago

    logger.debug(f"manejar_forma_pago: forma={tipo.value}")

    if tipo == FormaPago.SIS:

        logger.debug("Rellenando FUA para pago SIS")
        rellenar_fua(pedido)

    elif tipo == FormaPago.CONTADO:

        logger.debug("Pago CONTADO: no requiere campos adicionales")

    elif tipo == FormaPago.INTERVENCION_SANITARIA:

        logger.debug("Pago INTERVENCION_SANITARIA")

    else:

        raise ValueError(f"Forma de pago no soportada: {pedido.forma_pago.value}")


def selecionar_receta(pedido: Pedido) -> None:
    logger.debug(f"[RECETA] Seleccionando tipo receta: {pedido.tipo_receta.value}")
    sleep(0.5)
    Click(610, 346)
    sleep(0.5)
    if pedido.forma_pago == FormaPago.INTERVENCION_SANITARIA:
        sleep(0.5)
        Click(610, 346)
        sleep(0.5)
    Click(525, 406)
    sleep(0.5)


def _esperar_combo(
    name: str, intentos: int = 3, espera_seg: float = 5.0
) -> ComboBoxControl:
    """Espera a que el ComboBox exista.
    Reintenta `intentos` veces, esperando hasta `espera_seg` segundos por intento."""
    cbo = ComboBoxControl(Name=name)
    for intento in range(1, intentos + 1):
        if cbo.Exists(maxSearchSeconds=espera_seg, searchIntervalSeconds=0.5):
            return cbo
        print(f"CBO '{name}' no encontrado (intento {intento}/{intentos}).")
    raise RuntimeError(
        f"No se encontró el ComboBox '{name}' tras {intentos} intentos "
        f"de {espera_seg}s cada uno."
    )


FORMA_PAGO_MAP = {
    FormaPago.CONTADO: "CONTADO",
    FormaPago.INTERVENCION_SANITARIA: "INTERVENCION SANITAR",
    FormaPago.SIS: "SIS",
}


def selecionar_forma_pago(pedido: Pedido) -> None:
    cbo = _esperar_combo("CboDato")

    cbo.Click()
    sleep(1)

    if pedido.forma_pago == FormaPago.CONTADO:
        cbo.Click()
        sleep(1)
    elif pedido.forma_pago == FormaPago.INTERVENCION_SANITARIA:
        Click(537, 427)
        sleep(1)
    elif pedido.forma_pago == FormaPago.SIS:
        Click(615, 410)
        sleep(1)
        Click(495, 385)
    else:
        raise ValueError(f"Forma de pago no soportada: {pedido.forma_pago}")



def _cerrar_aviso_si_existe() -> None:
    try:
        aviso = WindowControl(Name="Aviso.")
        if aviso.Exists(maxSearchSeconds=0.5):
            boton = aviso.ButtonControl(Name="Aceptar")
            if boton.Exists(maxSearchSeconds=0.5):
                boton.Click()
                sleep(0.5)
    except Exception:
        pass


def rellenar_cabecera(
    pedido: Pedido,
) -> None:

    sleep(1.5)
    logger.debug("[CABECERA] Seleccionando forma de pago")

    selecionar_forma_pago(pedido)

    manejar_forma_pago(pedido)

    selecionar_receta(pedido)

    logger.debug(f"[CABECERA] Seleccionando cliente: {pedido.cliente.codigo}")
    if not seleccionar_cliente(pedido.cliente.codigo):
        _cerrar_aviso_si_existe()
        if pedido.cliente.nombre:
            logger.info(
                f"[CABECERA] Cliente no encontrado, registrando: "
                f"{pedido.cliente.nombre} (DNI {pedido.cliente.codigo})"
            )
            registrar_cliente_en_sismed(pedido.cliente)
            logger.info(
                f"[CABECERA] Cliente registrado, continuando flujo"
            )
        else:
            volver_a_menuprincipal()
            raise ClienteNoEncontradoError(
                f"Cliente {pedido.cliente.codigo} no encontrado en SISMED"
            )

    logger.debug(f"[CABECERA] Rellenando UPS: {pedido.ups_codigo}")
    rellenar_ups_pedido(pedido)

    if pedido.prescriptor is not None:
        presc: EditControl = WindowControl(Name="Registro de Pedido").EditControl(
            Name="TxtColPresc"
        )

        logger.debug(f"[CABECERA] Escribiendo prescriptor: {pedido.prescriptor.codigo}")
        escribir_input(
            presc,
            pedido.prescriptor.codigo,
        )

        presc.SendKeys("{Enter}")

        if pedido.diagnosticos:
            logger.debug(
                f"[CABECERA] Rellenando diagnosticos: {[d.codigo for d in pedido.diagnosticos]}"
            )
            rellenar_diagnosticos(
                WindowControl(Name="Registro de Pedido"),
                [d.codigo for d in pedido.diagnosticos],
            )
    else:
        logger.debug("[CABECERA] Sin prescriptor — saltando prescriptor y diagnosticos")


def guardar() -> None:

    cmd_save: ButtonControl = get_barrar_group().ButtonControl(
        searchDepth=1,
        Name="CmdSave",
    )

    cmd_save.Click()

    sleep(0.3)


def selecionar_receta_verificacion() -> None:
    logger.debug("[RECETA_VERIF] Seleccionando tipo receta (2 clicks)")
    sleep(0.5)
    Click(610, 345)
    sleep(0.5)
    Click(525, 408)
    sleep(0.5)


def verificar_receta() -> bool:
    sleep(1.5)
    for name in ("Aviso", "Microsoft Visual FoxPro"):
        w = WindowControl(Name=name)
        if w.Exists(maxSearchSeconds=1):
            logger.warning(f"Error de receta detectado: '{name}'. Corrigiendo...")
            w.ButtonControl(Name="Aceptar").Click()
            sleep(1)
            selecionar_receta_verificacion()
            guardar()
            return True
    return False


def extraer_correlativo_farmacia(forma_pago: FormaPago) -> str:
    """
    Extrae el número de la ventana que aparece después de guardar.
    - CONTADO: 'BOLETA DE VENTA #176-0000007' → '176-0000007'
    - SIS / INTERVENCION_SANITARIA: 'TICKET #003-0000008' → '003-0000008'
    """
    if forma_pago == FormaPago.CONTADO:
        ventana = WindowControl(RegexName=r"^BOLETA DE VENTA #")
        if not ventana.Exists(maxSearchSeconds=5):
            raise RuntimeError(
                "No se encontró la ventana BOLETA DE VENTA después de guardar"
            )
    else:
        ventana = WindowControl(RegexName=r"^TICKET #")
        if not ventana.Exists(maxSearchSeconds=5):
            raise RuntimeError("No se encontró la ventana TICKET después de guardar")

    match = re.search(r"#(.+)", ventana.Name)
    if not match:
        raise RuntimeError(f"No se pudo extraer correlativo del título: {ventana.Name}")

    correlativo = match.group(1).strip()
    tipo = "BOLETA" if forma_pago == FormaPago.CONTADO else "TICKET"
    logger.debug(f"[{tipo}] Correlativo extraído: {correlativo}")
    return correlativo


def procesar_boleta_venta(forma_pago: FormaPago) -> None:
    """
    Maneja la ventana que aparece después de guardar un pedido.
    - CONTADO: ventana 'BOLETA DE VENTA #...', extrae TxtValVta → TxtImpPag → Aceptar
    - SIS / INTERVENCION_SANITARIA: ventana 'TICKET #...', solo Aceptar
    """
    sleep(3)
    if forma_pago == FormaPago.CONTADO:
        ventana = WindowControl(RegexName=r"^BOLETA DE VENTA #")
        logger.debug("[BOLETA] Procesando pago CONTADO")

        # Extraer valor de TxtValVta
        txt_val_vta = ventana.EditControl(Name="TxtValVta")
        valor = txt_val_vta.GetValuePattern().Value
        logger.debug(f"[BOLETA] Valor TxtValVta: {valor}")

        # Si el valor es 0, usar 0.01 en vez de 0
        if valor.strip() == "0":
            valor = "0.01"
            logger.debug(f"[BOLETA] Valor 0 convertido a 0.01")

        # Ingresar valor en TxtImpPag
        txt_imp_pag = ventana.EditControl(Name="TxtImpPag")
        txt_imp_pag.Click()
        sleep(0.5)
        txt_imp_pag.SendKeys(valor)
        sleep(0.5)
    else:
        ventana = WindowControl(RegexName=r"^TICKET #")
        logger.debug("[TICKET] Procesando SIS / INTERVENCION_SANITARIA")

    # Para TODOS los casos: click Aceptar
    logger.debug(f"Haciendo click en Aceptar")
    ventana.ButtonControl(Name="Aceptar").Click()
    sleep(3)


def volver_a_menuprincipal() -> None:
    """
    Vuelve al menú principal después de procesar un pedido.
    - Click(1189, 214): Cierra ventana de registro de pedido
    - Click(1585, 15): Cierra ventana de farmacia Minsa sismed
    (La ventana de registro de consumo ya se cerró al aceptar la boleta)
    """
    # Cerrar ventana de registro de pedido
    Click(1189, 214)
    sleep(1.5)

    # Cerrar ventana de farmacia Minsa sismed
    Click(1585, 15)
    sleep(1.5)


def cerrar_sismed_pedido() -> None:

    # Click 1
    Click(1168, 188)
    sleep(3)

    # Click 2
    Click(1189, 214)
    sleep(3)

    # Click 3
    Click(1585, 15)
    sleep(3)

    # Click 4
    Click(1585, 15)
    sleep(3)


def procesar_pedido(
    pedido: Pedido,
) -> str:

    logger.debug(
        f"[PROCESAR] Iniciando pedido: farmacia={pedido.farmacia.codigo}, forma_pago={pedido.forma_pago.value}, medicamentos={len(pedido.Medicamentos)}"
    )

    navegar_a_pedidos(pedido)

    logger.debug("[PROCESAR] Navegacion OK, rellenando cabecera")
    rellenar_cabecera(pedido)

    logger.debug(
        f"[PROCESAR] Cabecera OK, agregando {len(pedido.Medicamentos)} productos"
    )
    sleep(0.2)
    SendKeys("{CONTROL}{DEL}")
    sleep(0.2)
    SendKeys("{CONTROL}{DEL}")
    sleep(0.2)
    agregar_productos(tuple(pedido.Medicamentos))

    logger.debug("[PROCESAR] Productos OK, guardando")
    guardar()
    verificar_receta()

    # Extraer correlativo real de la ventana (Boleta o Ticket según forma de pago)
    correlativo = extraer_correlativo_farmacia(pedido.forma_pago)
    logger.debug(f"[PROCESAR] Guardado OK, correlativo={correlativo}")

    # Procesar Boleta/Ticket (Aceptar, y si CONTADO: llenar pago)
    procesar_boleta_venta(pedido.forma_pago)

    # Volver al menú principal (unificado para todos los casos)
    volver_a_menuprincipal()

    logger.debug(f"[PROCESAR] Pedido completado: correlativo={correlativo}")
    return correlativo


MAX_REINTENTOS_PEDIDO = 2


def cerrar_ventanas_sismed() -> None:
    sleep(2)
    Click(1585, 15)
    sleep(3)
    Click(1585, 15)
    sleep(3)


def procesar_pedidos(pedidos: tuple[Pedido, ...]) -> dict:

    login(
        SISMED_USERNAME,
        SISMED_PASSWORD,
    )

    numero_procesado = obtener_siguiente_numero_procesado()
    total = len(pedidos)
    ok_count = 0
    error_count = 0
    sin_cliente_count = 0

    for idx, pedido in enumerate(pedidos, start=1):

        verificar_backup_si_aplica()
        esperar_hora_backup_si_aplica()

        reintentos = 0

        while reintentos < MAX_REINTENTOS_PEDIDO:

            try:

                correlativo = procesar_pedido(pedido)

                if pedido.update_key:
                    logger.debug(
                        f"[LOTE] Pedido {idx}/{total} OK, actualizando estado en BD (00)..."
                    )
                    try:
                        ejecutar_sp_update_estado(pedido.update_key, "00")
                    except Exception as e:
                        logger.warning(
                            f"[LOTE] No se pudo actualizar estado en BD "
                            f"para pedido {idx}/{total}: {str(e)[:120]}"
                        )

                row = crear_row_pedido(
                    i=numero_procesado,
                    username=SISMED_USERNAME,
                    correlativo_ksalud=pedido.correlativo_ksalud,
                    correlativo_sismed=correlativo,
                    pedido=pedido,
                    estado="OK_REPROCESADO" if reintentos > 0 else "OK",
                )

                guardar_movimientos(row)

                msg = f"[LOTE] Pedido {idx}/{total} OK: correlativo={correlativo}"
                if reintentos > 0:
                    msg += f" (tras {reintentos} reintento(s))"
                logger.success(msg)
                ok_count += 1

                break

            except ClienteNoEncontradoError as exc:
                motivo = str(exc).split("\n")[0][:120]
                logger.error(
                    f"[LOTE] Pedido {idx}/{total} cliente no encontrado: {motivo}"
                )
                sin_cliente_count += 1
                if pedido.update_key:
                    try:
                        ejecutar_sp_update_estado(pedido.update_key, "02")
                    except Exception as update_err:
                        logger.warning(
                            f"[LOTE] No se pudo actualizar estado BD: {update_err}"
                        )
                row = crear_row_pedido(
                    i=numero_procesado,
                    username=SISMED_USERNAME,
                    correlativo_ksalud=pedido.correlativo_ksalud,
                    correlativo_sismed="",
                    pedido=pedido,
                    estado="CLIENTE_NO_ENCONTRADO",
                    error=motivo,
                )
                guardar_movimientos(row)
                break

            except Exception as exc:

                reintentos += 1
                motivo = str(exc).split("\n")[0][:120]

                if reintentos >= MAX_REINTENTOS_PEDIDO:

                    logger.error(
                        f"[LOTE] Pedido {idx}/{total} falló definitivamente "
                        f"tras {reintentos} reintentos: {motivo}"
                    )
                    error_count += 1

                    if pedido.update_key:
                        try:
                            ejecutar_sp_update_estado(pedido.update_key, "01")
                        except Exception as update_err:
                            logger.warning(
                                f"[LOTE] No se pudo actualizar estado BD: {update_err}"
                            )

                    row = crear_row_pedido(
                        i=numero_procesado,
                        username=SISMED_USERNAME,
                        correlativo_ksalud=pedido.correlativo_ksalud,
                        correlativo_sismed="",
                        pedido=pedido,
                        estado="ERROR",
                        error=f"Se agotaron {MAX_REINTENTOS_PEDIDO} reintentos: {motivo}",
                    )

                    guardar_movimientos(row)
                    continue

                logger.warning(
                    f"[LOTE] Pedido {idx}/{total} falló "
                    f"(intento {reintentos}/{MAX_REINTENTOS_PEDIDO}), reintentando..."
                )

                row_retry = crear_row_pedido(
                    i=numero_procesado,
                    username=SISMED_USERNAME,
                    correlativo_ksalud=pedido.correlativo_ksalud,
                    correlativo_sismed="",
                    pedido=pedido,
                    estado="RETRY",
                    error=f"Fallo intento {reintentos}/{MAX_REINTENTOS_PEDIDO}: {motivo}",
                )

                guardar_movimientos(row_retry)

                try:
                    cerrar_ventanas_sismed()
                    login(SISMED_USERNAME, SISMED_PASSWORD)
                except Exception as cleanup_err:
                    logger.error(
                        f"[LOTE] INTERRUMPIDO: Error durante limpieza "
                        f"({cleanup_err}). Verifique SISMED "
                        f"(cierre ventanas de backup/manuales) "
                        f"y presione Enter para continuar..."
                    )
                    input()
                    login(SISMED_USERNAME, SISMED_PASSWORD)

        numero_procesado += 1

    logger.debug("[LOTE] Procesamiento de lote completado, cerrando SISMED")
    cerrar_sismed_pedido()

    return {
        "total": total,
        "ok": ok_count,
        "error": error_count,
        "sin_cliente": sin_cliente_count,
    }


def main(pedidos_override: tuple = None):
    if pedidos_override is not None:
        pedidos = pedidos_override
    else:
        from src import config
        from src.datos.sp_adapter import obtener_movimientos

        fecha_ini, fecha_fin = "2026-06-09", "2026-06-10"
        logger.info(f"Obteniendo pedidos desde SP ({fecha_ini} a {fecha_fin})...")
        pedidos, _, _, _ = obtener_movimientos(
            fecha_ini, fecha_fin, skip_errores=not config.procesar_errores
        )
    logger.info(f"SP devolvio: {len(pedidos)} pedidos")
    for i, p in enumerate(pedidos, start=1):
        logger.info(
            f"  #{i}: farmacia={p.farmacia.codigo}, forma_pago={p.forma_pago.value}"
        )
    procesar_pedidos(tuple(pedidos))


if __name__ == "__main__":
    main()
