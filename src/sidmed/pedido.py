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

    Click(355, 115)

    get_system_info_panel().SendKeys("{RIGHT}{Enter}")

    seleccionar_farmacia_por_codigo(pedido.farmacia.codigo)

    sleep(1)

    for _ in range(2):
        SendKeys("{DOWN}")

    SendKeys("{TAB}")

    SendKeys("{Enter}")

    sleep(0.5)


def rellenar_fua(pedido: Pedido) -> None:

    input_fua: EditControl = get_registro_pedido_window().EditControl(
        searchDepth=1,
        Name="Txtfua",
    )

    escribir_input(
        input_fua,
        pedido.fua,
    )


def rellenar_ups(codigo_ups: str) -> None:

    sleep(1)

    Click(730, 388)

    sleep(1)

    Click(1090, 345)

    sleep(0.5)

    SendKeys(
        "301"
    )  # NOTE: por ahora se asume que siempre se ingresa el ups 301 que significa consulta externa, para mas adelante si agregagan el campo de ups es ndada mas caambiar el senkeys

    sleep(1)

    accept_button: ButtonControl = get_registro_pedido_window().ButtonControl(
        Name="Aceptar"
    )

    if not accept_button.Exists(3):

        accept_button = ButtonControl(Name="Aceptar")

    if accept_button.Exists(3):

        accept_button.Click()

    else:

        raise Exception("No se encontró botón 'Aceptar' en UPS")


def manejar_forma_pago(pedido: Pedido) -> None:

    tipo = pedido.forma_pago

    if tipo == FormaPago.SIS:

        rellenar_fua(pedido)

    elif tipo == FormaPago.INTERVENCION_SANITARIA:

        rellenar_ups(pedido.ups_codigo)

    elif tipo == FormaPago.CONTADO:

        pass

    else:

        raise ValueError(f"Forma de pago no soportada: {pedido.forma_pago.value}")


def rellenar_cabecera(
    pedido: Pedido,
) -> None:

    seleccionar_combo_por_texto_con_autoenter(
        "CboDato",
        pedido.forma_pago.value,
    )

    manejar_forma_pago(pedido)

    seleccionar_combo_por_texto(
        "cmbTipoReceta",
        pedido.tipo_receta.value,
    )

    Click(770, 410)

    seleccionar_cliente(pedido.cliente.codigo)

    presc: EditControl = get_registro_pedido_window().EditControl(Name="TxtColPresc")

    escribir_input(
        presc,
        pedido.prescriptor.codigo,
    )

    presc.SendKeys("{Enter}")

    rellenar_diagnosticos(
        get_registro_pedido_window(),
        [d.codigo for d in pedido.diagnosticos],
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

    navegar_a_pedidos(pedido)

    rellenar_cabecera(pedido)

    agregar_productos(tuple(pedido.Medicamentos))

    guardar()

    sleep(0.5)

    correlativo = extraer_correlativo_farmacia()

    sleep(0.5)

    volver_a_menuprincipal()

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

    for pedido in pedidos:

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

        except Exception as exc:

            logger.exception("Error procesando un pedido.")

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

    cerrar_sismed_pedido()

    if rows:

        guardar_movimientos(rows)
