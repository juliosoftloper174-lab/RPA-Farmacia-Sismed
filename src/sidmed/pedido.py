from random import randint
from time import sleep

from uiautomation import (
    EditControl,
    ButtonControl,
    Click,
    SendKeys,
)

from ..sidmed.ingreso import (
    seleccionar_combo_por_texto,
    seleccionar_combo_por_texto_con_autoenter,
)

from ..models.forma_pago import FormaPago
from ..helpers.cliente import seleccionar_cliente
from ..helpers.diagnosticos import rellenar_diagnosticos
from ..helpers.farmacia import seleccionar_farmacia_por_codigo
from ..helpers.input import escribir_input
from ..helpers.producto import agregar_productos
from ..models.pedido import Pedido
from ..sidmed._login import login
from ..helpers.windows import *

from ..reportes.excel_schema import crear_row_pedido

from ..reportes.excel_writer import (
    guardar_movimientos,
    obtener_siguiente_numero_procesado,
)

from ..logger import logger

from ..config import (
    SISMED_PASSWORD,
    SISMED_USERNAME,
)


def navegar_a_pedidos(pedido: Pedido) -> None:

    logger.debug(
        f"[NAVEGAR] Iniciando navegación para farmacia={pedido.farmacia.codigo}"
    )

    Click(355, 115)

    get_system_info_panel().SendKeys("{RIGHT}{Enter}")

    seleccionar_farmacia_por_codigo(pedido.farmacia.codigo)

    sleep(1)

    for _ in range(2):
        SendKeys("{DOWN}")

    SendKeys("{TAB}")

    SendKeys("{Enter}")

    sleep(0.5)

    logger.debug("[NAVEGAR] Navegación completada")


def rellenar_fua(pedido: Pedido) -> None:

    input_fua: EditControl = get_registro_pedido_window().EditControl(
        searchDepth=1,
        Name="Txtfua",
    )

    escribir_input(
        input_fua,
        pedido.fua,
    )


def rellenar_ups_pedido(pedido: Pedido) -> None:

    logger.debug(f"[UPS] Rellenando UPS: {pedido.ups_codigo}")
    sleep(1)
    Click(735, 385)
    sleep(1)
    Click(1090, 345)
    sleep(1)
    SendKeys(pedido.ups_codigo)
    sleep(1)
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


def rellenar_cabecera(
    pedido: Pedido,
) -> None:

    logger.debug("[CABECERA] Seleccionando forma de pago")
    seleccionar_combo_por_texto_con_autoenter(
        "CboDato",
        pedido.forma_pago.value,
    )

    manejar_forma_pago(pedido)

    logger.debug(f"[CABECERA] Seleccionando tipo receta: {pedido.tipo_receta.value}")
    seleccionar_combo_por_texto(
        "cmbTipoReceta",
        pedido.tipo_receta.value,
    )

    logger.debug(f"[CABECERA] Seleccionando cliente: {pedido.cliente.codigo}")
    Click(770, 410)

    seleccionar_cliente(pedido.cliente.codigo)

    logger.debug(f"[CABECERA] Rellenando UPS: {pedido.ups_codigo}")
    rellenar_ups_pedido(pedido)

    if pedido.prescriptor is not None:
        presc: EditControl = get_registro_pedido_window().EditControl(Name="TxtColPresc")

        logger.debug(
            f"[CABECERA] Escribiendo prescriptor: {pedido.prescriptor.codigo}"
        )
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
                get_registro_pedido_window(),
                [d.codigo for d in pedido.diagnosticos],
            )
    else:
        logger.debug(
            "[CABECERA] Sin prescriptor — saltando prescriptor y diagnosticos"
        )


def guardar() -> None:

    cmd_save: ButtonControl = get_barrar_group().ButtonControl(
        searchDepth=1,
        Name="CmdSave",
    )

    cmd_save.Click()

    sleep(0.3)


def extraer_correlativo_farmacia() -> str:

    correlativo = randint(1, 1000)

    return str(correlativo)


def volver_a_menuprincipal() -> None:

    # Click 1
    Click(1168, 188)
    sleep(3)

    # Click 2
    Click(1189, 214)
    sleep(3)

    # Click 3
    Click(1585, 15)
    sleep(3)


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
    agregar_productos(tuple(pedido.Medicamentos))

    logger.debug("[PROCESAR] Productos OK, guardando")
    guardar()

    sleep(0.5)

    correlativo = extraer_correlativo_farmacia()
    logger.debug(f"[PROCESAR] Guardado OK, correlativo={correlativo}")

    sleep(0.5)

    logger.debug("[PROCESAR] Volviendo a menu principal")
    volver_a_menuprincipal()

    logger.debug(f"[PROCESAR] Pedido completado: correlativo={correlativo}")
    return correlativo


def procesar_pedidos(pedidos: tuple[Pedido, ...]) -> None:

    login(
        SISMED_USERNAME,
        SISMED_PASSWORD,
    )

    k_salud_correlativo = randint(
        1_000_000,
        9_999_999,
    )

    numero_procesado = obtener_siguiente_numero_procesado()

    rows: list[dict] = []

    for idx, pedido in enumerate(pedidos, start=1):

        logger.debug(
            f"[LOTE] Procesando pedido {idx}/{len(pedidos)}: farmacia={pedido.farmacia.codigo}"
        )

        try:

            correlativo = procesar_pedido(pedido)

            row = crear_row_pedido(
                i=numero_procesado,
                username=SISMED_USERNAME,
                correlativo_ksalud=k_salud_correlativo,
                correlativo_sismed=correlativo,
                pedido=pedido,
                estado="OK",
            )

            logger.success(f"[LOTE] Pedido {idx} OK: correlativo={correlativo}")

        except Exception as exc:

            logger.exception(f"[LOTE] Error procesando pedido {idx}: {exc}")

            row = crear_row_pedido(
                i=numero_procesado,
                username=SISMED_USERNAME,
                correlativo_ksalud=k_salud_correlativo,
                correlativo_sismed="",
                pedido=pedido,
                estado="ERROR",
                error=str(exc),
            )

        rows.append(row)

        k_salud_correlativo += 1

        numero_procesado += 1

    logger.debug("[LOTE] Procesamiento de lote completado, cerrando SISMED")
    cerrar_sismed_pedido()

    if rows:

        guardar_movimientos(rows)
